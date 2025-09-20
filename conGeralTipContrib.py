# conGeralTipContrib.py
import math
import psycopg2
from flask import request, render_template, url_for
from urllib.parse import urlencode
from conexao_bd import conectar_bd

PER_PAGE = 15

def _carregar_selects():
    """Carrega selects usados nos filtros."""
    conn = conectar_bd()
    categorias = politicas = unidades = []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idCatgFinanc","nomCatgFinanc" FROM "tbcatgfinanc" ORDER BY "nomCatgFinanc"')
        categorias = cur.fetchall()
        cur.execute('SELECT "idPolPub","nomPolPub" FROM "tbpolitpub" ORDER BY "nomPolPub"')
        politicas = cur.fetchall()
        cur.execute('SELECT "idTipUnEqv","nomUnEqv" FROM "tbtipuneqv" ORDER BY "nomUnEqv"')
        unidades = cur.fetchall()
        conn.close()
    return categorias, politicas, unidades

def _ler_filtros():
    src = request.args if request.method == 'GET' else request.form
    f = type('F', (), {})()
    f.busca        = (src.get('busca') or '').strip()         # texto livre em nomFinanc
    f.idCatgFinanc = src.get('idCatgFinanc') or ''            # categoria
    f.idPolPub     = src.get('idPolPub') or ''                # política pública
    f.idTipUnEqv   = src.get('idTipUnEqv') or ''              # unidade eqv.
    try: page = int(src.get('page', '1'))
    except: page = 1
    if page < 1: page = 1
    return f, page

def _montar_where(f, params):
    where = ['TRUE']
    if f.busca:
        where.append('UPPER(t."nomFinanc") LIKE UPPER(%s)')
        params.append(f'%{f.busca}%')
    if f.idCatgFinanc:
        where.append('t."idCatgFinanc" = %s')
        params.append(f.idCatgFinanc)
    if f.idPolPub:
        where.append('COALESCE(t."idPolPub",0) = %s')
        params.append(f.idPolPub)
    if f.idTipUnEqv:
        where.append('COALESCE(t."idTipUnEqv",0) = %s')
        params.append(f.idTipUnEqv)
    return ' AND '.join(where)

def _query_base(where):
    return f'''
      SELECT
        t."idTipFinanc"  AS idtipfinanc,
        t."nomFinanc"    AS nomfinanc,
        c."nomCatgFinanc" AS nom_catg,
        p."nomPolPub"     AS nom_pol,
        t."valPolPub"     AS valpolpub,
        t."percVal"       AS percval,
        u."nomUnEqv"      AS nom_uneqv,
        t."merecto"       AS merecto,
        t."valEqv"        AS valeqv
      FROM "tbtipfinanc" t
      LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc" = t."idCatgFinanc"
      LEFT JOIN "tbpolitpub"   p ON p."idPolPub"     = t."idPolPub"
      LEFT JOIN "tbtipuneqv"   u ON u."idTipUnEqv"   = t."idTipUnEqv"
      WHERE {where}
    '''

def _pagina_url_factory(f):
    def pagina_url(p):
        q = {
            'busca': f.busca or '',
            'idCatgFinanc': f.idCatgFinanc or '',
            'idPolPub': f.idPolPub or '',
            'idTipUnEqv': f.idTipUnEqv or '',
            'page': p
        }
        return url_for('conGeralTipContrib') + '?' + urlencode(q)
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
        print("Erro em conGeralTipContrib:", e)
    return rows, total

# --------- PÁGINAS ---------
def pagina_conGeralTipContrib():
    f, page = _ler_filtros()
    categorias, politicas, unidades = _carregar_selects()
    rows, total = _executar_consulta(f, page)
    pages = max(1, math.ceil(total / PER_PAGE))
    return render_template(
        'conGeralTipContrib.html',
        filtros=f, rows=rows, total=total,
        page=page, pages=pages,
        categorias=categorias, politicas=politicas, unidades=unidades,
        pagina_url=_pagina_url_factory(f)
    )

def conFiltroTipContrib():
    return pagina_conGeralTipContrib()
