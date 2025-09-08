import psycopg2
from flask import request, render_template, redirect, url_for
from conexao_bd import conectar_bd
from datetime import datetime

# ------------------------------
# Função: Cadastrar Tipo Contribuição
# ------------------------------

def cadastrar_tipcontrib():
    if request.method == 'POST':
        idTipContrib  = request.form['idTipContrib']
        nomContrib    = request.form['nomContrib']
        idCatgContrib = request.form['idCatgContrib']
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
            return redirect(url_for('tipContribCad'))

        try:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO "tbtipcontri"
                ("idTipContrib","nomContrib","idCatgContrib",
                 "idPolPub","valPolPub","percVal","idTipUnEqv","merecto")
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ''', (
                idTipContrib, nomContrib, idCatgContrib,
                idPolPub, valPolPub, percVal, idTipUnEqv, merecto
            ))
            conn.commit()
            conn.close()
            return redirect(url_for('tipContribCad'))

        except Exception as e:
            conn.rollback()
            conn.close()
            print("Erro ao cadastrar tipo contribuição:", e)
            return redirect(url_for('tipContribCad'))


# ------------------------------
# Função: Alterar Tipo Contribuição
# ------------------------------
def alterar_tipcontrib():
    if request.method == 'POST':
        idTipContrib = request.form['idTipContrib']
        nomContrib = request.form['nomContrib']
        idCatgContrib = request.form['idCatgContrib']
        idPolPub = request.form.get('idPolPub') or None
        percVal = request.form.get('percVal') or None
        idTipUnEqv = request.form.get('idTipUnEqv') or None
        merecto = request.form['merecto']

        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE tbtipcontri
                    SET nomContrib=%s, idCatgContrib=%s, idPolPub=%s,valPolPub=%s, percVal=%s, idTipUnEqv=%s, merecto=%s
                    WHERE idTipContrib=%s
                """, (nomContrib, idCatgContrib, idPolPub, valPolPub, percVal, idTipUnEqv, merecto))
                conn.commit()
                conn.close()
                return redirect(url_for("menuBBC"))
            except psycopg2.Error as e:
                conn.rollback()
                return render_template("tipContribCad.html", message=f"❌ Erro ao alterar: {e}")
        else:
            return "❌ Erro de conexão com BD."
