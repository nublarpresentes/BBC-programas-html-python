import psycopg2
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

# ---------------------------------
# Utilitários locais
# ---------------------------------
def _carrega_selects_basicos():
    categorias = politicas = unidades = []
    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idCatgFinanc","nomCatgFinanc","catgParcdoSN" FROM "tbcatgfinanc" ORDER BY "nomCatgFinanc"')
        categorias = cur.fetchall()
        cur.execute('SELECT "idPolPub","nomPolPub","valor","perct" FROM "tbpolitpub" ORDER BY "nomPolPub"')
        politicas = cur.fetchall()
        cur.execute('SELECT "idTipUnEqv","nomUnEqv" FROM "tbtipuneqv" ORDER BY "nomUnEqv"')
        unidades = cur.fetchall()
        conn.close()
    return categorias, politicas, unidades

def listar_tipcontrib():
    itens = []
    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT "idTipFinanc","nomFinanc","idCatgFinanc","idPolPub",
                   "valPolPub","percVal","idTipUnEqv","merecto","valEqv"
            FROM "tbtipfinanc"
            ORDER BY "idTipFinanc" DESC
        ''')
        itens = cur.fetchall()
        conn.close()
    return itens

def pegar_tipcontrib(id_):
    if not id_:
        return None
    conn = conectar_bd()
    if not conn:
        return None
    cur = conn.cursor()
    cur.execute('''
        SELECT "idTipFinanc","nomFinanc","idCatgFinanc","idPolPub",
               "valPolPub","percVal","idTipUnEqv","merecto","valEqv"
        FROM "tbtipfinanc" WHERE "idTipFinanc" = %s
    ''', (id_,))
    reg = cur.fetchone()
    conn.close()
    return reg

# ---------------------------------
# VIEWS
# ---------------------------------
def view_tipContribAlt():
    itens = listar_tipcontrib()
    categorias, politicas, unidades = _carrega_selects_basicos()
    sel_id = request.args.get('id')
    registro = pegar_tipcontrib(sel_id)
    return render_template('tipContribAlt.html',
                           itens=itens,
                           categorias=categorias,
                           politicas=politicas,
                           unidades=unidades,
                           registro=registro)

def view_tipContribExc():
    itens = listar_tipcontrib()
    categorias, politicas, unidades = _carrega_selects_basicos()
    sel_id = request.args.get('id')
    registro = pegar_tipcontrib(sel_id)
    return render_template('tipContribExc.html',
                           itens=itens,
                           categorias=categorias,
                           politicas=politicas,
                           unidades=unidades,
                           registro=registro)

# ---------------------------------
# AÇÕES
# ---------------------------------
def cadastrar_tipcontrib():
    if request.method != 'POST':
        return redirect(url_for('tipContribCad'))

    idTipFinanc  = request.form['idTipFinanc']
    nomFinanc    = request.form['nomFinanc']
    idCatgFinanc = request.form['idCatgFinanc']
    idPolPub     = request.form.get('idPolPub') or None
    idTipUnEqv   = request.form.get('idTipUnEqv') or None
    merecto      = request.form.get('merecto','')

    valPolPub = request.form.get('valPolPub') or None
    perct     = request.form.get('perct') or None
    valEqv    = request.form.get('valEqv') or None  # NOVO

    # normalização
    try: valPolPub = float(valPolPub) if valPolPub not in (None,'') else None
    except: valPolPub = None
    try: perct = float(perct) if perct not in (None,'') else 0.0
    except: perct = 0.0
    percVal = (valPolPub or 0.0) * perct if perct else None

    try: valEqv = float(valEqv) if valEqv not in (None,'') else None
    except: valEqv = None

    conn = conectar_bd()
    if not conn:
        return redirect(url_for('tipContribCad'))
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO "tbtipfinanc"
            ("idTipFinanc","nomFinanc","idCatgFinanc",
             "idPolPub","valPolPub","percVal","idTipUnEqv","merecto","valEqv")
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', (idTipFinanc, nomFinanc, idCatgFinanc,
              idPolPub, valPolPub, percVal, idTipUnEqv, merecto, valEqv))
        conn.commit()
        conn.close()
        flash("✅ Tipo de contribuição cadastrado com sucesso!")
        return redirect(url_for('tipContribCad'))
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Erro ao cadastrar tipo contribuicao:", e)
        return redirect(url_for('tipContribCad'))

def alterar_tipcontrib():
    if request.method != 'POST':
        return redirect(url_for('tipContribAlt'))

    idTipFinanc  = request.form['idTipFinanc']
    nomFinanc    = request.form['nomFinanc']
    idCatgFinanc = request.form['idCatgFinanc']
    idPolPub     = request.form.get('idPolPub') or None
    valPolPub    = request.form.get('valPolPub') or None
    perct        = request.form.get('perct') or None
    percVal      = request.form.get('percVal') or None
    idTipUnEqv   = request.form.get('idTipUnEqv') or None
    merecto      = request.form.get('merecto','')
    valEqv       = request.form.get('valEqv') or None  # NOVO

    # normalização
    try: valPolPub = float(valPolPub) if valPolPub not in (None,'') else None
    except: valPolPub = None
    try: perct = float(perct) if perct not in (None,'') else None
    except: perct = None
    try: percVal = float(percVal) if percVal not in (None,'') else None
    except: percVal = None
    try: valEqv = float(valEqv) if valEqv not in (None,'') else None
    except: valEqv = None

    conn = conectar_bd()
    if not conn:
        return render_template("tipContribAlt.html", message="❌ Erro de conexão com BD.")
    try:
        cur = conn.cursor()
        cur.execute('''
            UPDATE "tbtipfinanc"
               SET "nomFinanc"=%s,
                   "idCatgFinanc"=%s,
                   "idPolPub"=%s,
                   "valPolPub"=%s,
                   "percVal"=%s,
                   "idTipUnEqv"=%s,
                   "merecto"=%s,
                   "valEqv"=%s
             WHERE "idTipFinanc"=%s
        ''', (nomFinanc, idCatgFinanc, idPolPub, valPolPub, percVal, idTipUnEqv, merecto, valEqv, idTipFinanc))
        conn.commit()
        conn.close()
        flash("✅ Tipo de contribuição alterado com sucesso!")
        return redirect(url_for('tipContribAlt'))
    except psycopg2.Error as e:
        conn.rollback()
        conn.close()
        return render_template("tipContribAlt.html", message=f"❌ Erro ao alterar: {e}")

def excluir_tipo_contrib():
    if request.method != 'POST':
        return redirect(url_for('tipContribExc'))

    idTipFinanc = request.form.get('idTipFinanc')
    if not idTipFinanc:
        return redirect(url_for('tipContribExc'))

    conn = conectar_bd()
    if not conn:
        return redirect(url_for('tipContribExc'))
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "tbtipfinanc" WHERE "idTipFinanc"=%s', (idTipFinanc,))
        conn.commit()
        conn.close()
        flash("✅ Tipo de contribuição excluída com sucesso!")
        return redirect(url_for('tipContribExc'))
    except psycopg2.Error as e:
        conn.rollback()
        conn.close()
        itens = listar_tipcontrib()
        categorias, politicas, unidades = _carrega_selects_basicos()
        registro = pegar_tipcontrib(idTipFinanc)
        return render_template('tipContribExc.html',
                               itens=itens, categorias=categorias, politicas=politicas, unidades=unidades,
                               registro=registro, message=f"❌ Não foi possível excluir (FK?): {e}")
