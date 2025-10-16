# recpsa.py
import math
import psycopg2
from datetime import date, datetime
from flask import request, render_template, redirect, url_for, flash
from urllib.parse import urlencode
from conexao_bd import conectar_bd

PER_PAGE = 15

# --------- SELECTS p/ telas (cadastro e consulta) ----------
def _selects_recpsa():
    assentados, tipos, infra = [], [], []
    conn = conectar_bd()
    if not conn:
        return assentados, tipos, infra
    try:
        cur = conn.cursor()
        # Assentados
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome"')
        assentados = cur.fetchall()
        # Tipos de recompensa
        cur.execute('SELECT "idTipRecpsa","nomTipRecpsa" FROM "tbtiprecpsa" ORDER BY "nomTipRecpsa"')
        tipos = cur.fetchall()
        # Infraestrutura + categoria
        cur.execute("""
            SELECT i."idTipUsoInfr", i."nomInfr", i."valUsoInfr",
                   c."idCatgUsoInfr", c."nomCatgUsoInfr"
              FROM "tbtipusoinfr" i
         LEFT JOIN "tbcatgusoinfra" c ON c."idCatgUsoInfr" = i."idCatgUsoInfr"
          ORDER BY c."nomCatgUsoInfr", i."nomInfr"
        """)
        infra = cur.fetchall()
    finally:
        try: conn.close()
        except: pass
    return assentados, tipos, infra

def view_recpsaCad():
    assentados, tipos, infra = _selects_recpsa()
    return render_template('recpsaCad.html', assentados=assentados, tipos=tipos, infra=infra)

# --------- SALDO (regra do usuário) ----------
def _saldo_assentado(idAssent):
    """
    SALDO = (SOMA de todas as contribuições) − (não pagas)
    Não pagas = retribuições (PP) faltantes até o mês atual + mensalidades faltantes até o mês atual.
    PP: somar por política -> (mesAtual - qtdPagasNoAno) * perct(tbpolitpub)
    Mensalidade: (mesAtual - qtdPagasNoAno) * valEqv(tipo id=3)
    """
    conn = conectar_bd()
    if not conn:
        return 0.0
    try:
        cur = conn.cursor()
        ano = datetime.now().year
        mes_atual = datetime.now().month

        # 1) Soma contribuições (tipFinancCP = 1)
        cur.execute("""
            SELECT COALESCE(SUM(f."valFinanc" * COALESCE(NULLIF(f."qtdContr",0),1)),0)
              FROM "tbfinanc" f
             WHERE f."idAssent"=%s AND f."tipFinancCP"=1
        """, (idAssent,))
        soma_contrib = float((cur.fetchone() or [0])[0] or 0)

        # 2) PP faltantes por política (tipFinancCP=3; catg=1) ATÉ O MÊS ATUAL
        cur.execute("""
            SELECT f."idPolPub", COUNT(*) AS qtd
              FROM "tbfinanc" f
             WHERE f."idAssent"=%s
               AND f."tipFinancCP"=3
               AND f."idCatgFinanc"=1
               AND f."anoFinanc"=%s
             GROUP BY f."idPolPub"
        """, (idAssent, ano))
        pagos_por_polit = cur.fetchall()

        cur.execute('SELECT "idPolPub", COALESCE(perct,0) FROM "tbpolitpub"')
        perct_por_polit = {r[0]: float(r[1] or 0) for r in cur.fetchall()}

        nao_pagas_pp = 0.0
        for idPol, qtdPagas in pagos_por_polit:
            perct = perct_por_polit.get(idPol, 0.0)
            faltantes = max(0, mes_atual - int(qtdPagas or 0))
            nao_pagas_pp += faltantes * perct

        # 3) Mensalidades faltantes (idCatgFinanc=3) ATÉ O MÊS ATUAL
        cur.execute("""
            SELECT COUNT(*)
              FROM "tbfinanc" f
             WHERE f."idAssent"=%s
               AND f."tipFinancCP"=1
               AND f."idCatgFinanc"=3
               AND f."anoFinanc"=%s
        """, (idAssent, ano))
        qtd_mens_pagas = int((cur.fetchone() or [0])[0] or 0)

        cur.execute('SELECT COALESCE("valEqv",0) FROM "tbtipfinanc" WHERE "idTipFinanc"=3 LIMIT 1')
        val_mens = float((cur.fetchone() or [0])[0] or 0.0)

        falt_mens = max(0, mes_atual - qtd_mens_pagas)
        nao_pagas_mens = falt_mens * val_mens

        nao_pagas = nao_pagas_pp + nao_pagas_mens
        saldo = soma_contrib - nao_pagas
        return float(saldo)
    except Exception as e:
        print("Erro ao calcular saldo:", e)
        return 0.0
    finally:
        try: conn.close()
        except: pass

# --------- CADASTRAR ----------
def cadastrar_recpsa():
    if request.method != 'POST':
        return redirect(url_for('recpsaCad'))

    idAssent = request.form.get('idAssent')
    idTipRecpsa = request.form.get('idTipRecpsa')

    if not idAssent or not idTipRecpsa:
        flash('❌ Informe Assentado e Tipo de Recompensa.', 'danger')
        return redirect(url_for('recpsaCad'))

    try:
        idAssent = int(idAssent)
        idTipRecpsa = int(idTipRecpsa)
    except:
        flash('❌ Dados inválidos.', 'danger')
        return redirect(url_for('recpsaCad'))

    hoje = date.today()
    conn = conectar_bd()
    if not conn:
        flash('❌ Erro ao conectar no BD.', 'danger')
        return redirect(url_for('recpsaCad'))

    try:
        cur = conn.cursor()

        # Caminho 1: INFRAESTRUTURA (por enquanto id=1)
        if idTipRecpsa == 1:
            idTipUsoInfr = request.form.get('idTipUsoInfr') or ''
            if not idTipUsoInfr:
                flash('❌ Selecione a Infraestrutura.', 'danger')
                return redirect(url_for('recpsaCad'))
            try:
                idTipUsoInfr = int(idTipUsoInfr)
            except:
                flash('❌ Infraestrutura inválida.', 'danger')
                return redirect(url_for('recpsaCad'))

            # Carrega valor da infra
            cur.execute("""
                SELECT COALESCE("valUsoInfr",0)
                  FROM "tbtipusoinfr"
                 WHERE "idTipUsoInfr"=%s
            """, (idTipUsoInfr,))
            row = cur.fetchone()
            if not row:
                flash('❌ Infraestrutura não encontrada.', 'danger')
                return redirect(url_for('recpsaCad'))
            val_infr = float(row[0] or 0)

            # Quantidade e datas
            try:
                qtdEqv = int(request.form.get('qtdEqv_infra') or '1')
            except:
                qtdEqv = 1
            if qtdEqv < 1: qtdEqv = 1

            dtIni = request.form.get('dtIni_infra')
            dtFim = request.form.get('dtFim_infra')
            if not dtIni or not dtFim:
                flash('❌ Informe Início e Fim.', 'danger'); return redirect(url_for('recpsaCad'))

            # SALDO: deve ser >= valor infra * quantidade
            saldo = _saldo_assentado(idAssent)
            total_uso = val_infr * qtdEqv
            if saldo < total_uso:
                flash(f'❌ Saldo insuficiente: saldo R$ {saldo:.2f} < custo R$ {total_uso:.2f}.', 'danger')
                return redirect(url_for('recpsaCad'))

            # Inserir
            cur.execute("""
                INSERT INTO "tbrecpsa"
                ("idTipRecpsa","idAssent","valRecpsa","qtdEqv","idTipUsoInfr",
                 "dtCad","dtIniRecpsa","dtFimRecpsa","status")
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (idTipRecpsa, idAssent, val_infr, qtdEqv, idTipUsoInfr,
                  hoje, dtIni, dtFim, 1))
            conn.commit()
            flash('✅ Recompensa (Infra) cadastrada!', 'success')
            return redirect(url_for('recpsaCad'))

        # Caminho 2: NÃO-INFRA
        else:
            try:
                valRecpsa = float((request.form.get('valRecpsa_geral') or '0').replace(',', '.'))
            except:
                valRecpsa = 0.0
            if valRecpsa <= 0:
                flash('❌ Informe um valor válido.', 'danger')
                return redirect(url_for('recpsaCad'))

            try:
                qtdEqv = int(request.form.get('qtdEqv_geral') or '1')
            except:
                qtdEqv = 1
            if qtdEqv < 1: qtdEqv = 1

            dtIni = request.form.get('dtIni_geral')
            dtFim = request.form.get('dtFim_geral')
            if not dtIni or not dtFim:
                flash('❌ Informe Início e Fim.', 'danger'); return redirect(url_for('recpsaCad'))

            cur.execute("""
                INSERT INTO "tbrecpsa"
                ("idTipRecpsa","idAssent","valRecpsa","qtdEqv","idTipUsoInfr",
                 "dtCad","dtIniRecpsa","dtFimRecpsa","status")
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (idTipRecpsa, idAssent, valRecpsa, qtdEqv, None,
                  hoje, dtIni, dtFim, 1))
            conn.commit()
            flash('✅ Recompensa cadastrada!', 'success')
            return redirect(url_for('recpsaCad'))

    except Exception as e:
        try: conn.rollback()
        except: pass
        print("Erro ao cadastrar recpsa:", e)
        flash('❌ Erro ao cadastrar.', 'danger')
        return redirect(url_for('recpsaCad'))
    finally:
        try: conn.close()
        except: pass


# =================================================================
# ==================   CONSULTA GERAL (NOVO)   ====================
# =================================================================

def _ler_filtros_recpsa():
    src = request.args if request.method == 'GET' else request.form
    f = type('F', (), {})()
    f.idAssent     = (src.get('idAssent') or '').strip()
    f.idTipRecpsa  = (src.get('idTipRecpsa') or '').strip()
    f.idTipUsoInfr = (src.get('idTipUsoInfr') or '').strip()
    f.mesIni       = (src.get('mesIni') or '').strip()
    f.anoIni       = (src.get('anoIni') or '').strip()
    f.mesFim       = (src.get('mesFim') or '').strip()
    f.anoFim       = (src.get('anoFim') or '').strip()
    try:
        page = int(src.get('page', '1'))
    except:
        page = 1
    if page < 1: page = 1
    return f, page

def _montar_where_recpsa(f, params):
    where = ['TRUE']

    if f.idAssent:
        where.append('r."idAssent" = %s')
        params.append(int(f.idAssent))

    if f.idTipRecpsa:
        where.append('r."idTipRecpsa" = %s')
        params.append(int(f.idTipRecpsa))

    if f.idTipUsoInfr:
        where.append('r."idTipUsoInfr" = %s')
        params.append(int(f.idTipUsoInfr))

    # Período: usa dref = coalesce(dtIniRecpsa, dtCad)
    if f.anoIni and f.mesIni and f.anoFim and f.mesFim:
        where.append("""
          date_trunc('month', COALESCE(r."dtIniRecpsa", r."dtCad"))::date >= make_date(%s,%s,1)
          AND
          date_trunc('month', COALESCE(r."dtIniRecpsa", r."dtCad"))::date < (make_date(%s,%s,1) + INTERVAL '1 month')
        """)
        params.extend([int(f.anoIni), int(f.mesIni), int(f.anoFim), int(f.mesFim)])

    return ' AND '.join(where)

def _query_base_recpsa(where_sql: str) -> str:
    return f"""
      SELECT
        r."idAssent"                       AS id_assent,
        a."nome"                           AS nome_assent,
        r."idTipRecpsa"                    AS id_tiprec,
        tr."nomTipRecpsa"                  AS nom_tiprec,
        r."idTipUsoInfr"                   AS id_infr,
        ti."nomInfr"                       AS nom_infr,
        ci."nomCatgUsoInfr"                AS nom_catg_infr,
        r."qtdEqv"                         AS qtd,
        r."valRecpsa"                      AS val_unit,
        COALESCE(r."valRecpsa",0)*COALESCE(r."qtdEqv",1) AS total,
        r."dtCad"                          AS dt_cad,
        r."dtIniRecpsa"                    AS dt_ini,
        r."dtFimRecpsa"                    AS dt_fim,
        r."status"                         AS status,
        COALESCE(r."dtIniRecpsa", r."dtCad")::date AS dref
      FROM "tbrecpsa" r
      LEFT JOIN "tbassentado"   a  ON a."idAssent" = r."idAssent"
      LEFT JOIN "tbtiprecpsa"   tr ON tr."idTipRecpsa" = r."idTipRecpsa"
      LEFT JOIN "tbtipusoinfr"  ti ON ti."idTipUsoInfr" = r."idTipUsoInfr"
      LEFT JOIN "tbcatgusoinfra" ci ON ci."idCatgUsoInfr" = ti."idCatgUsoInfr"
      WHERE {where_sql}
    """

def _pagina_url_factory_recpsa(f):
    def pagina_url(p):
        q = {
            'idAssent': f.idAssent or '',
            'idTipRecpsa': f.idTipRecpsa or '',
            'idTipUsoInfr': f.idTipUsoInfr or '',
            'mesIni': f.mesIni or '',
            'anoIni': f.anoIni or '',
            'mesFim': f.mesFim or '',
            'anoFim': f.anoFim or '',
            'page': p
        }
        return url_for('conGeralRecpsa') + '?' + urlencode(q)
    return pagina_url

def _executar_consulta_recpsa(f, page):
    rows, total = [], 0
    conn = conectar_bd()
    if not conn:
        return rows, total
    try:
        cur = conn.cursor()
        params = []
        where_sql = _montar_where_recpsa(f, params)
        base = _query_base_recpsa(where_sql)

        # total
        cur.execute(f'SELECT COUNT(*) FROM ({base}) T', params)
        total = int(cur.fetchone()[0] or 0)

        # paginação
        limit = PER_PAGE
        offset = (page - 1) * PER_PAGE
        cur.execute(f"""
          {base}
          ORDER BY dref DESC, nome_assent ASC
          LIMIT %s OFFSET %s
        """, params + [limit, offset])

        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            rows.append({cols[i]: r[i] for i in range(len(cols))})
        conn.close()
    except Exception as e:
        try: conn.close()
        except: pass
        print("Erro em consulta de recompensas:", e)
    return rows, total


# --------- PÁGINAS (Consulta Geral) ----------
def pagina_conGeralRecpsa():
    f, page = _ler_filtros_recpsa()
    assentados, tipos, infra = _selects_recpsa()
    rows, total = _executar_consulta_recpsa(f, page)
    pages = max(1, math.ceil(total / PER_PAGE))
    return render_template(
        'conGeralRecpsa.html',
        assentados=assentados,
        tipos=tipos,
        infra=infra,
        filtros=f,
        rows=rows,
        total=total,
        page=page,
        pages=pages,
        pagina_url=_pagina_url_factory_recpsa(f)
    )

def conFiltroRecpsa():
    return pagina_conGeralRecpsa()
