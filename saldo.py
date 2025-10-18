# saldo.py
import psycopg2
from datetime import datetime, date
from flask import request, render_template, flash
from conexao_bd import conectar_bd

# =========================
# Helpers gerais
# =========================
def _listar_assentados():
    conn = conectar_bd()
    itens = []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome" ASC')
        itens = cur.fetchall()
        conn.close()
    return itens

def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except:
        return None

def _periodo_contrib_clause(dt_ini, dt_fim, params):
    """Filtro para somar contribuições pelo dtPagto."""
    if dt_ini and dt_fim:
        params += [dt_ini, dt_fim]
        return ' AND f."dtPagto" BETWEEN %s AND %s '
    elif dt_ini:
        params += [dt_ini]
        return ' AND f."dtPagto" >= %s '
    elif dt_fim:
        params += [dt_fim]
        return ' AND f."dtPagto" <= %s '
    return ''

def _iter_months(dini: date, dfim: date):
    """Gera o primeiro dia de cada mês entre dini..dfim (inclusive)."""
    y, m = dini.year, dini.month
    while (y < dfim.year) or (y == dfim.year and m <= dfim.month):
        yield date(y, m, 1)
        m += 1
        if m > 12:
            m = 1
            y += 1

# =========================
# Contribuições no período
# =========================
def _contribuicoes_no_periodo(conn, idAssent, dt_ini, dt_fim):
    """
    Soma das contribuições (tipFinancCP=1) no período,
    usando: valor efetivo = valFinanc * (qtdContr se não parcelado; 1 se parcelado).
    """
    cur = conn.cursor()
    params = [1]    # tipFinancCP = 1 (contribuições)
    where = ' f."tipFinancCP"=%s '
    if idAssent:
        where += ' AND f."idAssent"=%s '
        params.append(int(idAssent))

    where += ' AND COALESCE(f."valFinanc",0)>0 '
    where += _periodo_contrib_clause(dt_ini, dt_fim, params)

    sql = f"""
      SELECT COALESCE(SUM(
        CASE
          WHEN f."catgParcdoSN"='N' THEN f."valFinanc" * COALESCE(f."qtdContr",1)
          ELSE f."valFinanc"
        END
      ),0)
      FROM "tbfinanc" f
      WHERE {where}
    """
    cur.execute(sql, params)
    total = float(cur.fetchone()[0] or 0)
    return total

# =========================
# POLÍTICA PÚBLICA (por política e por mês/ano)
# =========================
def _pp_ativas_do_assentado(conn, idAssent):
    """
    Retorna PP ATIVAS (status=1) do assentado,
    com dtAtvPolPub e dados da política (valor, perct).
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT ap."idPolPub",
               ap."dtAtvPolPub",
               pp.valor,
               pp.perct
          FROM "tbassentpolpub" ap
          JOIN "tbpolitpub" pp ON pp."idPolPub" = ap."idPolPub"
         WHERE ap."idAssent"=%s
           AND ap.status = 1
           AND ap."dtAtvPolPub" IS NOT NULL
    """, (int(idAssent),))
    out = []
    for idPol, dtAtv, valor, perct in cur.fetchall():
        out.append({
            "idPolPub": int(idPol),
            "dtAtvPolPub": dtAtv,
            "valor": float(valor or 0),
            "perct": float(perct or 0),
        })
    return out

def _val_mens_pp(valor, perct) -> float:
    """Valor mensal devido à associação pela PP = valor * (perct/100)."""
    v = float(valor or 0)
    p = float(perct or 0)
    return round(v * (p / 100.0), 2)

def _meses_pp_pagos_por_politica(conn, idAssent, idPolPub, dt_ini, dt_fim):
    """
    Retorna um set de meses (primeiro dia do mês) em que HOUVE pagamento de PP
    para essa política (tip=3, idCatg=1, idPolPub=...) entre dt_ini..dt_fim.
    Considera ano/mes quando preenchidos; senão usa o mês de dtPagto.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT
               CASE
                 WHEN f."anoFinanc" IS NOT NULL AND f."mesFinanc" IS NOT NULL
                   THEN make_date(f."anoFinanc", f."mesFinanc", 1)
                 ELSE date_trunc('month', f."dtPagto")::date
               END AS mes_ref
          FROM "tbfinanc" f
         WHERE f."idAssent"=%s
           AND f."tipFinancCP"=3            -- retribuição
           AND f."idCatgFinanc"=1           -- categoria PP
           AND f."idPolPub"=%s
           AND COALESCE(f."valFinanc",0) > 0
           AND (
                 (f."anoFinanc" IS NOT NULL AND f."mesFinanc" IS NOT NULL
                    AND make_date(f."anoFinanc", f."mesFinanc", 1) BETWEEN %s AND %s)
                 OR (
                      (f."anoFinanc" IS NULL OR f."mesFinanc" IS NULL)
                      AND date_trunc('month', f."dtPagto")::date BETWEEN %s AND %s
                    )
               )
    """, (int(idAssent), int(idPolPub), dt_ini, dt_fim, dt_ini, dt_fim))
    return {r[0] for r in cur.fetchall() if r and r[0]}

def _pp_meses_em_aberto(conn, idAssent, ref):
    """
    Lista meses em aberto de PP (por política) desde dtAtvPolPub até ref,
    verificando tbfinanc por (tip=3, idCatg=1, idPolPub) e mês/ano.
    Retorna (lista_de_itens, total).
    """
    pps = _pp_ativas_do_assentado(conn, idAssent)
    if not pps:
        return [], 0.0

    ref_mes = date(ref.year, ref.month, 1)
    faltantes = []
    total = 0.0

    for pp in pps:
        dt_ini = date(pp["dtAtvPolPub"].year, pp["dtAtvPolPub"].month, 1)
        dt_fim = ref_mes
        if dt_fim < dt_ini:
            continue

        meses_pagos = _meses_pp_pagos_por_politica(conn, idAssent, pp["idPolPub"], dt_ini, dt_fim)
        val_mens = _val_mens_pp(pp["valor"], pp["perct"])
        if val_mens <= 0:
            continue

        for mes in _iter_months(dt_ini, dt_fim):
            if mes not in meses_pagos:
                faltantes.append({
                    'tipo': f'Política Pública (ID {pp["idPolPub"]})',
                    'mes': f'{mes.month:02}/{mes.year}',
                    'valor': round(val_mens, 2)
                })
                total += val_mens

    # ordenar por ano/mês
    faltantes.sort(key=lambda x: (int(x['mes'].split('/')[1]), int(x['mes'].split('/')[0])))
    return faltantes, round(total, 2)

def _calc_nao_pagas_pp(conn, idAssent, ref):
    """
    Total em aberto de PP (somente meses não pagos), somando por política.
    """
    _, total = _pp_meses_em_aberto(conn, idAssent, ref)
    return total

# =========================
# MENSALIDADE (desde dtCad abatendo pagamentos)
# =========================
def _valor_mensalidade_padrao(conn):
    """
    Busca valEqv do tipo 'mensalidade' (idTipFinanc = 3).
    Se não existir, retorna 0.
    """
    cur = conn.cursor()
    cur.execute('SELECT COALESCE(MAX("valEqv"),0) FROM "tbtipfinanc" WHERE "idTipFinanc"=3')
    return float(cur.fetchone()[0] or 0)

def _dtcad_assentado(conn, idAssent):
    cur = conn.cursor()
    cur.execute('SELECT "dtCad" FROM "tbassentado" WHERE "idAssent"=%s', (int(idAssent),))
    row = cur.fetchone()
    return row[0] if row and row[0] else None

def _meses_mensalidade_pagos(conn, idAssent, dt_ini, dt_fim):
    """
    Retorna um set com as datas (YYYY-MM-01) onde houve pagamento de mensalidade
    (tipFinancCP=1, idCatgFinanc=3, valFinanc>0) entre dt_ini..dt_fim.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT
               CASE
                 WHEN f."anoFinanc" IS NOT NULL AND f."mesFinanc" IS NOT NULL
                   THEN make_date(f."anoFinanc", f."mesFinanc", 1)
                 ELSE date_trunc('month', f."dtPagto")::date
               END AS mes_ref
          FROM "tbfinanc" f
         WHERE f."idAssent"=%s
           AND f."tipFinancCP"=1
           AND f."idCatgFinanc"=3
           AND COALESCE(f."valFinanc",0) > 0
           AND (
                 (f."anoFinanc" IS NOT NULL AND f."mesFinanc" IS NOT NULL
                    AND make_date(f."anoFinanc", f."mesFinanc", 1) BETWEEN %s AND %s)
                 OR (
                      (f."anoFinanc" IS NULL OR f."mesFinanc" IS NULL)
                      AND date_trunc('month', f."dtPagto")::date BETWEEN %s AND %s
                    )
               )
    """, (int(idAssent), dt_ini, dt_fim, dt_ini, dt_fim))
    return {r[0] for r in cur.fetchall() if r and r[0]}

def _calc_nao_pagas_mensalidade(conn, idA, ref):
    """
    Quanto falta pagar de MENSALIDADE desde o mês do dtCad do assentado
    até o mês/ano de `ref` (inclusive), abatendo os meses com pagamento
    (tip=1, idCatg=3, valFinanc>0).
    """
    val_mens = _valor_mensalidade_padrao(conn)
    if val_mens <= 0:
        return 0.0

    dtCad = _dtcad_assentado(conn, idA)
    if not dtCad:
        # Sem dtCad => por segurança, não cobra
        return 0.0

    inicio = date(dtCad.year, dtCad.month, 1)
    fim    = date(ref.year, ref.month, 1)
    if fim < inicio:
        return 0.0

    pagos = _meses_mensalidade_pagos(conn, idA, inicio, fim)

    devido = 0.0
    for mes in _iter_months(inicio, fim):
        if mes not in pagos:
            devido += val_mens

    return round(devido, 2)

# =========================
# Página: Consulta Geral — Saldo
# =========================
def _assentados_para_calcular(conn, idAssent_filtro):
    cur = conn.cursor()
    if idAssent_filtro:
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" WHERE "idAssent"=%s', (int(idAssent_filtro),))
    else:
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome" ASC')
    return cur.fetchall()

def pagina_conGeralSaldo():
    # Filtros
    src = request.args
    F = type('F', (), {})()
    F.idAssent = (src.get('idAssent') or '').strip()
    F.dtIni    = (src.get('dtIni') or '').strip()
    F.dtFim    = (src.get('dtFim') or '').strip()

    dt_ini = _parse_date(F.dtIni)
    dt_fim = _parse_date(F.dtFim)

    # data de referência p/ “não pagas”: usa dtFim ou hoje
    ref = dt_fim or date.today()

    # selects do filtro
    assentados_sel = _listar_assentados()

    rows = []
    sum_contrib = sum_nao_pp = sum_nao_mens = sum_nao_total = total_saldo = 0.0

    conn = conectar_bd()
    if conn:
        try:
            pessoas = _assentados_para_calcular(conn, F.idAssent)

            for idA, nome in pessoas:
                contrib = _contribuicoes_no_periodo(conn, idA, dt_ini, dt_fim)

                # PP (correto: por política e por mês/ano)
                nao_pp = _calc_nao_pagas_pp(conn, idA, ref)

                # Mensalidade (desde dtCad)
                nao_mens = _calc_nao_pagas_mensalidade(conn, idA, ref)

                nao_tot  = nao_pp + nao_mens
                saldo = contrib - nao_tot

                rows.append({
                    'idAssent': idA,
                    'nome': nome,
                    'contrib': round(contrib, 2),
                    'nao_pagas_pp': round(nao_pp, 2),
                    'nao_pagas_mens': round(nao_mens, 2),
                    'nao_pagas_total': round(nao_tot, 2),
                    'saldo': round(saldo, 2),
                })

                sum_contrib   += contrib
                sum_nao_pp    += nao_pp
                sum_nao_mens  += nao_mens
                sum_nao_total += nao_tot
                total_saldo   += saldo

        finally:
            if conn and not conn.closed:
                conn.close()

    # Mensagem de superávit/déficit (global)
    if total_saldo >= 0:
        flash("✅ Resultado do período: SUPERÁVIT.", "success")
    else:
        flash("⚠️ Resultado do período: DÉFICIT.", "danger")

    # ATENÇÃO: nome do template deve bater com o arquivo (case!)
    return render_template(
        'conGeralSaldo.html',
        filtros=F,
        assentados=assentados_sel,
        rows=rows,
        sum_contrib=round(sum_contrib,2),
        sum_nao_pp=round(sum_nao_pp,2),
        sum_nao_mens=round(sum_nao_mens,2),
        sum_nao_total=round(sum_nao_total,2),
        total_saldo=round(total_saldo,2),
    )

def conFiltroSaldo():
    return pagina_conGeralSaldo()

# =========================
# Página: Saldo por Assentado (detalhado)
# =========================
def _listar_contribuicoes(conn, idAssent, dt_ini=None, dt_fim=None):
    """
    Lista contribuições do assentado (tipFinancCP = 1), com:
      - data_ref (dtPagto OU make_date(ano,mes,1))
      - categoria, tipo "provável"
      - valor efetivo (valFinanc * qtdContr se não parcelado; senão valFinanc)
    """
    cur = conn.cursor()
    params = [1, int(idAssent)]
    where = ' f."tipFinancCP"=%s AND f."idAssent"=%s AND COALESCE(f."valFinanc",0)>0 '
    where += _periodo_contrib_clause(dt_ini, dt_fim, params)

    sql = f"""
      SELECT
        f."idSeqFinanc",
        f."dtPagto",
        f."anoFinanc",
        f."mesFinanc",
        f."valFinanc",
        f."catgParcdoSN",
        COALESCE(f."qtdContr",1) AS qtdContr,
        c."nomCatgFinanc" AS nom_catg,
        COALESCE(t."nomFinanc",'(tipo não definido)') AS nom_tipo,
        CASE
          WHEN f."anoFinanc" IS NOT NULL AND f."mesFinanc" IS NOT NULL
            THEN make_date(f."anoFinanc", f."mesFinanc", 1)
          ELSE date_trunc('month', f."dtPagto")::date
        END AS data_ref
      FROM "tbfinanc" f
      LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc"=f."idCatgFinanc"
      LEFT JOIN LATERAL (
        SELECT t.*
          FROM "tbtipfinanc" t
         WHERE t."idCatgFinanc" = f."idCatgFinanc"
         ORDER BY
           (t."idPolPub" IS NOT DISTINCT FROM f."idPolPub") DESC,
           (t."valEqv"   IS NOT DISTINCT FROM f."valFinanc") DESC,
           t."idTipFinanc" ASC
         LIMIT 1
      ) t ON TRUE
      WHERE {where}
      ORDER BY data_ref DESC, f."idSeqFinanc" DESC
    """
    cur.execute(sql, params)
    cols = [d[0] for d in cur.description]
    rows = []
    total = 0.0
    for r in cur.fetchall():
        d = {cols[i]: r[i] for i in range(len(cols))}
        if (d.get("catgParcdoSN") or 'N').upper() == 'N':
            efetivo = float(d.get("valFinanc") or 0) * float(d.get("qtdContr") or 1)
        else:
            efetivo = float(d.get("valFinanc") or 0)
        d["valor_efetivo"] = round(efetivo, 2)
        total += efetivo
        rows.append(d)
    return rows, round(total, 2)

def pagina_saldoAssent():
    """
    Mostra saldo detalhado de UM assentado:
      - filtro: idAssent obrigatório (dtIni/dtFim opcionais)
      - tabela de contribuições do período
      - tabela de 'em aberto' (PP + Mensalidade) até mês/ano de referência (usa dtFim ou hoje)
      - saldo final e mensagem SUPERÁVIT/DÉFICIT
    """
    src = request.args
    F = type('F', (), {})()
    F.idAssent = (src.get('idAssent') or '').strip()
    F.dtIni    = (src.get('dtIni') or '').strip()
    F.dtFim    = (src.get('dtFim') or '').strip()

    dt_ini = _parse_date(F.dtIni)
    dt_fim = _parse_date(F.dtFim)

    assentados = _listar_assentados()

    if not F.idAssent:
        return render_template('saldoAssent.html',
                               filtros=F,
                               assentados=assentados,
                               contribs=[],
                               total_contrib=0.0,
                               dividas=[],
                               total_dividas=0.0,
                               saldo=None)

    ref = dt_fim or date.today()

    contribs, total_contrib = [], 0.0
    dividas, total_dividas  = [], 0.0
    saldo_final = 0.0

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com BD.', 'danger')
        return render_template('saldoAssent.html',
                               filtros=F, assentados=assentados,
                               contribs=[], total_contrib=0.0,
                               dividas=[], total_dividas=0.0,
                               saldo=None)

    try:
        # Contribuições no período
        contribs, total_contrib = _listar_contribuicoes(conn, F.idAssent, dt_ini, dt_fim)

        # PP (lista meses em aberto por política)
        div_pp, total_div_pp = _pp_meses_em_aberto(conn, F.idAssent, ref)

        # Mensalidade (em aberto desde dtCad)
        total_div_m = _calc_nao_pagas_mensalidade(conn, F.idAssent, ref)
        # Lista sintética dos meses faltantes (opcional: exibimos N itens, todos como "Mensalidade")
        div_mens = []
        if total_div_m > 0:
            val_mens = _valor_mensalidade_padrao(conn)
            # quantidade de meses faltantes (aproximação por divisão inteira)
            if val_mens > 0:
                qtd = int(round(total_div_m / val_mens))
                div_mens = [{'tipo':'Mensalidade', 'mes': None, 'valor': round(val_mens,2)} for _ in range(qtd)]

        # Monta totais
        dividas = div_pp + div_mens
        total_dividas = round(total_div_pp + total_div_m, 2)
        saldo_final = round(float(total_contrib) - float(total_dividas), 2)

        if saldo_final >= 0:
            flash('✅ SUPERÁVIT', 'success')
        else:
            flash('⚠️ DÉFICIT', 'danger')

        return render_template('saldoAssent.html',
                               filtros=F,
                               assentados=assentados,
                               contribs=contribs,
                               total_contrib=total_contrib,
                               dividas=dividas,
                               total_dividas=total_dividas,
                               saldo=saldo_final)
    finally:
        if conn and not conn.closed:
            conn.close()
