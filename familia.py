# familia
# familia.py
import psycopg2
from datetime import date
from flask import request, render_template, redirect, url_for
from conexao_bd import conectar_bd

# ----------------------------------
# Utilitários de leitura
# ----------------------------------

# familia.py (trechos novos/alterados)
import psycopg2, re, unicodedata
from datetime import date
from flask import request, render_template, redirect, url_for
from conexao_bd import conectar_bd

# familia.py (trechos novos/alterados)
import psycopg2, re, unicodedata
from datetime import date
from flask import request, render_template, redirect, url_for
from conexao_bd import conectar_bd

from typing import Optional
import re
import unicodedata

# ------------------ helpers ------------------
_ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@-_")

def _strip_accents(txt: str) -> str:
    # remove acentos
    return unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore').decode('ascii')

def _sanitize_idfamilia(raw: str) -> str:
    """
    - tira espaços (inclui tabs), pontos e acentos
    - mantém somente [A-Za-z0-9@-_]
    - exige exatamente 12 chars
    """
    if raw is None:
        return ""
    s = raw.strip()
    s = _strip_accents(s)
    # remove espaços e pontos
    s = s.replace(" ", "").replace(".", "")
    # filtra apenas caracteres permitidos
    s = "".join(ch for ch in s if ch in _ALLOWED)
    return s


def _normalize_idfamilia(s: str) -> str:
    """
    Remove acentos e espaços, retorna a string normalizada.
    """
    # Remove acentos
    s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    # Troca espaços por hífen
    s = s.replace(" ", "-")
    return s


def _validate_idfamilia(s: str) -> Optional[str]:
    """
    Valida o código da família: deve ter entre 6 e 12 caracteres,
    sem acentos ou espaços. Pode conter letras, números, hífen ou @.
    """
    s_norm = _normalize_idfamilia(s)

    # Regex: só permite letras, números, hífen e arroba
    if not re.match(r'^[A-Za-z0-9@\-]{6,12}$', s_norm):
        return "Código inválido. Use apenas letras, números, '@' ou '-' e tenha entre 6 e 12 caracteres. Use '-' no lugar de espaços."

    return None



# ----------------------------------
# Cadastro
# ----------------------------------
def cadastrar_familia():
    if request.method == 'POST':
        raw_id = request.form.get('idFamilia') or ''
        idFamilia = _sanitize_idfamilia(raw_id)

        erro = _validate_idfamilia(idFamilia)
        if erro:
            return render_template('familiaCad.html', message=f"❌ {erro}")

        nomeFam    = (request.form.get('nomeFam') or '').strip()
        noMembros  = request.form.get('noMembros')

        noMembros = int(noMembros) if (noMembros and noMembros.isdigit()) else None
        dtCadastro = date.today()  # sempre data do sistema

        conn = conectar_bd()
        if not conn:
            return render_template('familiaCad.html', message="❌ Erro de conexão com BD.")

        try:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO "tbfamilia" ("idFamilia","nomeFam","noMembros","dtCadastro")
                VALUES (%s,%s,%s,%s)
            ''', (idFamilia, nomeFam, noMembros, dtCadastro))
            conn.commit()
            conn.close()
            return redirect(url_for('familiaCad'))
        except Exception as e:
            conn.rollback()
            conn.close()
            return render_template('familiaCad.html', message=f"❌ Erro ao cadastrar: {e}")

# ----------------------------------
# Alteração (dtCadastro NÃO muda)
# ----------------------------------
def alterar_familia():
    if request.method == 'POST':
        idFamilia = _sanitize_idfamilia(request.form.get('idFamilia') or '')

        erro = _validate_idfamilia(idFamilia)
        if erro:
            return render_template('familiaAlt.html',
                                   itens=listar_familias(),
                                   registro=pegar_familia(idFamilia),
                                   message=f"❌ {erro}")

        nomeFam   = (request.form.get('nomeFam') or '').strip()
        noMembros = request.form.get('noMembros')
        noMembros = int(noMembros) if (noMembros and noMembros.isdigit()) else None

        conn = conectar_bd()
        if not conn:
            return render_template('familiaAlt.html',
                                   itens=listar_familias(),
                                   registro=pegar_familia(idFamilia),
                                   message="❌ Erro de conexão com BD.")

        try:
            cur = conn.cursor()
            cur.execute('''
                UPDATE "tbfamilia"
                   SET "nomeFam"=%s,
                       "noMembros"=%s
                 WHERE "idFamilia"=%s
            ''', (nomeFam, noMembros, idFamilia))
            conn.commit()
            conn.close()
            return redirect(url_for('familiaAlt', msg='ok'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            return render_template('familiaAlt.html',
                                   itens=listar_familias(),
                                   registro=pegar_familia(idFamilia),
                                   message=f"❌ Erro ao alterar: {e}")




#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# ------------------ helpers ------------------

def listar_familias():
    conn = conectar_bd()
    itens = []
    if conn:
        cur = conn.cursor()
        # Ordena por dtCadastro (desc) e, em seguida, por id desc (lexicograficamente)
        cur.execute('''
            SELECT "idFamilia","nomeFam","noMembros","dtCadastro"
            FROM "tbfamilia"
            ORDER BY "dtCadastro" DESC NULLS LAST, "idFamilia" DESC
        ''')
        itens = cur.fetchall()
        conn.close()
    return itens

def pegar_familia(id_fam):
    if not id_fam:
        return None
    conn = conectar_bd()
    reg = None
    if conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT "idFamilia","nomeFam","noMembros","dtCadastro"
            FROM "tbfamilia"
            WHERE "idFamilia" = %s
        ''', (id_fam,))
        reg = cur.fetchone()
        conn.close()
    return reg

# ----------------------------------
# Página de Alteração (lista + painel de edição)
# ----------------------------------
def pagina_familiaAlt():
    itens = listar_familias()
    sel_id = request.args.get('id')
    registro = pegar_familia(sel_id)
    return render_template('familiaAlt.html', itens=itens, registro=registro)

def alterar_familia():
    if request.method == 'POST':
        idFamilia = (request.form.get('idFamilia') or '').strip()
        nomeFam   = (request.form.get('nomeFam') or '').strip()
        noMembros = request.form.get('noMembros')
        dtCad     = request.form.get('dtCadastro')

        noMembros = int(noMembros) if (noMembros and noMembros.isdigit()) else None
        dtCad = dtCad or None  # permite manter nulo se preferir

        conn = conectar_bd()
        if not conn:
            return redirect(url_for('familiaAlt'))

        try:
            cur = conn.cursor()
            cur.execute('''
                UPDATE "tbfamilia"
                   SET "nomeFam"=%s,
                       "noMembros"=%s,
                       "dtCadastro"=%s
                 WHERE "idFamilia"=%s
            ''', (nomeFam, noMembros, dtCad, idFamilia))
            conn.commit()
            conn.close()
            return redirect(url_for('familiaAlt', msg='ok'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            return render_template('familiaAlt.html', itens=listar_familias(),
                                   registro=pegar_familia(idFamilia),
                                   message=f"❌ Erro ao alterar: {e}")

# ----------------------------------
# Página de Exclusão (lista + painel de confirmação)
# ----------------------------------
def pagina_familiaExc():
    itens = listar_familias()
    sel_id = request.args.get('id')
    registro = pegar_familia(sel_id)
    return render_template('familiaExc.html', itens=itens, registro=registro)

def excluir_familia():
    if request.method == 'POST':
        idFamilia = request.form.get('idFamilia')
        if not idFamilia:
            return redirect(url_for('familiaExc'))

        conn = conectar_bd()
        if not conn:
            return redirect(url_for('familiaExc'))

        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM "tbfamilia" WHERE "idFamilia"=%s', (idFamilia,))
            conn.commit()
            conn.close()
            return redirect(url_for('familiaExc', msg='ok'))
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            return render_template('familiaExc.html',
                                   itens=listar_familias(),
                                   registro=pegar_familia(idFamilia),
                                   message=f"❌ Não foi possível excluir (FK?): {e}")
