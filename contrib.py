import psycopg2
from datetime import datetime, date
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

# ---------- CADASTRO ----------
#   ATENÇÃO  =>    A NOMENCLATURA DE CONTRIBUIÇÃO MUDOU PARA RETRIBUIÇÃO
#                  MAS OS NOMES DOS PROGRAMAS E DAS ROTINAS NÃO MUDARAM - ficou CONTRIB O PREFIXO;
#                  PORÉM AS AS INTERFACES / MENSAGENS MUDARAM DE CONTRIBUICAO PARA RETRIBUIÇÃO
#                  ou seja; no BANCO DE DADOS , O TIPO FINANC CONTINUA = 1 ( RETRIBUIÇÃO )
def cadastrar_contrib():
    if request.method != 'POST':
        return redirect(url_for('contribCad'))

    tipFinancCP  = (request.form.get('tipFinancCP') or '1').strip()
    idAssent     = request.form.get('idAssent') or request.form.get('matricula')
    idTipFinanc  = request.form.get('idTipFinanc')
    obs          = (request.form.get('obs','').strip())

    # OBS: não trabalhamos mais com Política Pública aqui
    idCatgFinanc = (request.form.get('idCatgFinanc') or '').strip()
    catgParcdoSN = (request.form.get('catgParcdoSN') or 'N').strip().upper()
    valFinanc_in = request.form.get('valFinanc')

    # quantidade (para itens NÃO parcelados)
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

        # Completa dados do tipo (e valida que NÃO é política pública)
        cur.execute("""
            SELECT
                t."idCatgFinanc",
                t."idPolPub",      -- se tiver algo aqui, é política (não permitido)
                t."valEqv"
            FROM "tbtipfinanc" t
            WHERE t."idTipFinanc"=%s
        """, (idTipFinanc,))
        row = cur.fetchone()
        if not row:
            conn.close()
            flash('❌ Tipo de retribuição inexistente.')
            return redirect(url_for('contribCad'))

        tipo_catg, tipo_polpub, valEqv = row

        # regra: retribuição NÃO aceita categoria 1 nem idPolPub definido
        if tipo_catg == 1 or tipo_polpub is not None:
            conn.close()
            flash('❌ Este tipo pertence à Política Pública. Use a tela de Retribuição.', 'danger')
            return redirect(url_for('contribCad'))

        # se idCatgFinanc veio vazio, use o do tipo
        if not idCatgFinanc:
            idCatgFinanc = tipo_catg

        # valor: usa valFinanc informado; se vazio, cai no valEqv do tipo
        try:
            valFinanc = float(valFinanc_in) if valFinanc_in not in (None,'') else float(valEqv or 0)
        except:
            valFinanc = 0.0
        if valFinanc <= 0:
            conn.close()
            flash('❌ Valor da retribuição não informado.', 'danger')
            return redirect(url_for('contribCad'))

        inseridos = 0

        # Se a categoria for parcelada (ex.: Mensalidade idCatg=3), respeita nº de parcelas
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
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL)
                """, (
                    idAssent, ano_atual, par, valFinanc,
                    int(idCatgFinanc), date.today(), obs, datetime.now().time(),
                    1, par, 'S'
                ))
                inseridos += 1

        # Não parcelado: grava qtdContr
        else:
            cur.execute("""
                INSERT INTO "tbfinanc"
                ("idAssent","anoFinanc","mesFinanc","valFinanc",
                 "idCatgFinanc","dtPagto","obs","horario",
                 "tipFinancCP","numParcela","catgParcdoSN","idPolPub","qtdContr")
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,%s)
            """, (
                idAssent, ano_atual, None, valFinanc,
                int(idCatgFinanc), date.today(), obs, datetime.now().time(),
                1, 0, 'N', float(qtdContr or 1.0)
            ))
            inseridos = 1

        conn.commit()
        flash(f"✅ Retribuição registrada ({inseridos} registro(s)).", 'success')
        return redirect(url_for('contribCad'))

    except Exception as e:
        try:
            if conn and not conn.closed:
                conn.rollback()
        except:
            pass
        print("Erro ao cadastrar retribuição:", e)
        flash("❌ Erro ao cadastrar.", 'danger')
        return redirect(url_for('contribCad'))
    finally:
        if conn and not conn.closed:
            conn.close()

# ---------- helpers ----------

def _selecoes_cadastro():
    """
    Assentados e Tipos PARA RETRIBUIÇÃO:
      - EXCLUI Política Pública (idCatgFinanc = 1).
    """
    conn = conectar_bd()
    assentados, tipos = [], []
    if conn:
        cur = conn.cursor()

        # Assentados (ordem alfabética)
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome" ASC')
        assentados = cur.fetchall()

        # Tipos de retribuição (tudo MENOS Política Pública)
        cur.execute("""
          SELECT
            t."idTipFinanc",   -- [0]
            t."nomFinanc",     -- [1]
            t."idCatgFinanc",  -- [2]  (≠ 1)
            t."valEqv",        -- [3]
            c."nomCatgFinanc", -- [4]
            c."catgParcdoSN",  -- [5]
            u."nomUnEqv"       -- [6]
          FROM "tbtipfinanc" t
          LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc"=t."idCatgFinanc"
          LEFT JOIN "tbtipuneqv"  u ON u."idTipUnEqv"=t."idTipUnEqv"
          WHERE t."idCatgFinanc" <> 1
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

# ---------- ALTERAÇÃO (sem mudanças estruturais) ----------

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

        # TIPOS (se quiser pode filtrar aqui também para ≠ 1, mas deixei geral)
        cur.execute('SELECT "idTipFinanc","nomFinanc" FROM "tbtipfinanc" ORDER BY "nomFinanc" ASC')
        tipos = cur.fetchall()

        params = [1]  # f."tipFinancCP" = 1 (retribuição)
        where = ['f."tipFinancCP" = %s']
        if filtros.idAssent:
            where.append('f."idAssent" = %s')
            params.append(int(filtros.idAssent))
        if filtros.idTipFinanc:
            where.append('t."idTipFinanc" = %s')
            params.append(int(filtros.idTipFinanc))

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
    qtdContr_in = request.form.get('qtdContr')
    numParcela_in = request.form.get('numParcela')

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

        if numParc_db is not None:
            if numParcela_in is not None and str(numParcela_in).strip() != '':
                try:
                    novo_num = int(numParcela_in)
                except:
                    novo_num = numParc_db
                if novo_num < 1: novo_num = 1
                if novo_num > 12: novo_num = 12
            else:
                novo_num = numParc_db

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
                    flash('⚠️ Já existe retribuição com este nº de parcela para este assentado/categoria/ano.', 'warning')
                    conn.close()
                    return redirect(url_for('contribAlt', id=idSeqFinanc))

            cur.execute("""
                UPDATE "tbfinanc"
                   SET "obs"=%s, "numParcela"=%s, "mesFinanc"=%s
                 WHERE "idSeqFinanc"=%s
            """, (obs, novo_num, novo_num, idSeqFinanc))

        else:
            qtdContr = _to_float(qtdContr_in, 1.0)
            if qtdContr <= 0:
                qtdContr = 1.0
            cur.execute("""
                UPDATE "tbfinanc"
                   SET "obs"=%s, "qtdContr"=%s
                 WHERE "idSeqFinanc"=%s
            """, (obs, qtdContr, idSeqFinanc))

        conn.commit()
        flash('✅ Retribuição alterada com sucesso!', 'success')
        return redirect(url_for('contribAlt'))

    except Exception as e:
        try:
            if conn and not conn.closed:
                conn.rollback()
        except:
            pass
        print('Erro ao alterar retribuição:', e)
        flash('❌ Erro ao alterar.', 'danger')
        return redirect(url_for('contribAlt'))
    finally:
        if conn and not conn.closed:
            conn.close()
