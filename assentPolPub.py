# assentPolPub.py
import psycopg2
from psycopg2 import errors
from datetime import date, datetime
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

# --------------------------
# SELECTS (Assentados / Políticas)
# --------------------------
def _listar_assentados():
    conn = conectar_bd(); itens=[]
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT "idAssent","nome" FROM "tbassentado" ORDER BY lower(nome)')
            itens = cur.fetchall()
        finally:
            try: conn.close()
            except: pass
    return itens

def _listar_politicas():
    conn = conectar_bd(); itens=[]
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT "idPolPub","nomPolPub" FROM "tbpolitpub" ORDER BY lower("nomPolPub")')
            itens = cur.fetchall()
        finally:
            try: conn.close()
            except: pass
    return itens

# --------------------------
# Util: descobrir a sequência do ID (robusto para maiúsc./minúsc.)
# --------------------------
def _get_serial_sequence_name(conn):
    """
    Tenta descobrir o nome da sequence associada à PK de tbassentpolpub.
    Funciona se a coluna estiver como "idAssentPolPub" (CamelCase) ou "idassentpolpub" (minúscula).
    """
    cur = conn.cursor()
    # 1) tenta com a grafia CamelCase (coluna criada com aspas)
    cur.execute("SELECT pg_get_serial_sequence('tbassentpolpub','idAssentPolPub')")
    seq1 = cur.fetchone()[0]
    if seq1:
        return seq1
    # 2) tenta com a grafia minúscula (coluna criada sem aspas)
    cur.execute("SELECT pg_get_serial_sequence('tbassentpolpub','idassentpolpub')")
    seq2 = cur.fetchone()[0]
    if seq2:
        return seq2
    return None  # sem sequence associada

def _ensure_seq_ok(conn):
    """Se a sequence existir e estiver atrás do MAX(id), faz setval para alinhar."""
    cur = conn.cursor()
    # maior id existente
    cur.execute('SELECT COALESCE(MAX("idAssentPolPub"),0) FROM "tbassentpolpub"')
    try:
        max_id = int(cur.fetchone()[0] or 0)
    except Exception:
        # tenta novamente com minúsculo (caso a coluna exista assim)
        cur.execute('SELECT COALESCE(MAX(idassentpolpub),0) FROM tbassentpolpub')
        max_id = int(cur.fetchone()[0] or 0)

    seqname = _get_serial_sequence_name(conn)
    if not seqname:
        return None  # sem sequence detectada

    # pega o last_value de forma segura
    try:
        cur.execute('SELECT last_value FROM %s' % seqname)
        last_val = int(cur.fetchone()[0] or 0)
    except Exception:
        last_val = 0

    if last_val < max_id:
        # realinha usando regclass seguro
        cur.execute('SELECT setval(%s::regclass, %s, true)', (seqname, max_id))
        conn.commit()

    return seqname

# --------------------------
# CADASTRO
# --------------------------
def view_assentPolPubCad():
    return render_template(
        "assentPolPubCad.html",
        assentados=_listar_assentados(),
        politicas=_listar_politicas()
    )

def _parse_date(s):
    if not s: return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except:
        return None

def cadastrar_assentPolPub():
    if request.method != "POST":
        return redirect(url_for("assentPolPubCad"))

    idAssent  = (request.form.get("idAssent") or "").strip()
    idPolPub  = (request.form.get("idPolPub") or "").strip()
    dtCad_str = (request.form.get("dtCad") or "").strip()
    status    = (request.form.get("status") or "").strip()

    if not idAssent or not idPolPub or not status:
        flash("Informe assentado, política pública e status.", "warning")
        return redirect(url_for("assentPolPubCad"))

    try:
        idAssent = int(idAssent)
        idPolPub = int(idPolPub)
        status   = int(status)  # 1=ATIVO, 2=AGUARDANDO, 3=INATIVO
    except Exception:
        flash("Dados inválidos (IDs/status).", "danger")
        return redirect(url_for("assentPolPubCad"))

    # data do cadastro
    dtCad = _parse_date(dtCad_str) or date.today()

    # Regras de datas conforme status
    dtAtv = None
    dtIna = None
    if status == 1:      # ATIVO
        dtAtv = dtCad
    elif status == 3:    # INATIVO
        dtIna = dtCad
    # status 2 (AGUARDANDO) => sem datas

    conn = conectar_bd()
    if not conn:
        flash("Erro de conexão com o banco.", "danger")
        return redirect(url_for("assentPolPubCad"))

    try:
        # alinhar sequence (defensivo)
        seqname = _ensure_seq_ok(conn)

        cur = conn.cursor()

        # === CHECAGEM DE DUPLICIDADE (idAssent + idPolPub) ===
        cur.execute("""
            SELECT 1
              FROM "tbassentpolpub"
             WHERE "idAssent"=%s
               AND "idPolPub"=%s
             LIMIT 1
        """, (idAssent, idPolPub))
        if cur.fetchone():
            flash("⚠️ Já existe esse vínculo (Assentado x Política Pública).", "warning")
            return redirect(url_for("assentPolPubCad"))

        # === INSERT ===
        sql = """
            INSERT INTO "tbassentpolpub"
              ("idAssent","idPolPub","dtCad","status","dtAtvPolPub","dtInatvPolPub")
            VALUES (%s,%s,%s,%s,%s,%s)
        """
        try:
            cur.execute(sql, (idAssent, idPolPub, dtCad, status, dtAtv, dtIna))
        except errors.UniqueViolation:
            # caso exista CONSTRAINT única no banco, capturamos e mostramos msg amigável
            conn.rollback()
            flash("⚠️ Já existe esse vínculo (Assentado x Política Pública).", "warning")
            return redirect(url_for("assentPolPubCad"))

        # tenta recuperar o ID via currval se a sequence foi descoberta
        new_id = None
        if seqname:
            try:
                cur.execute('SELECT currval(%s::regclass)', (seqname,))
                row = cur.fetchone()
                if row:
                    new_id = row[0]
            except Exception:
                new_id = None

        conn.commit()
        if new_id is not None:
            flash(f"✅ Vinculação cadastrada (ID {new_id}).", "success")
        else:
            flash("✅ Vinculação cadastrada.", "success")
        return redirect(url_for("assentPolPubCad"))

    except psycopg2.Error as e:
        try: conn.rollback()
        except: pass
        detalhe = getattr(getattr(e, "diag", None), "message_primary", None) or (e.pgerror or str(e))
        flash(f"❌ Não foi possível cadastrar. Detalhe: {detalhe}", "danger")
        return redirect(url_for("assentPolPubCad"))
    except Exception as e:
        try: conn.rollback()
        except: pass
        flash(f"❌ Erro inesperado: {str(e)}", "danger")
        return redirect(url_for("assentPolPubCad"))
    finally:
        try: conn.close()
        except: pass

# --------------------------
# LISTA + ALTERAÇÃO DE STATUS
# --------------------------
def _listar_vinculos(idAssent=None):
    conn = conectar_bd(); rows=[]
    if conn:
        try:
            cur = conn.cursor()
            where = ""
            params = []
            if idAssent:
                where = 'WHERE ap."idAssent"=%s'
                params.append(int(idAssent))
            cur.execute(f"""
                SELECT ap."idAssentPolPub",
                       ap."idAssent",
                       a.nome,
                       ap."idPolPub",
                       p."nomPolPub",
                       ap."dtCad",
                       ap.status,
                       ap."dtAtvPolPub",
                       ap."dtInatvPolPub"
                  FROM "tbassentpolpub" ap
                  LEFT JOIN "tbassentado" a ON a."idAssent"=ap."idAssent"
                  LEFT JOIN "tbpolitpub"  p ON p."idPolPub"=ap."idPolPub"
                {where}
                 ORDER BY ap."idAssentPolPub" DESC
            """, params)
            cols = [d[0] for d in cur.description]
            for r in cur.fetchall():
                rows.append({cols[i]: r[i] for i in range(len(cols))})
        finally:
            try: conn.close()
            except: pass
    return rows

def view_assentPolPubAlt():
    idAssent = (request.args.get("idAssent") or "").strip() or None
    vinculos = _listar_vinculos(idAssent)
    return render_template("assentPolPubAlt.html", vinculos=vinculos, assentados=_listar_assentados())

def alterar_status_assentPolPub():
    """
    Altera para status 1(ATIVO), 2(AGUARDANDO) ou 3(INATIVO),
    ajustando as datas com a data atual conforme a regra.
    """
    if request.method != "POST":
        return redirect(url_for("assentPolPubAlt"))

    idVinc = (request.form.get("idAssentPolPub") or "").strip()
    novo_status = (request.form.get("novo_status") or "").strip()
    if not idVinc or not novo_status:
        flash("Selecione o registro e o novo status.", "warning")
        return redirect(url_for("assentPolPubAlt"))

    try:
        idVinc = int(idVinc)
        novo_status = int(novo_status)
    except:
        flash("Dados inválidos.", "danger")
        return redirect(url_for("assentPolPubAlt"))

    hoje = date.today()

    set_dtAtv = None
    set_dtIna = None
    if novo_status == 1:        # ATIVO
        set_dtAtv, set_dtIna = hoje, None
    elif novo_status == 2:      # AGUARDANDO
        set_dtAtv, set_dtIna = None, None
    elif novo_status == 3:      # INATIVO
        set_dtAtv, set_dtIna = None, hoje
    else:
        flash("Status inválido.", "danger")
        return redirect(url_for("assentPolPubAlt"))

    conn = conectar_bd()
    if not conn:
        flash("Erro de conexão com o banco.", "danger")
        return redirect(url_for("assentPolPubAlt"))

    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE "tbassentpolpub"
               SET status=%s,
                   "dtAtvPolPub"=%s,
                   "dtInatvPolPub"=%s
             WHERE "idAssentPolPub"=%s
        """, (novo_status, set_dtAtv, set_dtIna, idVinc))
        conn.commit()
        flash("✅ Status atualizado.", "success")
        return redirect(url_for("assentPolPubAlt"))
    except psycopg2.Error as e:
        try: conn.rollback()
        except: pass
        detalhe = getattr(getattr(e, "diag", None), "message_primary", None) or (e.pgerror or str(e))
        flash(f"❌ Não foi possível atualizar. Detalhe: {detalhe}", "danger")
        return redirect(url_for("assentPolPubAlt"))
    finally:
        try: conn.close()
        except: pass

# --------------------------
# EXCLUSÃO
# --------------------------
def view_assentPolPubExc():
    vinculos = _listar_vinculos()
    return render_template("assentPolPubExc.html", vinculos=vinculos)

def excluir_assentPolPub():
    if request.method != "POST":
        return redirect(url_for("assentPolPubExc"))
    idVinc = (request.form.get("idAssentPolPub") or "").strip()
    try:
        idVinc = int(idVinc)
    except:
        flash("Registro inválido.", "warning")
        return redirect(url_for("assentPolPubExc"))

    conn = conectar_bd()
    if not conn:
        flash("Erro de conexão com o banco.", "danger")
        return redirect(url_for("assentPolPubExc"))

    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "tbassentpolpub" WHERE "idAssentPolPub"=%s', (idVinc,))
        conn.commit()
        flash("✅ Vinculação excluída.", "success")
        return redirect(url_for("assentPolPubExc"))
    except psycopg2.Error as e:
        try: conn.rollback()
        except: pass
        detalhe = getattr(getattr(e, "diag", None), "message_primary", None) or (e.pgerror or str(e))
        flash(f"❌ Não foi possível excluir. Detalhe: {detalhe}", "danger")
        return redirect(url_for("assentPolPubExc"))
    finally:
        try: conn.close()
        except: pass
