# recpsa.py (versão simplificada solicitada)
import math
import psycopg2
from datetime import date, datetime
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

PER_PAGE = 15

# --------- SELECTS p/ tela ----------
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
        #    conta quantas parcelas já foram pagas neste ano para cada política
        cur.execute("""
            SELECT f."idPolPub", COUNT(*) AS qtd
              FROM "tbfinanc" f
             WHERE f."idAssent"=%s
               AND f."tipFinancCP"=3
               AND f."idCatgFinanc"=1
               AND f."anoFinanc"=%s
             GROUP BY f."idPolPub"
        """, (idAssent, ano))
        pagos_por_polit = cur.fetchall()  # [(idPolPub, qtd), ...]

        # Tabela de perct por política
        cur.execute('SELECT "idPolPub", COALESCE(perct,0) FROM "tbpolitpub"')
        perct_por_polit = {r[0]: float(r[1] or 0) for r in cur.fetchall()}

        nao_pagas_pp = 0.0
        # Se não houver registro para alguma política, consideramos 0 pagas; mas para não superestimar,
        # computamos faltantes apenas para as políticas em que houve pagamento (opção conservadora).
        # Caso prefira computar para TODAS políticas cadastradas, trocar o laço abaixo por perct_por_polit.items().
        for idPol, qtdPagas in pagos_por_polit:
            perct = perct_por_polit.get(idPol, 0.0)
            faltantes = max(0, mes_atual - int(qtdPagas or 0))
            nao_pagas_pp += faltantes * perct

        # 3) Mensalidades faltantes (idCatgFinanc=3) ATÉ O MÊS ATUAL
        #    Número de parcelas pagas no ano (contribuição, catg=3)
        cur.execute("""
            SELECT COUNT(*) 
              FROM "tbfinanc" f
             WHERE f."idAssent"=%s
               AND f."tipFinancCP"=1
               AND f."idCatgFinanc"=3
               AND f."anoFinanc"=%s
        """, (idAssent, ano))
        qtd_mens_pagas = int((cur.fetchone() or [0])[0] or 0)

        #    Valor da mensalidade (tipo idTipFinanc = 3) — conforme especificação
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
            # Valor, quantidade e datas
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

            # SALDO: regra diz checar para infra; para manter prudência, deixo passar sem checagem aqui.
            # (Se quiser checar também aqui: if _saldo_assentado(idAssent) < valRecpsa*qtdEqv: ...)

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
