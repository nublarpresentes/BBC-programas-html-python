# assent.py
import math
import re
import psycopg2
from datetime import datetime
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

PER_PAGE = 15

# -------------------------
# Utilidades
# -------------------------
_only_digits = re.compile(r"\D+")

def _digits(s: str) -> str:
    return _only_digits.sub("", s or "")

def _valida_cpf_mod11(cpf_str: str) -> bool:
    """Valida CPF (11 dígitos) – módulo 11."""
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

    d1 = dv(cpf[:9])
    if d1 != int(cpf[9]):
        return False
    d2 = dv(cpf[:10])
    return d2 == int(cpf[10])

# -------------------------
# Selects auxiliares
# -------------------------
def _listar_ufs():
    conn = conectar_bd()
    ufs = []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT uf, estado FROM tbuf ORDER BY uf')
        ufs = cur.fetchall()
        conn.close()
    return ufs

def _listar_municipios(uf=None):
    conn = conectar_bd()
    mun = []
    if conn:
        cur = conn.cursor()
        if uf:
            cur.execute('SELECT "codMun","nomMun" FROM tbufmun WHERE "UF"=%s ORDER BY "nomMun"', (uf,))
        else:
            cur.execute('SELECT "codMun","nomMun" FROM tbufmun ORDER BY "nomMun"')
        mun = cur.fetchall()
        conn.close()
    return mun

def _listar_familias():
    conn = conectar_bd()
    fam = []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "idFamilia","nomeFam" FROM tbfamilia ORDER BY "nomeFam"')
        fam = cur.fetchall()
        conn.close()
    return fam

# -------------------------
# CADASTRO
# -------------------------
def view_assentCad():
    ufs = _listar_ufs()
    familias = _listar_familias()
    # para o formulário: inicialmente sem UF selecionada -> lista vazia de municípios
    municipios = []
    return render_template('assentCad.html', ufs=ufs, familias=familias, municipios=municipios, message='')

def cadastrar_assent():
    if request.method != 'POST':
        return redirect(url_for('assentCad'))

    # Campos mínimos solicitados
    nome       = (request.form.get('nome') or '').strip()
    genero     = (request.form.get('genero') or '').strip()[:1].upper()  # 'M' / 'F'
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
    idSitAssent = request.form.get('idSitAssent')  # '1' Ativo / '0' Inativo

    # validações básicas
    if not nome:
        flash("Informe o nome.", "warning")
        return redirect(url_for('assentCad'))

    if cpf and not _valida_cpf_mod11(cpf):
        flash("CPF inválido (módulo 11).", "danger")
        return redirect(url_for('assentCad'))

    try:
        dtNasc = datetime.strptime(dtNasc_str, "%Y-%m-%d").date() if dtNasc_str else None
    except Exception:
        flash("Data de nascimento inválida.", "danger")
        return redirect(url_for('assentCad'))

    # inserção
    conn = conectar_bd()
    if not conn:
        flash("Erro de conexão com o banco.", "danger")
        return redirect(url_for('assentCad'))

    try:
        cur = conn.cursor()
        cur.execute('''
          INSERT INTO tbassentado
            (nome, genero, mae, endereco, bairro, cpf, rg, "rgOrgExp",
             "dtNasc", "ufNasc", "codMunNas", email, "noWhatsapp", celular,
             "idFamilia", "idSitAssent")
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', (nome, genero, mae, endereco, bairro, cpf, rg, rgOrgExp,
              dtNasc, ufNasc or None, int(codMunNas) if codMunNas else None,
              email, int(noWhatsapp) if noWhatsapp else None,
              celular, idFamilia, int(idSitAssent) if idSitAssent is not None else None))
        conn.commit()
        conn.close()
        flash("✅ Assentado cadastrado com sucesso!", "success")
        return redirect(url_for('assentCad'))
    except Exception as e:
        conn.rollback()
        conn.close()
        print("ERRO cadastrar_assent:", e)
        flash("❌ Não foi possível cadastrar.", "danger")
        return redirect(url_for('assentCad'))

# -------------------------
# ALTERAÇÃO
# -------------------------
def _listar_assentados_basico():
    """Lista compacta para grade da tela de alteração/exclusão."""
    conn = conectar_bd()
    dados = []
    if conn:
        cur = conn.cursor()
        cur.execute('''
           SELECT "idAssent", nome, cpf, bairro, "idSitAssent"
             FROM tbassentado
            ORDER BY "idAssent" DESC
        ''')
        dados = cur.fetchall()
        conn.close()
    return dados

def _pegar_assentado(idAssent):
    conn = conectar_bd()
    reg = None
    if conn:
        cur = conn.cursor()
        cur.execute('''
          SELECT "idAssent", nome, genero, mae, endereco, bairro, cpf, rg, "rgOrgExp",
                 "dtNasc", "ufNasc", "codMunNas", email, "noWhatsapp", celular,
                 "idFamilia", "idSitAssent"
            FROM tbassentado
           WHERE "idAssent"=%s
        ''', (idAssent,))
        reg = cur.fetchone()
        conn.close()
    return reg

def view_assentAlt():
    itens   = _listar_assentados_basico()
    sel_id  = request.args.get('id')
    reg     = _pegar_assentado(sel_id) if sel_id else None
    ufs     = _listar_ufs()
    familias = _listar_familias()
    municipios = _listar_municipios(reg[10]) if reg and reg[10] else []  # ufNasc
    return render_template('assentAlt.html',
                           itens=itens, registro=reg,
                           ufs=ufs, familias=familias, municipios=municipios)

def alterar_assent():
    if request.method != 'POST':
        return redirect(url_for('assentAlt'))

    idAssent   = request.form.get('idAssent')
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

# -------------------------
# EXCLUSÃO
# -------------------------
def view_assentExc():
    itens  = _listar_assentados_basico()
    sel_id = request.args.get('id')
    reg    = _pegar_assentado(sel_id) if sel_id else None
    return render_template('assentExc.html', itens=itens, registro=reg)

def excluir_assent():
    if request.method != 'POST':
        return redirect(url_for('assentExc'))

    idAssent = request.form.get('idAssent')
    if not idAssent:
        flash("Registro não informado.", "warning")
        return redirect(url_for('assentExc'))

    conn = conectar_bd()
    if not conn:
        flash("Erro de conexão.", "danger")
        return redirect(url_for('assentExc'))

    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM tbassentado WHERE "idAssent"=%s', (int(idAssent),))
        conn.commit()
        conn.close()
        flash("✅ Assentado excluído com sucesso!", "success")
        return redirect(url_for('assentExc'))
    except psycopg2.Error as e:
        conn.rollback()
        conn.close()
        print("ERRO excluir_assent:", e)
        flash("❌ Não foi possível excluir (verifique vínculos).", "danger")
        return redirect(url_for('assentExc', id=idAssent))

# -------------------------
# CONSULTA GERAL (com filtros)
# -------------------------
def _ler_filtros_con():
    src = request.args if request.method == 'GET' else request.form
    f = type('F', (), {})()
    f.nome   = (src.get('nome') or '').strip()
    f.bairro = (src.get('bairro') or '').strip()
    f.cpf    = _digits(src.get('cpf') or '')
    f.ufNasc = (src.get('ufNasc') or '').strip()[:2].upper()
    f.idFamilia  = (src.get('idFamilia') or '').strip()
    f.idSitAssent = src.get('idSitAssent') if src.get('idSitAssent') in ('0','1') else ''
    try:
        page = int(src.get('page', '1'))
    except:
        page = 1
    if page < 1: page = 1
    return f, page

def _montar_where_con(f, params):
    w = ["TRUE"]
    if f.nome:
        w.append('unaccent(lower(a.nome)) LIKE unaccent(lower(%s))')
        params.append(f"%{f.nome}%")
    if f.bairro:
        w.append('unaccent(lower(a.bairro)) LIKE unaccent(lower(%s))')
        params.append(f"%{f.bairro}%")
    if f.cpf:
        w.append('a.cpf = %s')
        params.append(f.cpf)
    if f.ufNasc:
        w.append('a."ufNasc" = %s')
        params.append(f.ufNasc)
    if f.idFamilia:
        w.append('a."idFamilia" = %s')
        params.append(f.idFamilia)
    if f.idSitAssent != '':
        w.append('a."idSitAssent" = %s')
        params.append(int(f.idSitAssent))
    return " AND ".join(w)

def pagina_conGeralAssent():
    f, page = _ler_filtros_con()
    ufs = _listar_ufs()
    familias = _listar_familias()

    params = []
    where = _montar_where_con(f, params)

    base_sql = f'''
      SELECT a."idAssent", a.nome, a.cpf, a.bairro, a."idSitAssent",
             a."ufNasc", a."codMunNas", m."nomMun", a.email, a.celular
        FROM tbassentado a
        LEFT JOIN tbufmun m ON m."codMun" = a."codMunNas"
       WHERE {where}
    '''

    rows, total = [], 0
    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        cur.execute(f'SELECT COUNT(*) FROM ({base_sql}) T', params)
        total = cur.fetchone()[0] or 0

        limit = PER_PAGE
        offset = (page-1)*PER_PAGE
        cur.execute(f'''
          {base_sql}
          ORDER BY a.nome ASC
          LIMIT %s OFFSET %s
        ''', params + [limit, offset])

        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            rows.append({cols[i]: r[i] for i in range(len(cols))})
        conn.close()

    pages = max(1, math.ceil(total / PER_PAGE))

    def pagina_url(p):
        from urllib.parse import urlencode
        q = {
            'nome': f.nome or '',
            'bairro': f.bairro or '',
            'cpf': f.cpf or '',
            'ufNasc': f.ufNasc or '',
            'idFamilia': f.idFamilia or '',
            'idSitAssent': f.idSitAssent or '',
            'page': p
        }
        return url_for('conGeralAssent') + '?' + urlencode(q)

    return render_template('conGeralAssent.html',
                           filtros=f, ufs=ufs, familias=familias,
                           rows=rows, total=total, page=page, pages=pages,
                           pagina_url=pagina_url)

def conFiltroAssent():
    return pagina_conGeralAssent()

def obter_foto_assentado(idAssent):
    # Caminho completo para a imagem do tassentado
    caminho_imagem = os.path.join(PASTA_IMAGENS, f"{idAssent}.jpg")

    # Verifica se o arquivo de imagem existe
    if os.path.isfile(caminho_imagem):
        return send_file(caminho_imagem, mimetype='image/jpeg')
    else:
        # Se a imagem não existir, retorna uma imagem de placeholder ou outra resposta adequada
        return "Imagem não encontrada", 404


# Rota para deletar um assentado
def consulta_nome_assentado(nome):
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT idAssent, nome, foto FROM tbassentado WHERE nome LIKE %s", ('%' + nome + '%',))
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
