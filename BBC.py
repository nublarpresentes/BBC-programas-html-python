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

from assentado import (
    consulta_nome_assentado, obter_foto_assentado, incluir_assentado,
    atualizar_assentado, excluir_assentado, consulta_todos_assentados
)



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

@app.route('/assentCad')
def assentCad():
    return render_template('assentCad.html')


@app.route('/cadAssent', methods=['POST'])
def cadAssent():
    return incluir_assentado()

@app.route('/assentAlt')
def assentAlt():
    return render_template('assentAlt.html')

@app.route('/altAssent', methods=['POST'])
def altAssent():
    return atualizar_assentado()

@app.route('/assentExc')
def assentExc():
    return render_template('assentExc.html')

@app.route('/excAssent', methods=['POST'])
def excAssent():
    return excluir_assentado()


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

        cur.execute('SELECT "matricula","nome","idFamilia" FROM "tbassentado" ORDER BY "nome"')
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

# compat
@app.route('/conContrib')
def conContrib():
    return redirect(url_for('conGeralContrib', **request.args))

# Consulta Geral Contribuições
@app.route('/conGeralContrib', methods=['GET'])
def conGeralContrib():
    from conGeralContrib import pagina_conGeralContrib
    return pagina_conGeralContrib()

@app.route('/conFiltroContrib', methods=['GET', 'POST'])
def conFiltroContrib():
    from conGeralContrib import conFiltroContrib
    return conFiltroContrib()


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
@app.route('/conGeralPartlh', methods=['GET'])
def conGeralPartlh():
    from conGeralPartlh import pagina_conGeralPartlh
    return pagina_conGeralPartlh()

@app.route('/conFiltroPartlh', methods=['GET', 'POST'])
def conFiltroPartlh():
    from conGeralPartlh import conFiltroPartlh
    return conFiltroPartlh()

# Compat (se menu antigo apontar para /conPartlh)
@app.route('/conPartlh')
def conPartlh():
    from flask import redirect, url_for, request
    return redirect(url_for('conGeralPartlh', **request.args))



# ========== TIPO DE RETRIBUIÇÃO ==========

@app.route("/tipRetribCad")
def tipRetribCad():
    categorias, politicas, unidades, _ = _carrega_selects()
    return render_template("tipRetribCad.html", message="✅ Tipo de Retribuição Cadastrada com Sucesso!",
                           categorias=categorias, politicas=politicas, unidades=unidades)

@app.route('/cadTipRetrib', methods=['POST'])
def cadTipRetrib():
    return cadastrar_tipretrib()

@app.route('/tipRetribAlt')
def tipRetribAlt():
    return render_template('tipRetribAlt.html')

@app.route('/altTipRetrib', methods=['POST'])
def altTipRetrib():
    # usar a função importada corretamente
    return alterar_tipretrib()

@app.route('/tipRetribExc')
def tipRetribExc():
    return render_template('tipRetribExc.html')

@app.route('/excTipRetrib', methods=['POST'])
def excTipRetrib():
    # se houver função excluir_tipo_retrib, importe e use; mantive como placeholder
    from tipRetrib import excluir_tipo_retrib
    return excluir_tipo_retrib()


# ========== RETRIBUIÇÃO ==========

@app.route('/retribCad')
def retribCad():
    categorias, politicas, unidades, assentados = _carrega_selects()
    return render_template("retribCad.html", message="✅  Retribuição Cadastrada com Sucesso!",
                           categorias=categorias, assentados=assentados)

@app.route('/cadRetrib', methods=['POST'])
def cadRetrib():
    return cadastrar_retrib()


# ========== MENUS ==========

@app.route('/menuBBC')
def menuBBC():
    return render_template('menuBBC.html')

@app.route('/menuCaderneta')
def menuCaderneta():
    return render_template('menuCaderneta.html')

@app.route('/menuAssent')
def menuAssent():
    return render_template('menuAssent.html')

@app.route('/mensagem')
def mensagem():
    return render_template('mensagem.html')


# ========== UTILITÁRIOS / DADOS AUXILIARES ==========

def obter_dados_assent_matricula(matr):
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT nome, foto FROM tbassentado WHERE matricula = %s", (matr,))
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
            cur.execute("SELECT matricula, nome, foto FROM tbassentado WHERE nome LIKE %s", ('%' + nome + '%',))
            assentados = cur.fetchall()
            assentados_corrigidos = []
            for matricula, nome, foto in assentados:
                foto_corrigida = url_for('static', filename='img/' + (foto or ''))
                assentados_corrigidos.append([matricula, nome, foto_corrigida])
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
        matricula = request.form.get('matricula')
        if matricula:
            return dados_cartao(matricula)
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


# -------------------- RUN --------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
