# saldo.py
import psycopg2
from datetime import datetime, date
from flask import request, render_template, url_for, flash
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
    if not s: return None
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

def _months_between_inclusive(dini: date, dfim: date) -> int:
    """
    Número de meses entre duas datas (contando mês inicial e final).
    Ex.: 2025-02-10 .. 2025-04-01 => 3 (fev, mar, abr)
    """
    if dfim < dini:
        return 0
    return (dfim.year - dini.year) * 12 + (dfim.month - dini.month) + 1

# =========================
# Contribuições no período (continua igual)
# =========================
def _contribuicoes_no_periodo(conn, idAssent, dt_ini, dt_fim):
    """
    Soma das contribuições (tipFinancCP=1) no período,
    usando: valor efetivo = valFinanc * (qtdContr se não parcelado; 1 se parcelado).
    """
    cur = conn.cursor()
    params = [1]    # tipFinancCP = 1
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
# NOVO: cálculo correto de PP (baseado em tbassentpolpub + tbpolitpub)
# =========================
def _pp_ativas_do_assentado(conn, idAssent):
    """
    Retorna vínculos de PP ATIVOS (status=1) do assentado,
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
    rows = []
    for idPol, dtAtv, valor, perct in cur.fetchall():
        rows.append({
            "idPolPub": idPol,
            "dtAtvPolPub": dtAtv,
            "valor": float(valor or 0),
            "perct": float(perct or 0),
        })
    return rows

def _count_parcelas_pp_pagas(conn, idAssent, dt_ini: date, dt_fim: date):
    """
    Conta as parcelas de PP pagas (financeiro) entre dt_ini..dt_fim.
    Critérios: tipFinancCP=3 (retribuição), idCatgFinanc=1 (PP).
    Usa make_date(ano,mes,1) quando possível; senão, dtPagto (mês).
    """
    cur = conn.cursor()
    sql = """
        SELECT COUNT(*)
          FROM "tbfinanc" f
         WHERE f."idAssent"=%s
           AND f."tipFinancCP"=3
           AND f."idCatgFinanc"=1
           AND (
                 (f."anoFinanc" IS NOT NULL AND f."mesFinanc" IS NOT NULL
                  AND make_date(f."anoFinanc", f."mesFinanc", 1) BETWEEN %s AND %s)
                 OR (
                      (f."anoFinanc" IS NULL OR f."mesFinanc" IS NULL)
                      AND date_trunc('month', f."dtPagto")::date BETWEEN %s AND %s
                    )
               )
    """
    cur.execute(sql, (int(idAssent), dt_ini, dt_fim, dt_ini, dt_fim))
    return int(cur.fetchone()[0] or 0)

def _calc_nao_pagas_pp(conn, idAssent, ref_date: date) -> float:
    """
    Soma, para cada PP ativa do assentado:
      meses_devidos (de dtAtvPolPub até ref)  ×  (valor * perct)
      menos as parcelas pagas (financeiro) no mesmo intervalo.
    Observação: se houver >1 PP ativa simultânea, os pagamentos não distinguem idPolPub.
    Assumimos 1 PP por assentado ou uso conservador (não deixa negativo).
    """
    pps = _pp_ativas_do_assentado(conn, idAssent)
    if not pps:
        return 0.0

    total_devido = 0.0
    total_meses_devidos = 0

    # soma dos meses devidos e valor mensal (valPago) por PP
    for pp in pps:
        dt_ini = date(pp["dtAtvPolPub"].year, pp["dtAtvPolPub"].month, 1)
        dt_fim = date(ref_date.year, ref_date.month, 1)
        meses = _months_between_inclusive(dt_ini, dt_fim)
        if meses <= 0:
            continue
        # conforme sua regra: valPago = valor * perct (sem dividir por 100)
        valPago = pp["valor"] * pp["perct"]
        total_devido += meses * valPago
        total_meses_devidos += meses

    if total_meses_devidos == 0:
        return 0.0

    # parcelas pagas (todas de PP) no período global de todas as PP
    # janela = do MENOR dtAtvPolPub até ref_date
    menor_dt = min(date(pp["dtAtvPolPub"].year, pp["dtAtvPolPub"].month, 1) for pp in pps)
    maior_dt = date(ref_date.year, ref_date.month, 1)
    pagas = _count_parcelas_pp_pagas(conn, idAssent, menor_dt, maior_dt)

    # Apropriação conservadora: desconta as parcelas pagas, limitando a não ficar negativo
    # Distribuir exatamente por PP exigiria idPolPub no financeiro; não temos aqui.
    # Então reduz do total_devido um "teto" de pagas * (valor_médio por mês).
    # Para não superestimar, calculamos valor médio por mês (ponderado):
    if total_meses_devidos > 0:
        valor_medio_mes = total_devido / total_meses_devidos
    else:
        valor_medio_mes = 0.0

    abatimento = min(pagas, total_meses_devidos) * valor_medio_mes
    nao_pagas = max(0.0, total_devido - abatimento)
    return round(nao_pagas, 2)

# =========================
# Mensalidade padrão (continua)
# =========================

def _count_parcelas(conn, idAssent, tip, idCatg, ano_ref, mes_ref):
    """
    Conta quantas parcelas foram pagas até o mês de referência (1..mes_ref).
    - tip: 1 (contrib) ou 3 (retrib)
    - idCatg: 1 (PP) ou 3 (mensalidade)
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
          FROM "tbfinanc"
         WHERE "idAssent"=%s
           AND "tipFinancCP"=%s
           AND "idCatgFinanc"=%s
           AND "anoFinanc"=%s
           AND COALESCE("numParcela",0) BETWEEN 1 AND %s
    """, (int(idAssent), int(tip), int(idCatg), int(ano_ref), int(mes_ref)))
    return int(cur.fetchone()[0] or 0)


def _assentados_para_calcular(conn, idAssent_filtro):
    cur = conn.cursor()
    if idAssent_filtro:
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" WHERE "idAssent"=%s', (int(idAssent_filtro),))
    else:
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome" ASC')
    return cur.fetchall()

# =========================
# Página: Consulta Geral — Saldo
# =========================
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

                # NOVO: Não pagas PP correto (com vínculo ativo + dtAtvPolPub)
                nao_pp   = _calc_nao_pagas_pp(conn, idA, ref)

                # Mensalidade (permanece sua lógica atual)
                ano_ref = ref.year
                mes_ref = ref.month
                nao_mens = _calc_nao_pagas_mensalidade(conn, idA, ano_ref, mes_ref)

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

    return render_template(
        'ConGeralSaldo.html',
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

# ======== SALDO POR ASSENTADO (detalhado) ========
# (mantive sua página, mas ajustei a parte de PP para usar a nova regra também)

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
    ano_ref = ref.year
    mes_ref = ref.month

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
        contribs, total_contrib = _listar_contribuicoes(conn, F.idAssent, dt_ini, dt_fim)

        # PP (nova regra)
        div_pp, total_div_pp = _pp_meses_em_aberto(conn, F.idAssent, ref)

        # Mensalidade (reaproveita sua lógica anterior)
        val_mens = _valor_mensalidade_padrao(conn)
        pagos_m  = _count_parcelas(conn, F.idAssent, tip=1, idCatg=3, ano_ref=ano_ref, mes_ref=mes_ref)
        faltam_m = max(0, int(mes_ref) - pagos_m)
        div_mens = [{'tipo':'Mensalidade', 'mes': m, 'valor': round(val_mens,2)} for m in range(1, faltam_m+1)] if val_mens>0 else []
        total_div_m = round(faltam_m * val_mens, 2) if val_mens>0 else 0.0

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

def _calc_nao_pagas_pp(conn, idAssent, ref_date: date) -> float:
    """
    Para cada PP ativa:
      - meses devidos: de dtAtvPolPub até ref_date (por mês)
      - valor do mês: valor * (perct/100)
      - considera PAGO se existir lançamento em tbfinanc (tip=3, catg=1)
        com idPolPub da PP no mês/ano correspondente.
      - soma apenas meses NÃO pagos.
    """
    pps = _pp_ativas_do_assentado(conn, idAssent)
    if not pps:
        return 0.0

    ref_mes = date(ref_date.year, ref_date.month, 1)
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
                total += val_mens

    return round(total, 2)

def _pp_meses_em_aberto(conn, idAssent, ref: date):
    """
    Lista meses em aberto de PP (por política) desde dtAtvPolPub até ref,
    verificando tbfinanc por (tip=3, idCatg=1, idPolPub) e mês/ano.
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


# ---------------- Helpers de mês ----------------
def _iter_months(dini: date, dfim: date):
    """Gera o primeiro dia de cada mês entre dini..dfim (inclusive)."""
    y, m = dini.year, dini.month
    while (y < dfim.year) or (y == dfim.year and m <= dfim.month):
        yield date(y, m, 1)
        m += 1
        if m > 12:
            m = 1
            y += 1

# ---------------- Buscar dtCad do assentado ----------------
def _dtcad_assentado(conn, idAssent: int):
    cur = conn.cursor()
    cur.execute('SELECT "dtCad" FROM "tbassentado" WHERE "idAssent"=%s', (int(idAssent),))
    row = cur.fetchone()
    return row[0] if row and row[0] else None

# ---------------- Valor mensal da mensalidade (como já usava) ----------------
def _valor_mensalidade_padrao(conn) -> float:
    cur = conn.cursor()
    cur.execute('SELECT COALESCE(MAX("valEqv"),0) FROM "tbtipfinanc" WHERE "idTipFinanc"=3')
    return float(cur.fetchone()[0] or 0)

# ---------------- Meses de mensalidade pagos (tip=1, idCatg=3) desde dtCad ----------------
def _meses_mensalidade_pagos(conn, idAssent: int, dt_ini: date, dt_fim: date) -> set[date]:
    """
    Retorna um set com as datas (primeiro dia do mês) em que houve pagamento de mensalidade
    (tipFinancCP=1, idCatgFinanc=3, valFinanc>0) no período dt_ini..dt_fim.
    Considera ano/mes, ou dtPagto (mês) quando aqueles não vierem.
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

# ---------------- Novo cálculo: NÃO PAGAS — Mensalidade ----------------
def  _calc_nao_pagas_mensalidade(conn, idA, ref) -> float:
    """
    Calcula quanto falta pagar de MENSALIDADE desde o mês do dtCad do assentado
    até o mês/ano de ref_date, abatendo os meses que já possuem pagamento
    (tip=1, idCatg=3, valFinanc>0).
    """
    val_mens = _valor_mensalidade_padrao(conn)
    if val_mens <= 0:
        return 0.0

    dtCad = _dtcad_assentado(conn, idAssent)
    if not dtCad:
        # Sem dtCad => não cobra mensalidade por segurança
        return 0.0

    inicio = date(dtCad.year, dtCad.month, 1)
    fim    = date(ref_date.year, ref_date.month, 1)
    if fim < inicio:
        return 0.0

    pagos = _meses_mensalidade_pagos(conn, idAssent, inicio, fim)

    devido = 0.0
    for mes in _iter_months(inicio, fim):
        if mes not in pagos:
            devido += val_mens

    return round(devido, 2)


#-------------------------------- novo helpers

def _val_mens_pp(valor, perct) -> float:
    """Valor mensal devido à associação pela PP = valor * (perct/100)."""
    v = float(valor or 0)
    p = float(perct or 0)
    return round(v * (p / 100.0), 2)

def _meses_pp_pagos_por_politica(conn, idAssent: int, idPolPub: int, dt_ini: date, dt_fim: date) -> set[date]:
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
