# entidade.py
import math
import psycopg2
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

PER_PAGE = 15

# ======================
# VIEWS (TELAS)
# ======================

def view_entidadeCad():
    return render_template('entidadeCad.html')

def view_entidadeAlt():
    """Lista + edição inline quando vier ?id= """
    conn = conectar_bd()
    itens, registro = [], None
    sel_id = request.args.get('id')

    if conn:
        cur = conn.cursor()
        # lista últimas 200 por nome
        cur.execute('SELECT "idEntidade","nomEntidade" FROM "tbentidade" ORDER BY "nomEntidade" ASC LIMIT 200')
        itens = cur.fetchall()

        if sel_id:
            cur.execute('SELECT "idEntidade","nomEntidade" FROM "tbentidade" WHERE "idEntidade"=%s', (int(sel_id),))
            row = cur.fetchone()
            if row:
                registro = {"idEntidade": row[0], "nomEntidade": row[1]}
        conn.close()

    return render_template('entidadeAlt.html', itens=itens, registro=registro)

def view_entidadeExc():
    """Lista + confirmação quando vier ?id= """
    conn = conectar_bd()
    itens, registro = [], None
    sel_id = request.args.get('id')

    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idEntidade","nomEntidade" FROM "tbentidade" ORDER BY "nomEntidade" ASC LIMIT 200')
        itens = cur.fetchall()

        if sel_id:
            cur.execute('SELECT "idEntidade","nomEntidade" FROM "tbentidade" WHERE "idEntidade"=%s', (int(sel_id),))
            row = cur.fetchone()
            if row:
                registro = {"idEntidade": row[0], "nomEntidade": row[1]}
        conn.close()

    return render_template('entidadeExc.html', itens=itens, registro=registro)

# ======================
# AÇÕES (POST)
# ======================

def cadastrar_entidade():
    if request.method != 'POST':
        return redirect(url_for('entidadeCad'))

    nome = (request.form.get('nomEntidade') or '').strip()
    if not nome:
        flash('❌ Informe o nome da entidade.', 'danger')
        return redirect(url_for('entidadeCad'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.', 'danger')
        return redirect(url_for('entidadeCad'))

    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO "tbentidade" ("nomEntidade") VALUES (%s)', (nome,))
        conn.commit()
        flash('✅ Entidade cadastrada com sucesso!', 'success')
        return redirect(url_for('entidadeCad'))
    except Exception as e:
        try: conn.rollback()
        except: pass
        print('Erro ao cadastrar entidade:', e)
        flash('❌ Não foi possível cadastrar.', 'danger')
        return redirect(url_for('entidadeCad'))
    finally:
        try: conn.close()
        except: pass

def alterar_entidade():
    if request.method != 'POST':
        return redirect(url_for('entidadeAlt'))

    idEnt = request.form.get('idEntidade')
    nome  = (request.form.get('nomEntidade') or '').strip()

    if not idEnt or not nome:
        flash('❌ Dados insuficientes.', 'danger')
        return redirect(url_for('entidadeAlt'))

    try:
        idEnt = int(idEnt)
    except:
        flash('❌ ID inválido.', 'danger')
        return redirect(url_for('entidadeAlt'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.', 'danger')
        return redirect(url_for('entidadeAlt'))

    try:
        cur = conn.cursor()
        cur.execute('UPDATE "tbentidade" SET "nomEntidade"=%s WHERE "idEntidade"=%s', (nome, idEnt))
        conn.commit()
        flash('✅ Entidade alterada com sucesso!', 'success')
        return redirect(url_for('entidadeAlt'))
    except Exception as e:
        try: conn.rollback()
        except: pass
        print('Erro ao alterar entidade:', e)
        flash('❌ Não foi possível alterar.', 'danger')
        return redirect(url_for('entidadeAlt'))
    finally:
        try: conn.close()
        except: pass

def excluir_entidade():
    if request.method != 'POST':
        return redirect(url_for('entidadeExc'))

    idEnt = request.form.get('idEntidade')
    if not idEnt:
        flash('❌ Selecione um registro.', 'danger')
        return redirect(url_for('entidadeExc'))

    try:
        idEnt = int(idEnt)
    except:
        flash('❌ ID inválido.', 'danger')
        return redirect(url_for('entidadeExc'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.', 'danger')
        return redirect(url_for('entidadeExc'))

    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "tbentidade" WHERE "idEntidade"=%s', (idEnt,))
        conn.commit()
        flash('✅ Entidade excluída!', 'success')
        return redirect(url_for('entidadeExc'))
    except psycopg2.Error as e:
        try: conn.rollback()
        except: pass
        print('Erro ao excluir entidade:', e)
        flash('❌ Não foi possível excluir (registro em uso?).', 'danger')
        return redirect(url_for('entidadeExc'))
    finally:
        try: conn.close()
        except: pass

# ======================
# CONSULTA GERAL
# ======================

def _ler_filtros():
    src = request.args if request.method == 'GET' else request.form
    F = type('F', (), {})()
    F.nome = (src.get('nome') or '').strip()
    try:
        page = int(src.get('page','1'))
    except:
        page = 1
    if page < 1: page = 1
    return F, page

def _executar_consulta(F, page):
    rows, total = [], 0
    conn = conectar_bd()
    if not conn:
        return rows, total
    try:
        params = []
        where = ['TRUE']
        if F.nome:
            where.append('UPPER(e."nomEntidade") LIKE UPPER(%s)')
            params.append(f'%{F.nome}%')

        where_sql = ' AND '.join(where)
        base = f'''
          SELECT e."idEntidade", e."nomEntidade"
            FROM "tbentidade" e
           WHERE {where_sql}
        '''

        cur = conn.cursor()
        cur.execute(f'SELECT COUNT(*) FROM ({base}) X', params)
        total = cur.fetchone()[0] or 0

        limit = PER_PAGE
        offset = (page-1)*PER_PAGE
        cur.execute(f'''
          {base}
          ORDER BY e."nomEntidade" ASC
          LIMIT %s OFFSET %s
        ''', params + [limit, offset])

        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            rows.append({cols[i]: r[i] for i in range(len(cols))})
    finally:
        try: conn.close()
        except: pass
    return rows, total

def pagina_conEntidade():
    from urllib.parse import urlencode
    F, page = _ler_filtros()
    rows, total = _executar_consulta(F, page)
    pages = max(1, math.ceil(total / PER_PAGE))

    def pagina_url(p):
        q = {'nome':F.nome, 'page':p}
        return url_for('conEntidade') + '?' + urlencode(q)

    return render_template('conEntidade.html',
                           filtros=F, rows=rows, total=total,
                           page=page, pages=pages, pagina_url=pagina_url)

def conFiltroEntidade():
    return pagina_conEntidade()
