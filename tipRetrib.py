import psycopg2
from flask import request, render_template, redirect, url_for
from conexao_bd import conectar_bd
from datetime import datetime

# ------------------------------------
# Função: Cadastrar Tipo Contribuição
# -------------------------------------

def cadastrar_tipretrib():
    if request.method == 'POST':
        idTipFinanc  = request.form['idTipFinanc']
        nomFinanc    = request.form['nomFinanc']
        idCatgFinanc = request.form['idCatgFinanc']
        idPolPub      = request.form.get('idPolPub') or None
        idTipUnEqv    = request.form.get('idTipUnEqv') or None
        merecto       = request.form.get('merecto','')

        valPolPub = request.form.get('valPolPub') or None
        perct     = request.form.get('perct') or None

        # conversões numéricas
        valPolPub = float(valPolPub) if valPolPub not in (None,'') else None
        perct     = float(perct)     if perct     not in (None,'') else 0.0
        percVal   = (valPolPub or 0.0) * perct if perct else None

        conn = conectar_bd()
        if not conn:
            return redirect(url_for('tipRetribCad'))

        try:
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
            return redirect(url_for('tipRetribCad'))

        except Exception as e:
            conn.rollback()
            conn.close()
            print("Erro ao cadastrar tipo retribuição:", e)
            return redirect(url_for('tipRetribCad'))


# ----------------------------------
# Função: Alterar Tipo retribuicao
# ----------------------------------
def alterar_tipretrib():
    if request.method == 'POST':
        idTipFinanc = request.form['idTipFinanc']
        nomFinanc = request.form['nomFinanc']
        idCatgFinanc = request.form['idCatgFinanc']
        idPolPub = request.form.get('idPolPub') or None
        percVal = request.form.get('percVal') or None
        idTipUnEqv = request.form.get('idTipUnEqv') or None
        merecto = request.form['merecto']

        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE tbtipfinanc
                    SET nomFinanc=%s, idCatgFinanc=%s, idPolPub=%s,valPolPub=%s, percVal=%s, idTipUnEqv=%s, merecto=%s
                    WHERE idTipFinanc=%s
                """, (nomFinanc, idCatgFinanc, idPolPub, valPolPub, percVal, idTipUnEqv, merecto))
                conn.commit()
                conn.close()
                return redirect(url_for("menuBBC"))
            except psycopg2.Error as e:
                conn.rollback()
                return render_template("tipRetribCad.html", message=f"❌ Erro ao alterar: {e}")
        else:
            return "❌ Erro de conexão com BD."


def listar_tipcontrib():
    conn = conectar_bd()
    itens = []
    if conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t."idTipFinanc", t."nomFinanc",
                   COALESCE(cf."nomCatgFinanc",'') AS catg,
                   COALESCE(p."nomPolPub",'')      AS pol,
                   t."valPolPub", t."percVal",
                   COALESCE(u."nomUnEqv",'')       AS un,
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
    reg = None
    if conn:
        cur = conn.cursor()
        cur.execute("""
           SELECT "idTipFinanc","nomFinanc","idCatgFinanc","idPolPub",
                  "valPolPub","percVal","idTipUnEqv","merecto"
           FROM "tbtipfinanc" WHERE "idTipFinanc"=%s
        """, (id_,))
        reg = cur.fetchone()
        conn.close()
    return reg
