import psycopg2
from datetime import datetime, date
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

# ---------- CADASTRO ----------
def cadastrar_contrib():
    if request.method != 'POST':
        return redirect(url_for('contribCad'))

    tipFinancCP = request.form.get('tipFinancCP')  # "1"
    matricula   = request.form.get('matricula')
    idTipFinanc = request.form.get('idTipFinanc')
    obs         = request.form.get('obs','').strip()

    # vindos do JS com base no tipo
    idCatgFinanc = request.form.get('idCatgFinanc')
    catgParcdoSN = request.form.get('catgParcdoSN') or 'N'
    idPolPub     = request.form.get('idPolPub') or None
    valFinanc_in = request.form.get('valFinanc')  # calculado/front

    if tipFinancCP != '1' or not matricula or not idTipFinanc or not idCatgFinanc or not valFinanc_in:
        flash('❌ Dados insuficientes.')
        return redirect(url_for('contribCad'))

    # Normaliza valor
    try:
        valFinanc = float(valFinanc_in)
    except:
        flash('❌ Valor inválido.')
        return redirect(url_for('contribCad'))

    ano_atual = datetime.now().year

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro ao conectar no BD.')
        return redirect(url_for('contribCad'))

    try:
        cur = conn.cursor()

        inseridos = 0
        if catgParcdoSN == 'S':
            # quantas parcelas pagar agora
            qtd = request.form.get('qtdParcelas')
            try:
                qtd = int(qtd or '0')
            except:
                qtd = 0
            if qtd <= 0:
                conn.close()
                flash('❌ Informe o nº de parcelas a pagar.')
                return redirect(url_for('contribCad'))

            # já pagas no ano (para não passar de 12)
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
                flash('⚠️ Limite de 12 parcelas já alcançado neste ano. Nada foi inserido.')
                conn.close()
                return redirect(url_for('contribCad'))

            pagar = min(restantes, qtd)
            if pagar < qtd:
                flash(f'⚠️ Só havia espaço para {pagar} parcela(s) neste ano (máx 12).')

            for i in range(pagar):
                par = prox + i
                # mesFinanc = numParcela (1..12), dtPag=hoje, horario=agora
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
            # não parcelado → parcela única (numParcela=0/NULL; mesFinanc pode ser 0/NULL)
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
    """Assentados e Tipos (joinando catg/unidade p/ exibir no card)."""
    conn = conectar_bd()
    assentados, tipos = [], []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "matricula","nome" FROM "tbassentado" ORDER BY "nome" ASC')
        assentados = cur.fetchall()
        # (idTipFinanc, nomFinanc, idCatg, idPolPub, valPolPub, perct,
        #  idTipUnEqv, valEqv, nomCatg, catgParcdoSN, nomUnEqv)
        cur.execute("""
          SELECT t."idTipFinanc", t."nomFinanc", t."idCatgFinanc", t."idPolPub",
                 t."valPolPub", COALESCE(NULLIF(t."percVal",0), NULLIF(p."perct",0), 0) AS perct,
                 t."idTipUnEqv", t."valEqv",
                 c."nomCatgFinanc", c."catgParcdoSN",
                 u."nomUnEqv"
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