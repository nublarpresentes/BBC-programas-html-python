import psycopg2
from datetime import datetime

from flask import Flask, request, render_template, redirect, url_for, session, flash

# -------------------- IMPORTS DO PROJETO --------------------

from conexao_bd import conectar_bd

# Controle/WhatsApp/Cartão
from controleBBC import (
    dados_controle, cadastrar_controle, busca_controle, atualizar_matricula,
    dados_whatsapp, enviar_whatsapp, cartaoQR,
    gerar_pdf_Cartao, dados_cartao, cartaoQR, dados_cartao_turno, cartao_turno,
    dados_cartao_curso, cartao_curso
)

# Assentado

from assent import (
     obter_foto_assentado, view_assentCad, view_assentAlt, view_assentExc, _valida_cpf_mod11,
     cadastrar_assent, alterar_assent, excluir_assent
)



# Retribuição
from retrib import (
    view_retribCad, cadastrar_retrib,
    view_retribAlt, alterar_retrib,
    view_retribExc, excluir_retrib,
    pagina_conGeralRetrib, conFiltroRetrib,  # << nomes corretos da consulta geral
)




from tipRecpsa import (
    view_tipRecpsaCad, cadastrar_tiprecpsa,
    view_tipRecpsaAlt, alterar_tiprecpsa,
    view_tipRecpsaExc, excluir_tiprecpsa,
    pagina_conGeralTipRecpsa, conFiltroTipRecpsa
)


from tipUsoInfr import (
    view_tipUsoInfrCad, cadastrar_tipusoinfr,
    view_tipUsoInfrAlt, alterar_tipusoinfr,
    view_tipUsoInfrExc, excluir_tipusoinfr,
    pagina_conGeralTipUsoInfr,  conFiltroTipUsoInfr
)

from recpsa import (
    view_recpsaCad, cadastrar_recpsa
#   view_recpsaAlt, alterar_recpsa,
#     view_recpsaAlt, view_recpsaExc,
#    view_recpsaExc, excluir_recpsa,
#    pagina_conGeralRecpsa, conFiltroRecpsa
)

from catgUsoInfr import (
    view_catgUsoInfrCad, cadastrar_catgUsoInfr,
    view_catgUsoInfrAlt, alterar_catgUsoInfr,
    view_catgUsoInfrExc, excluir_catgUsoInfr,
    view_catgUsoInfrCon
)

from saldo import pagina_conGeralSaldo, conFiltroSaldo



# Usuário / Login
from usuario import acessoUsuario, cadastrar_usuario, recuperar_senha, alterar_senha, alterar_usuario

# Consultas
from consultas import consQTDdia, consQTDsem

# Tipo Contribuição
from tipContrib import (
    listar_tipcontrib, pegar_tipcontrib, excluir_tipo_contrib,
    cadastrar_tipcontrib, alterar_tipcontrib, view_tipContribAlt, view_tipContribExc
)

# Tipo Retribuição
from tipRetrib import cadastrar_tipretrib, alterar_tipretrib  # nomes corretos

# Contribuição
from contrib import cadastrar_contrib, alterar_contrib, view_contribCad, view_contribAlt

# Partilha (partlh)
from partlh import (
    view_partlhCad, cadastrar_partlh,
    view_partlhAlt, alterar_partlh,
    view_partlhExc, excluir_partlh
)

# Retribuição
from retrib import cadastrar_retrib, alterar_retrib

# Política Pública
from polPub import (
    cadastrar_politpub, alterar_politpub, excluir_politpub,
    listar_politpub, pegar_politpub, _listar_entidades
)

# Unidade de Equivalência
from unEqv import (
    cadastrar_uneqv, alterar_uneqv, excluir_uneqv,
    pagina_unEqvAlt, pagina_unEqvExc
)

# Família
from familia import cadastrar_familia, pagina_familiaAlt, alterar_familia, pagina_familiaExc, excluir_familia

# Situação Assentado
from sitAssent import cadastrar_sitassent, pagina_sitAssentAlt, alterar_sitassent, pagina_sitAssentExc, excluir_sitassent

# Categoria Assentado
from ctgAssent import cadastrar_ctgassent, pagina_ctgAssentAlt, alterar_ctgassent, pagina_ctgAssentExc, excluir_ctgassent

# Tipo Evento
from tipEvt import pagina_tipEvtAlt, pagina_tipEvtExc, cadastrar_tipevt, alterar_tipevt, excluir_tipevt

# Grupo de Partilha
from grpPartlh import (
    cadastrar_grpPartlh, alterar_grpPartlh, excluir_grpPartlh,
    pagina_grpPartlhAlt, pagina_grpPartlhExc, pagina_grpPartlhCon
)

# Grupo x Assentado
from grpAssent import (
    pagina_grpAssentCad, pagina_grpAssentAlt, pagina_grpAssentExc,
    cadastrar_grpAssent, alterar_grpAssent, excluir_grpAssent
)

# -------------------- FLASK APP --------------------

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = '@Sigma4321'
app.secret_key = "um_segredo_bem_dificil"

# -------------------- BÁSICO --------------------

@app.route('/')
def index():
    return render_template('index.html')


# ========== LOGIN / USUÁRIO ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    return acessoUsuario()

@app.route('/usuarioCad')
def usuarioCad():
    return render_template('usuarioCad.html')

@app.route('/cadUsuario', methods=['POST'])
def cadUsuario():
    return cadastrar_usuario()

@app.route('/usuarioAlt')
def usuarioAlt():
    return render_template('usuarioAlt.html')

@app.route('/altUsuario', methods=['POST'])
def altUsuario():
    return alterar_usuario()

@app.route('/senhaRec')
def senhaRec():
    return render_template('senhaRec.html')

@app.route('/recSenha', methods=['POST'])
def recSenha():
    return recuperar_senha()

@app.route('/senhaAlt')
def senhaAlt():
    return render_template('senhaAlt.html')

@app.route('/altSenha', methods=['POST'])
def altSenha():
    return alterar_senha()


# ========== TIPO DE EVENTO ==========

@app.route('/tipEvtCad')
def tipEvtCad():
    return render_template('tipEvtCad.html')

@app.route('/cadTipEvt', methods=['POST'])
def cadTipEvt():
    return cadastrar_tipevt()

@app.route('/tipEvtAlt')
def tipEvtAlt():
    return pagina_tipEvtAlt()

@app.route('/altTipEvt', methods=['POST'])
def altTipEvt():
    return alterar_tipevt()

@app.route('/tipEvtExc')
def tipEvtExc():
    return pagina_tipEvtExc()

@app.route('/excTipEvt', methods=['POST'])
def excTipEvt():
    return excluir_tipevt()


# ========== POLÍTICA PÚBLICA ==========

@app.route('/politPubCad')
def politPubCad():
    entidades = _listar_entidades()
    return render_template('politPubCad.html', entidades=entidades)

@app.route('/cadPolitPub', methods=['POST'])
def cadPolitPub():
    return cadastrar_politpub()

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


# ========== UNIDADE DE EQUIVALÊNCIA ==========

@app.route('/unEqvCad')
def unEqvCad():
    return render_template('unEqvCad.html')

@app.route('/cadUnEqv', methods=['POST'])
def cadUnEqv():
    return cadastrar_uneqv()

@app.route('/unEqvAlt')
def unEqvAlt():
    return pagina_unEqvAlt()

@app.route('/altUnEqv', methods=['POST'])
def altUnEqv():
    return alterar_uneqv()

@app.route('/unEqvExc')
def unEqvExc():
    return pagina_unEqvExc()

@app.route('/excUnEqv', methods=['POST'])
def excUnEqv():
    return excluir_uneqv()


# ========== FAMÍLIA ==========

@app.route('/familiaCad')
def familiaCad():
    return render_template('familiaCad.html')

@app.route('/cadFamilia', methods=['POST'])
def cadFamilia():
    return cadastrar_familia()

@app.route('/familiaAlt')
def familiaAlt():
    return pagina_familiaAlt()

@app.route('/altFamilia', methods=['POST'])
def altFamilia():
    return alterar_familia()

@app.route('/familiaExc')
def familiaExc():
    return pagina_familiaExc()

@app.route('/excFamilia', methods=['POST'])
def excFamilia():
    return excluir_familia()


# ========== SITUAÇÃO ASSENTADO ==========

@app.route('/sitAssentCad')
def sitAssentCad():
    return render_template('sitAssentCad.html')

@app.route('/cadSitAssent', methods=['POST'])
def cadSitAssent():
    return cadastrar_sitassent()

@app.route('/sitAssentAlt')
def sitAssentAlt():
    return pagina_sitAssentAlt()

@app.route('/altSitAssent', methods=['POST'])
def altSitAssent():
    return alterar_sitassent()

@app.route('/sitAssentExc')
def sitAssentExc():
    return pagina_sitAssentExc()

@app.route('/excSitAssent', methods=['POST'])
def excSitAssent():
    return excluir_sitassent()


# ========== CATEGORIA ASSENTADO ==========

@app.route('/ctgAssentCad')
def ctgAssentCad():
    return render_template('ctgAssentCad.html')

@app.route('/cadCtgAssent', methods=['POST'])
def cadCtgAssent():
    return cadastrar_ctgassent()

@app.route('/ctgAssentAlt')
def ctgAssentAlt():
    return pagina_ctgAssentAlt()

@app.route('/altCtgAssent', methods=['POST'])
def altCtgAssent():
    return alterar_ctgassent()

@app.route('/ctgAssentExc')
def ctgAssentExc():
    return pagina_ctgAssentExc()

@app.route('/excCtgAssent', methods=['POST'])
def excCtgAssent():
    return excluir_ctgassent()


# ========== ASSENTADO (CAD/ALT/EXC) ==========
# --- ASSENTADO: rotas (CRUD + Consulta Geral) ---
from assent import (
    view_assentCad, cadastrar_assent,
    view_assentAlt, alterar_assent,
    view_assentExc, excluir_assent,
    pagina_conGeralAssent, conFiltroAssent
)

@app.get('/menuAssent')
def menuAssent():
    return view_assentCad()

@app.get('/assentCad')
def assentCad():
    return view_assentCad()

@app.post('/cadAssent')
def cadAssent():
    return cadastrar_assent()

@app.get('/assentAlt')
def assentAlt():
    return view_assentAlt()

@app.post('/altAssent')
def altAssent():
    return alterar_assent()

@app.get('/assentExc')
def assentExc():
    return view_assentExc()

@app.post('/excAssent')
def excAssent():
    return excluir_assent()

@app.get('/conGeralAssent')
def conGeralAssent():
    return pagina_conGeralAssent()

@app.route('/conFiltroAssent', methods=['GET', 'POST'])
def conFiltroAssent_route():
    return conFiltroAssent()

# ========== SELECTS GERAIS (para telas que precisam) ==========

def _carrega_selects():
    conn = conectar_bd()
    categorias, politicas, unidades, assentados = [], [], [], []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idCatgFinanc","nomCatgFinanc","catgParcdoSN" FROM "tbcatgfinanc" ORDER BY "nomCatgFinanc"')
        categorias = cur.fetchall()

        cur.execute('SELECT "idPolPub","nomPolPub","valor","perct" FROM "tbpolitpub" ORDER BY "nomPolPub"')
        politicas = cur.fetchall()

        cur.execute('SELECT "idTipUnEqv","nomUnEqv" FROM "tbtipuneqv" ORDER BY "nomUnEqv"')
        unidades = cur.fetchall()

        # AQUI trocamos idAssent -> idAssent
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome"')
        assentados = cur.fetchall()

        conn.close()
    return categorias, politicas, unidades, assentados


# ========== TIPO DE CONTRIBUIÇÃO (CAD/ALT/EXC) ==========

@app.route("/tipContribCad")
def tipContribCad():
    categorias, politicas, unidades, _ = _carrega_selects()
    return render_template("tipContribCad.html", message="✅ Tipo de Contribuição Cadastrada com Sucesso!",
                           categorias=categorias, politicas=politicas, unidades=unidades)

@app.route('/cadTipContrib', methods=['POST'])
def cadTipContrib():
    return cadastrar_tipcontrib()

@app.route('/tipContribAlt')
def tipContribAlt():
    return view_tipContribAlt()

@app.route('/tipContribExc')
def tipContribExc():
    return view_tipContribExc()

@app.route('/altTipContrib', methods=['POST'])
def altTipContrib():
    return alterar_tipcontrib()

@app.route('/excTipContrib', methods=['POST'])
def excTipContrib():
    return excluir_tipo_contrib()


# ========== CONTRIBUIÇÃO (CAD/ALT + CONSULTA) ==========

@app.route('/contribCad')
def contribCad():
    return view_contribCad()

@app.route('/cadContrib', methods=['POST'])
def cadContrib():
    return cadastrar_contrib()

@app.route('/contribAlt')
def contribAlt():
    return view_contribAlt()

@app.route('/altContrib', methods=['POST'])
def altContrib():
    return alterar_contrib()

# --- Consulta Geral de Tipos de Contribuição ---
@app.route('/conGeralTipContrib', methods=['GET'])
def conGeralTipContrib():
    from conGeralTipContrib import pagina_conGeralTipContrib
    return pagina_conGeralTipContrib()

@app.route('/conFiltroTipContrib', methods=['GET','POST'])
def conFiltroTipContrib():
    from conGeralTipContrib import conFiltroTipContrib
    return conFiltroTipContrib()



# compat
@app.route('/conContrib')
def conContrib():
    return redirect(url_for('conGeralContrib', **request.args))

# ========== PARTILHA (partlh) — CAD/ALT/EXC + CONSULTA ==========

# Consulta Geral Partilha


def view_partlhAlt():
    return "Tela de Alteração de Partilha em construção"

def alterar_partlh():
    return "Alteração de Partilha em construção"

def view_partlhExc():
    return "Tela de Exclusão de Partilha em construção"

def excluir_partlh():
    return "Exclusão de Partilha em construção"

from partlh import (
    view_partlhCad, cadastrar_partlh,
    view_partlhAlt, alterar_partlh,
    view_partlhExc, excluir_partlh
)

# CAD
@app.get("/partlhCad")
def partlhCad():
    return view_partlhCad()

@app.post("/cadPartlh")
def route_cadPartlh():
    return cadastrar_partlh()

# ALT
@app.get("/partlhAlt")
def partlhAlt():
    return view_partlhAlt()

@app.post("/altPartlh")
def altPartlh():
    return alterar_partlh()

# EXC
@app.get("/partlhExc")
def partlhExc():
    return view_partlhExc()

@app.post("/excPartlh")
def excPartlh():
    return excluir_partlh()

# --- Consulta Geral de Partilha ---

# --- Consulta Geral de Tipos de Partilha ---
@app.route('/conGeralTipPartlh', methods=['GET'])
def conGeralTipPartlh():
    from conGeralTipPartlh import pagina_conGeralTipPartlh
    return pagina_conGeralTipPartlh()

@app.route('/conFiltroTipPartlh', methods=['GET','POST'])
def conFiltroTipPartlh():
    from conGeralTipPartlh import conFiltroTipPartlh
    return conFiltroTipPartlh()


# Compat (se menu antigo apontar para /conPartlh)
@app.route('/conPartlh')
def conPartlh():
    from flask import redirect, url_for, request
    return redirect(url_for('conGeralPartlh', **request.args))


# ========== MENUS ==========

@app.route('/menuBBC')
def menuBBC():
    return render_template('menuBBC.html')

@app.route('/menuCaderneta')
def menuCaderneta():
    return render_template('menuCaderneta.html')

@app.route('/mensagem')
def mensagem():
    return render_template('mensagem.html')


# ========== UTILITÁRIOS / DADOS AUXILIARES ==========

def obter_dados_assent_idassent(matr):
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT nome, foto FROM tbassentado WHERE idAssent = %s", (matr,))
            assentado = cur.fetchone()
            if not assentado:
                return None
            nome, foto = assentado
            foto_corrigida = url_for('static', filename='img/' + (foto or ''))
            conn.close()
            return [nome, foto_corrigida]
        except Exception as e:
            session['mensagem'] = "Erro ao obter dados do assentado por matrícula!"
            print("Erro obter_dados_assent_matricula:", e)
            return None
    return None

def obter_dados_assent_nome(nome):
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT idAssent, nome, foto FROM tbassentado WHERE nome LIKE %s", ('%' + nome + '%',))
            assentados = cur.fetchall()
            assentados_corrigidos = []
            for idAssent, nome, foto in assentados:
                foto_corrigida = url_for('static', filename='img/' + (foto or ''))
                assentados_corrigidos.append([idAssent, nome, foto_corrigida])
            conn.close()
            return assentados_corrigidos
        except Exception as e:
            session['mensagem'] = "Erro ao obter dados dos assentados por nome!"
            print("Erro obter_dados_assent_nome:", e)
            return []
    return []

@app.route('/usuario')
def obter_todos_usuario():
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT usuario, senha, nome, nivel, email FROM tbusuario ORDER BY nome")
            usuario = cur.fetchall()
            conn.close()
            return usuario
        except Exception as e:
            print("Erro ao obter dados dos usuarios:", e)
            return []
    return []


# ========== WHATSAPP / QRCODE / CARTÕES ==========

@app.route('/whatsapp', methods=['GET', 'POST'])
def rotina_whatsapp():
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
        idAssent = request.form.get('idAssent')
        if idAssent:
            return dados_cartao(idAssent)
        return "Matrícula não fornecida."
    return render_template('emitirCartao.html')

@app.route('/emitirCartaoTurno', methods=['GET', 'POST'])
def emitirCartaoTurno():
    if request.method == 'POST':
        turno = request.form.get('turno')
        if turno:
            return dados_cartao_turno(turno)
        return "Turno não fornecido."
    return render_template('emitirCartaoTurno.html')

@app.route('/emitirCartaoCurso', methods=['GET', 'POST'])
def emitirCartaoCurso():
    if request.method == 'POST':
        curso = request.form.get('curso')
        if curso:
            return dados_cartao_curso(curso)
        return "Curso não fornecido."
    return render_template('emitirCartaoCurso.html')


# ========== CONSULTAS SÍNTESE ==========

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
def sigConsQTDdia_action():
    return consQTDdia()

@app.route('/sigConsQTDsem', methods=['POST'])
def sigConsQTDsem_action():
    return consQTDsem()


# -------------------------------- REIRIBUIÇÃO ROTAS

# --------- TIPO DE RECOMPENSA (tbtiprecpsa) ---------

@app.route('/tipRecpsaCad')
def tipRecpsaCad():
    return view_tipRecpsaCad()

@app.route('/cadTipRecpsa', methods=['POST'])
def cadTipRecpsa():
    return cadastrar_tiprecpsa()

@app.route('/tipRecpsaAlt')
def tipRecpsaAlt():
    return view_tipRecpsaAlt()

@app.route('/altTipRecpsa', methods=['POST'])
def altTipRecpsa():
    return alterar_tiprecpsa()

@app.route('/tipRecpsaExc')
def tipRecpsaExc():
    return view_tipRecpsaExc()

@app.route('/excTipRecpsa', methods=['POST'])
def excTipRecpsa():
    return excluir_tiprecpsa()

# --- Consulta geral (com filtros)
@app.route('/conGeralTipRecpsa', methods=['GET'])
def conGeralTipRecpsa():
    return pagina_conGeralTipRecpsa()

@app.route('/conFiltroTipRecpsa', methods=['GET', 'POST'])
def conFiltroTipRecpsa_route():
    return conFiltroTipRecpsa()


# --------- TIPO DE USO DA INFRAESTRUTURA ---------
@app.route('/tipUsoInfrCad')
def tipUsoInfrCad():
    return view_tipUsoInfrCad()

@app.route('/cadTipUsoInfr', methods=['POST'])
def cadTipUsoInfr():
    return cadastrar_tipusoinfr()

@app.route('/tipUsoInfrAlt')
def tipUsoInfrAlt():
    return view_tipUsoInfrAlt()

@app.route('/altTipUsoInfr', methods=['POST'])
def altTipUsoInfr():
    return alterar_tipusoinfr()

@app.route('/tipUsoInfrExc')
def tipUsoInfrExc():
    return view_tipUsoInfrExc()

@app.route('/excTipUsoInfr', methods=['POST'])
def excTipUsoInfr():
    return excluir_tipusoinfr()

# --- Consulta geral
@app.route('/conGeralTipUsoInfr', methods=['GET'])
def conGeralTipUsoInfr():
    return pagina_conGeralTipUsoInfr()

@app.route('/conFiltroTipUsoInfr', methods=['GET', 'POST'])
def conFiltroTipUsoInfr_route():
    return conFiltroTipUsoInfr()


# --------- RECOMPENSAS (tbrecpsa) ---------
@app.route('/recpsaCad')
def recpsaCad():
    return view_recpsaCad()

@app.route('/cadRecpsa', methods=['POST'])
def cadRecpsa():
    return cadastrar_recpsa()

@app.route('/recpsaAlt')
def recpsaAlt():
    return view_recpsaAlt()

@app.route('/altRecpsa', methods=['POST'])
def altRecpsa():
    return alterar_recpsa()

@app.route('/recpsaExc')
def recpsaExc():
    return view_recpsaExc()

@app.route('/excRecpsa', methods=['POST'])
def excRecpsa():
    return excluir_recpsa()

# --- Consulta geral
@app.route('/conGeralRecpsa', methods=['GET'])
def conGeralRecpsa():
    return pagina_conGeralRecpsa()

@app.route('/conFiltroRecpsa', methods=['GET','POST'])
def conFiltroRecpsa_route():
    return conFiltroRecpsa()

@app.route('/menuRetrib')
def menuRetrib():
    # se você guarda o usuário na sessão, passe aqui; senão remove "usuario=..."
    return render_template('menuRetrib.html', usuario=session.get('usuario') if 'session' in globals() else None)

##------------------CATEGORIA USO DA INFRAESTRUTURA

# ---- Categoria do Uso da Infraestrutura ----
@app.route('/catgUsoInfrCad', methods=['GET'])
def catgUsoInfrCad():
    return view_catgUsoInfrCad()

@app.route('/cadCatgUsoInfr', methods=['POST'])
def cadCatgUsoInfr():
    return cadastrar_catgUsoInfr()

@app.route('/catgUsoInfrAlt', methods=['GET'])
def catgUsoInfrAlt():
    return view_catgUsoInfrAlt()

@app.route('/altCatgUsoInfr', methods=['POST'])
def altCatgUsoInfr():
    return alterar_catgUsoInfr()

@app.route('/catgUsoInfrExc', methods=['GET'])
def catgUsoInfrExc():
    return view_catgUsoInfrExc()

@app.route('/excCatgUsoInfr', methods=['POST'])
def excCatgUsoInfr():
    return excluir_catgUsoInfr()

@app.route('/catgUsoInfrCon', methods=['GET'])
def catgUsoInfrCon():
    return view_catgUsoInfrCon()


# BBC.py — ROTAS DE RETRIBUIÇÃO
# -------------------------------------------------
# ==========  RETRIBUIÇÃO ==========

@app.route('/retribCad', methods=['GET'])
def retribCad():
    return view_retribCad()

@app.route('/cadRetrib', methods=['POST'])
def cadRetrib():
    return cadastrar_retrib()

@app.route('/retribAlt', methods=['GET'])
def retribAlt():
    return view_retribAlt()

@app.route('/altRetrib', methods=['POST'])
def altRetrib():
    return alterar_retrib()

@app.route('/retribExc', methods=['GET'])
def retribExc():
    return view_retribExc()

@app.route('/excRetrib', methods=['POST'])
def excRetrib():
    return excluir_retrib()

# --- Consulta Geral de Retribuições ---
@app.get('/conGeralRetrib')
def conGeralRetrib():
    return pagina_conGeralRetrib()

@app.route('/conFiltroRetrib', methods=['GET', 'POST'])
def conFiltroRetrib_route():
    return conFiltroRetrib()

# -------- SALDO (Consulta Geral) --------
@app.route('/conGeralSaldo', methods=['GET'])
def conGeralSaldo():
    return pagina_conGeralSaldo()

@app.route('/conFiltroSaldo', methods=['GET', 'POST'])
def conFiltroSaldo_route():
    return conFiltroSaldo()


# -------------------- RUN --------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
