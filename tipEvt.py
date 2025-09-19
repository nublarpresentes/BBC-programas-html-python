# tipEvt.py
import psycopg2
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

# ===================== helpers =====================

def _listar_tipevt():
    """Retorna lista (id, nome) em ordem decrescente."""
    conn = conectar_bd()
    itens = []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idTipEvt","nomTipEvt" FROM "tbtipevt" ORDER BY "idTipEvt" DESC')
        itens = cur.fetchall()
        conn.close()
    return itens

def _pegar_tipevt(id_):
    """Retorna um registro único (id, nome) ou None."""
    if not id_:
        return None
    conn = conectar_bd()
    reg = None
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idTipEvt","nomTipEvt" FROM "tbtipevt" WHERE "idTipEvt"=%s', (id_,))
        reg = cur.fetchone()
        conn.close()
    return reg

# ===================== PÁGINAS (listar + painel) =====================

def pagina_tipEvtAlt():
    """Lista + painel de alteração (mesmo HTML)."""
    itens = _listar_tipevt()
    sel_id = request.args.get('id')
    registro = _pegar_tipevt(sel_id)
    return render_template('tipEvtAlt.html', itens=itens, registro=registro)

def pagina_tipEvtExc():
    """Lista + cartão de confirmação de exclusão (mesmo HTML)."""
    itens = _listar_tipevt()
    sel_id = request.args.get('id')
    registro = _pegar_tipevt(sel_id)
    return render_template('tipEvtExc.html', itens=itens, registro=registro)

# ===================== Ações =====================

def cadastrar_tipevt():
    if request.method != 'POST':
        return redirect(url_for('tipEvtCad'))

    nomTipEvt = (request.form.get('nomTipEvt') or '').strip()
    if not nomTipEvt:
        flash('Informe o nome do tipo de evento.', 'warning')
        return redirect(url_for('tipEvtCad'))

    conn = conectar_bd()
    if not conn:
        flash('Erro ao conectar no banco.', 'danger')
        return redirect(url_for('tipEvtCad'))

    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO "tbtipevt" ("nomTipEvt") VALUES (%s)', (nomTipEvt,))
        conn.commit()
        flash('✅ Tipo de evento cadastrado com sucesso!', 'success')
        return redirect(url_for('tipEvtCad'))
    except Exception as e:
        conn.rollback()
        flash(f'❌ Erro ao cadastrar: {e}', 'danger')
        return redirect(url_for('tipEvtCad'))
    finally:
        conn.close()

def alterar_tipevt():
    if request.method != 'POST':
        return redirect(url_for('tipEvtAlt'))

    idTipEvt = request.form.get('idTipEvt')
    nomTipEvt = (request.form.get('nomTipEvt') or '').strip()
    if not idTipEvt or not nomTipEvt:
        flash('Dados incompletos.', 'warning')
        return redirect(url_for('tipEvtAlt'))

    conn = conectar_bd()
    if not conn:
        flash('Erro ao conectar no banco.', 'danger')
        return redirect(url_for('tipEvtAlt'))

    try:
        cur = conn.cursor()
        cur.execute(
            'UPDATE "tbtipevt" SET "nomTipEvt"=%s WHERE "idTipEvt"=%s',
            (nomTipEvt, int(idTipEvt))
        )
        conn.commit()
        flash('✅ Alterado com sucesso!', 'success')
        return redirect(url_for('tipEvtAlt'))
    except Exception as e:
        conn.rollback()
        flash(f'❌ Erro ao alterar: {e}', 'danger')
        return redirect(url_for('tipEvtAlt'))
    finally:
        conn.close()

def excluir_tipevt():
    if request.method != 'POST':
        return redirect(url_for('tipEvtExc'))

    idTipEvt = request.form.get('idTipEvt')
    if not idTipEvt:
        flash('Registro não informado.', 'warning')
        return redirect(url_for('tipEvtExc'))

    conn = conectar_bd()
    if not conn:
        flash('Erro ao conectar no banco.', 'danger')
        return redirect(url_for('tipEvtExc'))

    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "tbtipevt" WHERE "idTipEvt"=%s', (int(idTipEvt),))
        conn.commit()
        flash('🗑️ Excluído com sucesso!', 'success')
        return redirect(url_for('tipEvtExc'))
    except psycopg2.Error as e:
        conn.rollback()
        flash(f'❌ Não foi possível excluir (FK?): {e.pgerror}', 'danger')
        return redirect(url_for('tipEvtExc'))
    finally:
        conn.close()
