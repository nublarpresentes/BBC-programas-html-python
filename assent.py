# assent.py
import re
import os, io
import psycopg2
from datetime import datetime, date
from PIL import Image, ImageOps
import qrcode

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.barcode import qr as rl_qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from flask import (
    request, render_template, redirect, url_for, flash,
    send_file, abort, current_app
)

from conexao_bd import conectar_bd

PER_PAGE = 15
_only_digits = re.compile(r"\D+")

# ==========================
# Helpers de caminho (sem path fixo do Windows)
# ==========================
def _pasta_static(*parts) -> str:
    """Retorna caminho absoluto dentro de <app>/static/..."""
    return os.path.join(current_app.root_path, "static", *parts)

def _pasta_imagens() -> str:
    """<app>/static/img"""
    path = _pasta_static("img")
    os.makedirs(path, exist_ok=True)
    return path

def _pasta_carteiras() -> str:
    """<app>/static/carteiras"""
    path = _pasta_static("carteiras")
    os.makedirs(path, exist_ok=True)
    return path

def _carteira_pdf_path(id_assent: int) -> str:
    """<app>/static/carteiras/<id>.pdf"""
    return os.path.join(_pasta_carteiras(), f"{id_assent}.pdf")

def _digits(s: str) -> str:
    return _only_digits.sub("", s or "")

def _valida_cpf_mod11(cpf_str: str) -> bool:
    cpf = _digits(cpf_str)
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False

    def dv(cpf9_10: str) -> int:
        n = len(cpf9_10) + 1
        soma = sum(int(d) * (n - i) for i, d in enumerate(cpf9_10))
        r = (soma * 10) % 11
        return 0 if r == 10 else r

    return dv(cpf[:9]) == int(cpf[9]) and dv(cpf[:10]) == int(cpf[10])

# ==========================
# Selects auxiliares
# ==========================
def _listar_ufs():
    conn = conectar_bd(); ufs = []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT uf, estado FROM tbuf ORDER BY uf')
        ufs = cur.fetchall()
        conn.close()
    return ufs

def _listar_municipios_all():
    """Carrega TODOS os municípios da tbmunicipio (codMun, nomMun, uf)."""
    conn = conectar_bd(); mun = []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "codMun","nomMun", uf FROM "tbmunicipio" ORDER BY uf, "nomMun"')
        mun = cur.fetchall()
        conn.close()
    return mun

def _listar_familias():
    conn = conectar_bd(); fam = []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idFamilia","nomeFam" FROM tbfamilia ORDER BY "nomeFam"')
        fam = cur.fetchall()
        conn.close()
    return fam

# ==========================
# Geração do idAssent AAAAMMSSSSS
# ==========================
def _gerar_idassent(conn, data_ref=None):
    if data_ref is None:
        data_ref = date.today()
    ano = data_ref.year
    mes = data_ref.month
    prefixo = ano * 100 + mes
    base = prefixo * 100000
    teto = base + 99999
    cur = conn.cursor()
    cur.execute("SELECT pg_advisory_xact_lock(%s)", (prefixo,))
    cur.execute("""
        SELECT COALESCE(MAX("idAssent"), %s)
          FROM "tbassentado"
         WHERE "idAssent" BETWEEN %s AND %s
    """, (base, base, teto))
    max_id = int(cur.fetchone()[0] or base)
    novo_id = max_id + 1
    if novo_id > teto:
        raise RuntimeError("Sequencial mensal esgotado (AAAAMM99999).")
    return novo_id

# ==========================
# Views: Cadastro/Alteração
# ==========================
def view_assentCad():
    ufs = _listar_ufs()
    familias = _listar_familias()
    municipios_all = _listar_municipios_all()  # (codMun, nomMun, uf)
    return render_template(
        'assentCad.html',
        ufs=ufs,
        familias=familias,
        municipios_all=municipios_all,
        message=''
    )

def cadastrar_assent():
    if request.method != 'POST':
        return redirect(url_for('assentCad'))

    # campos
    nome       = (request.form.get('nome') or '').strip()
    genero     = (request.form.get('genero') or '').strip()[:1].upper()
    mae        = (request.form.get('mae') or '').strip()
    endereco   = (request.form.get('endereco') or '').strip()
    cpf        = _digits(request.form.get('cpf') or '')
    rg         = (request.form.get('rg') or '').strip()
    rgOrgExp   = (request.form.get('rgOrgExp') or '').strip()
    dtNasc_str = (request.form.get('dtNasc') or '').strip()
    ufNasc     = (request.form.get('ufNasc') or '').strip()[:2].upper()
    codMunNas  = request.form.get('codMunNas') or None
    email      = (request.form.get('email') or '').strip()
    noWhatsapp = _digits(request.form.get('noWhatsapp') or '')
    celular    = _digits(request.form.get('celular') or '')
    idFamilia  = (request.form.get('idFamilia') or '').strip() or None

    # validações obrigatórias
    obrigatorios_faltando = []
    if not nome: obrigatorios_faltando.append("Nome")
    if not genero: obrigatorios_faltando.append("Gênero")
    if not mae: obrigatorios_faltando.append("Mãe")
    if not cpf: obrigatorios_faltando.append("CPF")
    if not dtNasc_str: obrigatorios_faltando.append("Data de Nascimento")
    if not ufNasc: obrigatorios_faltando.append("UF de Nascimento")
    if not celular: obrigatorios_faltando.append("Celular")
    if not email: obrigatorios_faltando.append("E-mail")

    if obrigatorios_faltando:
        flash("Campos obrigatórios faltando: " + ", ".join(obrigatorios_faltando), "warning")
        return redirect(url_for('assentCad'))

    if not _valida_cpf_mod11(cpf):
        flash("CPF inválido (módulo 11).", "danger")
        return redirect(url_for('assentCad'))

    try:
        dtNasc = datetime.strptime(dtNasc_str, "%Y-%m-%d").date()
    except Exception:
        flash("Data de nascimento inválida.", "danger")
        return redirect(url_for('assentCad'))

    # conexão
    conn = conectar_bd()
    if not conn:
        flash("Erro de conexão com o banco.", "danger")
        return redirect(url_for('assentCad'))

    try:
        cur = conn.cursor()
        novo_id = _gerar_idassent(conn)
        idSitAssent = 1  # ATIVO

        cur.execute('''
          INSERT INTO "tbassentado"
            ("idAssent", nome, genero, mae, endereco, cpf, rg, "rgOrgExp",
             "dtNasc", "ufNasc", "codMunNas", email, "noWhatsapp", celular,
             "idFamilia", "idSitAssent")
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', (novo_id, nome, genero, mae, endereco, cpf, rg, rgOrgExp,
              dtNasc, ufNasc,
              int(codMunNas) if codMunNas else None,
              email, int(noWhatsapp) if noWhatsapp else None,
              celular, idFamilia, idSitAssent))

        conn.commit()

        # === GERA A CARTEIRA (QR em memória, PDF em static/carteiras) ===
        try:
            _gerar_carteira_pdf(novo_id)
        except Exception as e:
            print("Aviso: cadastro ok, mas falhou ao gerar Carteira:", e)

        link_static = url_for('static', filename=f'carteiras/{novo_id}.pdf')
        flash(
            f'✅ Assentado cadastrado! ID: {novo_id} '
            f'<a href="{link_static}" target="_blank" class="btn btn-sm btn-outline-primary ms-2">ver carteira — qrcode</a>',
            "success"
        )
        return redirect(url_for('assentCad'))

    except psycopg2.Error as e:
        try: conn.rollback()
        except: pass
        flash(f"❌ Não foi possível cadastrar. Detalhe: {e.pgerror}", "danger")
        return redirect(url_for('assentCad'))
    except Exception as e:
        try: conn.rollback()
        except: pass
        flash(f"❌ Não foi possível cadastrar. Erro: {e}", "danger")
        return redirect(url_for('assentCad'))
    finally:
        try: conn.close()
        except: pass

# ==========================
# FOTO DO ASSENTADO
# ==========================
def obter_foto_assentado(idAssent):
    """
    Retorna a foto do assentado a partir de:
      static/img/<idAssent>.jpg  |  static/img/<idAssent>.png
    Se não houver, tenta static/img/sem_foto.jpg.
    """
    try:
        idAssent = int(idAssent)
    except:
        return abort(400)

    pasta = _pasta_imagens()
    caminho_jpg = os.path.join(pasta, f"{idAssent}.jpg")
    caminho_png = os.path.join(pasta, f"{idAssent}.png")
    placeholder = os.path.join(pasta, "sem_foto.jpg")

    if os.path.isfile(caminho_jpg):
        return send_file(caminho_jpg, mimetype="image/jpeg")
    if os.path.isfile(caminho_png):
        return send_file(caminho_png, mimetype="image/png")
    if os.path.isfile(placeholder):
        return send_file(placeholder, mimetype="image/jpeg")
    return abort(404)

# ==========================
# Alteração/Exclusão
# ==========================
def view_assentAlt():
    itens   = _listar_assentados_basico()
    sel_id  = request.args.get('id')
    reg     = _pegar_assentado(sel_id) if sel_id else None
    ufs     = _listar_ufs()
    familias = _listar_familias()
    municipios = _listar_municipios_all()
    return render_template(
        'assentAlt.html',
        itens=itens,
        registro=reg,
        ufs=ufs,
        familias=familias,
        municipios_all=municipios
    )

def view_assentExc():
    itens  = _listar_assentados_basico()
    sel_id = request.args.get('id')
    reg    = _pegar_assentado(sel_id) if sel_id else None
    return render_template('assentExc.html', itens=itens, registro=reg)

def alterar_assent():
    if request.method != 'POST':
        return redirect(url_for('assentAlt'))

    idAssent = request.form.get('idAssent')
    if not idAssent:
        flash("Registro não informado.", "warning")
        return redirect(url_for('assentAlt'))

    nome       = (request.form.get('nome') or '').strip()
    genero     = (request.form.get('genero') or '').strip()[:1].upper()
    mae        = (request.form.get('mae') or '').strip()
    endereco   = (request.form.get('endereco') or '').strip()
    bairro     = (request.form.get('bairro') or '').strip()
    cpf        = _digits(request.form.get('cpf') or '')
    rg         = (request.form.get('rg') or '').strip()
    rgOrgExp   = (request.form.get('rgOrgExp') or '').strip()
    dtNasc_str = (request.form.get('dtNasc') or '').strip()
    ufNasc     = (request.form.get('ufNasc') or '').strip()[:2].upper()
    codMunNas  = request.form.get('codMunNas') or None
    email      = (request.form.get('email') or '').strip()
    noWhatsapp = _digits(request.form.get('noWhatsapp') or '')
    celular    = _digits(request.form.get('celular') or '')
    idFamilia  = (request.form.get('idFamilia') or '').strip() or None
    idSitAssent = request.form.get('idSitAssent')

    if cpf and not _valida_cpf_mod11(cpf):
        flash("CPF inválido (módulo 11).", "danger")
        return redirect(url_for('assentAlt', id=idAssent))

    try:
        dtNasc = datetime.strptime(dtNasc_str, "%Y-%m-%d").date() if dtNasc_str else None
    except Exception:
        flash("Data de nascimento inválida.", "danger")
        return redirect(url_for('assentAlt', id=idAssent))

    conn = conectar_bd()
    if not conn:
        flash("Erro de conexão com o banco.", "danger")
        return redirect(url_for('assentAlt', id=idAssent))

    try:
        cur = conn.cursor()
        cur.execute('''
          UPDATE tbassentado
             SET nome=%s, genero=%s, mae=%s, endereco=%s, bairro=%s, cpf=%s, rg=%s, "rgOrgExp"=%s,
                 "dtNasc"=%s, "ufNasc"=%s, "codMunNas"=%s, email=%s, "noWhatsapp"=%s, celular=%s,
                 "idFamilia"=%s, "idSitAssent"=%s
           WHERE "idAssent"=%s
        ''', (nome, genero, mae, endereco, bairro, cpf, rg, rgOrgExp,
              dtNasc, ufNasc or None, int(codMunNas) if codMunNas else None,
              email, int(noWhatsapp) if noWhatsapp else None, celular,
              idFamilia, int(idSitAssent) if idSitAssent is not None else None,
              int(idAssent)))
        conn.commit()
        conn.close()
        flash("✅ Assentado alterado com sucesso!", "success")
        return redirect(url_for('assentAlt', id=idAssent))
    except Exception as e:
        conn.rollback()
        conn.close()
        print("ERRO alterar_assent:", e)
        flash("❌ Não foi possível alterar.", "danger")
        return redirect(url_for('assentAlt', id=idAssent))

# ==========================
# Carteira (QR em memória)
# ==========================
def _buscar_nome_assentado(id_assent: int) -> str:
    conn = conectar_bd()
    nome = ""
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT nome FROM tbassentado WHERE "idAssent"=%s', (int(id_assent),))
            row = cur.fetchone()
            if row:
                nome = row[0] or ""
        finally:
            try: conn.close()
            except: pass
    return nome

def _draw_qr_vector(c, data: str, x_pt: float, y_pt: float, size_mm: float):
    """QR vetorial (sempre nítido)."""
    widget = rl_qr.QrCodeWidget(data)
    w0, h0 = widget.getBounds()[2:]
    mm_to_pt = 72/25.4
    size_pt = size_mm*mm_to_pt
    d = Drawing(size_pt, size_pt, transform=[size_pt/w0, 0, 0, size_pt/h0, 0, 0])
    d.add(widget)
    renderPDF.draw(d, c, x_pt, y_pt)

def _gerar_carteira_pdf(id_assent: int) -> str:
    """
    Gera/atualiza a carteira PDF do assentado (com QR e dados básicos).
    Salva em <app>/static/carteiras/<id>.pdf
    """
    pdf_path = _carteira_pdf_path(id_assent)
    nome = _buscar_nome_assentado(id_assent) or "-"

    c = canvas.Canvas(pdf_path, pagesize=A4)
    W, H = A4  # ~ 595 x 842 pt

    card_w = 85 * mm
    card_h = 54 * mm
    x = (W - card_w) / 2
    y = H - card_h - 40 * mm

    # moldura
    c.roundRect(x, y, card_w, card_h, 6, stroke=1, fill=0)

    # título
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(x + card_w/2, y + card_h - 10*mm, "SBBC — Carteira do Assentado")

    # dados
    c.setFont("Helvetica", 11)
    c.drawString(x + 8*mm, y + card_h - 20*mm, f"Nome: {nome}")
    c.drawString(x + 8*mm, y + card_h - 27*mm, f"ID do Assentado: {id_assent}")

    # QR à direita
    try:
        qr_size_mm = 22
        qr_x = x + card_w - 28 * mm
        qr_y = y + 6 * mm
        _draw_qr_vector(c, str(id_assent), qr_x, qr_y, qr_size_mm)
    except Exception as e:
        print("Falha ao inserir QR vetorial:", e)

    # rodapé
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(x + card_w/2, y + 5*mm,
                        "Apresente esta carteira nas atividades/benefícios da associação.")

    c.showPage()
    c.save()
    return pdf_path

def ver_carteira_assentado(idAssent: int):
    """
    Gera se necessário e retorna o PDF da carteira do assentado.
    """
    try:
        idAssent = int(idAssent)
    except:
        return abort(400)

    pdf_path = _carteira_pdf_path(idAssent)
    if not os.path.isfile(pdf_path):
        _gerar_carteira_pdf(idAssent)

    if os.path.isfile(pdf_path):
        return send_file(pdf_path, mimetype="application/pdf")
    return abort(404)

# ==========================
# Listagens usadas nas telas e no menu
# ==========================
def _listar_assentados_basico():
    """
    Retorna lista [(idAssent, nome), ...] para popular selects/grades rápidas.
    """
    conn = conectar_bd(); itens = []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT "idAssent", nome FROM tbassentado ORDER BY nome ASC LIMIT 200')
            itens = cur.fetchall()
        finally:
            try: conn.close()
            except: pass
    return itens

def _pegar_assentado(sel_id):
    """Retorna registro completo (placeholder)."""
    if not sel_id:
        return None
    conn = conectar_bd(); reg = None
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT * FROM tbassentado WHERE "idAssent"=%s', (int(sel_id),))
            reg = cur.fetchone()
        finally:
            try: conn.close()
            except: pass
    return reg

def _listar_assentados_opcoes():
    conn = conectar_bd()
    itens = []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome" ASC')
        itens = cur.fetchall()
        conn.close()
    return itens

# ==========================
# MENU ASSENTADO (carrega grade inicial)
# ==========================
def view_menuAssent():
    # listas para os filtros do lado ESQUERDO
    assentados = _listar_assentados_opcoes()
    familias   = _listar_familias()

    # linhas iniciais no CENTRO (alguns assentados para exibir)
    base = _listar_assentados_basico()  # [(id, nome), ...]
    # ordena por nome e pega 15
    base.sort(key=lambda x: (x[1] or '').lower())
    rows = []
    for id_assent, nome in base[:15]:
        rows.append({
            "idAssent": id_assent,
            "idassent": id_assent,
            "nome": nome,
            "cpf": "-",
            "nomMun": "-",
            "email": "-",
            "celular": "-"
        })

    # objeto de filtros vazio para o template
    F = type('F', (), {})()
    F.idAssent = ''
    F.idFamilia = ''
    F.nome = ''
    F.bairro = ''
    F.cpf = ''
    F.ufNasc = ''
    F.idSitAssent = ''

    return render_template(
        'menuAssent.html',
        assentados=assentados,   # usado no <select> Assentado
        familias=familias,       # usado no <select> Família
        rows=rows,               # grade central
        filtros=F
    )

# ==========================
# CONSULTA do centro (menuAssent.html) — COM FILTROS
# ==========================
def pagina_conGeralAssent():
    """
    Lê filtros (GET/POST), consulta no banco e renderiza menuAssent.html
    com 'rows' preenchido para a tabela central.
    """
    src = request.args if request.method == 'GET' else request.form

    # objeto de filtros (compatível com template)
    F = type('F', (), {})()
    F.idAssent    = (src.get('idAssent') or '').strip()
    F.idFamilia   = (src.get('idFamilia') or '').strip()
    F.nome        = (src.get('nome') or '').strip()
    F.bairro      = (src.get('bairro') or '').strip()
    F.cpf         = (src.get('cpf') or '').strip()
    F.ufNasc      = (src.get('ufNasc') or '').strip()
    F.idSitAssent = (src.get('idSitAssent') or '').strip()

    # listas para os selects (lado esquerdo)
    assentados_opts = _listar_assentados_opcoes()
    familias_opts   = _listar_familias()

    # monta WHERE
    where = ["TRUE"]
    params = []
    if F.idAssent:
        where.append('a."idAssent" = %s')
        params.append(int(F.idAssent))
    if F.idFamilia:
        where.append('a."idFamilia" = %s')
        params.append(int(F.idFamilia))
    if F.nome:
        where.append('unaccent(lower(a.nome)) LIKE unaccent(lower(%s))')
        params.append(f"%{F.nome}%")
    if F.bairro:
        where.append('unaccent(lower(a.bairro)) LIKE unaccent(lower(%s))')
        params.append(f"%{F.bairro}%")
    if F.cpf:
        where.append('a.cpf = %s')
        params.append(F.cpf)
    if F.ufNasc:
        where.append('a."ufNasc" = %s')
        params.append(F.ufNasc)
    if F.idSitAssent in ('0', '1'):
        where.append('a."idSitAssent" = %s')
        params.append(int(F.idSitAssent))

    where_sql = " AND ".join(where)

    # consulta principal — usa tbmunicipio (nomMun)
    base_sql = f'''
      SELECT a."idAssent", a.nome, a.cpf, a.email, a.celular,
             a."codMunNas", m."nomMun"
        FROM tbassentado a
        LEFT JOIN "tbmunicipio" m ON m."codMun" = a."codMunNas"
       WHERE {where_sql}
       ORDER BY a.nome ASC
       LIMIT %s
    '''
    params_query = params + [200]  # limite de segurança para não travar a UI

    rows = []
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(base_sql, params_query)
            for (id_assent, nome, cpf, email, celular, codMun, nomMun) in cur.fetchall():
                rows.append({
                    "idAssent": id_assent,
                    "idassent": id_assent,  # para o template que usa r.idassent ou r.idAssent
                    "nome": nome,
                    "cpf": cpf or "-",
                    "nomMun": nomMun or "-",
                    "email": email or "-",
                    "celular": celular or "-"
                })
        finally:
            try: conn.close()
            except: pass

    # renderiza NA MESMA TELA do menu (central atualiza)
    return render_template(
        'menuAssent.html',
        assentados=assentados_opts,
        familias=familias_opts,
        rows=rows,
        filtros=F
    )

def conFiltroAssent():
    """Apenas redireciona para a mesma consulta (compat GET/POST)."""
    return pagina_conGeralAssent()

# ==========================
# BUSCA por nome (para gerarCarteira.html)
# ==========================
def _buscar_assentados_por_nome(filtro: str):
    """
    Retorna lista de (idAssent, nome, cpf, nome_familia) filtrada por nome (case-insensitive),
    ordenada alfabeticamente por nome.
    """
    conn = conectar_bd(); itens = []
    if conn:
        try:
            cur = conn.cursor()
            if filtro:
                cur.execute("""
                    SELECT a."idAssent", a.nome, a.cpf, COALESCE(f."nomeFam",'') AS nome_fam
                      FROM tbassentado a
                 LEFT JOIN tbfamilia f ON f."idFamilia" = a."idFamilia"
                     WHERE unaccent(lower(a.nome)) LIKE unaccent(lower(%s))
                     ORDER BY a.nome ASC
                """, (f"%{filtro}%",))
            else:
                cur.execute("""
                    SELECT a."idAssent", a.nome, a.cpf, COALESCE(f."nomeFam",'') AS nome_fam
                      FROM tbassentado a
                 LEFT JOIN tbfamilia f ON f."idFamilia" = a."idFamilia"
                     ORDER BY a.nome ASC
                """)
            itens = cur.fetchall()
        finally:
            try: conn.close()
            except: pass
    return itens

# ==========================
# VIEW: tela para gerar carteiras
# ==========================
def view_gerarCarteira():
    # filtro opcional na querystring
    filtro = (request.args.get("q") or "").strip()
    itens = _buscar_assentados_por_nome(filtro)
    return render_template("gerarCarteira.html", filtro=filtro, itens=itens)

# ==========================
# PDF: desenho e geração em lote
# ==========================
def _desenhar_carteira(c, id_assent: int, x: float, y: float):
    """Desenha UMA carteirinha no canvas `c` (layout simples)."""
    nome = _buscar_nome_assentado(id_assent) or ""
    card_w = 85*mm
    card_h = 54*mm
    pad = 6*mm

    # moldura
    c.roundRect(x, y, card_w, card_h, 6, stroke=1, fill=0)

    # topo: título
    title_y = y + card_h - 10*mm
    c.setFont("Helvetica-Bold", 12.5)
    c.drawCentredString(x + card_w/2, title_y, "Carteira do Assentado")
    c.setFont("Helvetica-Oblique", 8.5)
    c.drawCentredString(x + card_w/2, title_y - 5*mm, "( Banco do Bem Comum )")

    # QR
    qr_size_mm = 20
    qr_x = x + card_w - pad - qr_size_mm*mm
    qr_y = y + pad - 1*mm
    _draw_qr_vector(c, str(id_assent), qr_x, qr_y, qr_size_mm)

    # textos à esquerda
    labels = ["Matricula:", "Nome:"]
    values = [str(id_assent), nome]
    base_font = "Helvetica"; base_size = 10.5
    c.setFont(base_font, base_size)

    label_w = max(c.stringWidth(lbl, base_font, base_size) for lbl in labels) + 3
    value_x = x + pad + label_w
    col_right_x = qr_x - 6
    linha_y = y + card_h - 22*mm
    for lbl, val in zip(labels, values):
        c.setFont(base_font, base_size)
        c.drawString(x + pad, linha_y, lbl)
        c.drawString(value_x, linha_y, val)
        linha_y -= 7*mm

    # rodapé
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawCentredString(x + card_w/2, y + 4*mm, "( Carteira Associação -  Atividades / Beneficios )")

def _gerar_pdf_carteiras_lote(ids_ordenados: list[int]) -> str:
    """
    Gera um PDF temporário com 6 carteiras por página (3 linhas x 2 colunas).
    Retorna o caminho do arquivo gerado em static/carteiras/carteiras_lote.pdf
    """
    out_path = os.path.join(_pasta_carteiras(), "carteiras_lote.pdf")
    c = canvas.Canvas(out_path, pagesize=A4)
    W, H = A4

    card_w = 85*mm; card_h = 54*mm
    cols = 2; rows = 3
    h_gap = 10*mm; v_gap = 10*mm

    total_w = cols*card_w + (cols-1)*h_gap
    total_h = rows*card_h + (rows-1)*v_gap
    left = (W - total_w)/2
    top  = H - (H - total_h)/2  # topo da grade

    def pos(col, row):
        x = left + col*(card_w + h_gap)
        y = (top - card_h) - row*(card_h + v_gap)
        return x, y

    i = 0
    for idx, id_assent in enumerate(ids_ordenados):
        col = (i % (cols*rows)) % cols
        row = (i % (cols*rows)) // cols
        x, y = pos(col, row)
        _desenhar_carteira(c, id_assent, x, y)
        i += 1
        if i % (cols*rows) == 0 and idx < len(ids_ordenados) - 1:
            c.showPage()
    c.showPage(); c.save()
    return out_path

# ==========================
# ACTION: gerar PDF (POST)
# ==========================
def post_gerarCarteira():
    """
    POST da página gerarCarteira.html
    - Se houver 'ids' selecionados => gera somente os selecionados
    - Se não houver 'ids' e veio 'q' => gera com todos os resultados daquele filtro
    - Se vier apenas 'id' => gera carteira individual
    """
    ids_sel = request.form.getlist("ids")  # checkboxes
    filtro = (request.form.get("q") or "").strip()
    id_unico = request.form.get("id")  # botão 'gerar' da linha

    if id_unico:
        _gerar_carteira_pdf(int(id_unico))
        path = _carteira_pdf_path(int(id_unico))
        return send_file(path, mimetype="application/pdf", as_attachment=True,
                         download_name=f"carteira_{id_unico}.pdf")

    if ids_sel:
        ids = sorted({int(x) for x in ids_sel})
    else:
        itens = _buscar_assentados_por_nome(filtro)
        ids = [int(t[0]) for t in itens]

    if not ids:
        flash("Nenhum registro para gerar.", "warning")
        return redirect(url_for("gerarCarteira"))

    out = _gerar_pdf_carteiras_lote(ids)
    return send_file(out, mimetype="application/pdf", as_attachment=True,
                     download_name="carteiras_lote.pdf")
