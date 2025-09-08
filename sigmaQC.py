
import psycopg2

import requests

from datetime import datetime

from controleBBC import dados_controle, cadastrar_controle, busca_controle, atualizar_matricula,  \
                     dados_merenda, obter_dados_assentado, dados_whatsapp, enviar_whatsapp, cartaoQR, \
                     cadastro_merenda, obter_aluno, obter_turno,  \
                     gerar_pdf_Cartao, dados_cartao, cartaoQR, cartao_aluno, dados_cartao_turno, cartao_turno, \
                     dados_cartao_curso, cartao_curso

from catracaQC import dados_catraca, abrirCatraca, fechar_catraca, busca_catraca, atualizar_matricula,  \
                      obter_dados_assentado, cadastro_catraca


from consultas import consQTDdia, consQTDsem

from conexao_bd import conectar_bd

from flask import Flask, request, render_template, redirect, url_for, session
import subprocess


app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = '@Sigma4321'

# Função para estabelecer conexão com o banco de dados

# --  ROTINAS BÁSICAS:  CONECTAR - INDEx - MENU - FICAM POSICIONADAS ANTES DE TODAS - PADRÃO MEU------------------


# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')


# Rota para autenticação de usuário
@app.route('/menulogin', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        if verificar_credenciais(usuario, senha):
            return render_template('menuOld.html', message='Conexão com sucesso!')
        else:
            return render_template('index.html', message='Usuário ou senha incorretos')
    print("SIGMAQC..PY == MENU LOGIN ")
    return render_template('menuOld.html')


# Rota para a página de merenda
@app.route('/menuMerenda')
def menuMerenda():
    return render_template('menuMerenda.html')

# --  ROTINAS NECESSARIAS EM ORDEM ALFABETICA   -------------

# Rota para a página de alimento
@app.route('/templates/alimento')
def alimento():
    return render_template('/alimento.html')


# Rota para a página de assentado
@app.route('/assentado')
def assentado():
    return render_template('assentado.html')


@app.route('/buscacontrole')
def buscacontrole():
    # Redirecionar para a rota /dados_controle
    return busca_controle()


@app.route('/cadcontrole', methods=['GET', 'POST'])
def cadastro_controle():
    return cadastrar_controle()


@app.route('/controle')
def controle():
    # Redirecionar para a rota /dados_controle
    print("SIGMAQC..PY == sigma- dados")
    return dados_controle()


@app.route('/catraca')
def catraca():
    # Redirecionar para a rota /dados_catraca
    print("SIGMAQC..PY == sigma- dados")
    return dados_catraca()


@app.route('/abrir_Catraca', methods=['GET', 'POST'])
def abrir_Catraca():
    return abrirCatraca()


@app.route('/fecharcatraca', methods=['GET', 'POST'])
def fechar_contraca():
    return fechar_catraca()



@app.route('/mensagem')
def mensagem():
    return render_template('mensagem.html')


@app.route('/merenda', methods=['GET', 'POST'])
def merenda():
    session['mensagem'] = "  "
    print("SIGMAQC..PY ==l 111 ===> /merenda ")
    turno = " "
    if request.method == 'GET':
         matricula = request.args.get('matricula', '999')
    elif request.method == 'POST':
         matricula = request.form.get('matricula')
         turno = request.form.get('turno')

    if matricula == '999':
        matricula = '001'  # Valor padrão caso 'matricula' não seja fornecido

    # Renderiza o template merendaQC.html passando o parâmetro 'termo'
    session['mensagem'] = "  "
    return dados_merenda(matricula)


@app.route('/cadmerenda', methods=['GET', 'POST'])
def cad_merenda():
    print("SIGMAQC..PY ==# -------------/////// hoooje CAD MERENDA #######################")
    if request.method == 'POST':
        matricula = request.form.get('matricula')
        turno = request.form.get('turno')


    contrDiario = request.form.get('contrDiario')

    print("SIGMAQC..PY ==SIGMAQC..PY ===========> 22222 ####### CAD MEREDNA => ", contrDiario)

    # Renderiza o template merendaQC.html
    return cadastro_merenda()


@app.route('/merexcedente', methods=['GET', 'POST'])
def merenda_exced():
    print("SIGMAQC..PY ==*************** MERENDA EXCEDENTE() ******** PASSO2 PASSO2 PASSO2 /MERENDA()")
    turno = " "
    # Renderiza o template merendaQC.html passando o parâmetro 'termo'
    session['mensagem'] = "  "
    return dados_merenda_exced()


@app.route('/cadMerendaExced', methods=['GET', 'POST'])
def cad_merenda_exced():
    print("SIGMAQC..PY ==########################   CAD MERENDA #######################")
    turno = request.form.get('turno')

    matricula = turno + '999'
    print("SIGMAQC..PY ===========> 11111####### CAD MEREDNA => ", matricula)

    contrDiario = request.form.get('contrDiario')

    print("SIGMAQC..PY ===========> 22222 ####### CAD MEREDNA => ", contrDiario)

    # Renderiza o template merendaQC.html
    return cadastro_merenda_exced()


def obter_dados_aluno():
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT matricula, nome, foto FROM tbaluno ORDER BY nome")
            alunos = cur.fetchall()
            alunos_corrigidos = []
            for assentado in alunos:
                matricula, nome, foto = assentado  # Desempacotando os dados do assentado
                # Corrigindo o caminho da foto
                foto_corrigida = url_for('static', filename=f'img/{foto}')
                alunos_corrigidos.append((matricula, nome, foto_corrigida))
            conn.close()
            return alunos_corrigidos
        except Exception as e:
            session['mensagem'] = " Erro @@@ 111  oter_dados_aluno() !"
            print("SIGMAQC..PY ==Erro ao obter dados dos alunos:", e)
            return []
    else:
        return []


def obter_dados_contrMerendas():
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            # Selecionar os registros da tabela de controle de alimentos ativos
            cur.execute("SELECT mc.codCtrl, mc.codAlim, a.nome, mc.qtdTotal - mc.qtdEntregue AS disponivel "
                        "FROM tbmerctrl mc "
                        "INNER JOIN tbalimento a ON mc.codAlim = a.codAlim "
                        "WHERE mc.situacao = 1 "
                        "ORDER BY a.nome")
            contrMerendas = cur.fetchall()
            conn.close()


        except Exception as e:
            session['mensagem'] = " Erro ao obter dados de controle de merenda !"
            print("SIGMAQC..PY ==Erro ao obter dados de controle de merenda:", e)
            return []
    else:
        return []


def obter_dados_aluno_matricula(matr):
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT nome, foto FROM tbaluno WHERE matricula = %s", (matr,))
            assentado = cur.fetchone()
            if assentado is not None:
                print("SIGMAQC..PY ==44444  alunos ===>  ", assentado)
            if assentado:
                aluno_corrigido = list(assentado)
                aluno_corrigido[2] = url_for('static', filename='img/' + assentado[2])  # Corrigir o caminho da imagem
                print("SIGMAQC..PY ==55555  assentado corrigido ===>  ", aluno_corrigido)
                conn.close()
                return aluno_corrigido
            else:
                if assentado is not None:
                   print("SIGMAQC..PY ==assentado não encontrado")
                return None
        except Exception as e:
            session['mensagem'] = " Erro ao obter dados do assentado por matrícula !"
            print("SIGMAQC..PY ==Erro ao obter dados do assentado por matrícula:", e)
            return None
    else:
        return None


def obter_dados_aluno_nome(nome):
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT matricula, nome, foto FROM tbaluno WHERE nome LIKE %s", ('%' + nome + '%',))
            alunos = cur.fetchall()
            print("SIGMAQC..PY ==91919191  alunos ===>  ", alunos)
            alunos_corrigidos = []
            for assentado in alunos:
                aluno_corrigido = list(assentado)
                aluno_corrigido[2] = url_for('static', filename='img/' + assentado[2])  # Corrigir o caminho da imagem
                alunos_corrigidos.append(aluno_corrigido)
            conn.close()
            return alunos_corrigidos
        except Exception as e:
            session['mensagem'] = " Erro ao obter dados dos alunos por nome: !"
            print("SIGMAQC..PY ==Erro ao obter dados dos alunos por nome:", e)
            return []
    else:
        return []


# Rota para a página de usuario
@app.route('/usuario')
def obter_todos_usuario():
    conn = conectar()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT usuario, senha,  nome, nivel, email  FROM tbusuario ORDER BY nome")
            usuario = cur.fetchall()
            conn.close()
            return usuario
        except Exception as e:
            print("SIGMAQC..PY ==Erro ao obter dados dos usuarios:", e)
            return []
    else:
        return []


@app.route('/obter_aluno', methods=['POST'])
def obterAluno():
      return obter_aluno()


@app.route('/pesquisar_aluno', methods=['POST'])
def pesquisar_aluno():
    data_atual = datetime.now()
    tipo_consulta = request.form.get('tipo_consulta')
    assentado = None  # Defina a variável assentado como None no início
    matricula = request.form.get('matricula')
    turno = request.form.get('turno')
    print("SIGMAQC..PY ==@@ 111 PESQUISAR-assentado  (sigmaQC.py) - pesquisar_aluno()  turno=> ", turno)
    print("SIGMAQC..PY ==@@ 222  PESQUISAR-assentado (sigmaQC.py) - pesquisar_aluno()  matricula=> ", matricula)
    chave_pesquisa = turno + matricula.zfill(3)
    print("SIGMAQC..PY ==@@ 333  PESQUISAR-assentado (sigmaQC.py) - pesquisar_aluno()  chave=> ", chave_pesquisa)

    assentado = obter_dados_assentado(chave_pesquisa)
    print("SIGMAQC..PY ==@@ 444  PESQUISAR-assentado (sigmaQC.py) - pesquisar_aluno()  termo=>  ", assentado, " matricula => ", matricula)
    if assentado:
       print("SIGMAQC..PY == @@ 555  PESQUISAR-assentado (sigmaQC.py) - pesquisar_aluno()  assentado ===>  ", assentado[0])
    else:
       session['mensagem'] = " Não foram Encontrados Alunos Com Esse Nome !"

    if assentado is not None:
        print("SIGMAQC..PY == @@ 666  PESQUISAR-assentado (sigmaQC.py) ==>  ", assentado[0])
        session['mensagem'] = "  "
        return render_template('merendaQC.html', chave_pesquisa=chave_pesquisa, assentado=assentado,
                               contrabertos=contrabertos, ano=ano, mes=mes, data_atual=data_atual, qtddisp=qtddisp)
    else:
        print("SIGMAQC..PY == @@ 777  PESQUISAR-assentado (sigmaQC.py) ==>  ", assentado[0])
        session['mensagem'] = f"Não foi encontrado assentado com o código {chave_pesquisa}!"
        return dados_merenda()


@app.route('/ver_aluno', methods=['POST'])
def ver_aluno():
    aluno_selecionado_id = request.form.get('matricula')
    aluno_selecionado = obter_dados_aluno_matricula(aluno_selecionado_id)  # Substitua por sua função para obter dados do assentado por ID
    return render_template('merendaQC.html', assentado=aluno_selecionado)


# Função para verificar as credenciais do usuário
def verificar_credenciais(usuario, senha):
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT senha, nivel FROM tbusuario WHERE usuario = %s", (usuario,))
            resultado = cur.fetchone()
            conn.close()

            if resultado:
                if senha == resultado[0]:
                    return True
                else:
                    return False
               #  senha com funcao hash - criptografada - colocar depois
               #  senha_hash = resultado[0].encode('utf-8')
               #  if bcrypt.checkpw(senha.encode('utf-8'), senha_hash):
               #      return True
               # else:
               #      return False  # Senha incorreta
            else:
                session['mensagem'] = " Usuário Não Cadastrado !"
                return False  # Usuário não cadastrado
        except psycopg2.Error as e:
            return False
    else:
        return False


@app.route('/whatsapp', methods=['GET', 'POST'])
def rotina_whatsapp():
    print("SIGMAQC..PY ==*************** ENVIAR WHATSAPP ")

    # Renderiza o template enviarWhatsapp.html
    session['mensagem'] = "  "
    return dados_whatsapp()


@app.route('/enviarWhatsapp', methods=['POST'])
def enviar_msg_whatsapp():

  session['mensagem'] = "  "
  return enviar_whatsapp()


@app.route('/qrMatricula', methods=['POST'])
def qr_matricula():

  session['mensagem'] = "  "
  return atualizar_matricula()


@app.route('/cartaoQR', methods=['GET', 'POST'])
def cartaoQRaluno():

  session['mensagem'] = "  "
  return cartaoQR()


@app.route('/gerarQR_PDF', methods=['GET', 'POST'])
def gerarQRPDF():
   session['mensagem'] = "  "
   return gerar_pdf_Cartao()



@app.route('/emitirCartao', methods=['GET', 'POST'])
def emitirCartao():
    if request.method == 'POST':
        matricula = request.form.get('matricula')
        if matricula:
            return dados_cartao(matricula)
        else:
            return "Matrícula não fornecida."
    else:
        return render_template('emitirCartao.html')


@app.route('/emitirCartaoTurno', methods=['GET', 'POST'])
def emitirCartaoTurno():
    if request.method == 'POST':
        turno = request.form.get('turno')
        if turno:
            print("SIGMAQC..PY ==$$$$$$$$$$$$$$$   turno", turno)
            return dados_cartao_turno(turno)
        else:
            return "Turno não fornecida."
    else:
        return render_template('emitirCartaoTurno.html')


@app.route('/emitirCartaoCurso', methods=['GET', 'POST'])
def emitirCartaoCurso():
    if request.method == 'POST':
        curso = request.form.get('curso')
        if curso:
            print("SIGMAQC..PY ==$$$$$$$$$$$$$$$ curso curso   curso", curso)
            return dados_cartao_curso(curso)
        else:
            return "Curso não fornecido."
    else:
        return render_template('emitirCartaoCurso.html')


@app.route('/cartaoAlun', methods=['GET', 'POST'])
def cartaoAlun():
   session['mensagem'] = "  "
   return cartao_aluno()


@app.route('/cartaoTurno', methods=['GET', 'POST'])
def cartaoTurno():
   session['mensagem'] = "  "
   return cartao_turno()


@app.route('/cartaoCurso', methods=['GET', 'POST'])
def cartaoCurso():
   session['mensagem'] = "  "

   return cartao_curso()


@app.route('/sigQTDdia', methods=['GET', 'POST'])
def sigQTDdia():
    data_atual = datetime.now().date()
    ano_sistema = datetime.now().year
    session['mensagem'] = "  "
    return render_template('consQTDdia.html', data_atual=data_atual, ano_sistema=ano_sistema)


@app.route('/sigQTDsem', methods=['GET', 'POST'])
def sigQTDsem():
    data_atual = datetime.now().date()
    ano_sistema = datetime.now().year
    session['mensagem'] = "  "
    return render_template('consQTDsem.html', data_atual=data_atual, ano_sistema=ano_sistema)


@app.route('/sigConsQTDdia', methods=['POST'])
def sigConsQTDdia():

    return consQTDdia()


@app.route('/sigConsQTDsem', methods=['POST'])
def sigConsQTDsem():

    return consQTDsem()

#@app.route('/merenda3', methods=['POST'])
#def sigConsQTDsem():

#    return lerQRcode10()


#  aplicação Flask será acessível a partir de outros dispositivos na mesma rede, como o seu celular.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True )


