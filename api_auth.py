# BBC/api_auth.py
from flask import Blueprint, request, jsonify
from conexao_bd import conectar_bd

api_auth = Blueprint("api_auth", __name__, url_prefix="/api/auth")

@api_auth.post("/login")
def login():
    """
    Espera JSON: {"usuario": "...", "senha": "..."}
    Ajuste a consulta abaixo (tabela/colunas) ao seu esquema real.
    """
    data = request.get_json(silent=True) or {}
    usuario = (data.get("usuario") or "").strip()
    senha   = (data.get("senha") or "").strip()

    if not usuario or not senha:
        return jsonify({"ok": False, "message": "Informe usuário e senha."}), 400

    conn = conectar_bd()
    if not conn:
        return jsonify({"ok": False, "message": "Erro de conexão ao BD."}), 500

    try:
        cur = conn.cursor()
        # ===== AJUSTE AQUI para seu schema =====
        cur.execute("""
            SELECT id, nome, login, senha
              FROM tbusuario
             WHERE login = %s
             LIMIT 1
        """, (usuario,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify({"ok": False, "message": "Usuário não encontrado."}), 401

        uid, nome, login_db, senha_db = row

        # Se você usa senha com HASH (bcrypt/argon2), troque esta comparação por uma verificação de hash
        if str(senha) != str(senha_db):
            return jsonify({"ok": False, "message": "Senha inválida."}), 401

        # Sucesso
        return jsonify({
            "ok": True,
            "user": {"id": uid, "nome": nome, "login": login_db}
        }), 200

    except Exception as e:
        print("Erro login:", e)
        try:
            if conn and not conn.closed:
                conn.close()
        except: ...
        return jsonify({"ok": False, "message": "Erro no login."}), 500
