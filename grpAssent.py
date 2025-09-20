# grpAssent.py
import psycopg2
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

# ----------------- HELPERS -----------------
def _carregar_selects():
    """Carrega listas p/ selects (ordem alfabética)."""
    conn = conectar_bd()
    assentados, grupos = [], []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome" ASC')
            assentados = cur.fetchall()
            cur.execute('SELECT "idGrpPartlh","nomGrpParth" FROM "tbgrppartlh" ORDER BY "nomGrpParth" ASC')
            grupos = cur.fetchall()
        finally:
            conn.close()
    return assentados, grupos

def _listar_vinculos(idAssent=None, idGrpParth=None):
    """Lista vínculos com filtros opcionais."""
    conn = conectar_bd()
    itens = []
    if conn:
        try:
            cur = conn.cursor()
            where = []
            params = []
            if idAssent:
                where.append('ag."idAssent" = %s')
                params.append(idAssent)
            if idGrpParth:
                where.append('ag."idGrpParth" = %s')
                params.append(int(idGrpParth))
            where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''

            cur.execute(f"""
                SELECT ag.idassentgrp,
                       ag.idAssent,
                       a."nome" AS nome_assentado,
                       ag."idGrpParth",
                       g."nomGrpParth" AS nome_grupo
                  FROM "tbassentgrp" ag
             LEFT JOIN "tbassentado" a ON a."idAssent" = ag."idAssent"
             LEFT JOIN "tbgrppartlh" g ON g."idGrpPartlh" = ag."idGrpParth"
                {where_sql}
              ORDER BY ag.idassentgrp DESC
            """, params)
            itens = cur.fetchall()
        finally:
            conn.close()
    return itens

def _pegar_vinculo(id_):
    if not id_:
        return None
    conn = conectar_bd()
    reg = None
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT ag.idassentgrp,
                       ag.idAssent,
                       a."nome" AS nome_assentado,
                       ag."idGrpParth",
                       g."nomGrpParth" AS nome_grupo
                  FROM "tbassentgrp" ag
             LEFT JOIN "tbassentado" a ON a."idAssent" = ag."idAssent"
             LEFT JOIN "tbgrppartlh" g ON g."idGrpPartlh" = ag."idGrpParth"
                 WHERE ag.idassentgrp = %s
            """, (id_,))
            reg = cur.fetchone()
        finally:
            conn.close()
    return reg

def _ja_existe(idAssent, idGrpParth):
    """Evita duplicar mesma matrícula no mesmo grupo."""
    conn = conectar_bd()
    existe = False
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 1
                  FROM "tbassentgrp"
                 WHERE "idAssent"=%s AND "idGrpParth"=%s
                 LIMIT 1
            """, (idAssent, idGrpParth))
            existe = cur.fetchone() is not None
        finally:
            conn.close()
    return existe

def _ler_filtros():
    """Lê filtros de querystring (GET) p/ listar/filtrar."""
    idAssent = request.args.get('idAssent', '').strip()
    idGrpParth = request.args.get('idGrpParth', '').strip()
    # normaliza vazio -> None
    idAssent = idAssent or None
    idGrpParth = idGrpParth or None
    return idAssent, idGrpParth

# ----------------- PÁGINAS -----------------
def pagina_grpAssentCad():
    assentados, grupos = _carregar_selects()
    return render_template('grpAssentCad.html', assentados=assentados, grupos=grupos)

def pagina_grpAssentAlt():
    sel_id = request.args.get('id')
    # filtros de lista
    f_matricula, f_idGrpParth = _ler_filtros()
    itens = _listar_vinculos(f_matricula, f_idGrpParth)
    registro = _pegar_vinculo(sel_id)
    assentados, grupos = _carregar_selects()
    return render_template('grpAssentAlt.html',
                           itens=itens, registro=registro,
                           assentados=assentados, grupos=grupos,
                           f_matricula=f_matricula or '',
                           f_idGrpParth=f_idGrpParth or '')

def pagina_grpAssentExc():
    sel_id = request.args.get('id')
    f_matricula, f_idGrpParth = _ler_filtros()
    itens = _listar_vinculos(f_matricula, f_idGrpParth)
    registro = _pegar_vinculo(sel_id)
    assentados, grupos = _carregar_selects()
    return render_template('grpAssentExc.html',
                           itens=itens, registro=registro,
                           assentados=assentados, grupos=grupos,
                           f_matricula=f_matricula or '',
                           f_idGrpParth=f_idGrpParth or '')

# ----------------- AÇÕES -----------------
def cadastrar_grpAssent():
    if request.method != 'POST':
        return redirect(url_for('grpAssentCad'))

    idAssent  = request.form.get('idAssent')
    idGrpParth = request.form.get('idGrpParth')  # nome exato do DDL (sem 'l')

    if not idAssent or not idGrpParth:
        flash('Informe Assentado e Grupo.', 'warning')
        return redirect(url_for('grpAssentCad'))

    if _ja_existe(idAssent, int(idGrpParth)):
        flash('⚠️ Esse assentado já está nesse grupo.', 'warning')
        return redirect(url_for('grpAssentCad'))

    conn = conectar_bd()
    if not conn:
        flash('Erro de conexão com o banco.', 'danger')
        return redirect(url_for('grpAssentCad'))

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO "tbassentgrp" ("idAssent","idGrpParth")
            VALUES (%s,%s)
        """, (idAssent, int(idGrpParth)))
        conn.commit()
        flash('✅ Vinculado com sucesso!', 'success')
        return redirect(url_for('grpAssentCad'))
    except Exception as e:
        conn.rollback()
        flash(f'❌ Erro ao cadastrar: {e}', 'danger')
        return redirect(url_for('grpAssentCad'))
    finally:
        conn.close()

def alterar_grpAssent():
    if request.method != 'POST':
        return redirect(url_for('grpAssentAlt'))

    idassentgrp = request.form.get('idassentgrp')
    idAssent   = request.form.get('idAssent')
    idGrpParth  = request.form.get('idGrpParth')

    if not idassentgrp or not idAssent or not idGrpParth:
        flash('Dados incompletos.', 'warning')
        return redirect(url_for('grpAssentAlt'))

    # evita duplicar destino
    if _ja_existe(idAssent, int(idGrpParth)):
        flash('⚠️ Já existe esse vínculo (assentado + grupo).', 'warning')
        return redirect(url_for('grpAssentAlt'))

    conn = conectar_bd()
    if not conn:
        flash('Erro de conexão com o banco.', 'danger')
        return redirect(url_for('grpAssentAlt'))

    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE "tbassentgrp"
               SET "idAssent"=%s,
                   "idGrpParth"=%s
             WHERE idassentgrp=%s
        """, (idAssent, int(idGrpParth), int(idassentgrp)))
        conn.commit()
        flash('✅ Alterado com sucesso!', 'success')
        return redirect(url_for('grpAssentAlt'))
    except Exception as e:
        conn.rollback()
        flash(f'❌ Erro ao alterar: {e}', 'danger')
        return redirect(url_for('grpAssentAlt'))
    finally:
        conn.close()

def excluir_grpAssent():
    if request.method != 'POST':
        return redirect(url_for('grpAssentExc'))

    idassentgrp = request.form.get('idassentgrp')
    if not idassentgrp:
        flash('Registro não informado.', 'warning')
        return redirect(url_for('grpAssentExc'))

    conn = conectar_bd()
    if not conn:
        flash('Erro de conexão com o banco.', 'danger')
        return redirect(url_for('grpAssentExc'))

    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "tbassentgrp" WHERE idassentgrp=%s', (int(idassentgrp),))
        conn.commit()
        flash('🗑️ Excluído com sucesso!', 'success')
        return redirect(url_for('grpAssentExc'))
    except psycopg2.Error as e:
        conn.rollback()
        flash(f'❌ Não foi possível excluir (FK?): {e.pgerror}', 'danger')
        return redirect(url_for('grpAssentExc'))
    finally:
        conn.close()
