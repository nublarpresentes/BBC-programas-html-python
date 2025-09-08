# import bcrypt
import psycopg2
from flask import Flask, request, render_template
# from conexao_bd import conectar_bd

from conexao_bd import conectar_bd

app = Flask(__name__)

# Rota para realizar o login
@app.route('/acessoUsuario', methods=['POST'])
def acessoUsuario():
    if request.method == 'POST':
        usuario = int(request.form['usuario'])
        senha = request.form['senha']

        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT senha FROM tbusuario WHERE usuario = %s", (usuario,))
                resultado = cur.fetchone()
                conn.close()

                if resultado:
                   return render_template('menu.html', message='Conexão com sucesso!')
                  #  senha_hash = resultado[0].encode('utf-8')
                   # if bcrypt.checkpw(senha.encode('utf-8'), senha_hash):
                  #      return "Login realizado com sucesso!"
                  #  else:
                  #      return "Usuário ou senha incorretos."
                else:
                    return render_template('index.html', message='*** Usuário não cadastrado !')
                   # return "Usuário não cadastrado."
            except psycopg2.Error as e:
                return f"Erro ao realizar login: {e}"
        else:
            return "Erro ao conectar ao banco de dados."


# Função para cadastrar um novo usuário
@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    if request.method == 'POST':
        usuario = int(request.form['usuario'])
        nome = int(request.form['nome'])
        senha = request.form['senha']
        email = request.form['email']

      # Hash da senha
        hashed_senha = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO tbusuario (usuario, nome, senha, email) VALUES (%s, %s, %s, %s)", (usuario, nome, hashed_senha, email))
                conn.commit()
                conn.close()
                return "Usuário cadastrado com sucesso!"
            except psycopg2.Error as e:
                conn.rollback()
                return f"Erro ao cadastrar usuário: {e}"
        else:
            return "Erro ao conectar ao banco de dados."

# Rota para alterar a senha do usuário
@app.route('/alterar_senha', methods=['POST'])
def alterar_senha():
    if request.method == 'POST':
        usuario = int(request.form['usuario'])
        nova_senha = request.form['nova_senha']

        # Hash da nova senha
        hashed_nova_senha = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt())

        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("UPDATE tbusuario SET senha = %s WHERE usuario = %s", (hashed_nova_senha, usuario))
                conn.commit()
                conn.close()
                return "Senha alterada com sucesso!"
            except psycopg2.Error as e:
                conn.rollback()
                return f"Erro ao alterar senha: {e}"
        else:
            return "Erro ao conectar ao banco de dados."

# Rota para recuperar a senha
@app.route('/recuperar_senha', methods=['POST'])
def recuperar_senha():
    if request.method == 'POST':
        usuario = int(request.form['usuario'])
        email = request.form['email']

        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT email FROM tbusuario WHERE usuario = %s", (usuario,))
                resultado = cur.fetchone()
                conn.close()

                if resultado:
                    email_cadastrado = resultado[0]
                    if email_cadastrado == email:
                        msg = Message('Recuperação de Senha', recipients=[email])
                        msg.body = f'Olá, você solicitou a recuperação de senha. Sua senha é: {senha}'
                        mail.send(msg)
                        return "E-mail enviado com sucesso!"
                    else:
                        return "O e-mail informado não corresponde ao cadastrado para este usuário."
                else:
                    return "Usuário não cadastrado."
            except psycopg2.Error as e:
                return f"Erro ao recuperar senha: {e}"
        else:
            return "Erro ao conectar ao banco de dados."

if __name__ == '__main__':
    app.run(debug=True)
