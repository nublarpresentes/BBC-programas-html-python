# grpPartlh.py
import psycopg2
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

# ----------------- HELPERS -----------------
def _listar_grupos():
    conn = conectar_bd()
    itens = []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT "idGrpPartlh", "nomGrpParth"
                  FROM "tbgrppartlh"
                 ORDER BY "idGrpPartlh" DESC
            """)
            itens = cur.fetchall()
        finally:
            conn.close()
    return itens

def _pegar_grupo(id_):
    if not id_:
        return None
    conn = conectar_bd()
    reg = None
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT "idGrpPartlh", "nomGrpParth"
                  FROM "tbgrppartlh"
                 WHERE "idGrpPartlh"=%s
            """, (id_,))
            reg = cur.fetchone()
        finally:
            conn.close()
    return reg

# ----------------- PÁGINAS -----------------
def pagina_grpPartlhAlt():
    itens = _listar_grupos()
    sel_id = request.args.get('id')
    registro = _pegar_grupo(sel_id)
    return render_template('grpPartlhAlt.html', itens=itens, registro=registro)

def pagina_grpPartlhExc():
    itens = _listar_grupos()
    sel_id = request.args.get('id')
    registro = _pegar_grupo(sel_id)
    return render_template('grpPartlhExc.html', itens=itens, registro=registro)

def pagina_grpPartlhCon():
    itens = _listar_grupos()
    return render_template('grpPartlhCon.html', itens=itens)

# ----------------- AÇÕES -----------------
def cadastrar_grpPartlh():
    if request.method != 'POST':
        return redirect(url_for('grpPartlhCad'))

    nom = (request.form.get('nomGrpParth') or '').strip()
    if not nom:
        flash('Informe o nome do grupo.', 'warning')
        return redirect(url_for('grpPartlhCad'))

    conn = conectar_bd()
    if not conn:
        flash('Erro de conexão com o banco.', 'danger')
        return redirect(url_for('grpPartlhCad'))

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO "tbgrppartlh" ("nomGrpParth")
            VALUES (%s)
        """, (nom,))
        conn.commit()
        flash('✅ Grupo de Partilha cadastrado com sucesso!', 'success')
        return redirect(url_for('grpPartlhCad'))
    except Exception as e:
        conn.rollback()
        flash(f'❌ Erro ao cadastrar: {e}', 'danger')
        return redirect(url_for('grpPartlhCad'))
    finally:
        conn.close()

def alterar_grpPartlh():
    if request.method != 'POST':
        return redirect(url_for('grpPartlhAlt'))

    id_ = request.form.get('idGrpPartlh')
    nom = (request.form.get('nomGrpParth') or '').strip()
    if not id_ or not nom:
        flash('Dados incompletos.', 'warning')
        return redirect(url_for('grpPartlhAlt'))

    conn = conectar_bd()
    if not conn:
        flash('Erro de conexão com o banco.', 'danger')
        return redirect(url_for('grpPartlhAlt'))

    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE "tbgrppartlh"
               SET "nomGrpParth"=%s
             WHERE "idGrpPartlh"=%s
        """, (nom, int(id_)))
        conn.commit()
        flash('✅ Alterado com sucesso!', 'success')
        return redirect(url_for('grpPartlhAlt'))
    except Exception as e:
        conn.rollback()
        flash(f'❌ Erro ao alterar: {e}', 'danger')
        return redirect(url_for('grpPartlhAlt'))
    finally:
        conn.close()

def excluir_grpPartlh():
    if request.method != 'POST':
        return redirect(url_for('grpPartlhExc'))

    id_ = request.form.get('idGrpPartlh')
    if not id_:
        flash('Registro não informado.', 'warning')
        return redirect(url_for('grpPartlhExc'))

    conn = conectar_bd()
    if not conn:
        flash('Erro de conexão com o banco.', 'danger')
        return redirect(url_for('grpPartlhExc'))

    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "tbgrppartlh" WHERE "idGrpPartlh"=%s', (int(id_),))
        conn.commit()
        flash('🗑️ Excluído com sucesso!', 'success')
        return redirect(url_for('grpPartlhExc'))
    except psycopg2.Error as e:
        conn.rollback()
        flash(f'❌ Não foi possível excluir (FK?): {e.pgerror}', 'danger')
        return redirect(url_for('grpPartlhExc'))
    finally:
        conn.close()
