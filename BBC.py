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

# Assentado (tudo que a UI precisa)
from assent import (
    view_menuAssent,
    obter_foto_assentado,
    view_assentCad, cadastrar_assent,
    view_assentAlt, alterar_assent,
    view_assentExc,
    ver_carteira_assentado,
    view_gerarCarteira, post_gerarCarteira,
    pagina_conGeralAssent, conFiltroAssent
)

# Retribuição
from retrib import (
    view_retribCad, cadastrar_retrib,
    view_retribAlt, alterar_retrib,
    view_retribExc, excluir_retrib,
    pagina_conGeralRetrib, conFiltroRetrib,
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
    pagina_conGeralTipUsoInfr, conFiltroTipUsoInfr
)

from entidade import (
    view_entidadeCad, cadastrar_entidade,
    view_entidadeAlt, alterar_entidade,
    view_entidadeExc, excluir_entidade,
    pagina_conEntidade, conFiltroEntidade
)

from recpsa import (
    view_recpsaCad, cadastrar_recpsa
    # (demais telas de recpsa podem ser adicionadas quando necessário)
)

from catgUsoInfr import (
    view_catgUsoInfrCad, cadastrar_catgUsoInfr,
    view_catgUsoInfrAlt, alterar_catgUsoInfr,
    view_catgUsoInfrExc, excluir_catgUsoInfr,
    view_catgUsoInfrCon
)

from polPub import (
    cadastrar_politpub, alterar_politpub, excluir_politpub,
    listar_politpub, pegar_politpub, _listar_entidades,
    pagina_conPolitPub, conFiltroPolitPub
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
from tipRetrib import cadastrar_tipretrib, alterar_tipretrib

# Contribuição
from contrib import cadastrar_contrib, alterar_contrib, view_contribCad, view_contribAlt

# Partilha (partlh)
from partlh import (
    view_partlhCad, cadastrar_partlh,
    view_partlhAlt, alterar_partlh,
    view_partlhExc, excluir_partlh
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

from evento import (
    view_menuEvento,
    # Tipos
    view_tipEvtCad, cadastrar_tipevt, pagina_tipEvtAlt, alterar_tipevt, pagina_tipEvtExc, excluir_tipevt,
    # Eventos
    view_evtCad, cadastrar_evt,
    view_evtAlt, alterar_evento,
    view_evtExc, excluir_evento,
    pagina_evtCon, view_evtPresencaSel, gerar_lista_presenca_pdf,
    view_evtPresenca, registrar_evtPresenca
)

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

#============  *00 *BÁSICO ==================================================================
@app.route('/')
def index():
    return render_template('index.html')

# ========== *01 *USUÁRIO ================================================================
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

# ========== *02 *EVENTO ================================================================
@app.get('/evtCad')
def evtCad_view():
    return view_evtCad()

@app.post('/cadEvento')
def cadEvento_post():
    return cadastrar_evt()

@app.get('/cadEvento')
def cadEvento_get():
    return redirect(url_for('evtCad_view'))

@app.get('/evtAlt')
def evtAlt_view():
    return view_evtAlt()

@app.post('/altEvento')
def altEvento_post():
    return alterar_evento()

@app.get('/evtExc')
def evtExc_view():
    return view_evtExc()

@app.post('/excEvento')
def excEvento_post():
    return excluir_evento()

@app.get('/evtCon')
def evtCon_view():
    return pagina_evtCon()

@app.get('/evento/<int:idEvt>')
def evento_detalhe(idEvt: int):
    conn = conectar_bd()
    if not conn:
        flash("Não foi possível abrir o evento.", "danger")
        return redirect(url_for('menu'))
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT e."idEvt", e."nomEvt", COALESCE(e.descricao,''), COALESCE(e."fotoCapa",''),
                   e."dtIniPer", e."dtFimPer", e.turno, t."nomTipEvt"
              FROM tbevento e
              LEFT JOIN tbtipevt t ON t."idTipEvt" = e."idTipEvt"
             WHERE e."idEvt"=%s
        """, (idEvt,))
        row = cur.fetchone()
        if not row:
            flash("Evento não encontrado.", "warning")
            return redirect(url_for('menu'))
        evento = {
            "idEvt": row[0],
            "titulo": row[1],
            "descricao": row[2],
            "foto": row[3],
            "dtIniPer": row[4],
            "dtFimPer": row[5],
            "turno": row[6],
            "tipo": row[7],
        }
        return render_template('evtDetalhe.html', evento=evento)
    finally:
        try: conn.close()
        except: pass

@app.get('/menuEventos')
def menuEventos():
    from evento import view_menuEventos
    return view_menuEventos()

# --------- PRESENÇA EM EVENTO ---------
@app.get('/evtPres')
def evtPres_view():
    return view_evtPresenca()

@app.post('/evtPres')
def evtPres_post():
    return registrar_evtPresenca()

@app.get('/evtPresenca')
def evtPresencaSel_view():
    return view_evtPresencaSel()

@app.post('/evtPresencaPDF')
def evtPresencaPDF_post():
    return gerar_lista_presenca_pdf()

# ============= *03 *POLÍTICA PÚBLICA  ==================================================
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

@app.route('/politPubCon')
def politPubCon():
    entidades = _listar_entidades()
    return render_template('politPubCon.html', entidades=entidades)

@app.route('/conPolitPub', methods=['GET'])
def conPolitPub():
    return pagina_conPolitPub()

@app.route('/conFiltroPolitPub', methods=['GET','POST'])
def conFiltroPolitPub_route():
    return conFiltroPolitPub()

# ============  *04   *UNIDADE EQUIVALÊNCIA  ============================================
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

# =============  *05   *FAMÍLIA =========================================================
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

# ============ *06  *SITUAÇÃO ASSENTADO  ================================================
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

# ============   *07 *CATEGORIA ASSENTADO  ==============================================
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

# =============  *08  *ASSENTADO  =======================================================
@app.get('/menuAssent')
def menuAssent():
    return view_menuAssent()

@app.get('/conGeralAssent')
def conGeralAssent():
    return pagina_conGeralAssent()

@app.route('/conFiltroAssent', methods=['GET', 'POST'])
def conFiltroAssent_route():
    return conFiltroAssent()

@app.get('/assentCad')
def assentCad():
    return view_assentCad()

@app.post('/assentCad')
def cadAssent():
    return cadastrar_assent()

@app.get('/assentAlt')
def assentAlt():
    return view_assentAlt()

@app.post('/assentAlt')
def altAssent():
    return alterar_assent()

@app.get('/assentExc')
def assentExc():
    return view_assentExc()

@app.get('/carteira/<int:idAssent>')
def verCarteiraAssentado(idAssent: int):
    return ver_carteira_assentado(idAssent)

@app.get('/fotoAssent/<int:idAssent>')
def fotoAssent(idAssent: int):
    return obter_foto_assentado(idAssent)

@app.get("/gerarCarteira")
def gerarCarteira_get():
    return view_gerarCarteira()

@app.post("/gerarCarteira")
def gerarCarteira_post():
    return post_gerarCarteira()

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

@app.route('/cartaoQR', methods=['GET', 'POST'])
def cartaoQRassent():
    session['mensagem'] = "  "
    return cartaoQR()

@app.route('/gerarQR_PDF', methods=['GET', 'POST'])
def gerarQRPDF():
    session['mensagem'] = "  "
    return gerar_pdf_Cartao()

# =============   *09 *TIPO CONTRIBUIÇÃO  ===============================================
@app.route("/tipContribCad")
def tipContribCad():
    categorias, politicas, unidades, _ = _carrega_selects()
    return render_template(
        "tipContribCad.html",
        message="✅ Tipo de Contribuição Cadastrada com Sucesso!",
        categorias=categorias, politicas=politicas, unidades=unidades
    )

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

@app.route('/conGeralTipContrib', methods=['GET'])
def conGeralTipContrib():
    from conGeralTipContrib import pagina_conGeralTipContrib
    return pagina_conGeralTipContrib()

@app.route('/conFiltroTipContrib', methods=['GET','POST'])
def conFiltroTipContrib():
    from conGeralTipContrib import conFiltroTipContrib
    return conFiltroTipContrib()

# =============   *10  *CONTRIBUIÇÃO  ====================================================
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

@app.route('/conContrib')
def conContrib():
    return redirect(url_for('conGeralContrib', **request.args))

@app.route('/conGeralContrib', methods=['GET'])
def conGeralContrib():
    from conGeralContrib import pagina_conGeralContrib
    return pagina_conGeralContrib()

@app.route('/conFiltroContrib', methods=['GET', 'POST'])
def conFiltroContrib():
    from conGeralContrib import conFiltroContrib as _conFiltroContrib
    return _conFiltroContrib()

# ============  *11  *PARTILHA ===========================================================
@app.get("/partlhCad")
def partlhCad():
    return view_partlhCad()

@app.post("/cadPartlh")
def route_cadPartlh():
    return cadastrar_partlh()

@app.get("/partlhAlt")
def partlhAlt():
    return view_partlhAlt()

@app.post("/altPartlh")
def altPartlh():
    return alterar_partlh()

@app.get("/partlhExc")
def partlhExc():
    return view_partlhExc()

@app.post("/excPartlh")
def excPartlh():
    return excluir_partlh()

@app.route('/conGeralTipPartlh', methods=['GET'])
def conGeralTipPartlh():
    from conGeralTipPartlh import pagina_conGeralTipPartlh
    return pagina_conGeralTipPartlh()

@app.route('/conFiltroTipPartlh', methods=['GET','POST'])
def conFiltroTipPartlh():
    from conGeralTipPartlh import conFiltroTipPartlh
    return conFiltroTipPartlh()

@app.route('/conPartlh')
def conPartlh():
    return redirect(url_for('conGeralPartlh', **request.args))

# =============  *12  *RETRIBUIÇÃO =======================================================
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

@app.get('/conGeralRetrib')
def conGeralRetrib():
    return pagina_conGeralRetrib()

@app.route('/conFiltroRetrib', methods=['GET', 'POST'])
def conFiltroRetrib_route():
    return conFiltroRetrib()

#================  *13  *TIPO RECOMPENSA  ===============================================
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

@app.route('/conGeralTipRecpsa', methods=['GET'])
def conGeralTipRecpsa():
    return pagina_conGeralTipRecpsa()

@app.route('/conFiltroTipRecpsa', methods=['GET', 'POST'])
def conFiltroTipRecpsa_route():
    return conFiltroTipRecpsa()

#================  *14  *USO DA INFRAESTRUTURA ==========================================
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

@app.route('/conGeralTipUsoInfr', methods=['GET'])
def conGeralTipUsoInfr():
    return pagina_conGeralTipUsoInfr()

@app.route('/conFiltroTipUsoInfr', methods=['GET', 'POST'])
def conFiltroTipUsoInfr_route():
    return conFiltroTipUsoInfr()

#===============  *15  *RECOMPENSAS  =====================================================
@app.route('/recpsaCad')
def recpsaCad():
    return view_recpsaCad()

@app.route('/cadRecpsa', methods=['POST'])
def cadRecpsa():
    return cadastrar_recpsa()

@app.get('/conGeralRecpsa')
def conGeralRecpsa_alias():
    return pagina_conGeralRetrib()

@app.route('/conGeralRecpsa', methods=['GET'])
def conGeralRecpsa():
    from recpsa import pagina_conGeralRecpsa
    return pagina_conGeralRecpsa()

@app.route('/conFiltroRecpsa', methods=['GET','POST'])
def conFiltroRecpsa_route():
    from recpsa import conFiltroRecpsa
    return conFiltroRecpsa()

#==============  *16  *CATEGORIA USO INFRAESTRUTURA  ====================================
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

# ============  *18  *ENTIDADES   =======================================================
@app.route('/entidadeCad')
def entidadeCad():
    return view_entidadeCad()

@app.route('/cadEntidade', methods=['POST'])
def cadEntidade():
    return cadastrar_entidade()

@app.route('/entidadeAlt')
def entidadeAlt():
    return view_entidadeAlt()

@app.route('/altEntidade', methods=['POST'])
def altEntidade():
    return alterar_entidade()

@app.route('/entidadeExc')
def entidadeExc():
    return view_entidadeExc()

@app.route('/excEntidade', methods=['POST'])
def excEntidade():
    return excluir_entidade()

@app.route('/entidadeCon', methods=['GET', 'POST'])
def conEntidade():
    return pagina_conEntidade()

#=============   *19   *SALDO  ===========================================================
@app.route('/conGeralSaldo', methods=['GET'])
def conGeralSaldo():
    return pagina_conGeralSaldo()

@app.route('/conFiltroSaldo', methods=['GET', 'POST'])
def conFiltroSaldo_route():
    return conFiltroSaldo()

# =============  *20   *SELECT / MENUS / UTILITÁRIOS =====================================
@app.get('/menuBBC')
def menuBBC():
    from flask import session  # (garante acesso ao session aqui)

    conn = conectar_bd()
    noticia_capa = None
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT "nomEvt", "fotoCapa", "idEvt"
                FROM tbevento
                WHERE capa = 'S' AND "idTipEvt" = 1
                ORDER BY "idEvt" DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            if row:
                noticia_capa = {
                    "titulo": row[0],
                    "foto": row[1],
                    "idEvt": row[2]
                }
        finally:
            try: conn.close()
            except: pass

    # >>>>>> AQUI está a mudança: usar menuBBC.html em vez de menu.html
    usuario = session.get('usuario', 'Usuário')
    return render_template('menuBBC.html', usuario=usuario, noticia_capa=noticia_capa)

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

        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome"')
        assentados = cur.fetchall()
        conn.close()
    return categorias, politicas, unidades, assentados

@app.route('/menuCaderneta')
def menuCaderneta():
    return render_template('menuCaderneta.html')

@app.route('/mensagem')
def mensagem():
    return render_template('mensagem.html')

@app.route('/menuRetrib')
def menuRetrib():
    return render_template('menuRetrib.html', usuario=session.get('usuario') if 'session' in globals() else None)

@app.route('/whatsapp', methods=['GET', 'POST'])
def rotina_whatsapp():
    session['mensagem'] = "  "
    return dados_whatsapp()

@app.route('/enviarWhatsapp', methods=['POST'])
def enviar_msg_whatsapp():
    session['mensagem'] = "  "
    return enviar_whatsapp()

def _buscar_noticia_capa():
    conn = conectar_bd()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT "idEvt", "nomEvt", COALESCE(descricao, ''), COALESCE("fotoCapa", '')
              FROM tbevento
             WHERE "idTipEvt" = 1
               AND UPPER(COALESCE(capa,'N')) = 'S'
             ORDER BY "idEvt" DESC
             LIMIT 1
        """)
        row = cur.fetchone()
        if not row:
            return None
        idEvt, nomEvt, descricao, fotoCapa = row
        return {
            "idEvt": idEvt,
            "titulo": nomEvt,
            "descricao": descricao,
            "foto": fotoCapa
        }
    finally:
        try: conn.close()
        except: pass


@app.get('/menu')
def menu():
    usuario = session.get('usuario', 'Visitante')
    conn = conectar_bd()
    noticia_capa = None
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT "nomEvt", "fotoCapa", "idEvt"
                FROM tbevento
                WHERE capa = 'S' AND "idTipEvt" = 1
                ORDER BY "idEvt" DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            if row:
                noticia_capa = {"titulo": row[0], "foto": row[1], "idEvt": row[2]}
        finally:
            try: conn.close()
            except: pass
    return render_template('menu.html', usuario=session.get('usuario', 'Usuário'), noticia_capa=noticia_capa)




def _pegar_noticia_capa():
    conn = conectar_bd()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT e."idEvt",
                   e."nomEvt",
                   COALESCE(e.descricao, ''),
                   COALESCE(e."fotoCapa", '')
              FROM tbevento e
             WHERE e."idTipEvt" = 1
               AND e.capa = 'S'
             ORDER BY e."idEvt" DESC
             LIMIT 1
        """)
        row = cur.fetchone()
        if not row:
            return None
        return {
            "idEvt": row[0],
            "titulo": row[1],
            "descricao": row[2],
            "foto": row[3],
        }
    finally:
        try: conn.close()
        except: pass

# -------------------- RUN --------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
