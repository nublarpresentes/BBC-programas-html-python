# polPub.py
import psycopg2
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

# ---------- Helpers (dados para selects) ----------
def _listar_entidades():
    """Lista entidades para o <select> (id, nome)."""
    entidades = []
    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        # ajuste o nome da tabela/colunas se necessário
        cur.execute('SELECT "idEntidade","nomEntidade" FROM "tbentidade" ORDER BY "nomEntidade"')
        entidades = cur.fetchall()
        conn.close()
    return entidades

def listar_politpub():
    """Lista políticas públicas para a grade (mais recentes primeiro)."""
    itens = []
    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT "idPolPub","nomPolPub","IdEntidade","valor","perct"
            FROM "tbpolitpub"
            ORDER BY "idPolPub" DESC
        ''')
        itens = cur.fetchall()
        conn.close()
    return itens

def pegar_politpub(id_):
    """Busca 1 registro pelo id."""
    if not id_:
        return None
    conn = conectar_bd()
    reg = None
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT "idPolPub","nomPolPub","IdEntidade","valor","perct"
            FROM "tbpolitpub"
            WHERE "idPolPub" = %s
        ''', (id_,))
        reg = cur.fetchone()
        conn.close()
    return reg

# ---------- Inclusão ----------
def cadastrar_politpub():
    if request.method == 'POST':
        nomPolPub  = request.form.get('nomPolPub','').strip()
        IdEntidade = request.form.get('IdEntidade') or None
        valor      = request.form.get('valor') or None
        perct      = request.form.get('perct') or None

        # validações simples
        if not nomPolPub:
            entidades = _listar_entidades()
            return render_template('politPubCad.html',
                                   message='❌ Informe o nome da Política Pública.',
                                   entidades=entidades)

        # conversões numéricas (aceita vazio -> NULL)
        try:
            valor = float(valor) if valor not in (None,'') else None
        except:
            valor = None
        try:
            perct = float(perct) if perct not in (None,'') else None
        except:
            perct = None

        conn = conectar_bd()
        if not conn:
            entidades = _listar_entidades()
            return render_template('politPubCad.html',
                                   message='❌ Erro de conexão com BD.',
                                   entidades=entidades)
        try:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO "tbpolitpub" ("nomPolPub","IdEntidade","valor","perct")
                VALUES (%s,%s,%s,%s)
            ''', (nomPolPub, IdEntidade, valor, perct))
            conn.commit()
            conn.close()
            flash('✅ Política Pública cadastrada com sucesso!', 'success')
            return redirect(url_for('politPubCad'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            entidades = _listar_entidades()
            return render_template('politPubCad.html',
                                   message=f'❌ Erro ao cadastrar: {e.pgerror}',
                                   entidades=entidades)

# ---------- Alteração ----------
def alterar_politpub():
    if request.method == 'POST':
        idPolPub   = request.form.get('idPolPub')
        nomPolPub  = request.form.get('nomPolPub','').strip()
        IdEntidade = request.form.get('IdEntidade') or None
        valor      = request.form.get('valor') or None
        perct      = request.form.get('perct') or None

        if not idPolPub:
            flash('❌ Registro não informado.', 'danger')
            return redirect(url_for('politPubAlt'))

        try:
            valor = float(valor) if valor not in (None,'') else None
        except:
            valor = None
        try:
            perct = float(perct) if perct not in (None,'') else None
        except:
            perct = None

        conn = conectar_bd()
        if not conn:
            flash('❌ Erro de conexão com BD.', 'danger')
            return redirect(url_for('politPubAlt'))

        try:
            cur = conn.cursor()
            cur.execute('''
                UPDATE "tbpolitpub"
                   SET "nomPolPub"=%s,
                       "IdEntidade"=%s,
                       "valor"=%s,
                       "perct"=%s
                 WHERE "idPolPub"=%s
            ''', (nomPolPub, IdEntidade, valor, perct, idPolPub))
            conn.commit()
            conn.close()
            flash('✅ Alterado com sucesso!', 'success')
            return redirect(url_for('politPubAlt'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            flash(f'❌ Erro ao alterar: {e.pgerror}', 'danger')
            return redirect(url_for('politPubAlt'))

# ---------- Exclusão ----------
def excluir_politpub():
    if request.method == 'POST':
        idPolPub = request.form.get('idPolPub')
        if not idPolPub:
            flash('❌ Registro não informado.', 'danger')
            return redirect(url_for('politPubExc'))

        conn = conectar_bd()
        if not conn:
            flash('❌ Erro de conexão com BD.', 'danger')
            return redirect(url_for('politPubExc'))

        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM "tbpolitpub" WHERE "idPolPub"=%s', (idPolPub,))
            conn.commit()
            conn.close()
            flash('✅ Excluído com sucesso!', 'success')
            return redirect(url_for('politPubExc'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            flash(f'❌ Não foi possível excluir (FK?): {e.pgerror}', 'danger')
            return redirect(url_for('politPubExc'))
