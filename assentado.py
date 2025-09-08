from flask import Flask, request, render_template, send_file
# import bcrypt
import os
from conexao_bd import conectar_bd

app = Flask(__name__, template_folder='templates')

# Obtendo a conexão
conn = conectar_bd()

# Rota principal
@app.route('/consulta_todos_assentados')
def consulta_todos_assentados():
    # Obtendo todos os alunos do banco de dados
    cur.execute("SELECT * FROM tbassentado")
    alunos = cur.fetchall()
    return render_template('listaAssentados.html', assentados=assentados)


# Restante das rotas e lógica do cadastro de alunos

# Rota para adicionar um novo tassentado
@app.route('/assentado/incluir_assentado', methods=['POST'])
def incluir_assentado():
  conn = conectar_bd()

  if conn:
     try:
       # Abrindo um cursor
        cur = conn.cursor()
       # Executando o comando SQL
        matricula = request.form['matricula']
        nome = request.form['nome']
        genero = request.form['genero']
        foto = request.form['foto']
        idTipAssent = request.form['idTipAssent']
        idSitAssent = request.form['idSitAssent']

        cur.execute("INSERT INTO tbassentado (matricula, nome, genero, foto, idTipAssent, idSitAssent) "
                   "VALUES (%s, %s, %s, %s, %s, %s)", (matricula, nome, genero, foto, idSitAssent, idTipAssent))
        # Commit da transação
        conn.commit()
        print("Inserção realizada com sucesso!")


     except Exception as e:
      # Em caso de erro, rollback da transação
        conn.rollback()
        print("Erro durante a inserção:", e)
     finally:
        #Fechando o cursor
        cur.close()
        return render_template('assentado.html')
  else:
        return None

# Restante das rotas e lógica do cadastro de alunos

# Diretório  onde as imagens dos alunos estão armazenadas
PASTA_IMAGENS = "/img"

# Rota para deletar um assentado
@app.route('/assentado/excluir_assentado/<int:matricula>')
def excluir_assentado(matricula):
    cur.execute("DELETE FROM tbassentado WHERE matricula = %s", (matricula,))
    conn.commit()
    return redirect(url_for('/templastes/assentado'))

@app.route('/assentado/atualizar_assentado', methods=['POST'])
# @app.route('/assentado/atualizar_assentado/<int:matricula>')
def atualizar_assentado(matricula, nome):
    matricula = request.form['matricula']
    nome = request.form['nome']
    genero = request.form['genero']
    foto = request.form['foto']
    idTipAssent = request.form['idTipAssent']
    idSitAssent = request.form['idSitAssent']

    cur.execute("UPDATE tbassentado SET nome = %s , genero = %s, idTipAssent = %s ,"
                " idSitAssent = %s  WHERE matricula = %s",
                (nome, genero, idTipAssent, idSitAssent, idSitAssent, matricula))
    conn.commit()


@app.route('/obter_foto_assentado/<matricula>')
def obter_foto_assentado(matricula):
    # Caminho completo para a imagem do tassentado
    caminho_imagem = os.path.join(PASTA_IMAGENS, f"{matricula}.jpg")

    # Verifica se o arquivo de imagem existe
    if os.path.isfile(caminho_imagem):
        return send_file(caminho_imagem, mimetype='image/jpeg')
    else:
        # Se a imagem não existir, retorna uma imagem de placeholder ou outra resposta adequada
        return "Imagem não encontrada", 404



# Rota para deletar um assentado
@app.route('/assentado/consulta_nome_assentado/<int:matricula>')
def consulta_nome_assentado(nome):
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT matricula, nome, foto FROM tbassentado WHERE nome LIKE %s", ('%' + nome + '%',))
            assentados = cur.fetchall()
            assentados_corrigidos = []
            for assentado in assentados:
                assent_corrigido = list(assentado)
                assent_corrigido[2] = url_for('static', filename='img/' + assentado[2])  # Corrigir o caminho da imagem
                assentados_corrigidos.append(assent_corrigido)
            conn.close()
            return assentados_corrigidos
        except Exception as e:
            session['mensagem'] = " Erro ao obter dados dos assentados por nome: !"
            print("BBCQC..PY ==Erro ao obter dados dos assentados por nome:", e)
            return []
    else:
        return []



if __name__ == '__main__':
    app.run(debug=True)

# Fechando cursor e conexão
#cur.close()
#conn.close()
