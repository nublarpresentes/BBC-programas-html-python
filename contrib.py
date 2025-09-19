import psycopg2
from datetime import datetime, date
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

# ---------- CADASTRO ----------

def cadastrar_contrib():
    if request.method != 'POST':
        return redirect(url_for('contribCad'))

    tipFinancCP = request.form.get('tipFinancCP')  # fixo "1"
    matricula   = request.form.get('matricula')
    idTipFinanc = request.form.get('idTipFinanc')
    obs         = request.form.get('obs','').strip()

    idCatgFinanc = request.form.get('idCatgFinanc')
    catgParcdoSN = request.form.get('catgParcdoSN') or 'N'
    idPolPub     = request.form.get('idPolPub') or None
    valFinanc_in = request.form.get('valFinanc')

    if tipFinancCP != '1' or not matricula or not idTipFinanc or not idCatgFinanc:
        flash('❌ Dados insuficientes.')
        return redirect(url_for('contribCad'))

    ano_atual = datetime.now().year

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro ao conectar no BD.')
        return redirect(url_for('contribCad'))

    try:
        cur = conn.cursor()

        # --- Valor para Política Pública ou outros tipos ---
        if idPolPub:
            # Busca percVal direto do tbtipfinanc
            cur.execute('SELECT COALESCE("percVal",0) FROM "tbtipfinanc" WHERE "idTipFinanc"=%s', (idTipFinanc,))
            row_val = cur.fetchone()
            valFinanc = float(row_val[0] or 0)
            if valFinanc <= 0:
                conn.close()
                flash('❌ Política Pública sem valor definido em percVal.')
                return redirect(url_for('contribCad'))
        else:
            try:
                valFinanc = float(valFinanc_in)
            except:
                conn.close()
                flash('❌ Valor inválido.')
                return redirect(url_for('contribCad'))

        inseridos = 0
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
                 WHERE "matricula"=%s AND "idCatgFinanc"=%s AND "tipFinancCP"=1
                   AND "anoFinanc"=%s
            """, (matricula, int(idCatgFinanc), ano_atual))
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
                    ("matricula","anoFinanc","mesFinanc","valFinanc",
                     "idCatgFinanc","dtPagto","obs","horario",
                     "tipFinancCP","numParcela","catgParcdoSN","idPolPub")
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    matricula, ano_atual, par, valFinanc,
                    int(idCatgFinanc), date.today(), obs, datetime.now().time(),
                    1, par, 'S', int(idPolPub) if idPolPub else None
                ))
                inseridos += 1

        else:
            cur.execute("""
                INSERT INTO "tbfinanc"
                ("matricula","anoFinanc","mesFinanc","valFinanc",
                 "idCatgFinanc","dtPagto","obs","horario",
                 "tipFinancCP","numParcela","catgParcdoSN","idPolPub")
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                matricula, ano_atual, None, valFinanc,
                int(idCatgFinanc), date.today(), obs, datetime.now().time(),
                1, 0, 'N', int(idPolPub) if idPolPub else None
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
        cur.execute('SELECT "matricula","nome" FROM "tbassentado" ORDER BY "nome" ASC')
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
    filtros.matricula = src.get('matricula') or ''
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
        cur.execute('SELECT "matricula","nome" FROM "tbassentado" ORDER BY "nome" ASC')
        assentados = cur.fetchall()
        cur.execute('SELECT "idTipFinanc","nomFinanc" FROM "tbtipfinanc" ORDER BY "nomFinanc" ASC')
        tipos = cur.fetchall()

        params = [1]  # tipFinancCP = 1
        where = ['f."tipFinancCP" = %s']
        if filtros.matricula:
            where.append('f."matricula"=%s'); params.append(filtros.matricula)
        if filtros.idTipFinanc:
            where.append('t."idTipFinanc"=%s'); params.append(int(filtros.idTipFinanc))

        cur.execute(f"""
          SELECT f."idSeqFinanc" AS idseq, f."matricula", a."nome",
                 t."nomFinanc" AS nomtip, c."nomCatgFinanc" AS nomcatg,
                 f."anoFinanc" AS ano, f."mesFinanc" AS mes,
                 f."numParcela" AS numparc, f."valFinanc" AS valor, f."obs" AS obs
            FROM "tbfinanc" f
            LEFT JOIN "tbassentado"  a ON a."matricula"=f."matricula"
            LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc"=f."idCatgFinanc"
            LEFT JOIN "tbtipfinanc"  t ON t."idCatgFinanc"=f."idCatgFinanc"
           WHERE {" AND ".join(where)}
           ORDER BY f."anoFinanc" DESC, COALESCE(f."numParcela",0) DESC, a."nome" ASC, f."idSeqFinanc" DESC
           LIMIT 200
        """, params)
        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            itens.append({cols[i]: r[i] for i in range(len(cols))})

        if sel_id:
            cur.execute("""
              SELECT f."idSeqFinanc" AS idseq, f."matricula", a."nome",
                     t."nomFinanc" AS nomtip, c."nomCatgFinanc" AS nomcatg,
                     f."anoFinanc" AS ano, f."mesFinanc" AS mes,
                     f."numParcela" AS numparc, f."valFinanc" AS valor, f."obs" AS obs
                FROM "tbfinanc" f
                LEFT JOIN "tbassentado"  a ON a."matricula"=f."matricula"
                LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc"=f."idCatgFinanc"
                LEFT JOIN "tbtipfinanc"  t ON t."idCatgFinanc"=f."idCatgFinanc"
               WHERE f."idSeqFinanc"=%s
            """, (int(sel_id),))
            row = cur.fetchone()
            if row:
                registro = {cols[i]: row[i] for i in range(len(cols))}
        conn.close()

    return render_template('contribAlt.html',
                           assentados=assentados, tipos=tipos,
                           filtros=filtros, itens=itens, registro=registro)

def alterar_contrib():
    if request.method != 'POST':
        return redirect(url_for('contribAlt'))

    idSeqFinanc = request.form.get('idSeqFinanc')
    obs = request.form.get('obs','').strip()
    if not idSeqFinanc:
        return redirect(url_for('contribAlt'))

    conn = conectar_bd()
    if not conn:
        return redirect(url_for('contribAlt'))

    try:
        cur = conn.cursor()
        cur.execute('UPDATE "tbfinanc" SET "obs"=%s WHERE "idSeqFinanc"=%s',
                    (obs, int(idSeqFinanc)))
        conn.commit()
        flash("✅ Contribuição alterada com sucesso!")
        return redirect(url_for('contribAlt'))
    except Exception as e:
        try:
            if conn and not conn.closed: conn.rollback()
        except: pass
        print("Erro ao alterar contribuição:", e)
        return redirect(url_for('contribAlt'))
    finally:
        if conn and not conn.closed: conn.close()

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@