# catg_usoinfr.py
import psycopg2
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

TABELA = '"tbcatgusoinfra"'

# ========================= CADASTRO =========================
def view_catgUsoInfrCad():
    return render_template('catgUsoInfrCad.html')

def cadastrar_catgUsoInfr():
    if request.method != 'POST':
        return redirect(url_for('catgUsoInfrCad'))

    nome = (request.form.get('nomCatgUsoInfr') or '').strip()
    if not nome:
        flash('❌ Informe o nome da categoria.', 'danger')
        return redirect(url_for('catgUsoInfrCad'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro ao conectar no BD.', 'danger')
        return redirect(url_for('catgUsoInfrCad'))
    try:
        cur = conn.cursor()
        # evita duplicado (case-insensitive)
        cur.execute(f'SELECT 1 FROM {TABELA} WHERE UPPER("nomCatgUsoInfr")=UPPER(%s) LIMIT 1', (nome,))
        if cur.fetchone():
            flash('⚠️ Já existe uma categoria com esse nome.', 'warning')
            conn.close()
            return redirect(url_for('catgUsoInfrCad'))

        cur.execute(f'INSERT INTO {TABELA} ("nomCatgUsoInfr") VALUES (%s)', (nome,))
        conn.commit()
        flash('✅ Categoria cadastrada!', 'success')
        return redirect(url_for('catgUsoInfrCad'))
    except Exception as e:
        if conn and not conn.closed: conn.rollback()
        print('Erro ao cadastrar catg uso infra:', e)
        flash('❌ Erro ao cadastrar.', 'danger')
        return redirect(url_for('catgUsoInfrCad'))
    finally:
        if conn and not conn.closed: conn.close()

# ========================= ALTERAÇÃO =========================
def view_catgUsoInfrAlt():
    sel_id = request.args.get('id') or ''
    registro = None
    itens = []

    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        # lista últimas 200
        cur.execute(f'''
            SELECT "idCatgUsoInfr","nomCatgUsoInfr"
              FROM {TABELA}
             ORDER BY "nomCatgUsoInfr" ASC
             LIMIT 200
        ''')
        itens = cur.fetchall()

        if sel_id:
            cur.execute(f'''
                SELECT "idCatgUsoInfr","nomCatgUsoInfr"
                  FROM {TABELA} WHERE "idCatgUsoInfr"=%s
            ''', (int(sel_id),))
            row = cur.fetchone()
            if row:
                registro = {'id': row[0], 'nome': row[1]}
        conn.close()

    return render_template('catgUsoInfrAlt.html', itens=itens, registro=registro)

def alterar_catgUsoInfr():
    if request.method != 'POST':
        return redirect(url_for('catgUsoInfrAlt'))

    id_ = request.form.get('idCatgUsoInfr')
    nome = (request.form.get('nomCatgUsoInfr') or '').strip()
    if not id_:
        return redirect(url_for('catgUsoInfrAlt'))
    if not nome:
        flash('❌ Nome não pode ser vazio.', 'danger')
        return redirect(url_for('catgUsoInfrAlt', id=id_))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro ao conectar no BD.', 'danger')
        return redirect(url_for('catgUsoInfrAlt', id=id_))
    try:
        cur = conn.cursor()
        # check duplicado (exceto o próprio id)
        cur.execute(f'''
            SELECT 1 FROM {TABELA}
             WHERE UPPER("nomCatgUsoInfr")=UPPER(%s)
               AND "idCatgUsoInfr"<>%s
             LIMIT 1
        ''', (nome, int(id_)))
        if cur.fetchone():
            flash('⚠️ Já existe categoria com esse nome.', 'warning')
            conn.close()
            return redirect(url_for('catgUsoInfrAlt', id=id_))

        cur.execute(f'''
            UPDATE {TABELA}
               SET "nomCatgUsoInfr"=%s
             WHERE "idCatgUsoInfr"=%s
        ''', (nome, int(id_)))
        conn.commit()
        flash('✅ Categoria alterada com sucesso!', 'success')
        return redirect(url_for('catgUsoInfrAlt'))
    except Exception as e:
        if conn and not conn.closed: conn.rollback()
        print('Erro ao alterar catg uso infra:', e)
        flash('❌ Erro ao alterar.', 'danger')
        return redirect(url_for('catgUsoInfrAlt', id=id_))
    finally:
        if conn and not conn.closed: conn.close()

# ========================= EXCLUSÃO =========================
def view_catgUsoInfrExc():
    sel_id = request.args.get('id') or ''
    registro = None
    itens = []

    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        cur.execute(f'''
            SELECT "idCatgUsoInfr","nomCatgUsoInfr"
              FROM {TABELA}
             ORDER BY "nomCatgUsoInfr" ASC
             LIMIT 200
        ''')
        itens = cur.fetchall()

        if sel_id:
            cur.execute(f'''
                SELECT "idCatgUsoInfr","nomCatgUsoInfr"
                  FROM {TABELA}
                 WHERE "idCatgUsoInfr"=%s
            ''', (int(sel_id),))
            row = cur.fetchone()
            if row:
                registro = {'id': row[0], 'nome': row[1]}
        conn.close()

    return render_template('catgUsoInfrExc.html', itens=itens, registro=registro)

def excluir_catgUsoInfr():
    if request.method != 'POST':
        return redirect(url_for('catgUsoInfrExc'))
    id_ = request.form.get('idCatgUsoInfr')
    if not id_:
        return redirect(url_for('catgUsoInfrExc'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro ao conectar no BD.', 'danger')
        return redirect(url_for('catgUsoInfrExc'))
    try:
        cur = conn.cursor()
        cur.execute(f'DELETE FROM {TABELA} WHERE "idCatgUsoInfr"=%s', (int(id_),))
        conn.commit()
        flash('✅ Categoria excluída!', 'success')
        return redirect(url_for('catgUsoInfrExc'))
    except psycopg2.Error as e:
        if conn and not conn.closed: conn.rollback()
        print('Erro ao excluir catg uso infra:', e)
        flash('❌ Não foi possível excluir (uso em outra tabela?).', 'danger')
        return redirect(url_for('catgUsoInfrExc'))
    finally:
        if conn and not conn.closed: conn.close()

# ========================= CONSULTA =========================
def view_catgUsoInfrCon():
    filtro = (request.args.get('q') or '').strip()
    itens = []
    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        if filtro:
            cur.execute(f'''
                SELECT "idCatgUsoInfr","nomCatgUsoInfr"
                  FROM {TABELA}
                 WHERE UPPER("nomCatgUsoInfr") LIKE UPPER(%s)
                 ORDER BY "nomCatgUsoInfr" ASC
            ''', (f'%{filtro}%',))
        else:
            cur.execute(f'''
                SELECT "idCatgUsoInfr","nomCatgUsoInfr"
                  FROM {TABELA}
                 ORDER BY "nomCatgUsoInfr" ASC
                 LIMIT 300
            ''')
        itens = cur.fetchall()
        conn.close()

    return render_template('catgUsoInfrCon.html', itens=itens, q=filtro)
