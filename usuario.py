import bcrypt
import psycopg2
import secrets
from flask import Flask, request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd
from datetime import datetime
from flask_mail import Mail, Message

app = Flask(__name__)

import bcrypt

# Configurações do servidor de e-mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seuemail@gmail.com'
app.config['MAIL_PASSWORD'] = 'senha_de_app_google'  # não é a senha normal, é senha de aplicativo
app.config['MAIL_DEFAULT_SENDER'] = ('BBC Sistema', 'seuemail@gmail.com')  # 👈 remetente padrão

mail = Mail(app)


@app.route('/acessoUsuario', methods=['POST'])
def acessoUsuario():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT senha FROM tbusuario WHERE usuario = %s", (usuario,))
                resultado = cur.fetchone()
                conn.close()

                if resultado:
                    senha_hash_banco = resultado[0]  # vem como string do BD

                    # garante que está em bytes
                    if isinstance(senha_hash_banco, str):
                        senha_hash_banco = senha_hash_banco.encode('utf-8')

                    # compara senha digitada com a hash do banco
                    if bcrypt.checkpw(senha.encode('utf-8'), senha_hash_banco):
                        return render_template('menu.html', message='Login realizado com sucesso!')
                       # flash("✅ Login realizado com sucesso!", "success")
                       # return redirect(url_for("menu.html"))  # rota limpa do login
                    else:
                        return render_template('index.html', message='*** Usuário ou senha incorretos!')
                else:
                    return render_template('index.html', message='*** Usuário não cadastrado !')

            except psycopg2.Error as e:
                return f"Erro ao realizar login: {e}"
        else:
            return "Erro ao conectar ao banco de dados..."

# Rota para realizar o login

# ------------------------------
# Função para cadastrar um novo usuário - nao precisa de rota , pois é chamado direo do form
# ------------------------------

def cadastrar_usuario():
    if request.method == 'POST':
        usuario = request.form['usuario']
        nome = request.form['nome']
        senha = request.form['senha']
        email = request.form['email']

        # Hash da senha (salvamos como string)
        hashed_senha = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO tbusuario (usuario, nome, senha, email) VALUES (%s, %s, %s, %s)",
                    (usuario, nome, hashed_senha, email)
                )
                conn.commit()
                conn.close()
                return render_template("index.html", message="✅ Usuário cadastrado com sucesso!")
            except psycopg2.Error as e:
                conn.rollback()
                return render_template("usuarioCad.html", message=f"Erro ao cadastrar usuário: {e}")
        else:
            return "Erro ao conectar ao banco de dados."

def alterar_usuario():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        nome = request.form['nome']
        email = request.form['email']

        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                # Buscar senha armazenada
                cur.execute("SELECT senha FROM tbusuario WHERE usuario = %s", (usuario,))
                resultado = cur.fetchone()

                if not resultado:
                    conn.close()
                    return render_template("usuarioAlt.html", message="❌ Usuário não encontrado!")

                senha_hash = resultado[0].encode('utf-8')

                # Validar senha digitada com hash
                if not bcrypt.checkpw(senha.encode('utf-8'), senha_hash):
                    conn.close()
                    return render_template("usuarioAlt.html", message="❌ Senha incorreta!")

                # Atualizar nome, email e data
                cur.execute("""
                    UPDATE tbusuario
                    SET nome = %s, email = %s, datUltAtulz = %s
                    WHERE usuario = %s
                """, (nome, email, datetime.now(), usuario))

                conn.commit()
                conn.close()
                return redirect(url_for("menu"))  # volta ao menu
            except psycopg2.Error as e:
                conn.rollback()
                return render_template("usuarioAlt.html", message=f"Erro ao alterar usuário: {e}")
        else:
            return "❌ Erro ao conectar ao banco de dados."


# Rota para alterar a senha do usuário
@app.route('/alterar_senha', methods=['POST'])
def alterar_senha():
    usuario = request.form['usuario']
    senha_atual = request.form['senha']
    nova_senha = request.form['nova_senha']
    confirmar_senha = request.form['confirmar_senha']

    # Confirmação de senha
    if nova_senha != confirmar_senha:
        return render_template('senhaAlt.html', message="❌ Nova senha e confirmação não coincidem!")

    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            # Verifica usuário e senha atual
            cur.execute("SELECT senha FROM tbusuario WHERE usuario = %s", (usuario,))
            resultado = cur.fetchone()

            if not resultado:
                conn.close()
                return render_template('senhaAlt.html', message="Usuário não encontrado!")

            senha_hash_banco = resultado[0]
            if isinstance(senha_hash_banco, str):
                senha_hash_banco = senha_hash_banco.encode('utf-8')

            # Verifica senha atual
            if not bcrypt.checkpw(senha_atual.encode('utf-8'), senha_hash_banco):
                conn.close()
                return render_template('senhaAlt.html', message="❌ Senha atual incorreta!")

            # Gera hash da nova senha
            hashed_nova_senha = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt())

            # Atualiza senha e timestamp
            cur.execute("""
                UPDATE tbusuario 
                SET senha = %s, "datUltAtulz" = %s 
                WHERE usuario = %s
            """, (hashed_nova_senha.decode('utf-8'), datetime.now(), usuario))

            conn.commit()
            conn.close()
            return render_template('senhaAlt.html', message="✅ Senha alterada com sucesso!")

        except psycopg2.Error as e:
            conn.rollback()
            return f"Erro ao alterar senha: {e}"

    else:
        return "Erro ao conectar ao banco de dados."



# Rota para recuperar a senha
@app.route('/recuperar_senha', methods=['POST'])
def recuperar_senha():
    if request.method == 'POST':
        usuario = request.form['usuario']
        email = request.form['email']

        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT email FROM tbusuario WHERE usuario = %s", (usuario,))
                resultado = cur.fetchone()

                if resultado:
                    email_cadastrado = resultado[0]

                    if email_cadastrado == email:
                        # 1. Gerar nova senha temporária
                        nova_senha = secrets.token_urlsafe(6)  # ex: 'dR9s2A@x'

                        # 2. Hash da nova senha (convertendo para string antes de salvar no banco)
                        hashed_senha = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                        # 3. Atualizar no banco
                        cur.execute("UPDATE tbusuario SET senha = %s WHERE usuario = %s", (hashed_senha, usuario))
                        conn.commit()
                        conn.close()

                        # 4. Enviar e-mail com a nova senha em texto puro
                        msg = Message('Recuperação de Senha', recipients=[email])
                        msg.body = (
                            f"Olá {usuario},\n\n"
                            f"Você solicitou a recuperação de senha.\n"
                            f"Sua nova senha temporária é: {nova_senha}\n\n"
                            f"⚠️ Recomendamos alterá-la assim que fizer login."
                        )
                        mail.send(msg)

                        return "✅ E-mail enviado com sucesso!"
                    else:
                        conn.close()
                        return render_template('senhaRec.html',
                                        message="❌ O e-mail informado não corresponde ao cadastrado para este usuário.")
                else:
                    conn.close()
                    return render_template('senhaRec.html', message="❌ Usuário não cadastrado.")
            except psycopg2.Error as e:
                 return render_template('senhaRec.html', message="❌ Erro ao recuperar senha {e}")
        else:
            return render_template('senhaRec.html' , message="❌ Erro ao conectar ao banco de dados.")


if __name__ == '__main__':
    app.run(debug=True)
