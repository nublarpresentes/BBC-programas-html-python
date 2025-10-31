# wrapper de API do assent.py
#
# api_assent.py
from flask import Blueprint, jsonify, request
from conexao_bd import conectar_bd

api_assent = Blueprint("api_assent", __name__, url_prefix="/api/assent")

# --------- UTIL: converte linhas em dicts simples ----------
def rows_to_dicts(cursor, rows):
    cols = [d[0] for d in cursor.description]
    out = []
    for r in rows:
        out.append({cols[i]: r[i] for i in range(len(cols))})
    return out

@api_assent.get("/list")
def api_assent_list():
    """
    Lista básica para popular selects/listas no mobile.
    Retorna: [{"idAssent": 123, "nome": "Fulano"}, ...]
    Aceita query ?limit=200 (padrão 200)
    """
    limit = request.args.get("limit", "200")
    try:
        limit = int(limit)
    except:
        limit = 200

    conn = conectar_bd()
    if not conn:
        return jsonify({"ok": False, "message": "Erro ao conectar no BD."}), 500

    try:
        cur = conn.cursor()
        cur.execute('SELECT "idAssent", nome FROM tbassentado ORDER BY nome ASC LIMIT %s', (limit,))
        rows = cur.fetchall()
        data = [{"idAssent": r[0], "nome": r[1]} for r in rows]
        return jsonify({"ok": True, "items": data})
    finally:
        try: conn.close()
        except: ...

@api_assent.get("/get/<int:id_assent>")
def api_assent_get(id_assent: int):
    """
    Detalhes de um assentado (campos mais usados).
    """
    conn = conectar_bd()
    if not conn:
        return jsonify({"ok": False, "message": "Erro ao conectar no BD."}), 500

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
              a."idAssent", a.nome, a.genero, a.mae, a.endereco, a.bairro,
              a.cpf, a.email, a.celular, a."idFamilia", a."idSitAssent",
              a."idCtgAssent"
            FROM tbassentado a
            WHERE a."idAssent"=%s
        """, (id_assent,))
        row = cur.fetchone()
        if not row:
            return jsonify({"ok": False, "message": "Não encontrado."}), 404

        cols = [d[0] for d in cur.description]
        data = {cols[i]: row[i] for i in range(len(cols))}
        return jsonify({"ok": True, "item": data})
    finally:
        try: conn.close()
        except: ...

@api_assent.get("/search")
def api_assent_search():
    """
    Busca por nome (case-insensitive).
    /api/assent/search?nome=ana&limit=50
    """
    nome = (request.args.get("nome") or "").strip()
    limit = request.args.get("limit", "50")
    try:
        limit = int(limit)
    except:
        limit = 50

    conn = conectar_bd()
    if not conn:
        return jsonify({"ok": False, "message": "Erro ao conectar no BD."}), 500

    try:
        cur = conn.cursor()
        if nome:
            cur.execute("""
                SELECT a."idAssent", a.nome
                  FROM tbassentado a
                 WHERE unaccent(lower(a.nome)) LIKE unaccent(lower(%s))
                 ORDER BY a.nome ASC
                 LIMIT %s
            """, (f"%{nome}%", limit))
        else:
            cur.execute('SELECT a."idAssent", a.nome FROM tbassentado a ORDER BY a.nome ASC LIMIT %s', (limit,))
        rows = cur.fetchall()
        data = [{"idAssent": r[0], "nome": r[1]} for r in rows]
        return jsonify({"ok": True, "items": data})
    finally:
        try: conn.close()
        except: ...

