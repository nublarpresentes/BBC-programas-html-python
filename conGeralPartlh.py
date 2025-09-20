# conGeralPartlh.py
import math
import psycopg2
from flask import request, render_template, url_for
from urllib.parse import urlencode
from conexao_bd import conectar_bd

PER_PAGE = 15

def _carregar_selects():
    """Assentados e Grupos de Partilha (ordem ascendente)."""
    conn = conectar_bd()
    assentados, grupos = [], []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome" ASC')
        assentados = cur.fetchall()
        cur.execute('SELECT "idGrpPartlh","nomGrpParth" FROM "tbgrppartlh" ORDER BY "nomGrpParth" ASC')
        grupos = cur.fetchall()
        conn.close()
    return assentados, grupos

def _ler_filtros():
    """Lê filtros de GET/POST e normaliza."""
    src = request.args if request.method == 'GET' else request.form
    filtros = type('F', (), {})()
    filtros.idAssent    = src.get('idAssent') or ''
    filtros.idGrpPartlh  = src.get('idGrpPartlh') or ''
    filtros.mesIni       = src.get('mesIni') or ''
    filtros.anoIni       = src.get('anoIni') or ''
    filtros.mesFim       = src.get('mesFim') or ''
    filtros.anoFim       = src.get('anoFim') or ''
    try:
        page = int(src.get('page', '1'))
    except:
        page = 1
    if page < 1:
        page = 1
    return filtros, page

def _montar_where(filtros, params):
    """Monta WHERE para PARTILHA (tipFinancCP = 2)."""
    where = ['f."tipFinancCP" = 2']
    if filtros.idAssent:
        where.append('f."idAssent" = %s')
        params.append(filtros.idAssent)
    if filtros.idGrpPartlh:
        where.append('f."idGrpPartlh" = %s')
        params.append(int(filtros.idGrpPartlh))

    # Período: (ano,mes) entre (anoIni,mesIni) e (anoFim,mesFim)
    # dref = 1º dia do mês de (ano,mes) se existirem; senão, usa dtPagto no 1º dia do mês
    if filtros.anoIni and filtros.mesIni and filtros.anoFim and filtros.mesFim:
        where.append("""
             (
               CASE
                 WHEN f."anoFinanc" IS NOT NULL AND f."mesFinanc" IS NOT NULL
                   THEN make_date(f."anoFinanc", f."mesFinanc", 1)
                 ELSE date_trunc('month', f."dtPagto")::date
               END
             ) >= make_date(%s,%s,1)
             AND
             (
               CASE
                 WHEN f."anoFinanc" IS NOT NULL AND f."mesFinanc" IS NOT NULL
                   THEN make_date(f."anoFinanc", f."mesFinanc", 1)
                 ELSE date_trunc('month', f."dtPagto")::date
               END
             ) < (make_date(%s,%s,1) + INTERVAL '1 month')
        """)
        params.extend([int(filtros.anoIni), int(filtros.mesIni),
                       int(filtros.anoFim), int(filtros.mesFim)])

    return ' AND '.join(where) if where else 'TRUE'

def _query_base(where):
    return f'''
      SELECT
         f."idAssent",
         a."nome" AS nome_assent,
         g."nomGrpParth" AS nom_grupo,
         f."mesFinanc" AS mes,
         f."anoFinanc" AS ano,
         f."valFinanc" AS valor,
         f."numParcela" AS num_parc,
         -- data de referência para ordenação/filtro
         CASE
           WHEN f."anoFinanc" IS NOT NULL AND f."mesFinanc" IS NOT NULL
             THEN make_date(f."anoFinanc", f."mesFinanc", 1)
           ELSE date_trunc('month', f."dtPagto")::date
         END AS dref
      FROM "tbfinanc" f
      LEFT JOIN "tbassentado"  a ON a."idAssent"=f."idAssent"
      LEFT JOIN "tbgrppartlh"  g ON g."idGrpPartlh"=f."idGrpPartlh"
      WHERE {where}
    '''

def _pagina_url_factory(filtros):
    """Gera função Jinja para montar URLs de página preservando filtros."""
    def pagina_url(p):
        q = {
            'idAssent': filtros.idAssent or '',
            'idGrpPartlh': filtros.idGrpPartlh or '',
            'mesIni': filtros.mesIni or '',
            'anoIni': filtros.anoIni or '',
            'mesFim': filtros.mesFim or '',
            'anoFim': filtros.anoFim or '',
            'page': p
        }
        return url_for('conGeralPartlh') + '?' + urlencode(q)
    return pagina_url

def _executar_consulta(filtros, page):
    conn = conectar_bd()
    rows, total = [], 0
    if not conn:
        return rows, total

    params = []
    where = _montar_where(filtros, params)
    base = _query_base(where)

    try:
        cur = conn.cursor()
        # total
        cur.execute(f'SELECT COUNT(*) FROM ({base}) T', params)
        total = cur.fetchone()[0] or 0

        # paginação
        limit = PER_PAGE
        offset = (page-1)*PER_PAGE
        cur.execute(f'''
            {base}
            ORDER BY dref DESC, nome_assent ASC
            LIMIT %s OFFSET %s
        ''', params + [limit, offset])

        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            rows.append({cols[i]: r[i] for i in range(len(cols))})
        conn.close()
    except Exception as e:
        try:
            conn.close()
        except:
            pass
        print("Erro em consulta de partilhas:", e)
    return rows, total

# --------- PÁGINAS ---------

def pagina_conGeralPartlh():
    """GET inicial (ou com querystring)."""
    filtros, page = _ler_filtros()
    assentados, grupos = _carregar_selects()
    rows, total = _executar_consulta(filtros, page)
    pages = max(1, math.ceil(total / PER_PAGE))
    return render_template(
        'conGeralPartlh.html',
        assentados=assentados,
        grupos=grupos,
        filtros=filtros,
        rows=rows,
        total=total,
        page=page,
        pages=pages,
        pagina_url=_pagina_url_factory(filtros)
    )

def conFiltroPartlh():
    """Recebe filtros (GET/POST) e renderiza com paginação."""
    return pagina_conGeralPartlh()
