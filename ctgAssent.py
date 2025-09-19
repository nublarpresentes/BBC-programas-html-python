# ctgAssent.py
import psycopg2
from flask import request, render_template, redirect, url_for
from conexao_bd import conectar_bd

# -------- utilidades --------
def _listar():
    conn = conectar_bd()
    itens = []
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT "idCtgAssent","nomCtgAssent","descricao"
            FROM "tbctgassent"
            ORDER BY "idCtgAssent" DESC
        ''')
        itens = cur.fetchall()
        conn.close()
    return itens

def _pegar(id_):
    if not id_:
        return None
    conn = conectar_bd()
    reg = None
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT "idCtgAssent","nomCtgAssent","descricao"
            FROM "tbctgassent"
            WHERE "idCtgAssent"=%s
        ''', (id_,))
        reg = cur.fetchone()
        conn.close()
    return reg

# -------- CADASTRAR --------
def cadastrar_ctgassent():
    if request.method == 'POST':
        nome = request.form.get('nomCtgAssent','').strip()
        desc = request.form.get('descricao','').strip()

        if not nome:
            return render_template('ctgAssentCad.html', message="❌ Informe o nome da categoria.")

        conn = conectar_bd()
        if not conn:
            return render_template('ctgAssentCad.html', message="❌ Erro de conexão com BD.")

        try:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO "tbctgassent" ("nomCtgAssent","descricao")
                VALUES (%s,%s)
            ''', (nome, desc))
            conn.commit()
            conn.close()
            return render_template('ctgAssentCad.html', message="✅ Categoria cadastrada com sucesso!")
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            return render_template('ctgAssentCad.html', message=f"❌ Erro ao cadastrar: {e}")

# -------- PÁGINA ALT (GET) --------
def pagina_ctgAssentAlt():
    itens = _listar()
    sel_id = request.args.get('id')
    registro = _pegar(sel_id)
    msg_ok = "✅ Alterado com sucesso!" if request.args.get('msg') == 'ok' else None
    return render_template('ctgAssentAlt.html', itens=itens, registro=registro, msg_ok=msg_ok)

# -------- ALTERAR (POST) --------
def alterar_ctgassent():
    if request.method == 'POST':
        idCtgAssent = request.form.get('idCtgAssent')
        nome = request.form.get('nomCtgAssent','').strip()
        desc = request.form.get('descricao','').strip()

        if not (idCtgAssent and nome):
            itens = _listar()
            registro = _pegar(idCtgAssent)
            return render_template('ctgAssentAlt.html', itens=itens, registro=registro,
                                   message="❌ Informe os dados obrigatórios.")

        conn = conectar_bd()
        if not conn:
            itens = _listar()
            registro = _pegar(idCtgAssent)
            return render_template('ctgAssentAlt.html', itens=itens, registro=registro,
                                   message="❌ Erro de conexão com BD.")

        try:
            cur = conn.cursor()
            cur.execute('''
                UPDATE "tbctgassent"
                SET "nomCtgAssent"=%s, "descricao"=%s
                WHERE "idCtgAssent"=%s
            ''', (nome, desc, idCtgAssent))
            conn.commit()
            conn.close()
            return redirect(url_for('ctgAssentAlt', msg='ok'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            itens = _listar()
            registro = _pegar(idCtgAssent)
            return render_template('ctgAssentAlt.html', itens=itens, registro=registro,
                                   message=f"❌ Erro ao alterar: {e}")

# -------- PÁGINA EXC (GET) --------
def pagina_ctgAssentExc():
    itens = _listar()
    sel_id = request.args.get('id')
    registro = _pegar(sel_id)
    return render_template('ctgAssentExc.html', itens=itens, registro=registro)

# -------- EXCLUIR (POST) --------
def excluir_ctgassent():
    if request.method == 'POST':
        idCtgAssent = request.form.get('idCtgAssent')
        if not idCtgAssent:
            return redirect(url_for('ctgAssentExc'))

        conn = conectar_bd()
        if not conn:
            return redirect(url_for('ctgAssentExc'))

        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM "tbctgassent" WHERE "idCtgAssent"=%s', (idCtgAssent,))
            conn.commit()
            conn.close()
            return redirect(url_for('ctgAssentExc'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            itens = _listar()
            return render_template('ctgAssentExc.html', itens=itens, registro=None,
                                   message=f"❌ Não foi possível excluir (FK?): {e}")
