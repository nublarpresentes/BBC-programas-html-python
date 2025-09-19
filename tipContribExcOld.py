import psycopg2
from flask import request, render_template, redirect, url_for
from conexao_bd import conectar_bd
from datetime import datetime

# -------------------------------------
# Função: Cadastrar Tipo Contribuição
# ------------------------------------

def cadastrar_tipcontrib():
    if request.method == 'POST':
        print(f"111 cadastrar_tipcontrib " )
        idTipFinanc  = request.form['idTipFinanc']
        nomFinanc    = request.form['nomFinanc']
        idCatgFinanc = request.form['idCatgFinanc']
        idPolPub      = request.form.get('idPolPub') or None
        idTipUnEqv    = request.form.get('idTipUnEqv') or None
        merecto       = request.form.get('merecto','')

        valPolPub = request.form.get('valPolPub') or None
        perct     = request.form.get('perct') or None
        print(f"222 cadastrar_tipcontrib poli pub e valor  ", {idPolPub},{valPolPub} )
        # conversões numéricas
        valPolPub = float(valPolPub) if valPolPub not in (None,'') else None
        perct     = float(perct)     if perct     not in (None,'') else 0.0
        percVal   = (valPolPub or 0.0) * perct if perct else None

        conn = conectar_bd()
        if not conn:
            return redirect(url_for('tipContribCad'))

        try:
            print(f"333 cadastrar_tipcontrib dentro do try ", {idPolPub}, {valPolPub})
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO "tbtipfinanc"
                ("idTipFinanc","nomFinanc","idCatgFinanc",
                 "idPolPub","valPolPub","percVal","idTipUnEqv","merecto")
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ''', (
                idTipFinanc, nomFinanc, idCatgFinanc,
                idPolPub, valPolPub, percVal, idTipUnEqv, merecto
            ))
            conn.commit()
            conn.close()
            return redirect(url_for('tipContribCad'))

        except Exception as e:
            conn.rollback()
            conn.close()
            print("Erro ao cadastrar tipo contribuicao", e)
            return redirect(url_for('tipContribCad'))

# ----------------------------------
# Função: Alterar Tipo de Contribuição
# ----------------------------------
def alterar_tipcontrib():
    if request.method == 'POST':
        idTipFinanc  = request.form['idTipFinanc']
        nomFinanc    = request.form['nomFinanc']
        idCatgFinanc = request.form['idCatgFinanc']

        idPolPub   = request.form.get('idPolPub') or None
        valPolPub  = request.form.get('valPolPub') or None
        perct      = request.form.get('perct') or None   # percentual cru (ex.: 0.12)
        percVal    = request.form.get('percVal') or None # valor cobrado já calculado/mostrado

        idTipUnEqv = request.form.get('idTipUnEqv') or None
        merecto    = request.form.get('merecto', '')

        # normalizações numéricas
        if valPolPub not in (None, ''):
            try: valPolPub = float(valPolPub)
            except: valPolPub = None
        else:
            valPolPub = None

        if perct not in (None, ''):
            try: perct = float(perct)
            except: perct = None
        else:
            perct = None

        if percVal not in (None, ''):
            try: percVal = float(percVal)
            except: percVal = None
        else:
            percVal = None

        conn = conectar_bd()
        if not conn:
            return render_template("tipContribAlt.html", message="❌ Erro de conexão com BD.")

        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE "tbtipfinanc"
                SET "nomFinanc"=%s,
                    "idCatgFinanc"=%s,
                    "idPolPub"=%s,
                    "valPolPub"=%s,
                    "percVal"=%s,
                    "idTipUnEqv"=%s,
                    "merecto"=%s
                WHERE "idTipFinanc"=%s
            """, (nomFinanc, idCatgFinanc, idPolPub, valPolPub, percVal, idTipUnEqv, merecto, idTipFinanc))
            conn.commit()
            conn.close()
            return redirect(url_for("tipContribAlt"))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            return render_template("tipContribAlt.html", message=f"❌ Erro ao alterar: {e}")


# ----------------------------------
# Função: Excluir Tipo de Contribuição
# ----------------------------------
def excluir_tipo_contrib():
    if request.method == 'POST':
        idTipFinanc = request.form.get('idTipFinanc')
        if not idTipFinanc:
            return redirect(url_for('tipContribAlt'))

        conn = conectar_bd()
        if not conn:
            return redirect(url_for('tipContribAlt'))

        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM "tbtipfinanc" WHERE "idTipFinanc" = %s', (idTipFinanc,))
            conn.commit()
            conn.close()
            return redirect(url_for('tipContribAlt'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            # Em caso de FK, o banco pode bloquear exclusão.
            # Você pode tratar mostrando uma msg amigável:
            return render_template("tipContribExc.html", registro=None, message=f"❌ Não foi possível excluir (FK?): {e}")
# --- helper: lista para a tela de exclusão ---
def listar_tipcontrib():
    conn = conectar_bd()
    itens = []
    if conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t."idTipFinanc",
                   t."nomFinanc",
                   COALESCE(cf."nomCatgFinanc",'')   AS catg,
                   COALESCE(p."nomPolPub",'')        AS pol,
                   t."valPolPub",
                   t."percVal",
                   COALESCE(u."nomUnEqv",'')         AS un,
                   t."merecto"
            FROM "tbtipfinanc" t
            LEFT JOIN "tbcatgfinanc" cf ON cf."idCatgFinanc" = t."idCatgFinanc"
            LEFT JOIN "tbpolitpub"   p  ON p."idPolPub"      = t."idPolPub"
            LEFT JOIN "tbtipuneqv"   u  ON u."idTipUnEqv"    = t."idTipUnEqv"
            ORDER BY t."idTipFinanc" DESC
        """)
        itens = cur.fetchall()
        conn.close()
    return itens

def pegar_tipcontrib(id_):
    if not id_:
        return None
    conn = conectar_bd()
    registro = None
    if conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT "idTipFinanc","nomFinanc","idCatgFinanc","idPolPub",
                   "valPolPub","percVal","idTipUnEqv","merecto"
            FROM "tbtipfinanc"
            WHERE "idTipFinanc" = %s
        """, (id_,))
        registro = cur.fetchone()
        conn.close()
    return registro

