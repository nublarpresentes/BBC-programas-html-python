# retrib.py
import math
import psycopg2
from datetime import datetime, date
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

PER_PAGE = 15

# ==========================================================
# ATENÇÃO: sua constraint atual não aceita tipFinancCP=3.
# Rode no BD (uma única vez) antes de usar retribuição:
#
# ALTER TABLE public.tbfinanc
#   DROP CONSTRAINT IF EXISTS ck_tipfin;
# ALTER TABLE public.tbfinanc
#   ADD  CONSTRAINT ck_tipfin CHECK ("tipFinancCP" = ANY (ARRAY[1,2,3]));
# ==========================================================


# ==========================
# SELECTS (cadastro/consulta)
# ==========================
def _selecoes_retrib():
    """
    Assentados + Tipos (SOMENTE categoria 1 = Política Pública),
    já com os campos que a tela usa via data-*
    """
    conn = conectar_bd()
    assentados, tipos = [], []
    if conn:
        cur = conn.cursor()
        # Assentados
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome" ASC')
        assentados = cur.fetchall()

        # Tipos da categoria 1 (Política Pública)
        cur.execute("""
          SELECT
            t."idTipFinanc",         -- 0
            t."nomFinanc",           -- 1
            t."idCatgFinanc",        -- 2 (sempre 1)
            t."idPolPub",            -- 3 (obrigatório p/ política)
            t."valPolPub",           -- 4 (informativo)
            t."percVal"  AS percval, -- 5 valor pronto p/ lançar
            p."perct"    AS pol_perc,-- 6 informativo
            t."idTipUnEqv",          -- 7
            t."valEqv",              -- 8
            c."nomCatgFinanc",       -- 9
            c."catgParcdoSN",        --10 (para política deve ser 'S')
            u."nomUnEqv"             --11
          FROM "tbtipfinanc" t
          LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc"=t."idCatgFinanc"
          LEFT JOIN "tbpolitpub"  p ON p."idPolPub"=t."idPolPub"
          LEFT JOIN "tbtipuneqv"  u ON u."idTipUnEqv"=t."idTipUnEqv"
          WHERE t."idCatgFinanc" = 1
          ORDER BY t."nomFinanc" ASC
        """)
        tipos = cur.fetchall()
        conn.close()
    return assentados, tipos


# ==========================
# VIEWS
# ==========================
def view_retribCad():
    assentados, tipos = _selecoes_retrib()
    return render_template('retribCad.html', assentados=assentados, tipos=tipos)


def view_retribAlt():
    filtros, sel_id = _carregar_filtros_alt()
    conn = conectar_bd()
    assentados, tipos = [], []
    itens = []
    registro = None

    if conn:
        cur = conn.cursor()
        # filtros selects
        cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY "nome" ASC')
        assentados = cur.fetchall()
        # somente tipos catg=1
        cur.execute('SELECT "idTipFinanc","nomFinanc" FROM "tbtipfinanc" WHERE "idCatgFinanc"=1 ORDER BY "nomFinanc" ASC')
        tipos = cur.fetchall()

        params = [3]  # tipFinancCP = 3 (RETRIBUIÇÃO)
        where = ['f."tipFinancCP" = %s']
        if filtros.idAssent:
            where.append('f."idAssent"=%s'); params.append(int(filtros.idAssent))
        if filtros.idTipFinanc:
            where.append('t."idTipFinanc"=%s'); params.append(int(filtros.idTipFinanc))

        # lista últimos 200
        cur.execute(f"""
            SELECT
                f."idSeqFinanc" AS idseq,
                f."idAssent"    AS idassent,
                a."nome",
                COALESCE(t."nomFinanc",'(tipo não definido)') AS nomtip,
                c."nomCatgFinanc" AS nomcatg,
                f."anoFinanc"  AS ano,
                f."mesFinanc"  AS mes,
                f."numParcela" AS numparc,
                f."valFinanc"  AS valor,
                f."obs"        AS obs
            FROM "tbfinanc" f
            LEFT JOIN "tbassentado"  a ON a."idAssent"     = f."idAssent"
            LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc" = f."idCatgFinanc"
            LEFT JOIN LATERAL (
                SELECT t.*
                  FROM "tbtipfinanc" t
                 WHERE t."idCatgFinanc"=1
                   AND (t."idPolPub" IS NOT DISTINCT FROM f."idPolPub")
                 ORDER BY t."idTipFinanc" ASC
                 LIMIT 1
            ) t ON TRUE
            WHERE {" AND ".join(where)}
            ORDER BY f."anoFinanc" DESC, COALESCE(f."numParcela",0) DESC, a."nome" ASC, f."idSeqFinanc" DESC
            LIMIT 200
        """, params)
        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            itens.append({cols[i]: r[i] for i in range(len(cols))})

        # registro selecionado
        if sel_id:
            cur.execute("""
                SELECT
                    f."idSeqFinanc" AS idseq,
                    f."idAssent"    AS idassent,
                    a."nome",
                    COALESCE(t."nomFinanc",'(tipo não definido)') AS nomtip,
                    c."nomCatgFinanc" AS nomcatg,
                    f."anoFinanc"  AS ano,
                    f."mesFinanc"  AS mes,
                    f."numParcela" AS numparc,
                    f."valFinanc"  AS valor,
                    f."obs"        AS obs
                FROM "tbfinanc" f
                LEFT JOIN "tbassentado"  a ON a."idAssent"     = f."idAssent"
                LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc" = f."idCatgFinanc"
                LEFT JOIN LATERAL (
                    SELECT t.*
                      FROM "tbtipfinanc" t
                     WHERE t."idCatgFinanc"=1
                       AND (t."idPolPub" IS NOT DISTINCT FROM f."idPolPub")
                     ORDER BY t."idTipFinanc" ASC
                     LIMIT 1
                ) t ON TRUE
                WHERE f."idSeqFinanc"=%s
            """, (int(sel_id),))
            row = cur.fetchone()
            if row:
                cols = [d[0] for d in cur.description]
                registro = {cols[i]: row[i] for i in range(len(cols))}
        conn.close()

    return render_template('retribAlt.html',
                           assentados=assentados, tipos=tipos,
                           filtros=filtros, itens=itens, registro=registro)


def view_retribExc():
    sel_id = request.args.get('id')
    registro = None
    conn = conectar_bd()
    if conn:
        cur = conn.cursor()
        # detalhe
        cur.execute("""
          SELECT f."idSeqFinanc", a."nome", f."anoFinanc", f."numParcela", f."valFinanc"
            FROM "tbfinanc" f
            LEFT JOIN "tbassentado" a ON a."idAssent"=f."idAssent"
           WHERE f."tipFinancCP"=3 AND f."idSeqFinanc"=%s
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
          SELECT f."idSeqFinanc", a."nome", f."anoFinanc", f."numParcela", f."valFinanc"
            FROM "tbfinanc" f
            LEFT JOIN "tbassentado" a ON a."idAssent"=f."idAssent"
           WHERE f."tipFinancCP"=3
           ORDER BY f."idSeqFinanc" DESC
           LIMIT 200
        """)
        itens = cur.fetchall()
        conn.close()

    return render_template('retribExc.html', itens=itens, registro=registro)


def pagina_conGeralRetrib():
    F, page = _ler_filtros()
    rows, total = _executar_consulta(F, page)
    pages = max(1, math.ceil(total / PER_PAGE))

    assentados, tipos = _selecoes_retrib()

    from urllib.parse import urlencode
    def pagina_url(p):
        q = {'idAssent':F.idAssent,'idTipFinanc':F.idTipFinanc,'nome':F.nome,
             'valMin':F.valMin,'valMax':F.valMax,'page':p}
        return url_for('conGeralRetrib') + '?' + urlencode(q)

    return render_template('conGeralRetrib.html',
        filtros=F, rows=rows, total=total, page=page, pages=pages,
        pagina_url=pagina_url, assentados=assentados, tipos=tipos)

def conFiltroRetrib():
    return pagina_conGeralRetrib()


# ==========================
# AÇÕES (POST)
# ==========================
def cadastrar_retrib():
    if request.method != 'POST':
        return redirect(url_for('retribCad'))

    idAssent     = request.form.get('idAssent')
    idTipFinanc  = request.form.get('idTipFinanc')
    obs          = (request.form.get('obs') or '').strip()
    idCatgFinanc = request.form.get('idCatgFinanc') or ''  # virá do JS
    catgParcdoSN = (request.form.get('catgParcdoSN') or 'S').strip().upper()
    idPolPub     = request.form.get('idPolPub') or ''
    valFinanc_in = request.form.get('valFinanc')
    qtdParcelas  = request.form.get('qtdParcelas')  # obrigatório para política

    if not idPolPub:
        cur = None
        conn_tmp = conectar_bd()
        if conn_tmp:
            try:
                cur = conn_tmp.cursor()
                cur.execute('SELECT "idPolPub", "idCatgFinanc" FROM "tbtipfinanc" WHERE "idTipFinanc"=%s',
                            (idTipFinanc,))
                r = cur.fetchone()
                if r:
                    idPolPub_db, idCatg_db = r
                    if idPolPub_db:
                        idPolPub = str(idPolPub_db)
                    # também força categoria=1 se necessário
                    if not idCatgFinanc:
                        idCatgFinanc = str(idCatg_db or 1)
            finally:
                conn_tmp.close()

            # política pública exige categoria=1, parcelado e idPolPub
        if not idCatgFinanc:
            idCatgFinanc = 1
        try:
            idCatgFinanc = int(idCatgFinanc)
        except:
            idCatgFinanc = 1

        if idCatgFinanc != 1 or catgParcdoSN != 'S':
            flash('❌ Retribuição só permite Política Pública (catg=1, parcelado).', 'danger')
            return redirect(url_for('retribCad'))

        if not idPolPub:
            flash('❌ Tipo selecionado sem Política Pública vinculada.', 'danger')
            return redirect(url_for('retribCad'))

    # validações básicas
    if not idAssent or not idTipFinanc:
        flash('❌ Dados insuficientes.', 'danger')
        return redirect(url_for('retribCad'))

    try:
        idAssent = int(idAssent)
        idTipFinanc = int(idTipFinanc)
    except:
        flash('❌ Assentado/Tipo inválidos.', 'danger')
        return redirect(url_for('retribCad'))

    # política pública exige categoria=1, parcelado e idPolPub
    if not idCatgFinanc:
        idCatgFinanc = 1
    try:
        idCatgFinanc = int(idCatgFinanc)
    except:
        idCatgFinanc = 1

    if idCatgFinanc != 1 or catgParcdoSN != 'S':
        flash('❌ Retribuição só permite Política Pública (catg=1, parcelado).', 'danger')
        return redirect(url_for('retribCad'))

    if not idPolPub:
        flash('❌ Tipo selecionado sem Política Pública vinculada.', 'danger')
        return redirect(url_for('retribCad'))

    ano_atual = datetime.now().year

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro ao conectar no BD.', 'danger')
        return redirect(url_for('retribCad'))

    try:
        cur = conn.cursor()

        # carrega percVal do tipo (valor pronto p/ política)
        cur.execute('SELECT "percVal" FROM "tbtipfinanc" WHERE "idTipFinanc"=%s', (idTipFinanc,))
        row = cur.fetchone()
        percVal = float(row[0] or 0) if row else 0.0
        if percVal <= 0:
            conn.close()
            flash('❌ Política Pública sem valor definido.', 'danger')
            return redirect(url_for('retribCad'))

        # nº de parcelas a lançar agora
        try:
            qtd = int(qtdParcelas or '0')
        except:
            qtd = 0
        if qtd <= 0:
            conn.close()
            flash('❌ Informe o nº de parcelas a pagar.', 'danger')
            return redirect(url_for('retribCad'))

        # verifica parcelas já usadas neste ano
        cur.execute("""
            SELECT COALESCE(MAX("numParcela"),0), COUNT(*)
              FROM "tbfinanc"
             WHERE "idAssent"=%s
               AND "idCatgFinanc"=1
               AND "tipFinancCP"=3
               AND "anoFinanc"=%s
        """, (idAssent, ano_atual))
        mx, cnt = cur.fetchone() or (0,0)
        prox = mx + 1
        restantes = max(0, 12 - cnt)
        if restantes <= 0:
            flash('⚠️ Limite de 12 parcelas já alcançado neste ano.', 'warning')
            conn.close()
            return redirect(url_for('retribCad'))

        pagar = min(restantes, qtd)
        if pagar < qtd:
            flash(f'⚠️ Só havia espaço para {pagar} parcela(s) neste ano (máx 12).', 'warning')

        inseridos = 0
        for i in range(pagar):
            par = prox + i
            cur.execute("""
                INSERT INTO "tbfinanc"
                ("idAssent","anoFinanc","mesFinanc","valFinanc",
                 "idCatgFinanc","dtPagto","obs","horario",
                 "tipFinancCP","numParcela","catgParcdoSN","idPolPub")
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                idAssent, ano_atual, par, percVal,
                1, date.today(), obs, datetime.now().time(),
                3, par, 'S', int(idPolPub)
            ))
            inseridos += 1

        conn.commit()
        flash(f"✅ Retribuição registrada ({inseridos} parcela(s)).", 'success')
        return redirect(url_for('retribCad'))

    except Exception as e:
        try:
            if conn and not conn.closed:
                conn.rollback()
        except:
            pass
        print("Erro ao cadastrar retribuição:", e)
        flash("❌ Erro ao cadastrar.", 'danger')
        return redirect(url_for('retribCad'))
    finally:
        if conn and not conn.closed:
            conn.close()


def alterar_retrib():
    if request.method != 'POST':
        return redirect(url_for('retribAlt'))

    idSeqFinanc = request.form.get('idSeqFinanc')
    if not idSeqFinanc:
        return redirect(url_for('retribAlt'))

    obs = (request.form.get('obs') or '').strip()
    numParcela_in = request.form.get('numParcela')

    try:
        idSeqFinanc = int(idSeqFinanc)
    except:
        flash('❌ ID inválido.', 'danger')
        return redirect(url_for('retribAlt'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro de conexão com o BD.', 'danger')
        return redirect(url_for('retribAlt'))

    try:
        cur = conn.cursor()
        # dados do registro (deve ser retribuição)
        cur.execute("""
            SELECT "idAssent","idCatgFinanc","anoFinanc","numParcela"
              FROM "tbfinanc"
             WHERE "idSeqFinanc"=%s AND "tipFinancCP"=3
        """, (idSeqFinanc,))
        row = cur.fetchone()
        if not row:
            conn.close()
            flash('❌ Registro não encontrado (ou não é retribuição).', 'danger')
            return redirect(url_for('retribAlt'))

        idAssent_db, idCatg_db, ano_db, numParc_db = row

        # retribuição é parcelada (catg=1), então permitimos alterar número da parcela (1..12)
        novo_num = numParc_db
        if numParcela_in is not None and str(numParcela_in).strip() != '':
            try:
                novo_num = int(numParcela_in)
            except:
                novo_num = numParc_db
            if novo_num < 1: novo_num = 1
            if novo_num > 12: novo_num = 12

        # colisão?
        if novo_num != numParc_db:
            cur.execute("""
                SELECT COUNT(*) FROM "tbfinanc"
                 WHERE "idAssent"=%s AND "idCatgFinanc"=1 AND "tipFinancCP"=3
                   AND "anoFinanc"=%s AND "numParcela"=%s AND "idSeqFinanc"<>%s
            """, (idAssent_db, ano_db, novo_num, idSeqFinanc))
            ja_existe = (cur.fetchone() or [0])[0]
            if ja_existe:
                flash('⚠️ Já existe retribuição com este nº de parcela para este assentado/ano.', 'warning')
                conn.close()
                return redirect(url_for('retribAlt', id=idSeqFinanc))

        # UPDATE
        cur.execute("""
            UPDATE "tbfinanc"
               SET "obs"=%s, "numParcela"=%s, "mesFinanc"=%s
             WHERE "idSeqFinanc"=%s
        """, (obs, novo_num, novo_num, idSeqFinanc))

        conn.commit()
        flash('✅ Retribuição alterada com sucesso!', 'success')
        return redirect(url_for('retribAlt'))

    except Exception as e:
        try:
            if conn and not conn.closed: conn.rollback()
        except: pass
        print("Erro ao alterar retribuição:", e)
        flash('❌ Erro ao alterar.', 'danger')
        return redirect(url_for('retribAlt'))
    finally:
        if conn and not conn.closed: conn.close()


def excluir_retrib():
    if request.method != 'POST':
        return redirect(url_for('retribExc'))

    idSeqFinanc = request.form.get('idSeqFinanc')
    if not idSeqFinanc:
        flash('❌ Selecione um registro.', 'danger')
        return redirect(url_for('retribExc'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro ao conectar no BD.', 'danger')
        return redirect(url_for('retribExc'))

    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "tbfinanc" WHERE "idSeqFinanc"=%s AND "tipFinancCP"=3', (int(idSeqFinanc),))
        conn.commit()
        flash('✅ Retribuição excluída!', 'success')
        return redirect(url_for('retribExc'))
    except psycopg2.Error as e:
        try:
            conn.rollback()
        except: pass
        print("Erro ao excluir retribuição:", e)
        flash('❌ Não foi possível excluir (FK?).', 'danger')
        return redirect(url_for('retribExc'))
    finally:
        if conn and not conn.closed: conn.close()


# ==========================
# CONSULTA GERAL
# ==========================
def _ler_filtros():
    src = request.args if request.method=='GET' else request.form
    F = type('F', (), {})()
    F.idAssent     = (src.get('idAssent') or '').strip()
    F.idTipFinanc  = (src.get('idTipFinanc') or '').strip()
    F.nome         = (src.get('nome') or '').strip()
    F.valMin       = (src.get('valMin') or '').strip().replace(',','.')
    F.valMax       = (src.get('valMax') or '').strip().replace(',','.')
    try:
        page = int(src.get('page','1'))
    except:
        page = 1
    if page < 1: page = 1
    return F, page


def _montar_where(F, params):
    w = ['f."tipFinancCP"=3']
    if F.idAssent:
        w.append('f."idAssent"=%s'); params.append(int(F.idAssent))
    if F.idTipFinanc:
        w.append('t."idTipFinanc"=%s'); params.append(int(F.idTipFinanc))
    if F.nome:
        w.append('UPPER(a."nome") LIKE UPPER(%s)'); params.append(f'%{F.nome}%')
    if F.valMin:
        try: v=float(F.valMin); w.append('f."valFinanc">=%s'); params.append(v)
        except: pass
    if F.valMax:
        try: v=float(F.valMax); w.append('f."valFinanc"<=%s'); params.append(v)
        except: pass
    return ' AND '.join(w)


def _executar_consulta(F, page):
    rows, total = [], 0
    conn = conectar_bd()
    if not conn:
        return rows, total
    try:
        params = []
        where = _montar_where(F, params)
        base = f"""
          SELECT f."idSeqFinanc", a."nome" AS nom_assent,
                 COALESCE(t."nomFinanc",'') AS nom_tipo,
                 f."anoFinanc", f."numParcela", f."valFinanc"
            FROM "tbfinanc" f
            LEFT JOIN "tbassentado"  a ON a."idAssent"=f."idAssent"
            LEFT JOIN LATERAL (
               SELECT t.* FROM "tbtipfinanc" t
                WHERE t."idCatgFinanc"=1
                  AND (t."idPolPub" IS NOT DISTINCT FROM f."idPolPub")
                ORDER BY t."idTipFinanc" ASC
                LIMIT 1
            ) t ON TRUE
           WHERE {where}
        """
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM ({base}) X", params)
        total = cur.fetchone()[0] or 0

        limit = PER_PAGE
        offset = (page-1)*PER_PAGE

        cur.execute(f"""
           {base}
           ORDER BY a."nome" ASC, f."anoFinanc" DESC, COALESCE(f."numParcela",0) DESC
           LIMIT %s OFFSET %s
        """, params + [limit, offset])

        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            rows.append({cols[i]: r[i] for i in range(len(cols))})
        conn.close()
    except Exception as e:
        print("Erro consulta retrib:", e)
        try: conn.close()
        except: pass
    return rows, total


def _carregar_filtros_alt():
    src = request.args
    filtros = type('F', (), {})()
    filtros.idAssent    = src.get('idAssent') or ''
    filtros.idTipFinanc = src.get('idTipFinanc') or ''
    sel_id = src.get('id') or ''
    return filtros, sel_id
