# tipUsoInfr.py
import math
import psycopg2
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

PER_PAGE = 15

# =========================
# Utilitários
# =========================
def listar_tipusoinfr():
    conn = conectar_bd()
    itens = []
    if conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT "idTipUsoInfr","nomInfr","valUsoInfr"
              FROM "tbtipusoinfr"
             ORDER BY "idTipUsoInfr" DESC
        """)
        itens = cur.fetchall()
        conn.close()
    return itens

def pegar_tipusoinfr(id_):
    if not id_:
        return None
    conn = conectar_bd()
    if not conn:
        return None
    cur = conn.cursor()
    cur.execute("""
        SELECT "idTipUsoInfr","nomInfr","valUsoInfr"
          FROM "tbtipusoinfr"
         WHERE "idTipUsoInfr"=%s
    """, (int(id_),))
    reg = cur.fetchone()
    conn.close()
    return reg

# =========================
# Views (páginas)
# =========================
def view_tipUsoInfrCad():
    return render_template('tipUsoInfrCad.html')

def view_tipUsoInfrAlt():
    itens = listar_tipusoinfr()
    sel_id = request.args.get('id')
    registro = pegar_tipusoinfr(sel_id) if sel_id else None
    return render_template('tipUsoInfrAlt.html', itens=itens, registro=registro)

def view_tipUsoInfrExc():
    itens = listar_tipusoinfr()
    sel_id = request.args.get('id')
    registro = pegar_tipusoinfr(sel_id) if sel_id else None
    return render_template('tipUsoInfrExc.html', itens=itens, registro=registro)

# =========================
# Ações (POST)
# =========================
def cadastrar_tipusoinfr():
    if request.method != 'POST':
        return redirect(url_for('tipUsoInfrCad'))

    nomInfr = (request.form.get('nomInfr') or '').strip()
    valUsoInfr_in = (request.form.get('valUsoInfr') or '').strip().replace(',', '.')
    if not nomInfr:
        flash('❌ Informe o nome do tipo de infraestrutura.', 'danger')
        return redirect(url_for('tipUsoInfrCad'))

    try:
        valUsoInfr = float(valUsoInfr_in) if valUsoInfr_in else 0.0
        if valUsoInfr < 0:
            raise ValueError()
    except:
        flash('❌ Valor inválido.', 'danger')
        return redirect(url_for('tipUsoInfrCad'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.', 'danger')
        return redirect(url_for('tipUsoInfrCad'))

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO "tbtipusoinfr" ("nomInfr","valUsoInfr")
            VALUES (%s,%s)
        """, (nomInfr, valUsoInfr))
        conn.commit()
        conn.close()
        flash('✅ Tipo de uso de infraestrutura cadastrado!', 'success')
        return redirect(url_for('tipUsoInfrCad'))
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Erro ao cadastrar tipousoinfr:", e)
        flash('❌ Erro ao cadastrar.', 'danger')
        return redirect(url_for('tipUsoInfrCad'))

def alterar_tipusoinfr():
    if request.method != 'POST':
        return redirect(url_for('tipUsoInfrAlt'))

    idTipUsoInfr = request.form.get('idTipUsoInfr')
    nomInfr = (request.form.get('nomInfr') or '').strip()
    valUsoInfr_in = (request.form.get('valUsoInfr') or '').strip().replace(',', '.')

    if not idTipUsoInfr or not nomInfr:
        flash('❌ Dados insuficientes.', 'danger')
        return redirect(url_for('tipUsoInfrAlt'))

    try:
        valUsoInfr = float(valUsoInfr_in) if valUsoInfr_in else 0.0
        if valUsoInfr < 0:
            raise ValueError()
    except:
        flash('❌ Valor inválido.', 'danger')
        return redirect(url_for('tipUsoInfrAlt'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.', 'danger')
        return redirect(url_for('tipUsoInfrAlt'))

    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE "tbtipusoinfr"
               SET "nomInfr"=%s, "valUsoInfr"=%s
             WHERE "idTipUsoInfr"=%s
        """, (nomInfr, valUsoInfr, int(idTipUsoInfr)))
        conn.commit()
        conn.close()
        flash('✅ Registro alterado!', 'success')
        return redirect(url_for('tipUsoInfrAlt'))
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Erro ao alterar tipousoinfr:", e)
        flash('❌ Erro ao alterar.', 'danger')
        return redirect(url_for('tipUsoInfrAlt'))

def excluir_tipusoinfr():
    if request.method != 'POST':
        return redirect(url_for('tipUsoInfrExc'))

    idTipUsoInfr = request.form.get('idTipUsoInfr')
    if not idTipUsoInfr:
        flash('❌ Selecione um registro.', 'danger')
        return redirect(url_for('tipUsoInfrExc'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.', 'danger')
        return redirect(url_for('tipUsoInfrExc'))

    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "tbtipusoinfr" WHERE "idTipUsoInfr"=%s', (int(idTipUsoInfr),))
        conn.commit()
        conn.close()
        flash('✅ Registro excluído!', 'success')
        return redirect(url_for('tipUsoInfrExc'))
    except psycopg2.Error as e:
        conn.rollback()
        conn.close()
        print("Erro ao excluir tipousoinfr:", e)
        flash('❌ Não foi possível excluir (FK?).', 'danger')
        return redirect(url_for('tipUsoInfrExc'))

# =========================
# Consulta geral com filtros
# =========================
def _ler_filtros():
    src = request.args if request.method == 'GET' else request.form
    filtros = type('F', (), {})()
    filtros.nome = (src.get('nome') or '').strip()
    filtros.valMin = (src.get('valMin') or '').strip().replace(',', '.')
    filtros.valMax = (src.get('valMax') or '').strip().replace(',', '.')
    try:
        page = int(src.get('page', '1'))
    except:
        page = 1
    if page < 1:
        page = 1
    return filtros, page

def _montar_where(filtros, params):
    where = ['TRUE']
    if filtros.nome:
        where.append('UPPER(t."nomInfr") LIKE UPPER(%s)')
        params.append(f'%{filtros.nome}%')
    # faixa de valores
    if filtros.valMin:
        try:
            v = float(filtros.valMin)
            where.append('t."valUsoInfr" >= %s')
            params.append(v)
        except:
            pass
    if filtros.valMax:
        try:
            v = float(filtros.valMax)
            where.append('t."valUsoInfr" <= %s')
            params.append(v)
        except:
            pass
    return ' AND '.join(where)

def _executar_consulta(filtros, page):
    conn = conectar_bd()
    rows, total = [], 0
    if not conn:
        return rows, total
    params = []
    where = _montar_where(filtros, params)
    base = f"""
        SELECT t."idTipUsoInfr", t."nomInfr", t."valUsoInfr"
          FROM "tbtipusoinfr" t
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
            ORDER BY t."nomInfr" ASC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            rows.append({cols[i]: r[i] for i in range(len(cols))})
        conn.close()
    except Exception as e:
        conn.close()
        print("Erro em consulta geral tipusoinfr:", e)
    return rows, total

def pagina_conGeralTipUsoInfr():
    filtros, page = _ler_filtros()
    rows, total = _executar_consulta(filtros, page)
    pages = max(1, math.ceil(total / PER_PAGE))

    from urllib.parse import urlencode
    def pagina_url(p):
        q = {
            'nome': filtros.nome,
            'valMin': filtros.valMin,
            'valMax': filtros.valMax,
            'page': p
        }
        return url_for('conGeralTipUsoInfr') + '?' + urlencode(q)

    return render_template('conGeralTipUsoInfr.html',
                           filtros=filtros,
                           rows=rows,
                           total=total,
                           page=page,
                           pages=pages,
                           pagina_url=pagina_url)

def conFiltroTipUsoInfr():
    return pagina_conGeralTipUsoInfr()
