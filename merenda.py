from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime
from conexao_bd import conectar

app = Flask(__name__, template_folder='templates')



# Função para conectar ao banco de dados
def conectar_bd():
    conn = conectar()  # Função conectar() deve ser definida em conexao_bd.py
    return conn



# Rota para inserir registro de merenda
@app.route('/inserir_merenda', methods=['GET', 'POST'])
def inserir_merenda():
    if request.method == 'POST':
        matricula = request.form['matricula']
        dtMerenda = request.form['dtMerenda']
        hrMerenda = request.form['hrMerenda']
        obs = request.form['obs']
        codCtrl = request.form['codCtrl']
        contraTurno = request.form['contraTurno']
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                # Checar se já existe registro para a mesma matricula, data e hora
                cur.execute("SELECT * FROM tbmerenda WHERE matricula = %s AND dtMerenda = %s AND hrMerenda = %s", (matricula, dtMerenda, hrMerenda))
                if cur.fetchone():
                    return "Merenda já cadastrada para esse assentado nessa data e hora."
                else:
                    # Inserir registro de merenda
                    cur.execute("INSERT INTO tbmerenda (matricula, dtMerenda, hrMerenda, obs, codCtrl, contraTurno) VALUES (%s, %s, %s, %s, %s, %s)", (matricula, dtMerenda, hrMerenda, obs, codCtrl, contraTurno))
                    conn.commit()
                    return "Merenda cadastrada com sucesso!"
            except Exception as e:
                conn.rollback()
                return f"Erro ao cadastrar merenda: {str(e)}"
            finally:
                cur.close()
                conn.close()
    else:
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                # Selecionar matrícula, nome e foto dos assentados em ordem alfabética
                cur.execute("SELECT matricula, nome, foto FROM tbassentado ORDER BY nome")
                assentados = cur.fetchall()
                return render_template('inserir_merenda.html', assentados=assentados)
            except Exception as e:
                return f"Erro ao carregar assentados: {str(e)}"
            finally:
                cur.close()
                conn.close()
        else:
            return "Erro ao conectar ao banco de dados."

# Restante das rotas e lógica do CRUD de merenda

@app.route('/cadMerenda', methods=['GET', 'POST'])
def cadMerenda():
    if request.method == 'POST':
        matricula = request.form['matricula']
        codAlim = request.form['codAlim']
        dtMerenda = datetime.now().date()
        hrMerenda = datetime.now().strftime('%H:%M')

        print("**  MERENDA.PY  = # merenda.py/////// amanhaaaaaaCAD MERENDA #######################")

        # Verifica se o alimento existe
        if not verificar_alimento_existe(codAlim):
            return render_template('merendaQC.html', message='Código de alimento inválido')

        conn = conectar()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO tbmerenda (matricula, codAlim, dtMerenda, hrMerenda) VALUES (%s, %s, %s, %s)", (matricula, codAlim, dtMerenda, hrMerenda))
                conn.commit()
                conn.close()
                return render_template('merendaQC.html', message='Merenda cadastrada com sucesso')
            except Exception as e:
                print("**  MERENDA.PY  = Erro ao cadastrar merenda:", e)
                return render_template('merendaQC.html', message='Erro ao cadastrar merenda')
        else:
            return render_template('merendaQC.html', message='Erro de conexão com o banco de dados')

    return render_template('merendaQC.html')


# Rota para inserir registro de merenda
# @app.route('/templates/merendaQC.html', methods=['GET', 'POST'])
def obter_dados_assentado():
    conn = conectar()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT matricula, nome, foto FROM tbassentado ORDER BY nome")
            assentados = cur.fetchall()
            conn.close()
            return assentados
        except Exception as e:
            print("**  MERENDA.PY  = Erro ao obter dados dos assentados:", e)
            return []
    else:
        return []

# Exemplo de uso
assentados = obter_dados_assentado()
for assentado in assentados:
    print(assentado)


def obter_dados():
        assentados = obter_dados_assentado()
        contrMerendas = obter_dados_contrMerendas()
        return render_template('/merendaQC.html', assentados=assentados, contrMerendas=contrMerendas )


def verificar_alimento_existe(codAlim):
    conn = conectar()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT EXISTS(SELECT 1 FROM tbalimento WHERE codAlim = %s)", (codAlim,))
            result = cur.fetchone()[0]
            conn.close()
            return result
        except Exception as e:
            print("**  MERENDA.PY  = Erro ao verificar se alimento existe:", e)
            return False
    else:
        return False


if __name__ == '__main__':
    app.run(debug=True)
