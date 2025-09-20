
import psycopg2

# import requests

from datetime import datetime

from controleBBC import dados_controle, cadastrar_controle, busca_controle, atualizar_matricula, \
     dados_whatsapp, enviar_whatsapp, cartaoQR, \
     gerar_pdf_Cartao, dados_cartao, cartaoQR, dados_cartao_turno, cartao_turno, \
     dados_cartao_curso, cartao_curso

#--------------------- contribuicoes e retribuicoes ------------------------------------

from tipContrib import listar_tipcontrib, pegar_tipcontrib, excluir_tipo_contrib, \
     cadastrar_tipcontrib , alterar_tipcontrib, view_tipContribAlt, \
    view_tipContribExc



from tipRetrib import cadastrar_tipretrib , alterar_tipretrib

from contrib import cadastrar_contrib , alterar_contrib
from retrib import cadastrar_retrib , alterar_retrib

#------------------------------------------------------------------------------------------

from assentado import  consulta_nome_assentado, obter_foto_assentado, incluir_assentado, \
atualizar_assentado, excluir_assentado, consulta_todos_assentados


# depois
from assentado import (
    consulta_nome_assentado, obter_foto_assentado, incluir_assentado,
    atualizar_assentado, excluir_assentado, consulta_todos_assentados
)

from usuario import  acessoUsuario, cadastrar_usuario, recuperar_senha, alterar_senha, alterar_usuario


from consultas import consQTDdia, consQTDsem

from conexao_bd import conectar_bd

from flask import Flask, request, render_template, redirect, url_for, session, flash

import subprocess


app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = '@Sigma4321'
app.secret_key = "um_segredo_bem_dificil"  # pode ser qualquer string
# Função para estabelecer conexão com o banco de dados

# --  ROTINAS BÁSICAS:  CONECTAR - INDEx - MENU - FICAM POSICIONADAS ANTES DE TODAS - PADRÃO MEU------------------

# Função para estabelecer conexão com o banco de dados

# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')


# Rota para autenticação de usuário

@app.route('/login', methods=['GET', 'POST'])
def login():
    return acessoUsuario()


# Rota para a conta usuario
@app.route('/usuarioCad')
def usuarioCad():
    return render_template('usuarioCad.html')

@app.route('/cadUsuario', methods=['POST'])
def cadUsuario():
    # Redirecionar para a rota
    return cadastrar_usuario()


# Rota para a altercao do usuario
@app.route('/usuarioAlt')
def usuarioAlt():
    return render_template('usuarioAlt.html')

@app.route('/altUsuario', methods=['POST'])
def altUsuario():
    # Redirecionar para a rota
    print("passou duas vezesu")
    return alterar_usuario()

# Rota para a recuperacao de senha
@app.route('/senhaRec')
def senhaRec():
    return render_template('senhaRec.html')

@app.route('/recSenha', methods=['POST'])
def recSenha():
    # Redirecionar para a rota
    return recuperar_senha()

#----------------------------------------------
# Rota para a alterar senha
@app.route('/senhaAlt')
def senhaAlt():
    return render_template('senhaAlt.html')

@app.route('/altSenha', methods=['POST'])
def altSenha():
    # Redirecionar para a rota
    return alterar_senha()

#---------------------------------------------------
# Rota para cad  politica publica

# BBC.py (trechos)

from polPub import (
    cadastrar_politpub, alterar_politpub, excluir_politpub,
    listar_politpub, pegar_politpub, _listar_entidades
)

# ---------- CADASTRAR ----------
# BBC.py (trechos)

from polPub import (
    cadastrar_politpub, alterar_politpub, excluir_politpub,
    listar_politpub, pegar_politpub, _listar_entidades
)

# ---------- CADASTRAR ----------
@app.route('/politPubCad')
def politPubCad():
    entidades = _listar_entidades()
    return render_template('politPubCad.html', entidades=entidades)

@app.route('/cadPolitPub', methods=['POST'])
def cadPolitPub():
    return cadastrar_politpub()

# ---------- ALTERAR (lista + form) ----------
@app.route('/politPubAlt')
def politPubAlt():
    itens = listar_politpub()
    registro = None
    sel_id = request.args.get('id')
    if sel_id:
        registro = pegar_politpub(sel_id)
    entidades = _listar_entidades()
    return render_template('politPubAlt.html', itens=itens, registro=registro, entidades=entidades)

@app.route('/altPolitPub', methods=['POST'])
def altPolitPub():
    return alterar_politpub()

# ---------- EXCLUIR (lista + confirmar) ----------
@app.route('/politPubExc')
def politPubExc():
    itens = listar_politpub()
    registro = None
    sel_id = request.args.get('id')
    if sel_id:
        registro = pegar_politpub(sel_id)
    return render_template('politPubExc.html', itens=itens, registro=registro)

@app.route('/excPolitPub', methods=['POST'])
def excPolitPub():
    return excluir_politpub()

#---------------------------------------------------
# Rota para cadastro  unidade Equivalia
# BBC.py (apenas as rotas relacionadas a UnEqv)

from unEqv import (
    cadastrar_uneqv,
    alterar_uneqv,
    excluir_uneqv,
    pagina_unEqvAlt,
    pagina_unEqvExc,
)

# --- Inclusão
@app.route('/unEqvCad')
def unEqvCad():
    return render_template('unEqvCad.html')

@app.route('/cadUnEqv', methods=['POST'])
def cadUnEqv():
    return cadastrar_uneqv()

# --- Alteração (lista + painel de edição no mesmo HTML)
@app.route('/unEqvAlt')
def unEqvAlt():
    return pagina_unEqvAlt()

@app.route('/altUnEqv', methods=['POST'])
def altUnEqv():
    return alterar_uneqv()

# --- Exclusão (lista + painel de confirmação)
@app.route('/unEqvExc')
def unEqvExc():
    return pagina_unEqvExc()

@app.route('/excUnEqv', methods=['POST'])
def excUnEqv():
    return excluir_uneqv()

#--------------------   familia ------------------

# --------------------  Família  --------------------
@app.route('/familiaCad')
def familiaCad():
    return render_template('familiaCad.html')

@app.route('/cadFamilia', methods=['POST'])
def cadFamilia():
    from familia import cadastrar_familia
    return cadastrar_familia()

# Alteração (lista + painel de edição no mesmo HTML)
@app.route('/familiaAlt')
def familiaAlt():
    from familia import pagina_familiaAlt
    return pagina_familiaAlt()

@app.route('/altFamilia', methods=['POST'])
def altFamilia():
    from familia import alterar_familia
    return alterar_familia()

# Exclusão (lista + painel de confirmação)
@app.route('/familiaExc')
def familiaExc():
    from familia import pagina_familiaExc
    return pagina_familiaExc()

@app.route('/excFamilia', methods=['POST'])
def excFamilia():
    from familia import excluir_familia
    return excluir_familia()


#------------  situacao assentado

# --- Situação do Assentado
@app.route('/sitAssentCad')
def sitAssentCad():
    return render_template('sitAssentCad.html')

@app.route('/cadSitAssent', methods=['POST'])
def cadSitAssent():
    from sitAssent import cadastrar_sitassent
    return cadastrar_sitassent()

@app.route('/sitAssentAlt')
def sitAssentAlt():
    from sitAssent import pagina_sitAssentAlt
    return pagina_sitAssentAlt()

@app.route('/altSitAssent', methods=['POST'])
def altSitAssent():
    from sitAssent import alterar_sitassent
    return alterar_sitassent()

@app.route('/sitAssentExc')
def sitAssentExc():
    from sitAssent import pagina_sitAssentExc
    return pagina_sitAssentExc()

@app.route('/excSitAssent', methods=['POST'])
def excSitAssent():
    from sitAssent import excluir_sitassent
    return excluir_sitassent()

# ------------  categoria assentado
@app.route('/ctgAssentCad')
def ctgAssentCad():
    return render_template('ctgAssentCad.html')

@app.route('/cadCtgAssent', methods=['POST'])
def cadCtgAssent():
    from ctgAssent import cadastrar_ctgassent
    return cadastrar_ctgassent()

# Alteração (lista + painel de edição no mesmo HTML)
@app.route('/ctgAssentAlt')
def ctgAssentAlt():
    from ctgAssent import pagina_ctgAssentAlt
    return pagina_ctgAssentAlt()

@app.route('/altCtgAssent', methods=['POST'])
def altCtgAssent():
    from ctgAssent import alterar_ctgassent
    return alterar_ctgassent()

# Exclusão (lista + painel de confirmação)
@app.route('/ctgAssentExc')
def ctgAssentExc():
    from ctgAssent import pagina_ctgAssentExc
    return pagina_ctgAssentExc()

@app.route('/excCtgAssent', methods=['POST'])
def excCtgAssent():
    from ctgAssent import excluir_ctgassent
    return excluir_ctgassent()


#------- cadastro assentado ----------------------
# Rota para cad   assentado
@app.route('/assentCad')
def assentCad():
    return render_template('assentCad.html')

@app.route('/cadAssent', methods=['POST'])
def cadAssent():
    # Redirecionar para a rota
    return cadastrar_assentado()

#------- alterar dados  assentado ----------------------
# Rota para cad   assentado
@app.route('/assentAlt')
def assentAlt():
    return render_template('assentAlt.html')

@app.route('/altAssent', methods=['POST'])
def altAssent():
    # Redirecionar para a rota
    return alterar_assentado()


#------- excluir  assentado ----------------------
# Rota para cad   assentado
@app.route('/assentExc')
def assentExc():
    return render_template('assentExc.html')

@app.route('/excAssent', methods=['POST'])
def excAssent():
    # Redirecionar para a rota
    return excluir_assentado()
#---------------------------------------------------
# Rota para alterar  situacao assentado


def _carrega_selects():
    conn = conectar_bd()
    categorias, politicas, unidades, assentados = [], [], [], []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idCatgFinanc","nomCatgFinanc", "catgParcdoSN" FROM "tbcatgfinanc" ORDER BY "nomCatgFinanc"')
        categorias = cur.fetchall()

        cur.execute('SELECT "idPolPub","nomPolPub","valor","perct" FROM "tbpolitpub" ORDER BY "nomPolPub"')
        politicas = cur.fetchall()

        cur.execute('SELECT "idTipUnEqv","nomUnEqv" FROM "tbtipuneqv" ORDER BY "nomUnEqv"')
        unidades = cur.fetchall()

        cur.execute(
            'SELECT "matricula","nome", "idFamilia" FROM "tbassentado" ORDER BY "nome"')
        assentados = cur.fetchall()

        conn.close()

    return categorias, politicas, unidades, assentados

#------- cadastro tipo de contribuicao ----------------------
# Rota para cad tipo de contribuicao
@app.route("/tipContribCad")
def tipContribCad():
    categorias, politicas, unidades, assentados = _carrega_selects()
    return render_template(
        "tipContribCad.html", message="✅ Tipo de Contribuição Cadastrada com Sucesso!",
        categorias=categorias,
        politicas=politicas,
        unidades=unidades
    )


@app.route('/cadTipContrib', methods=['POST'])
def cadTipContrib():
    # Redirecionar para a rota
    return cadastrar_tipcontrib()


# ALTERAR – lista + formulário (GET) e salvar (POST separado)
@app.route('/tipContribAlt')
def tipContribAlt():
    return view_tipContribAlt()


# EXCLUIR – lista + cartão de confirmação (GET) e exclusão (POST separado)
@app.route('/tipContribExc')
def tipContribExc():
    return view_tipContribExc()


@app.route('/altTipContrib', methods=['POST'])
def altTipContrib():
    return alterar_tipcontrib()


# -------CONSULTAS CONTRIBUICAO -----------------------

# --- Consulta Geral de Contribuições ---
@app.route('/conGeralContrib', methods=['GET'])
def conGeralContrib():
    from conGeralContrib import pagina_conGeralContrib
    return pagina_conGeralContrib()

@app.route('/conFiltroContrib', methods=['GET', 'POST'])
def conFiltroContrib():
    from conGeralContrib import conFiltroContrib
    return conFiltroContrib()

# Compat: se o menu ainda aponta para /conContrib, redireciona:
@app.route('/conContrib')
def conContrib():
    from flask import redirect, url_for, request
    return redirect(url_for('conGeralContrib', **request.args))



#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

#------- excluir tipo de contribuicao ----------------------

# Rota para cad tipo de retribuicao
@app.route("/tipRetribCad")
def tipRetribCad():
    categorias, politicas, unidades, assentados = _carrega_selects()
    return render_template(
        "tipRetribCad.html", message="✅ Tipo de Retribuição Cadastrada com Sucesso!",
        categorias=categorias,
        politicas=politicas,
        unidades=unidades
    )


@app.route('/cadTipRetrib', methods=['POST'])
def cadTipRetrib():
    # Redirecionar para a rota
    return cadastrar_tipretrib()

#------- alterar tipo de retrib ----------------------
# Rota para cad tipo de retr
@app.route('/tipRetribAlt')
def tipRetribAlt():
    return render_template('tipRetribAlt.html')

@app.route('/altTipRetrib', methods=['POST'])
def altTipRetrib():
    # Redirecionar para a rota
    return alterar_tip_retrib()

@app.route('/excTipContrib', methods=['POST'])
def excTipContrib():
    return excluir_tipo_contrib()


#------- excluir tipo de financas ----------------------
# Rota para exc tipo de financas
@app.route('/tipRetribExc')
def tipRetribExc():
    return render_template('tipRetribExc.html')

@app.route('/excTipRetrib', methods=['POST'])
def excTipRetrib():
    # Redirecionar para a rota
    return excluir_tipo_retrib()


# Rota para a cadastro de contribuicao
@app.route('/contribCad')
def contribCad():
    categorias, politicas, unidades, assentados = _carrega_selects()
    return render_template(
        "contribCad.html", message="✅  Contribuição Cadastrada com Sucesso!",
        categorias=categorias,
        assentados=assentados
    )

    return render_template('contribCad.html')

@app.route('/cadContrib', methods=['POST'])
def cadContrib():
    # Redirecionar para a rota
    return cadastrar_contrib()

# Rota para a cadastro retribuicao
@app.route('/retribCad')
def retribCad():
    categorias, politicas, unidades, assentados = _carrega_selects()
    return render_template(
        "retribCad.html", message="✅  Retribuição Cadastrada com Sucesso!",
        categorias=categorias,
        assentados=assentados
    )


    return render_template('retribCad.html')

@app.route('/cadRetrib', methods=['POST'])
def cadRetrib():
    # Redirecionar para a rota
    return cadastrar_retrib()


#------- cadastro e rotas  ----------------------
# Rota para menu BBC
@app.route('/menuBBC')
def menuBBC():
    return render_template('menuBBC.html')

@app.route('/menuAssent')
def menuAssent():
    return render_template('menuAssent.html')

@app.route('/menuCaderneta')
def menuCaderneta():
    return render_template('menuCaderneta.html')

#------- cadastro tipo de painel contribuicao ----------------------
# Rota para cad tipo de contribuicao
@app.route('/panlFinanCad ')
def panlFinanCad ():
    return render_template('panlFinanCad .html')

@app.route('/cadPanlFinanc ', methods=['POST'])
def cadPanlFinanc ():
    # Redirecionar para a rota
    return cadastrar_painel_contrib()

@app.route('/mensagem')
def mensagem():
    return render_template('mensagem.html')


@app.route('/cadPainelFinanc ', methods=['GET', 'POST'])
def cadPainelFinanc ():
    session['mensagem'] = "  "
    print("BBCQC..PY ==l 111 ===> /cadPainelFinanc  ")
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


@app.route('/cadStaAssent', methods=['GET', 'POST'])
def cad_sta_assentado():
    print("BBCQC..PY ==# -------------/////// hoooje CAD cadPainelFinanc  #######################")
    if request.method == 'POST':
        matricula = request.form.get('matricula')
        idStaAsent = request.form.get('idStaAsent')


  #  contrDiario = request.form.get('contrDiario')

    print("BBCQC..PY ==BBCQC..PY ===========> 22222 ####### CAD MEREDNA => ", contrDiario)

    # Renderiza o template merendaQC.html
    return cadastro_sta_asentado()

@app.route('/obter_dados_assent', methods=['GET', 'POST'])
def obter_dados_assent():
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT matricula, nome, foto FROM tbassentado ORDER BY nome")
            assentados = cur.fetchall()
            assentados_corrigidos = []
            for assentado in assentados:
                matricula, nome, foto = assentado  # Desempacotando os dados do assentado
                # Corrigindo o caminho da foto
                foto_corrigida = url_for('static', filename=f'img/{foto}')
                assentados_corrigidos.append((matricula, nome, foto_corrigida))
            conn.close()
            return assentados_corrigidos
        except Exception as e:
            session['mensagem'] = " Erro @@@ 111  oter_dados_aluno() !"
            print("BBCQC..PY ==Erro ao obter dados dos alunos:", e)
            return []
    else:
        return []


def obter_dados_painel_contrib():
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
            session['mensagem'] = " Erro ao obter dados de controle de cadPainelFinanc  !"
            print("BBCQC..PY ==Erro ao obter dados de controle de cadPainelFinanc :", e)
            return []
    else:
        return []


def obter_dados_assent_matricula(matr):
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT nome, foto FROM tbassentado WHERE matricula = %s", (matr,))
            assentado = cur.fetchone()
            if assentado is not None:
                print("BBCQC..PY ==44444  alunos ===>  ", assentado)
            if assentado:
                assent_corrigido = list(assentado)
                assent_corrigido[2] = url_for('static', filename='img/' + assentado[2])  # Corrigir o caminho da imagem
                print("BBCQC..PY ==55555  assentado corrigido ===>  ", assent_corrigido)
                conn.close()
                return assent_corrigido
            else:
                if assentado is not None:
                   print("BBCQC..PY ==assentado não encontrado")
                return None
        except Exception as e:
            session['mensagem'] = " Erro ao obter dados do assentado por matrícula !"
            print("BBCQC..PY ==Erro ao obter dados do assentado por matrícula:", e)
            return None
    else:
        return None


def obter_dados_assent_nome(nome):
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT matricula, nome, foto FROM tbassentado WHERE nome LIKE %s", ('%' + nome + '%',))
            assentados = cur.fetchall()
            print("BBCQC..PY ==91919191  alunos ===>  ", alunos)
            assentados_corrigidos = []
            for assentado in alunos:
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
            print("BBCQC..PY ==Erro ao obter dados dos usuarios:", e)
            return []
    else:
        return []


@app.route('/pesquisar_assent', methods=['POST'])
def pesquisar_assent():
    data_atual = datetime.now()
    tipo_consulta = request.form.get('tipo_consulta')
    assentado = None  # Defina a variável assentado como None no início
    matricula = request.form.get('matricula')
    idSitAssent = request.form.get('idSitAssent')
    idStaAssent = request.form.get('idStaAssent')

    print("BBCQC..PY ==@@ 111 PESQUISAR-assentado  (BBCQC.py) - pesquisar_assent()  turno=> ", turno)
    print("BBCQC..PY ==@@ 222  PESQUISAR-assentado (BBCQC.py) - pesquisar_assent()  matricula=> ", matricula)
    chave_pesquisa = idStaAssent + matricula.zfill(3)
    print("BBCQC..PY ==@@ 333  PESQUISAR-assentado (BBCQC.py) - pesquisar_assent()  chave=> ", chave_pesquisa)

    assentado = obter_dados_assentado(chave_pesquisa)
    print("BBCQC..PY ==@@ 444  PESQUISAR-assentado (BBCQC.py) - pesquisar_assent()  termo=>  ", assentado, " matricula => ", matricula)
    if assentado:
       print("BBCQC..PY == @@ 555  PESQUISAR-assentado (BBCQC.py) - pesquisar_assent()  assentado ===>  ", assentado[0])
    else:
       session['mensagem'] = " Não foram Encontrados assentados Com Esse Nome !"

    if assentado is not None:
        print("BBCQC..PY == @@ 666  PESQUISAR-assentado (BBCQC.py) ==>  ", assentado[0])
        session['mensagem'] = "  "
        return render_template('merendaQC.html', chave_pesquisa=chave_pesquisa, assentado=assentado,
                               contrabertos=contrabertos, ano=ano, mes=mes, data_atual=data_atual, qtddisp=qtddisp)
    else:
        print("BBCQC..PY == @@ 777  PESQUISAR-assentado (BBCQC.py) ==>  ", assentado[0])
        session['mensagem'] = f"Não foi encontrado assentado com o código {chave_pesquisa}!"
        return dados_merenda()



@app.route('/ver_assent', methods=['POST'])
def ver_assent():
    assent_selecionado_id = request.form.get('matricula')
    assent_selecionado = obter_dados_assent-matricula(aluno_selecionado_id)  # Substitua por sua função para obter dados do assentado por ID
    return render_template('merendaQC.html', assentado=assent_selecionado)


# Função para verificar as credenciais do usuário
def verificar_credenciais(usuario, senha):
    print("BBC2 ..PY == sigma- dados")
    conn = conectar_bd()
    if conn:
        try:
            print("BBC3 ..PY == sigma- dados")
            cur = conn.cursor()
            cur.execute("SELECT senha, nivel FROM tbusuario WHERE usuario = %s", (usuario,))
            resultado = cur.fetchone()
            conn.close()
            print("BBC4 ..PY == sigma- dados", resultado)
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
    print("BBCQC..PY ==*************** ENVIAR WHATSAPP ")

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
def cartaoQRassent():

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
            print("BBCQC..PY ==$$$$$$$$$$$$$$$   turno", turno)
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
            print("BBCQC..PY ==$$$$$$$$$$$$$$$ curso curso   curso", curso)
            return dados_cartao_curso(curso)
        else:
            return "Curso não fornecido."
    else:
        return render_template('emitirCartaoCurso.html')


@app.route('/cartaoAssent', methods=['GET', 'POST'])
def cartaoAssent():
   session['mensagem'] = "  "
   return cartao_assentado()


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


