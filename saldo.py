# saldo.py
import psycopg2
from datetime import datetime, date
from flask import request, render_template, url_for, flash
from conexao_bd import conectar_bd

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

def _contribuicoes_no_periodo(conn, idAssent, dt_ini, dt_fim):
    """
    Soma das contribuições (tipFinancCP=1) no período,
    usando: valor da linha = valFinanc * (qtdContr se não parcelado; 1 se parcelado).
    """
    cur = conn.cursor()
    params = [1]    # tipFinancCP = 1
    where = ' f."tipFinancCP"=%s '
    if idAssent:
        where += ' AND f."idAssent"=%s '
        params.append(int(idAssent))

    where += ' AND COALESCE(f."valFinanc",0)>0 '

    # período via dtPagto
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

def _valor_mensalidade_padrao(conn):
    """
    Busca valEqv do tipo 'mensalidade' (idTipFinanc = 3).
    Se não existir, retorna 0.
    """
    cur = conn.cursor()
    cur.execute('SELECT COALESCE(MAX("valEqv"),0) FROM "tbtipfinanc" WHERE "idTipFinanc"=3')
    return float(cur.fetchone()[0] or 0)

def _pp_val_parcela_assentado(conn, idAssent, ano_ref):
    """
    Valor por parcela da PP para o assentado no ano de referência.
    Regra:
      - tenta pegar o maior valFinanc lançado (retribuição) no ano (tip=3, catg=1).
      - se não houver, usa média dos percVal de catg=1 (fallback).
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(MAX(f."valFinanc"),0)
          FROM "tbfinanc" f
         WHERE f."tipFinancCP"=3
           AND f."idCatgFinanc"=1
           AND f."anoFinanc"=%s
           AND f."idAssent"=%s
    """, (int(ano_ref), int(idAssent)))
    val = float(cur.fetchone()[0] or 0)
    if val > 0:
        return val

    # fallback (média geral dos percVal de política pública)
    cur.execute('SELECT COALESCE(AVG(t."percVal"),0) FROM "tbtipfinanc" t WHERE t."idCatgFinanc"=1')
    return float(cur.fetchone()[0] or 0)

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

def _calc_nao_pagas_pp(conn, idAssent, ano_ref, mes_ref):
    val_parcela = _pp_val_parcela_assentado(conn, idAssent, ano_ref)
    if val_parcela <= 0:
        return 0.0
    pagas = _count_parcelas(conn, idAssent, tip=3, idCatg=1, ano_ref=ano_ref, mes_ref=mes_ref)
    faltam = max(0, int(mes_ref) - pagas)
    return float(faltam) * float(val_parcela)

def _calc_nao_pagas_mensalidade(conn, idAssent, ano_ref, mes_ref):
    val_mens = _valor_mensalidade_padrao(conn)
    if val_mens <= 0:
        return 0.0
    pagas = _count_parcelas(conn, idAssent, tip=1, idCatg=3, ano_ref=ano_ref, mes_ref=mes_ref)
    faltam = max(0, int(mes_ref) - pagas)
    return float(faltam) * float(val_mens)

def _assentados_para_calcular(conn, idAssent_filtro):
    """
    Retorna [(idAssent, nome)] a considerar.
    Se filtro vier vazio, pega todos.
    """
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

    # mês/ano de referência p/ “não pagas”
    hoje = date.today()
    ref = dt_fim or hoje
    ano_ref = ref.year
    mes_ref = ref.month

    # selects do filtro
    assentados_sel = _listar_assentados()

    rows = []
    sum_contrib = sum_nao_pp = sum_nao_mens = sum_nao_total = total_saldo = 0.0

    conn = conectar_bd()
    if conn:
        try:
            # Quem calcular
            pessoas = _assentados_para_calcular(conn, F.idAssent)

            for idA, nome in pessoas:
                # Contribuições (no período)
                contrib = _contribuicoes_no_periodo(conn, idA, dt_ini, dt_fim)

                # Não pagas (até mes/ano de referência)
                nao_pp   = _calc_nao_pagas_pp(conn, idA, ano_ref, mes_ref)
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
    # Nossa página já lê filtros por GET; reutilizamos
    return pagina_conGeralSaldo()

# ======== SALDO POR ASSENTADO (página detalhada) ========
from datetime import date

def _parse_date(s):
    if not s: return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except:
        return None

def _periodo_contrib_clause(dt_ini, dt_fim, params):
    """Filtro para somar/listar contribuições pelo dtPagto."""
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
        # valor efetivo
        if (d.get("catgParcdoSN") or 'N').upper() == 'N':
            efetivo = float(d.get("valFinanc") or 0) * float(d.get("qtdContr") or 1)
        else:
            efetivo = float(d.get("valFinanc") or 0)
        d["valor_efetivo"] = round(efetivo, 2)
        total += efetivo
        rows.append(d)
    return rows, round(total, 2)

def _valor_mensalidade_padrao(conn):
    cur = conn.cursor()
    cur.execute('SELECT COALESCE(MAX("valEqv"),0) FROM "tbtipfinanc" WHERE "idTipFinanc"=3')
    return float(cur.fetchone()[0] or 0)

def _pp_val_parcela_assentado(conn, idAssent, ano_ref):
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(MAX(f."valFinanc"),0)
          FROM "tbfinanc" f
         WHERE f."tipFinancCP"=3
           AND f."idCatgFinanc"=1
           AND f."anoFinanc"=%s
           AND f."idAssent"=%s
    """, (int(ano_ref), int(idAssent)))
    val = float(cur.fetchone()[0] or 0)
    if val > 0:
        return val
    cur.execute('SELECT COALESCE(AVG(t."percVal"),0) FROM "tbtipfinanc" t WHERE t."idCatgFinanc"=1')
    return float(cur.fetchone()[0] or 0)

def _parcelas_pagas(conn, idAssent, tip, idCatg, ano_ref, mes_ref):
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE("numParcela",0)
          FROM "tbfinanc"
         WHERE "idAssent"=%s
           AND "tipFinancCP"=%s
           AND "idCatgFinanc"=%s
           AND "anoFinanc"=%s
           AND COALESCE("numParcela",0) BETWEEN 1 AND %s
    """, (int(idAssent), int(tip), int(idCatg), int(ano_ref), int(mes_ref)))
    return {int(x[0]) for x in cur.fetchall() if x and x[0]}

def _dividas_ate_mes(conn, idAssent, ano_ref, mes_ref):
    """
    Lista as parcelas em aberto para PP (tip=3, catg=1) e
    Mensalidade (tip=1, catg=3) até o mês de referência (1..mes_ref).
    """
    faltantes = []

    # --- PP ---
    val_pp = _pp_val_parcela_assentado(conn, idAssent, ano_ref)
    if val_pp > 0:
        pagos_pp = _parcelas_pagas(conn, idAssent, tip=3, idCatg=1, ano_ref=ano_ref, mes_ref=mes_ref)
        for m in range(1, int(mes_ref)+1):
            if m not in pagos_pp:
                faltantes.append({'tipo':'Política Pública', 'mes': m, 'valor': round(val_pp,2)})

    # --- Mensalidade (catg=3) ---
    val_mens = _valor_mensalidade_padrao(conn)
    if val_mens > 0:
        pagos_m = _parcelas_pagas(conn, idAssent, tip=1, idCatg=3, ano_ref=ano_ref, mes_ref=mes_ref)
        for m in range(1, int(mes_ref)+1):
            if m not in pagos_m:
                faltantes.append({'tipo':'Mensalidade', 'mes': m, 'valor': round(val_mens,2)})

    # ordena por tipo e mês
    faltantes.sort(key=lambda x: (x['tipo'], x['mes']))
    total_div = round(sum(x['valor'] for x in faltantes), 2)
    return faltantes, total_div

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

    # se não escolheu assentado, só mostra o filtro
    if not F.idAssent:
        return render_template('saldoAssent.html',
                               filtros=F,
                               assentados=assentados,
                               contribs=[],
                               total_contrib=0.0,
                               dividas=[],
                               total_dividas=0.0,
                               saldo=None)

    # mês/ano de referência para dívidas: usa dtFim ou hoje
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
        dividas, total_dividas  = _dividas_ate_mes(conn, F.idAssent, ano_ref, mes_ref)
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
