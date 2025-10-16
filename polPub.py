# polPub.py
import math
import psycopg2
from urllib.parse import urlencode
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd


PER_PAGE = 15  # paginação da consulta

# ---------- Helpers (dados para selects) ----------
def _listar_entidades():
    """Lista entidades para o <select> (id, nome)."""
    entidades = []
    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idEntidade","nomEntidade" FROM "tbentidade" ORDER BY "nomEntidade"')
        entidades = cur.fetchall()
        conn.close()
    return entidades

def listar_politpub():
    """Lista políticas públicas para a grade (mais recentes primeiro)."""
    itens = []
    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT "idPolPub","nomPolPub","IdEntidade","valor","perct"
            FROM "tbpolitpub"
            ORDER BY "idPolPub" DESC
        ''')
        itens = cur.fetchall()
        conn.close()
    return itens

def pegar_politpub(id_):
    """Busca 1 registro pelo id."""
    if not id_:
        return None
    conn = conectar_bd()
    reg = None
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT "idPolPub","nomPolPub","IdEntidade","valor","perct"
            FROM "tbpolitpub"
            WHERE "idPolPub" = %s
        ''', (id_,))
        reg = cur.fetchone()
        conn.close()
    return reg

# ---------- Inclusão ----------
def cadastrar_politpub():
    if request.method == 'POST':
        nomPolPub  = request.form.get('nomPolPub','').strip()
        IdEntidade = request.form.get('IdEntidade') or None
        valor      = request.form.get('valor') or None
        perct      = request.form.get('perct') or None

        # validações simples
        if not nomPolPub:
            entidades = _listar_entidades()
            return render_template('politPubCad.html',
                                   message='❌ Informe o nome da Política Pública.',
                                   entidades=entidades)

        # conversões numéricas (aceita vazio -> NULL)
        try:
            valor = float(valor) if valor not in (None,'') else None
        except:
            valor = None
        try:
            perct = float(perct) if perct not in (None,'') else None
        except:
            perct = None

        conn = conectar_bd()
        if not conn:
            entidades = _listar_entidades()
            return render_template('politPubCad.html',
                                   message='❌ Erro de conexão com BD.',
                                   entidades=entidades)
        try:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO "tbpolitpub" ("nomPolPub","IdEntidade","valor","perct")
                VALUES (%s,%s,%s,%s)
            ''', (nomPolPub, IdEntidade, valor, perct))
            conn.commit()
            conn.close()
            flash('✅ Política Pública cadastrada com sucesso!', 'success')
            return redirect(url_for('politPubCad'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            entidades = _listar_entidades()
            return render_template('politPubCad.html',
                                   message=f'❌ Erro ao cadastrar: {e.pgerror}',
                                   entidades=entidades)

# ---------- Alteração ----------
def alterar_politpub():
    if request.method == 'POST':
        idPolPub   = request.form.get('idPolPub')
        nomPolPub  = request.form.get('nomPolPub','').strip()
        IdEntidade = request.form.get('IdEntidade') or None
        valor      = request.form.get('valor') or None
        perct      = request.form.get('perct') or None

        if not idPolPub:
            flash('❌ Registro não informado.', 'danger')
            return redirect(url_for('politPubAlt'))

        try:
            valor = float(valor) if valor not in (None,'') else None
        except:
            valor = None
        try:
            perct = float(perct) if perct not in (None,'') else None
        except:
            perct = None

        conn = conectar_bd()
        if not conn:
            flash('❌ Erro de conexão com BD.', 'danger')
            return redirect(url_for('politPubAlt'))

        try:
            cur = conn.cursor()
            cur.execute('''
                UPDATE "tbpolitpub"
                   SET "nomPolPub"=%s,
                       "IdEntidade"=%s,
                       "valor"=%s,
                       "perct"=%s
                 WHERE "idPolPub"=%s
            ''', (nomPolPub, IdEntidade, valor, perct, idPolPub))
            conn.commit()
            conn.close()
            flash('✅ Alterado com sucesso!', 'success')
            return redirect(url_for('politPubAlt'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            flash(f'❌ Erro ao alterar: {e.pgerror}', 'danger')
            return redirect(url_for('politPubAlt'))

# ---------- Exclusão ----------
def excluir_politpub():
    if request.method == 'POST':
        idPolPub = request.form.get('idPolPub')
        if not idPolPub:
            flash('❌ Registro não informado.', 'danger')
            return redirect(url_for('politPubExc'))

        conn = conectar_bd()
        if not conn:
            flash('❌ Erro de conexão com BD.', 'danger')
            return redirect(url_for('politPubExc'))

        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM "tbpolitpub" WHERE "idPolPub"=%s', (idPolPub,))
            conn.commit()
            conn.close()
            flash('✅ Excluído com sucesso!', 'success')
            return redirect(url_for('politPubExc'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            flash(f'❌ Não foi possível excluir (FK?): {e.pgerror}', 'danger')
            return redirect(url_for('politPubExc'))

# =========================================================
# CONSULTA — POLÍTICAS PÚBLICAS (filtros + paginação)
# =========================================================
def _pp_ler_filtros():
    src = request.args if request.method == 'GET' else request.form
    F = type('F', (), {})()
    F.nome       = (src.get('nome') or '').strip()
    F.idEntidade = (src.get('idEntidade') or '').strip()
    F.valMin     = (src.get('valMin') or '').strip().replace(',','.')
    F.valMax     = (src.get('valMax') or '').strip().replace(',','.')
    F.percMin    = (src.get('percMin') or '').strip().replace(',','.')
    F.percMax    = (src.get('percMax') or '').strip().replace(',','.')
    try:
        page = int(src.get('page', '1'))
    except:
        page = 1
    if page < 1:
        page = 1
    return F, page

def _pp_where(F, params):
    w = ['TRUE']
    if F.nome:
        w.append('UPPER(p."nomPolPub") LIKE UPPER(%s)')
        params.append(f'%{F.nome}%')
    if F.idEntidade:
        w.append('p."IdEntidade" = %s')
        params.append(int(F.idEntidade))
    if F.valMin:
        try: w.append('COALESCE(p.valor,0) >= %s'); params.append(float(F.valMin))
        except: pass
    if F.valMax:
        try: w.append('COALESCE(p.valor,0) <= %s'); params.append(float(F.valMax))
        except: pass
    if F.percMin:
        try: w.append('COALESCE(p.perct,0) >= %s'); params.append(float(F.percMin))
        except: pass
    if F.percMax:
        try: w.append('COALESCE(p.perct,0) <= %s'); params.append(float(F.percMax))
        except: pass
    return ' AND '.join(w)

def _pp_query_base(where):
    return f'''
      SELECT
        p."idPolPub",
        p."nomPolPub",
        p."IdEntidade",
        COALESCE(e."nomEntidade",'(s/ entidade)') AS nom_entidade,
        COALESCE(p.valor,0) AS valor,
        COALESCE(p.perct,0) AS perct
      FROM "tbpolitpub" p
      LEFT JOIN "tbentidade" e ON e."idEntidade" = p."IdEntidade"
      WHERE {where}
    '''

def _pp_pagina_url_factory(F):
    def pagina_url(p):
        q = {
            'nome': F.nome or '',
            'idEntidade': F.idEntidade or '',
            'valMin': F.valMin or '',
            'valMax': F.valMax or '',
            'percMin': F.percMin or '',
            'percMax': F.percMax or '',
            'page': p
        }
        return url_for('conPolitPub') + '?' + urlencode(q)
    return pagina_url

def _pp_executar(F, page):
    rows, total = [], 0
    conn = conectar_bd()
    if not conn:
        return rows, total
    try:
        params = []
        where = _pp_where(F, params)
        base = _pp_query_base(where)

        cur = conn.cursor()
        # total
        cur.execute(f'SELECT COUNT(*) FROM ({base}) X', params)
        total = cur.fetchone()[0] or 0

        # paginação
        limit = PER_PAGE
        offset = (page - 1) * PER_PAGE

        cur.execute(f'''
          {base}
          ORDER BY p."nomPolPub" ASC
          LIMIT %s OFFSET %s
        ''', params + [limit, offset])

        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            rows.append({cols[i]: r[i] for i in range(len(cols))})
    finally:
        try: conn.close()
        except: pass
    return rows, total

def pagina_conPolitPub():
    F, page = _pp_ler_filtros()
    entidades = _listar_entidades()
    rows, total = _pp_executar(F, page)
    pages = max(1, math.ceil(total / PER_PAGE))
    return render_template(
        'politPubCon.html',
        filtros=F,
        entidades=entidades,
        rows=rows, total=total,
        page=page, pages=pages,
        pagina_url=_pp_pagina_url_factory(F)
    )

# --- CONSULTA (LISTAGEM) DE POLÍTICAS PÚBLICAS ---

PER_PAGE = 15

def _carregar_selects_con():
    # entidades p/ filtro
    return _listar_entidades()

def _ler_filtros_con():
    src = request.args if request.method == 'GET' else request.form
    F = type('F', (), {})()
    F.idEntidade = (src.get('idEntidade') or '').strip()
    F.nome       = (src.get('nome') or '').strip()
    F.valMin     = (src.get('valMin') or '').strip().replace(',','.')
    F.valMax     = (src.get('valMax') or '').strip().replace(',','.')
    try:
        page = int(src.get('page','1'))
    except:
        page = 1
    if page < 1: page = 1
    return F, page

def _montar_where_con(F, params):
    w = ['TRUE']
    if F.idEntidade:
        w.append('"IdEntidade" = %s'); params.append(int(F.idEntidade))
    if F.nome:
        w.append('UPPER("nomPolPub") LIKE UPPER(%s)'); params.append(f'%{F.nome}%')
    if F.valMin:
        try: v=float(F.valMin); w.append('"valor" >= %s'); params.append(v)
        except: pass
    if F.valMax:
        try: v=float(F.valMax); w.append('"valor" <= %s'); params.append(v)
        except: pass
    return ' AND '.join(w)

def _executar_consulta_con(F, page):
    rows, total = [], 0
    conn = conectar_bd()
    if not conn:
        return rows, total
    try:
        cur = conn.cursor()
        params = []
        where = _montar_where_con(F, params)
        base = f'''
          SELECT p."idPolPub", p."nomPolPub", p."IdEntidade", p."valor", p."perct",
                 e."nomEntidade"
            FROM "tbpolitpub" p
            LEFT JOIN "tbentidade" e ON e."idEntidade" = p."IdEntidade"
           WHERE {where}
        '''
        cur.execute(f'SELECT COUNT(*) FROM ({base}) X', params)
        total = cur.fetchone()[0] or 0

        limit = PER_PAGE
        offset = (page-1)*PER_PAGE
        cur.execute(f'''
          {base}
          ORDER BY p."nomPolPub" ASC
          LIMIT %s OFFSET %s
        ''', params + [limit, offset])

        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            rows.append({cols[i]: r[i] for i in range(len(cols))})
        conn.close()
    except Exception as e:
        try: conn.close()
        except: pass
        print('Erro consulta politpub:', e)
    return rows, total

def pagina_politPubCon():
    filtros, page = _ler_filtros_con()
    entidades = _carregar_selects_con()
    rows, total = _executar_consulta_con(filtros, page)
    pages = max(1, math.ceil(total / PER_PAGE))

    def pagina_url(p):
        q = {
            'idEntidade': filtros.idEntidade,
            'nome': filtros.nome,
            'valMin': filtros.valMin,
            'valMax': filtros.valMax,
            'page': p
        }
        return url_for('politPubCon') + '?' + urlencode(q)

    return render_template(
        'politPubCon.html',      # <<<<<<<<<< usa o SEU template
        entidades=entidades,
        filtros=filtros,
        rows=rows,
        total=total,
        page=page,
        pages=pages,
        pagina_url=pagina_url
    )

def conFiltroPolitPub():
    # apenas reusa a mesma página com os filtros recebidos
    return pagina_politPubCon()
