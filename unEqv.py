# unEqv.py
import psycopg2
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

# ------------------------------
# Utilidades (listar/pegar)
# ------------------------------
def listar_uneqv():
    conn = conectar_bd()
    itens = []
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT "idTipUnEqv","nomUnEqv"
            FROM "tbtipuneqv"
            ORDER BY "idTipUnEqv" DESC
        ''')
        itens = cur.fetchall()
        conn.close()
    return itens

def pegar_uneqv(sel_id):
    if not sel_id:
        return None
    conn = conectar_bd()
    reg = None
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT "idTipUnEqv","nomUnEqv"
            FROM "tbtipuneqv"
            WHERE "idTipUnEqv" = %s
        ''', (sel_id,))
        reg = cur.fetchone()
        conn.close()
    return reg

# ------------------------------
# PÁGINAS (render) – deixamos fora do BBC.py
# ------------------------------
def pagina_unEqvAlt():
    itens = listar_uneqv()
    sel_id = request.args.get('id')
    registro = pegar_uneqv(sel_id)
    return render_template('unEqvAlt.html', itens=itens, registro=registro)

def pagina_unEqvExc():
    itens = listar_uneqv()
    sel_id = request.args.get('id')
    registro = pegar_uneqv(sel_id)
    return render_template('unEqvExc.html', itens=itens, registro=registro)

# ------------------------------
# INCLUSÃO
# ------------------------------
def cadastrar_uneqv():
    if request.method == 'POST':
        nomUnEqv = request.form.get('nomUnEqv', '').strip()
        if not nomUnEqv:
            flash('Informe o nome da unidade de equivalia.', 'warning')
            return redirect(url_for('unEqvCad'))

        conn = conectar_bd()
        if not conn:
            flash('❌ Erro de conexão com BD.', 'danger')
            return redirect(url_for('unEqvCad'))

        try:
            cur = conn.cursor()
            # idTipUnEqv é SERIAL (DEFAULT nextval), não informar no INSERT
            cur.execute('''
                INSERT INTO "tbtipuneqv" ("nomUnEqv")
                VALUES (%s)
            ''', (nomUnEqv,))
            conn.commit()
            conn.close()
            flash('✅ Unidade de Equivalia cadastrada com sucesso!', 'success')
            return redirect(url_for('unEqvCad'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            flash(f'❌ Erro ao cadastrar: {e}', 'danger')
            return redirect(url_for('unEqvCad'))

# ------------------------------
# ALTERAÇÃO
# ------------------------------
def alterar_uneqv():
    if request.method == 'POST':
        idTipUnEqv = request.form.get('idTipUnEqv')
        nomUnEqv   = request.form.get('nomUnEqv', '').strip()

        if not idTipUnEqv:
            flash('Registro inválido.', 'warning')
            return redirect(url_for('unEqvAlt'))

        if not nomUnEqv:
            flash('Informe o nome da unidade de equivalia.', 'warning')
            return redirect(url_for('unEqvAlt', id=idTipUnEqv))

        conn = conectar_bd()
        if not conn:
            flash('❌ Erro de conexão com BD.', 'danger')
            return redirect(url_for('unEqvAlt'))

        try:
            cur = conn.cursor()
            cur.execute('''
                UPDATE "tbtipuneqv"
                SET "nomUnEqv"=%s
                WHERE "idTipUnEqv"=%s
            ''', (nomUnEqv, idTipUnEqv))
            conn.commit()
            conn.close()
            flash('✅ Alterado com sucesso!', 'success')
            return redirect(url_for('unEqvAlt'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            flash(f'❌ Erro ao alterar: {e}', 'danger')
            return redirect(url_for('unEqvAlt', id=idTipUnEqv))

# ------------------------------
# EXCLUSÃO
# ------------------------------
def excluir_uneqv():
    if request.method == 'POST':
        idTipUnEqv = request.form.get('idTipUnEqv')
        if not idTipUnEqv:
            flash('Registro inválido.', 'warning')
            return redirect(url_for('unEqvExc'))

        conn = conectar_bd()
        if not conn:
            flash('❌ Erro de conexão com BD.', 'danger')
            return redirect(url_for('unEqvExc'))

        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM "tbtipuneqv" WHERE "idTipUnEqv" = %s', (idTipUnEqv,))
            conn.commit()
            conn.close()
            flash('🗑️ Excluído com sucesso!', 'success')
            return redirect(url_for('unEqvExc'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            flash(f'❌ Não foi possível excluir (FK? Em uso): {e}', 'danger')
            return redirect(url_for('unEqvExc', id=idTipUnEqv))
