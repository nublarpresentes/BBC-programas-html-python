# sitAssent.py
import psycopg2
from flask import request, render_template, redirect, url_for
from conexao_bd import conectar_bd

# ========== CADASTRAR ==========
def cadastrar_sitassent():
    if request.method == 'POST':
        nom = request.form.get('nomSitAssent','').strip()
        desc = request.form.get('descricao','').strip()

        if not nom:
            return render_template('sitAssentCad.html', message="❌ Informe o nome da Situação.")

        conn = conectar_bd()
        if not conn:
            return render_template('sitAssentCad.html', message="❌ Erro de conexão com o BD.")

        try:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO "tbsitassent" ("nomSitAssent","descricao")
                VALUES (%s,%s)
            ''', (nom, desc))
            conn.commit()
            conn.close()
            # sucesso → volta ao cadastro vazio
            return render_template('sitAssentCad.html', message="✅ Situação cadastrada com sucesso!")
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            return render_template('sitAssentCad.html', message=f"❌ Erro ao cadastrar: {e}")

# Utilitário para listar
def _listar_sitassent():
    conn = conectar_bd()
    itens = []
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT "idSitAssent","nomSitAssent","descricao"
            FROM "tbsitassent"
            ORDER BY "idSitAssent" DESC
        ''')
        itens = cur.fetchall()
        conn.close()
    return itens

# Utilitário para pegar 1 registro
def _pegar_sitassent(id_):
    if not id_:
        return None
    conn = conectar_bd()
    reg = None
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT "idSitAssent","nomSitAssent","descricao"
            FROM "tbsitassent"
            WHERE "idSitAssent" = %s
        ''', (id_,))
        reg = cur.fetchone()
        conn.close()
    return reg

# ========== PÁGINA: LISTA + ALTERAR (GET) ==========
def pagina_sitAssentAlt():
    itens = _listar_sitassent()
    sel_id = request.args.get('id')
    registro = _pegar_sitassent(sel_id)
    return render_template('sitAssentAlt.html', itens=itens, registro=registro)

# ========== ALTERAR (POST) ==========
def alterar_sitassent():
    if request.method == 'POST':
        idSitAssent = request.form.get('idSitAssent')
        nom = request.form.get('nomSitAssent','').strip()
        desc = request.form.get('descricao','').strip()

        if not (idSitAssent and nom):
            # volta para página de alt com mensagem
            itens = _listar_sitassent()
            registro = _pegar_sitassent(idSitAssent)
            return render_template('sitAssentAlt.html', itens=itens, registro=registro,
                                   message="❌ Informe os dados obrigatórios.")

        conn = conectar_bd()
        if not conn:
            itens = _listar_sitassent()
            registro = _pegar_sitassent(idSitAssent)
            return render_template('sitAssentAlt.html', itens=itens, registro=registro,
                                   message="❌ Erro de conexão com o BD.")

        try:
            cur = conn.cursor()
            cur.execute('''
                UPDATE "tbsitassent"
                SET "nomSitAssent"=%s, "descricao"=%s
                WHERE "idSitAssent"=%s
            ''', (nom, desc, idSitAssent))
            conn.commit()
            conn.close()
            # redireciona para a lista com msg
            return redirect(url_for('sitAssentAlt', msg="ok"))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            itens = _listar_sitassent()
            registro = _pegar_sitassent(idSitAssent)
            return render_template('sitAssentAlt.html', itens=itens, registro=registro,
                                   message=f"❌ Erro ao alterar: {e}")

# ========== PÁGINA: LISTA + CONFIRMAR EXCLUSÃO (GET) ==========
def pagina_sitAssentExc():
    itens = _listar_sitassent()
    sel_id = request.args.get('id')
    registro = _pegar_sitassent(sel_id)
    return render_template('sitAssentExc.html', itens=itens, registro=registro)

# ========== EXCLUIR (POST) ==========
def excluir_sitassent():
    if request.method == 'POST':
        idSitAssent = request.form.get('idSitAssent')
        if not idSitAssent:
            return redirect(url_for('sitAssentExc'))

        conn = conectar_bd()
        if not conn:
            return redirect(url_for('sitAssentExc'))

        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM "tbsitassent" WHERE "idSitAssent"=%s', (idSitAssent,))
            conn.commit()
            conn.close()
            return redirect(url_for('sitAssentExc'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            itens = _listar_sitassent()
            return render_template('sitAssentExc.html', itens=itens, registro=None,
                                   message=f"❌ Não foi possível excluir (FK?): {e}")
