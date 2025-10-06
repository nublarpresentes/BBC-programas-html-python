# tipRecpsa.py
import math
import psycopg2
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

PER_PAGE = 15

# -------------------------
# Utilitários
# -------------------------
def _listar_politicas():
    conn = conectar_bd()
    politicas = []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idPolPub","nomPolPub" FROM "tbpolitpub" ORDER BY "nomPolPub" ASC')
        politicas = cur.fetchall()
        conn.close()
    return politicas

def listar_tiprecpsa():
    """Lista todos os tipos de recompensa (com nome de política, se houver)."""
    conn = conectar_bd()
    itens = []
    if conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t."idTipRecpsa", t."nomTipRecpsa", t."idPolPub",
                   p."nomPolPub"
              FROM "tbtiprecpsa" t
              LEFT JOIN "tbpolitpub" p ON p."idPolPub"=t."idPolPub"
             ORDER BY t."idTipRecpsa" DESC
        """)
        itens = cur.fetchall()
        conn.close()
    return itens

def pegar_tiprecpsa(id_):
    if not id_:
        return None
    conn = conectar_bd()
    if not conn:
        return None
    cur = conn.cursor()
    cur.execute("""
        SELECT t."idTipRecpsa", t."nomTipRecpsa", t."idPolPub"
          FROM "tbtiprecpsa" t
         WHERE t."idTipRecpsa"=%s
    """, (id_,))
    reg = cur.fetchone()
    conn.close()
    return reg

# -------------------------
# VIEWS (páginas)
# -------------------------
def view_tipRecpsaCad():
    politicas = _listar_politicas()
    return render_template('tipRecpsaCad.html', politicas=politicas)

def view_tipRecpsaAlt():
    politicas = _listar_politicas()
    itens = listar_tiprecpsa()
    sel_id = request.args.get('id')
    registro = pegar_tiprecpsa(sel_id) if sel_id else None
    return render_template('tipRecpsaAlt.html',
                           politicas=politicas, itens=itens, registro=registro)

def view_tipRecpsaExc():
    politicas = _listar_politicas()
    itens = listar_tiprecpsa()
    sel_id = request.args.get('id')
    registro = pegar_tiprecpsa(sel_id) if sel_id else None
    return render_template('tipRecpsaExc.html',
                           politicas=politicas, itens=itens, registro=registro)

# -------------------------
# AÇÕES (POST)
# -------------------------
def cadastrar_tiprecpsa():
    if request.method != 'POST':
        return redirect(url_for('tipRecpsaCad'))

    nomTipRecpsa = (request.form.get('nomTipRecpsa') or '').strip()
    idPolPub  = request.form.get('idPolPub') or None

    if not nomTipRecpsa:
        flash('❌ Informe o nome da recompensa.')
        return redirect(url_for('tipRecpsaCad'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.')
        return redirect(url_for('tipRecpsaCad'))

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO "tbtiprecpsa" ("nomTipRecpsa","idPolPub")
            VALUES (%s, %s)
        """, (nomTipRecpsa, int(idPolPub) if idPolPub else None))
        conn.commit()
        conn.close()
        flash('✅ Tipo de recompensa cadastrado com sucesso!', 'success')
        return redirect(url_for('tipRecpsaCad'))
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Erro ao cadastrar tipo de recompensa:", e)
        flash('❌ Erro ao cadastrar.', 'danger')
        return redirect(url_for('tipRecpsaCad'))

def alterar_tiprecpsa():
    if request.method != 'POST':
        return redirect(url_for('tipRecpsaAlt'))

    idTipRecpsa = request.form.get('idTipRecpsa')
    nomTipRecpsa   = (request.form.get('nomTipRecpsa') or '').strip()
    idPolPub    = request.form.get('idPolPub') or None

    if not idTipRecpsa or not nomTipRecpsa:
        flash('❌ Dados insuficientes.')
        return redirect(url_for('tipRecpsaAlt'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.')
        return redirect(url_for('tipRecpsaAlt'))

    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE "tbtiprecpsa"
               SET "nomTipRecpsa"=%s, "idPolPub"=%s
             WHERE "idTipRecpsa"=%s
        """, (nomTipRecpsa, int(idPolPub) if idPolPub else None, int(idTipRecpsa)))
        conn.commit()
        conn.close()
        flash('✅ Tipo de recompensa alterado com sucesso!', 'success')
        return redirect(url_for('tipRecpsaAlt'))
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Erro ao alterar tipo de recompensa:", e)
        flash('❌ Erro ao alterar.', 'danger')
        return redirect(url_for('tipRecpsaAlt'))

def excluir_tiprecpsa():
    if request.method != 'POST':
        return redirect(url_for('tipRecpsaExc'))

    idTipRecpsa = request.form.get('idTipRecpsa')
    if not idTipRecpsa:
        flash('❌ Selecione um registro para excluir.')
        return redirect(url_for('tipRecpsaExc'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.')
        return redirect(url_for('tipRecpsaExc'))

    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "tbtiprecpsa" WHERE "idTipRecpsa"=%s', (int(idTipRecpsa),))
        conn.commit()
        conn.close()
        flash('✅ Tipo de recompensa excluído com sucesso!', 'success')
        return redirect(url_for('tipRecpsaExc'))
    except psycopg2.Error as e:
        conn.rollback()
        conn.close()
        print("Erro ao excluir tipo de recompensa:", e)
        flash('❌ Não foi possível excluir (FK?).', 'danger')
        return redirect(url_for('tipRecpsaExc'))

# -------------------------
# Consulta geral com filtros
# -------------------------
def _ler_filtros():
    src = request.args if request.method == 'GET' else request.form
    filtros = type('F', (), {})()
    filtros.nome    = (src.get('nome') or '').strip()
    filtros.idPolPub = (src.get('idPolPub') or '').strip()
    try:
        page = int(src.get('page', '1'))
    except:
        page = 1
    if page < 1: page = 1
    return filtros, page

def _montar_where(filtros, params):
    where = ['TRUE']
    if filtros.nome:
        where.append('UPPER(t."nomTipRecpsa") LIKE UPPER(%s)')
        params.append(f'%{filtros.nome}%')
    if filtros.idPolPub:
        where.append('t."idPolPub"=%s')
        params.append(int(filtros.idPolPub))
    return ' AND '.join(where)

def _executar_consulta(filtros, page):
    conn = conectar_bd()
    rows, total = [], 0
    if not conn:
        return rows, total
    params = []
    where = _montar_where(filtros, params)
    base = f"""
        SELECT t."idTipRecpsa", t."nomTipRecpsa", t."idPolPub", p."nomPolPub"
          FROM "tbtiprecpsa" t
          LEFT JOIN "tbpolitpub" p ON p."idPolPub"=t."idPolPub"
         WHERE {where}
    """
    try:
        cur = conn.cursor()
        cur.execute(f'SELECT COUNT(*) FROM ({base}) X', params)
        total = cur.fetchone()[0] or 0

        limit = PER_PAGE
        offset = (page-1)*PER_PAGE
        cur.execute(f"""
            {base}
            ORDER BY t."nomTipRecpsa" ASC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            rows.append({cols[i]: r[i] for i in range(len(cols))})
        conn.close()
    except Exception as e:
        conn.close()
        print("Erro em consulta geral tiprecpsa:", e)
    return rows, total

def pagina_conGeralTipRecpsa():
    filtros, page = _ler_filtros()
    politicas = _listar_politicas()
    rows, total = _executar_consulta(filtros, page)
    pages = max(1, math.ceil(total / PER_PAGE))

    # helper pra paginação no template
    from urllib.parse import urlencode
    def pagina_url(p):
        q = {
            'nome': filtros.nome,
            'idPolPub': filtros.idPolPub,
            'page': p
        }
        return url_for('conGeralTipRecpsa') + '?' + urlencode(q)

    return render_template('conGeralTipRecpsa.html',
                           politicas=politicas,
                           filtros=filtros,
                           rows=rows,
                           total=total,
                           page=page,
                           pages=pages,
                           pagina_url=pagina_url)

def conFiltroTipRecpsa():
    return pagina_conGeralTipRecpsa()
