import psycopg2
from datetime import datetime, date
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

# ---------- CADASTRO ----------


def cadastrar_contrib():
    if request.method != 'POST':
        return redirect(url_for('contribCad'))

    tipFinancCP  = (request.form.get('tipFinancCP') or '1').strip()
    idAssent     = request.form.get('idAssent') or request.form.get('matricula')
    idTipFinanc  = request.form.get('idTipFinanc')
    obs          = request.form.get('obs','').strip()

    idCatgFinanc = request.form.get('idCatgFinanc') or ''
    catgParcdoSN = (request.form.get('catgParcdoSN') or 'N').strip().upper()
    idPolPub     = request.form.get('idPolPub') or ''
    valFinanc_in = request.form.get('valFinanc')

    # NOVO: quantidade (só para não-política e não-mensalidade)
    qtdContr_in  = request.form.get('qtdContr')
    def _parse_float(x, padrao=1.0):
        try:
            if x is None or str(x).strip()=='':
                return padrao
            return float(str(x).replace(',','.'))
        except:
            return padrao
    qtdContr = _parse_float(qtdContr_in, 1.0)

    if tipFinancCP != '1' or not idAssent or not idTipFinanc:
        flash('❌ Dados insuficientes.')
        return redirect(url_for('contribCad'))

    try:
        idAssent = int(idAssent)
        idTipFinanc = int(idTipFinanc)
    except:
        flash('❌ Assentado/Tipo inválidos.')
        return redirect(url_for('contribCad'))

    ano_atual = datetime.now().year

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro ao conectar no BD.')
        return redirect(url_for('contribCad'))

    try:
        cur = conn.cursor()

        # Completa dados do tipo (se necessário)
        if not idCatgFinanc or idPolPub == '':
            cur.execute("""
                SELECT t."idCatgFinanc", t."idPolPub", t."percVal", t."valEqv"
                FROM "tbtipfinanc" t
                WHERE t."idTipFinanc"=%s
            """, (idTipFinanc,))
            row = cur.fetchone()
            if not row:
                conn.close()
                flash('❌ Tipo de contribuição inexistente.')
                return redirect(url_for('contribCad'))
            if not idCatgFinanc:
                idCatgFinanc = row[0]
            if idPolPub == '':
                idPolPub = row[1]  # pode ser None
            percVal = row[2]
            valEqv  = row[3]
        else:
            cur.execute("""
                SELECT t."percVal", t."valEqv"
                FROM "tbtipfinanc" t
                WHERE t."idTipFinanc"=%s
            """, (idTipFinanc,))
            row = cur.fetchone()
            percVal = row[0] if row else None
            valEqv  = row[1] if row else None

        # Valor
        if idPolPub:  # Política Pública
            try:
                valFinanc = float(percVal or 0)
            except:
                valFinanc = 0.0
            if valFinanc <= 0:
                conn.close()
                flash('❌ Política Pública sem valor definido (percVal).')
                return redirect(url_for('contribCad'))
        else:  # Demais (inclui Mensalidade e outros)
            try:
                valFinanc = float(valFinanc_in) if valFinanc_in not in (None,'') else float(valEqv or 0)
            except:
                valFinanc = 0.0
            if valFinanc <= 0:
                conn.close()
                flash('❌ Valor da contribuição não informado.')
                return redirect(url_for('contribCad'))

        inseridos = 0

        # Mensalidade/parceladas: SEM qtdContr, mantém lógica de parcelas
        if catgParcdoSN == 'S':
            qtd = request.form.get('qtdParcelas')
            try:
                qtd = int(qtd or '0')
            except:
                qtd = 0
            if qtd <= 0:
                conn.close()
                flash('❌ Informe o nº de parcelas a pagar.')
                return redirect(url_for('contribCad'))

            cur.execute("""
                SELECT COALESCE(MAX("numParcela"),0), COUNT(*)
                  FROM "tbfinanc"
                 WHERE "idAssent"=%s
                   AND "idCatgFinanc"=%s
                   AND "tipFinancCP"=1
                   AND "anoFinanc"=%s
            """, (idAssent, int(idCatgFinanc), ano_atual))
            mx, cnt = cur.fetchone() or (0,0)
            prox = mx + 1
            restantes = max(0, 12 - cnt)
            if restantes <= 0:
                flash('⚠️ Limite de 12 parcelas já alcançado neste ano.')
                conn.close()
                return redirect(url_for('contribCad'))

            pagar = min(restantes, qtd)
            if pagar < qtd:
                flash(f'⚠️ Só havia espaço para {pagar} parcela(s) neste ano (máx 12).')

            for i in range(pagar):
                par = prox + i
                cur.execute("""
                    INSERT INTO "tbfinanc"
                    ("idAssent","anoFinanc","mesFinanc","valFinanc",
                     "idCatgFinanc","dtPagto","obs","horario",
                     "tipFinancCP","numParcela","catgParcdoSN","idPolPub")
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    idAssent, ano_atual, par, valFinanc,
                    int(idCatgFinanc), date.today(), obs, datetime.now().time(),
                    1, par, 'S', int(idPolPub) if idPolPub else None
                ))
                inseridos += 1

        # Não parcelado (não-política e não-mensalidade): grava qtdContr
        else:
            cur.execute("""
                INSERT INTO "tbfinanc"
                ("idAssent","anoFinanc","mesFinanc","valFinanc",
                 "idCatgFinanc","dtPagto","obs","horario",
                 "tipFinancCP","numParcela","catgParcdoSN","idPolPub","qtdContr")
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                idAssent, ano_atual, None, valFinanc,
                int(idCatgFinanc), date.today(), obs, datetime.now().time(),
                1, 0, 'N', int(idPolPub) if idPolPub else None,
                float(qtdContr or 1.0)
            ))
            inseridos = 1

        conn.commit()
        flash(f"✅ Contribuição registrada ({inseridos} registro(s)).")
        return redirect(url_for('contribCad'))

    except Exception as e:
        try:
            if conn and not conn.closed:
                conn.rollback()
        except:
            pass
        print("Erro ao cadastrar contribuição:", e)
        flash("❌ Erro ao cadastrar.")
        return redirect(url_for('contribCad'))
    finally:
        if conn and not conn.closed:
            conn.close()

# ---------- helpers ----------
def _selecoes_cadastro():
    """Assentados e Tipos (com percVal para Política Pública)."""
    conn = conectar_bd()
    assentados, tipos = [], []
    if conn:
        cur = conn.cursor()

        # Assentados (ordem alfabética)
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome" ASC')
        assentados = cur.fetchall()

        # Tipos de contribuição + dados necessários p/ JS
        cur.execute("""
          SELECT
            t."idTipFinanc",         -- [0]
            t."nomFinanc",           -- [1]
            t."idCatgFinanc",        -- [2]
            t."idPolPub",            -- [3]
            t."valPolPub",           -- [4]
            t."percVal"  AS percval, -- [5] valor pronto p/ Política Pública
            p."perct"    AS pol_perc,-- [6] apenas informativo
            t."idTipUnEqv",          -- [7]
            t."valEqv",              -- [8]
            c."nomCatgFinanc",       -- [9]
            c."catgParcdoSN",        -- [10]
            u."nomUnEqv"             -- [11]
          FROM "tbtipfinanc" t
          LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc"=t."idCatgFinanc"
          LEFT JOIN "tbpolitpub"  p ON p."idPolPub"=t."idPolPub"
          LEFT JOIN "tbtipuneqv"  u ON u."idTipUnEqv"=t."idTipUnEqv"
          ORDER BY t."nomFinanc" ASC
        """)
        tipos = cur.fetchall()
        conn.close()
    return assentados, tipos

def _carregar_filtros_alt():
    src = request.args
    filtros = type('F', (), {})()
    filtros.idAssent    = src.get('idAssent') or ''
    filtros.idTipFinanc = src.get('idTipFinanc') or ''
    sel_id = src.get('id') or ''
    return filtros, sel_id

# ---------- VIEW CADASTRO ----------
def view_contribCad():
    assentados, tipos = _selecoes_cadastro()
    return render_template('contribCad.html', assentados=assentados, tipos=tipos)

# ---------- ALTERAÇÃO ----------
def view_contribAlt():
    filtros, sel_id = _carregar_filtros_alt()

    conn = conectar_bd()
    assentados, tipos = [], []
    itens = []
    registro = None

    if conn:
        cur = conn.cursor()

        # selects para filtros
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome" ASC')
        assentados = cur.fetchall()

        cur.execute('SELECT "idTipFinanc","nomFinanc" FROM "tbtipfinanc" ORDER BY "nomFinanc" ASC')
        tipos = cur.fetchall()

        # monta WHERE
        params = [1]  # f."tipFinancCP" = 1 (contribuição)
        where = ['f."tipFinancCP" = %s']
        if filtros.idAssent:
            where.append('f."idAssent" = %s')
            params.append(int(filtros.idAssent))
        if filtros.idTipFinanc:
            # IMPORTANTE: filtra pelo tipo já resolvido no LATERAL (alias t)
            where.append('t."idTipFinanc" = %s')
            params.append(int(filtros.idTipFinanc))

        # LISTA (eliminação de duplicatas via LEFT JOIN LATERAL)
        cur.execute(f"""
            SELECT
                f."idSeqFinanc" AS idseq,
                f."idAssent"    AS idassent,
                a."nome",
                COALESCE(t."nomFinanc",'(tipo não definido)') AS nomtip,
                c."nomCatgFinanc" AS nomcatg,
                f."anoFinanc"  AS ano,
                f."mesFinanc"  AS mes,
                f."numParcela" AS numparc,
                f."valFinanc"  AS valor,
                f."qtdContr"   AS qtdcontr,
                f."obs"        AS obs,
                f."idCatgFinanc" AS idcatg  
            FROM "tbfinanc" f
            LEFT JOIN "tbassentado"  a ON a."idAssent"     = f."idAssent"
            LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc" = f."idCatgFinanc"
            /* escolhe exatamente 1 tipo “mais provável” p/ este lançamento */
            LEFT JOIN LATERAL (
                SELECT t.*
                FROM "tbtipfinanc" t
                WHERE t."idCatgFinanc" = f."idCatgFinanc"
                ORDER BY
                    /* 1º: se for política, prioriza o tipo com a mesma política do lançamento */
                    (t."idPolPub" IS NOT DISTINCT FROM f."idPolPub") DESC,
                    /* 2º: senão, tenta bater pelo valor equivalente */
                    (t."valEqv"   IS NOT DISTINCT FROM f."valFinanc") DESC,
                    /* 3º: fallback determinístico */
                    t."idTipFinanc" ASC
                LIMIT 1
            ) t ON TRUE
            WHERE {" AND ".join(where)}
            ORDER BY
                f."anoFinanc" DESC,
                COALESCE(f."numParcela",0) DESC,
                a."nome" ASC,
                f."idSeqFinanc" DESC
            LIMIT 200
        """, params)

        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            itens.append({cols[i]: r[i] for i in range(len(cols))})

        # DETALHE (registro selecionado)
        if sel_id:
            cur.execute("""
                SELECT
                    f."idSeqFinanc" AS idseq,
                    f."idAssent"    AS idassent,
                    a."nome",
                    COALESCE(t."nomFinanc",'(tipo não definido)') AS nomtip,
                    c."nomCatgFinanc" AS nomcatg,
                    f."anoFinanc"  AS ano,
                    f."mesFinanc"  AS mes,
                    f."numParcela" AS numparc,
                    f."valFinanc"  AS valor,
                    f."qtdContr"   AS qtdcontr,
                    f."obs"        AS obs,
                    f."idCatgFinanc" AS idcatg
                FROM "tbfinanc" f
                LEFT JOIN "tbassentado"  a ON a."idAssent"     = f."idAssent"
                LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc" = f."idCatgFinanc"
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
                WHERE f."idSeqFinanc" = %s
            """, (int(sel_id),))
            row = cur.fetchone()
            if row:
                cols = [d[0] for d in cur.description]
                registro = {cols[i]: row[i] for i in range(len(cols))}

        conn.close()

    return render_template(
        'contribAlt.html',
        assentados=assentados,
        tipos=tipos,
        filtros=filtros,
        itens=itens,
        registro=registro
    )

def alterar_contrib():
    if request.method != 'POST':
        return redirect(url_for('contribAlt'))

    idSeqFinanc = request.form.get('idSeqFinanc')
    if not idSeqFinanc:
        return redirect(url_for('contribAlt'))

    obs = (request.form.get('obs') or '').strip()
    # pode vir vazio em não-parcelado; em parcelado ignoraremos
    qtdContr_in = request.form.get('qtdContr')
    numParcela_in = request.form.get('numParcela')  # só terá valor se parcelado (campo aparece no HTML)

    # normalizações
    def _to_float(x, d=1.0):
        try:
            if x is None or str(x).strip() == '':
                return d
            return float(str(x).replace(',', '.'))
        except:
            return d

    try:
        idSeqFinanc = int(idSeqFinanc)
    except:
        flash('❌ ID inválido.', 'danger')
        return redirect(url_for('contribAlt'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.', 'danger')
        return redirect(url_for('contribAlt'))

    try:
        cur = conn.cursor()

        # Carrega dados essenciais do registro
        cur.execute("""
            SELECT
                f."idAssent",
                f."idCatgFinanc",
                f."anoFinanc",
                f."numParcela",
                COALESCE(f."qtdContr", NULL) AS qtdContr
            FROM "tbfinanc" f
            WHERE f."idSeqFinanc" = %s
        """, (idSeqFinanc,))
        row = cur.fetchone()
        if not row:
            conn.close()
            flash('❌ Registro não encontrado.', 'danger')
            return redirect(url_for('contribAlt'))

        idAssent_db, idCatg_db, ano_db, numParc_db, qtdContr_db = row

        # Se o registro é parcelado (numParcela não nulo), podemos tentar alterar o nº da parcela
        if numParc_db is not None:
            # Tenta converter novo número (se enviado)
            if numParcela_in is not None and str(numParcela_in).strip() != '':
                try:
                    novo_num = int(numParcela_in)
                except:
                    novo_num = numParc_db
                # limita entre 1..12
                if novo_num < 1: novo_num = 1
                if novo_num > 12: novo_num = 12
            else:
                novo_num = numParc_db  # nenhum valor enviado

            # Se realmente mudou, valida colisão
            if novo_num != numParc_db:
                cur.execute("""
                    SELECT COUNT(*) FROM "tbfinanc"
                    WHERE "idAssent"=%s
                      AND "idCatgFinanc"=%s
                      AND "tipFinancCP"=1
                      AND "anoFinanc"=%s
                      AND "numParcela"=%s
                      AND "idSeqFinanc"<>%s
                """, (idAssent_db, idCatg_db, ano_db, novo_num, idSeqFinanc))
                ja_existe = (cur.fetchone() or [0])[0]
                if ja_existe:
                    # colisão: alguém já usa esta parcela neste ano/categoria/assentado
                    flash('⚠️ Já existe contribuição com este nº de parcela para este assentado/categoria/ano.', 'warning')
                    conn.close()
                    # volta para a mesma tela destacando o mesmo registro
                    return redirect(url_for('contribAlt', id=idSeqFinanc))

            # Atualiza: obs e (se mudou) numParcela/mesFinanc
            cur.execute("""
                UPDATE "tbfinanc"
                   SET "obs"=%s,
                       "numParcela"=%s,
                       "mesFinanc"=%s
                 WHERE "idSeqFinanc"=%s
            """, (obs, novo_num, novo_num, idSeqFinanc))

        else:
            # NÃO parcelado: permite alterar qtdContr + obs
            qtdContr = _to_float(qtdContr_in, 1.0)
            if qtdContr <= 0:
                qtdContr = 1.0
            cur.execute("""
                UPDATE "tbfinanc"
                   SET "obs"=%s,
                       "qtdContr"=%s
                 WHERE "idSeqFinanc"=%s
            """, (obs, qtdContr, idSeqFinanc))

        conn.commit()
        flash('✅ Contribuição alterada com sucesso!', 'success')
        return redirect(url_for('contribAlt'))

    except Exception as e:
        try:
            if conn and not conn.closed:
                conn.rollback()
        except:
            pass
        print('Erro ao alterar contribuição:', e)
        flash('❌ Erro ao alterar.', 'danger')
        return redirect(url_for('contribAlt'))
    finally:
        if conn and not conn.closed:
            conn.close()
