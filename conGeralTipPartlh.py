# conGeralTipPartlh.py
import math
import psycopg2
from flask import request, render_template, url_for
from urllib.parse import urlencode
from conexao_bd import conectar_bd

PER_PAGE = 15
CAT_POLITICA = 1
CAT_MENSALID = 3

def _carregar_selects():
    """Categorias (exceto 1 e 3), unidades; política NÃO se aplica à partilha."""
    conn = conectar_bd()
    categorias = unidades = []
    if conn:
        cur = conn.cursor()
        cur.execute('''
          SELECT "idCatgFinanc","nomCatgFinanc"
            FROM "tbcatgfinanc"
           WHERE "idCatgFinanc" NOT IN (%s,%s)
           ORDER BY "nomCatgFinanc"
        ''', (CAT_POLITICA, CAT_MENSALID))
        categorias = cur.fetchall()
        cur.execute('SELECT "idTipUnEqv","nomUnEqv" FROM "tbtipuneqv" ORDER BY "nomUnEqv"')
        unidades = cur.fetchall()
        conn.close()
    return categorias, unidades

def _ler_filtros():
    src = request.args if request.method == 'GET' else request.form
    f = type('F', (), {})()
    f.busca        = (src.get('busca') or '').strip()
    f.idCatgFinanc = src.get('idCatgFinanc') or ''
    f.idTipUnEqv   = src.get('idTipUnEqv') or ''
    try: page = int(src.get('page', '1'))
    except: page = 1
    if page < 1: page = 1
    return f, page

def _montar_where(f, params):
    where = ['t."idCatgFinanc" NOT IN (%s,%s)']
    params += [CAT_POLITICA, CAT_MENSALID]
    if f.busca:
        where.append('UPPER(t."nomFinanc") LIKE UPPER(%s)')
        params.append(f'%{f.busca}%')
    if f.idCatgFinanc:
        where.append('t."idCatgFinanc" = %s')
        params.append(f.idCatgFinanc)
    if f.idTipUnEqv:
        where.append('COALESCE(t."idTipUnEqv",0) = %s')
        params.append(f.idTipUnEqv)
    return ' AND '.join(where)

def _query_base(where):
    return f'''
      SELECT
        t."idTipFinanc"   AS idtipfinanc,
        t."nomFinanc"     AS nomfinanc,
        c."nomCatgFinanc" AS nom_catg,
        u."nomUnEqv"      AS nom_uneqv,
        t."merecto"       AS merecto,
        t."valEqv"        AS valeqv
      FROM "tbtipfinanc" t
      LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc" = t."idCatgFinanc"
      LEFT JOIN "tbtipuneqv"   u ON u."idTipUnEqv"   = t."idTipUnEqv"
      WHERE {where}
    '''


def _pagina_url_factory(f):
    def pagina_url(p):
        q = {
            'busca': f.busca or '',
            'idCatgFinanc': f.idCatgFinanc or '',
            'idTipUnEqv': f.idTipUnEqv or '',
            'page': p
        }
        return url_for('conGeralTipPartlh') + '?' + urlencode(q)
    return pagina_url

def _executar_consulta(f, page):
    conn = conectar_bd()
    rows, total = [], 0
    if not conn:
        return rows, total
    params = []
    where = _montar_where(f, params)
    base  = _query_base(where)
    try:
        cur = conn.cursor()
        cur.execute(f'SELECT COUNT(*) FROM ({base}) X', params)
        total = cur.fetchone()[0] or 0
        limit  = PER_PAGE
        offset = (page-1) * PER_PAGE
        cur.execute(f'''
            {base}
            ORDER BY t."idTipFinanc" DESC
            LIMIT %s OFFSET %s
        ''', params + [limit, offset])
        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            rows.append({cols[i]: r[i] for i in range(len(cols))})
        conn.close()
    except Exception as e:
        conn.close()
        print("Erro em conGeralTipPartlh:", e)
    return rows, total

# --------- PÁGINAS ---------
def pagina_conGeralTipPartlh():
    f, page = _ler_filtros()
    categorias, unidades = _carregar_selects()
    rows, total = _executar_consulta(f, page)
    pages = max(1, math.ceil(total / PER_PAGE))
    return render_template(
        'conGeralTipPartlh.html',
        filtros=f, rows=rows, total=total,
        page=page, pages=pages,
        categorias=categorias, unidades=unidades,
        pagina_url=_pagina_url_factory(f)
    )

def conFiltroTipPartlh():
    return pagina_conGeralTipPartlh()
