# recpsa.py
import math
import psycopg2
from datetime import date
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

PER_PAGE = 15

# =========================================
# SELECTS BÁSICOS (assentados, tipos, infra)
# =========================================
def _carregar_selects():
    assentados, tipos, infra = [], [], []
    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        # Assentados
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome" ASC')
        assentados = cur.fetchall()
        # Tipos de recompensa
        cur.execute('SELECT "idTipRecpsa","nomRecpsa","idPolPub" FROM "tbtiprecpsa" ORDER BY "nomRecpsa" ASC')
        tipos = cur.fetchall()
        # Tipos de uso de infraestrutura
        cur.execute('SELECT "idTipUsoInfr","nomInfr","valUsoInfr" FROM "tbtipusoinfr" ORDER BY "nomInfr" ASC')
        infra = cur.fetchall()
        conn.close()
    return assentados, tipos, infra

# =========================================
# HELPERS de consulta à Política/Infra
# =========================================
def _pegar_politica(idPolPub):
    if not idPolPub:
        return None
    conn = conectar_bd()
    if not conn:
        return None
    cur = conn.cursor()
    cur.execute('SELECT "idPolPub","nomPolPub","valor","perct" FROM "tbpolitpub" WHERE "idPolPub"=%s', (int(idPolPub),))
    row = cur.fetchone()
    conn.close()
    return row   # (idPolPub, nom, valor, perct)

def _pegar_infra(idTipUsoInfr):
    if not idTipUsoInfr:
        return None
    conn = conectar_bd()
    if not conn:
        return None
    cur = conn.cursor()
    cur.execute('SELECT "idTipUsoInfr","nomInfr","valUsoInfr" FROM "tbtipusoinfr" WHERE "idTipUsoInfr"=%s', (int(idTipUsoInfr),))
    row = cur.fetchone()
    conn.close()
    return row   # (id, nome, valor)

# =========================================
# PÁGINAS (views)
# =========================================
def view_recpsaCad():
    assentados, tipos, infra = _carregar_selects()
    return render_template('recpsaCad.html', assentados=assentados, tipos=tipos, infra=infra)

def view_recpsaAlt():
    assentados, tipos, infra = _carregar_selects()
    sel_id = request.args.get('id')  # idRecpsa
    itens, registro = [], None

    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        # lista últimos 200
        cur.execute("""
          SELECT r."idRecpsa",
                 r."idTipRecpa",
                 tr."nomRecpsa",
                 r."idAssent",
                 a."nome" AS nom_assent,
                 r."valRecpsa",
                 r."qtdEqv",
                 r."idPolPub",
                 p."nomPolPub",
                 r."idTipUsoInfr",
                 i."nomInfr"
            FROM "tbrecpsa" r
            LEFT JOIN "tbassentado"  a  ON a."idAssent" = r."idAssent"
            LEFT JOIN "tbtiprecpsa"  tr ON tr."idTipRecpsa" = r."idTipRecpa"
            LEFT JOIN "tbpolitpub"   p  ON p."idPolPub" = r."idPolPub"
            LEFT JOIN "tbtipusoinfr" i  ON i."idTipUsoInfr" = r."idTipUsoInfr"
           ORDER BY r."idRecpsa" DESC
           LIMIT 200
        """)
        cols = [d[0] for d in cur.description]
        for rr in cur.fetchall():
            itens.append({cols[i]: rr[i] for i in range(len(cols))})

        if sel_id:
            cur.execute("""
              SELECT r."idRecpsa",
                     r."idTipRecpa",
                     tr."nomRecpsa",
                     r."idAssent",
                     a."nome" AS nom_assent,
                     r."valRecpsa",
                     r."qtdEqv",
                     r."idPolPub",
                     p."nomPolPub",
                     r."idTipUsoInfr",
                     i."nomInfr"
                FROM "tbrecpsa" r
                LEFT JOIN "tbassentado"  a  ON a."idAssent" = r."idAssent"
                LEFT JOIN "tbtiprecpsa"  tr ON tr."idTipRecpsa" = r."idTipRecpa"
                LEFT JOIN "tbpolitpub"   p  ON p."idPolPub" = r."idPolPub"
                LEFT JOIN "tbtipusoinfr" i  ON i."idTipUsoInfr" = r."idTipUsoInfr"
               WHERE r."idRecpsa"=%s
            """, (int(sel_id),))
            row = cur.fetchone()
            if row:
                registro = {cols[i]: row[i] for i in range(len(cols))}
        conn.close()

    return render_template('recpsaAlt.html',
                           assentados=assentados, tipos=tipos, infra=infra,
                           itens=itens, registro=registro)

def view_recpsaExc():
    sel_id = request.args.get('id')
    registro = None
    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        cur.execute("""
          SELECT r."idRecpsa",
                 r."idTipRecpa",
                 tr."nomRecpsa",
                 r."idAssent",
                 a."nome" AS nom_assent,
                 r."valRecpsa",
                 r."qtdEqv",
                 r."idPolPub",
                 p."nomPolPub",
                 r."idTipUsoInfr",
                 i."nomInfr"
            FROM "tbrecpsa" r
            LEFT JOIN "tbassentado"  a  ON a."idAssent" = r."idAssent"
            LEFT JOIN "tbtiprecpsa"  tr ON tr."idTipRecpsa" = r."idTipRecpa"
            LEFT JOIN "tbpolitpub"   p  ON p."idPolPub" = r."idPolPub"
            LEFT JOIN "tbtipusoinfr" i  ON i."idTipUsoInfr" = r."idTipUsoInfr"
           WHERE r."idRecpsa"=%s
        """, (int(sel_id),))
        row = cur.fetchone()
        if row:
            cols = [d[0] for d in cur.description]
            registro = {cols[i]: row[i] for i in range(len(cols))}
        conn.close()

    itens = []
    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        cur.execute("""
          SELECT r."idRecpsa",
                 tr."nomRecpsa",
                 a."nome" AS nom_assent,
                 r."valRecpsa",
                 r."qtdEqv",
                 COALESCE(p."nomPolPub",'') AS nompol,
                 COALESCE(i."nomInfr",'')   AS nominfr
            FROM "tbrecpsa" r
            LEFT JOIN "tbassentado"  a  ON a."idAssent" = r."idAssent"
            LEFT JOIN "tbtiprecpsa"  tr ON tr."idTipRecpsa" = r."idTipRecpa"
            LEFT JOIN "tbpolitpub"   p  ON p."idPolPub" = r."idPolPub"
            LEFT JOIN "tbtipusoinfr" i  ON i."idTipUsoInfr" = r."idTipUsoInfr"
           ORDER BY r."idRecpsa" DESC
           LIMIT 200
        """)
        itens = cur.fetchall()
        conn.close()

    return render_template('recpsaExc.html', itens=itens, registro=registro)

# =========================================
# AÇÕES (POST)
# =========================================
def cadastrar_recpsa():
    if request.method != 'POST':
        return redirect(url_for('recpsaCad'))

    idAssent     = request.form.get('idAssent')
    idTipRecpa   = request.form.get('idTipRecpsa')  # campo do form
    qtdEqv_in    = request.form.get('qtdEqv')
    idTipUsoInfr = request.form.get('idTipUsoInfr') or None

    if not idAssent or not idTipRecpa:
        flash('❌ Dados insuficientes.', 'danger')
        return redirect(url_for('recpsaCad'))

    try:
        qtdEqv = int(qtdEqv_in or '1')
        if qtdEqv < 1:
            qtdEqv = 1
    except:
        qtdEqv = 1

    # Regras:
    # - Se tipo == 1 (Política Pública): buscar idPolPub no tipo, depois pegar (valor, perct) na tbpolitpub e calcular valRecpsa = valor * perct
    # - Caso contrário: precisa escolher um tipo de infra; valRecpsa = valUsoInfr
    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.', 'danger')
        return redirect(url_for('recpsaCad'))

    try:
        cur = conn.cursor()

        # Carrega o tipo
        cur.execute('SELECT "idTipRecpsa","nomRecpsa","idPolPub" FROM "tbtiprecpsa" WHERE "idTipRecpsa"=%s', (int(idTipRecpa),))
        tp = cur.fetchone()
        if not tp:
            conn.close()
            flash('❌ Tipo de recompensa não encontrado.', 'danger')
            return redirect(url_for('recpsaCad'))

        idPolPub = tp[2]
        valRecpsa = None

        if int(idTipRecpa) == 1:
            if not idPolPub:
                conn.close()
                flash('❌ Tipo 1 requer Política Pública vinculada.', 'danger')
                return redirect(url_for('recpsaCad'))
            pol = _pegar_politica(idPolPub)
            if not pol:
                conn.close()
                flash('❌ Política Pública não encontrada.', 'danger')
                return redirect(url_for('recpsaCad'))
            _, nom, valor, perct = pol
            try:
                valor = float(valor or 0)
                perct = float(perct or 0)
                valRecpsa = valor * perct
            except:
                valRecpsa = 0.0
            idTipUsoInfr = None  # não se aplica
        else:
            if not idTipUsoInfr:
                conn.close()
                flash('❌ Escolha o tipo de uso de infraestrutura.', 'danger')
                return redirect(url_for('recpsaCad'))
            inf = _pegar_infra(idTipUsoInfr)
            if not inf:
                conn.close()
                flash('❌ Tipo de infra não encontrado.', 'danger')
                return redirect(url_for('recpsaCad'))
            valRecpsa = float(inf[2] or 0)
            idPolPub = None  # não se aplica

        # Insere
        cur.execute("""
            INSERT INTO "tbrecpsa"
            ("idTipRecpa","idAssent","valRecpsa","qtdEqv","idPolPub","idTipUsoInfr","dtCad")
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            int(idTipRecpa),
            int(idAssent),
            float(valRecpsa),
            int(qtdEqv),
            int(idPolPub) if idPolPub else None,
            int(idTipUsoInfr) if idTipUsoInfr else None,
            date.today()
        ))
        conn.commit()


        conn.close()
        flash('✅ Recompensa cadastrada!', 'success')
        return redirect(url_for('recpsaCad'))
    except Exception as e:
        try:
            if conn and not conn.closed:
                conn.rollback()
        except:
            pass
        import traceback
        print("Erro ao cadastrar recompensa:", repr(e))
        traceback.print_exc()  # imprime stack + mensagem do psycopg2
        flash('❌ Erro ao cadastrar !!', 'danger')
        return redirect(url_for('recpsaCad'))


def alterar_recpsa():
    if request.method != 'POST':
        return redirect(url_for('recpsaAlt'))

    idRecpsa     = request.form.get('idRecpsa')
    idAssent     = request.form.get('idAssent')
    idTipRecpa   = request.form.get('idTipRecpsa')
    qtdEqv_in    = request.form.get('qtdEqv')
    idTipUsoInfr = request.form.get('idTipUsoInfr') or None

    if not idRecpsa or not idAssent or not idTipRecpa:
        flash('❌ Dados insuficientes.', 'danger')
        return redirect(url_for('recpsaAlt'))

    try:
        qtdEqv = int(qtdEqv_in or '1')
        if qtdEqv < 1:
            qtdEqv = 1
    except:
        qtdEqv = 1

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.', 'danger')
        return redirect(url_for('recpsaAlt'))

    try:
        cur = conn.cursor()
        # Pega tipo
        cur.execute('SELECT "idTipRecpsa","idPolPub" FROM "tbtiprecpsa" WHERE "idTipRecpsa"=%s', (int(idTipRecpa),))
        tp = cur.fetchone()
        if not tp:
            conn.close()
            flash('❌ Tipo de recompensa não encontrado.', 'danger')
            return redirect(url_for('recpsaAlt'))

        idPolPub = tp[1]
        valRecpsa = None

        if int(idTipRecpa) == 1:
            if not idPolPub:
                conn.close()
                flash('❌ Tipo 1 requer Política Pública vinculada.', 'danger')
                return redirect(url_for('recpsaAlt'))
            pol = _pegar_politica(idPolPub)
            if not pol:
                conn.close()
                flash('❌ Política Pública não encontrada.', 'danger')
                return redirect(url_for('recpsaAlt'))
            _, _, valor, perct = pol
            try:
                valor = float(valor or 0)
                perct = float(perct or 0)
                valRecpsa = valor * perct
            except:
                valRecpsa = 0.0
            idTipUsoInfr = None
            upd = ('UPDATE "tbrecpsa" SET "dtCad"=%s,"idTipRecpa"=%s,"idAssent"=%s,"valRecpsa"=%s,"qtdEqv"=%s,"idPolPub"=%s,"idTipUsoInfr"=NULL WHERE "idRecpsa"=%s',
                   (date.today(), int(idTipRecpa), int(idAssent), valRecpsa, qtdEqv, int(idPolPub), int(idRecpsa)))
        else:
            if not idTipUsoInfr:
                conn.close()
                flash('❌ Escolha o tipo de uso de infraestrutura.', 'danger')
                return redirect(url_for('recpsaAlt'))
            inf = _pegar_infra(idTipUsoInfr)
            if not inf:
                conn.close()
                flash('❌ Tipo de infra não encontrado.', 'danger')
                return redirect(url_for('recpsaAlt'))
            valRecpsa = float(inf[2] or 0)
            idPolPub = None
            upd = ('UPDATE "tbrecpsa" SET "dtCad"=%s, "idTipRecpa"=%s,"idAssent"=%s,"valRecpsa"=%s,"qtdEqv"=%s,"idPolPub"=NULL,"idTipUsoInfr"=%s WHERE "idRecpsa"=%s',
                   (date.today(), int(idTipRecpa), int(idAssent), valRecpsa, qtdEqv, int(idTipUsoInfr), int(idRecpsa)))

        cur.execute(*upd)
        conn.commit()
        conn.close()
        flash('✅ Recompensa alterada!', 'success')
        return redirect(url_for('recpsaAlt'))
    except Exception as e:
        try:
            if conn and not conn.closed:
                conn.rollback()
        except:
            pass
        print("Erro ao alterar recompensa:", e)
        flash('❌ Erro ao alterar.', 'danger')
        return redirect(url_for('recpsaAlt'))
    finally:
        if conn and not conn.closed:
            conn.close()

def excluir_recpsa():
    if request.method != 'POST':
        return redirect(url_for('recpsaExc'))

    idRecpsa = request.form.get('idRecpsa')
    if not idRecpsa:
        flash('❌ Selecione um registro.', 'danger')
        return redirect(url_for('recpsaExc'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.', 'danger')
        return redirect(url_for('recpsaExc'))
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "tbrecpsa" WHERE "idRecpsa"=%s', (int(idRecpsa),))
        conn.commit()
        conn.close()
        flash('✅ Recompensa excluída!', 'success')
        return redirect(url_for('recpsaExc'))
    except psycopg2.Error as e:
        conn.rollback()
        conn.close()
        print("Erro ao excluir recompensa:", e)
        flash('❌ Não foi possível excluir (FK?).', 'danger')
        return redirect(url_for('recpsaExc'))

# =========================================
# CONSULTA GERAL (com filtros)
# =========================================
def _ler_filtros():
    src = request.args if request.method == 'GET' else request.form
    F = type('F', (), {})()
    F.idAssent   = (src.get('idAssent') or '').strip()
    F.idTipRecpsa= (src.get('idTipRecpsa') or '').strip()
    F.idTipUsoInfr = (src.get('idTipUsoInfr') or '').strip()
    F.nome       = (src.get('nome') or '').strip()
    F.valMin     = (src.get('valMin') or '').strip().replace(',', '.')
    F.valMax     = (src.get('valMax') or '').strip().replace(',', '.')
    try:
        page = int(src.get('page', '1'))
    except:
        page = 1
    if page < 1:
        page = 1
    return F, page

def _montar_where(F, params):
    w = ['TRUE']
    if F.idAssent:
        w.append('r."idAssent"=%s'); params.append(int(F.idAssent))
    if F.idTipRecpsa:
        w.append('r."idTipRecpa"=%s'); params.append(int(F.idTipRecpsa))
    if F.idTipUsoInfr:
        w.append('r."idTipUsoInfr"=%s'); params.append(int(F.idTipUsoInfr))
    if F.nome:
        w.append('UPPER(a."nome") LIKE UPPER(%s)'); params.append(f'%{F.nome}%')
    if F.valMin:
        try: v = float(F.valMin); w.append('r."valRecpsa" >= %s'); params.append(v)
        except: pass
    if F.valMax:
        try: v = float(F.valMax); w.append('r."valRecpsa" <= %s'); params.append(v)
        except: pass
    return ' AND '.join(w)

def _executar_consulta(F, page):
    conn = conectar_bd()
    rows, total = [], 0
    if not conn:
        return rows, total

    params = []
    where = _montar_where(F, params)
    base = f"""
      SELECT r."idRecpsa",
             a."nome" AS nom_assent,
             tr."nomRecpsa" AS nom_tipo,
             COALESCE(p."nomPolPub",'') AS nom_polit,
             COALESCE(i."nomInfr",'')   AS nom_infr,
             r."valRecpsa",
             r."qtdEqv"
        FROM "tbrecpsa" r
        LEFT JOIN "tbassentado"  a  ON a."idAssent" = r."idAssent"
        LEFT JOIN "tbtiprecpsa"  tr ON tr."idTipRecpsa" = r."idTipRecpa"
        LEFT JOIN "tbpolitpub"   p  ON p."idPolPub" = r."idPolPub"
        LEFT JOIN "tbtipusoinfr" i  ON i."idTipUsoInfr" = r."idTipUsoInfr"
       WHERE {where}
    """

    try:
        cur = conn.cursor()
        cur.execute(f'SELECT COUNT(*) FROM ({base}) X', params)
        total = cur.fetchone()[0] or 0

        limit = PER_PAGE
        offset = (page - 1) * PER_PAGE
        cur.execute(f"""
          {base}
          ORDER BY a."nome" ASC, r."idRecpsa" DESC
          LIMIT %s OFFSET %s
        """, params + [limit, offset])

        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            rows.append({cols[i]: r[i] for i in range(len(cols))})
        conn.close()
    except Exception as e:
        conn.close()
        print("Erro em consulta geral recpsa:", e)
    return rows, total

def pagina_conGeralRecpsa():

    F, page = _ler_filtros()
    rows, total = _executar_consulta(F, page)
    pages = max(1, math.ceil(total / PER_PAGE))

    # selects para filtros
    assentados, tipos, infra = _carregar_selects()

    from urllib.parse import urlencode
    def pagina_url(p):
        q = {
            'idAssent': F.idAssent,
            'idTipRecpsa': F.idTipRecpsa,
            'idTipUsoInfr': F.idTipUsoInfr,
            'nome': F.nome, 'valMin': F.valMin, 'valMax': F.valMax, 'page': p
        }
        return url_for('conGeralRecpsa') + '?' + urlencode(q)

    return render_template('conGeralRecpsa.html',
                           filtros=F,
                           rows=rows, total=total, page=page, pages=pages,
                           pagina_url=pagina_url,
                           assentados=assentados, tipos=tipos, infra=infra)

def conFiltroRecpsa():
    return pagina_conGeralRecpsa()
