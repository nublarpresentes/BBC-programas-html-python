# evento.py
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import (
    request, render_template, redirect, url_for, flash, current_app
)
import psycopg2

# ---- PDF
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from flask import send_file


from conexao_bd import conectar_bd

# ==========================
# Helpers de caminho
# ==========================
def _pasta_static(*parts) -> str:
    """<app>/static/..."""
    return os.path.join(current_app.root_path, "static", *parts)

def _pasta_img_eventos() -> str:
    """<app>/static/img/eventos"""
    path = _pasta_static("img", "eventos")
    os.makedirs(path, exist_ok=True)
    return path


# ==========================
# ====== TIPO DE EVENTO =====
# ==========================
def _listar_tipos_evento():
    conn = conectar_bd(); itens = []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT "idTipEvt","nomTipEvt" FROM "tbtipevt" ORDER BY "nomTipEvt"')
            itens = cur.fetchall()
        finally:
            try: conn.close()
            except: pass
    return itens

def view_tipEvtCad():
    """Tela simples de cadastro de Tipo de Evento."""
    return render_template("tipEvtCad.html")

def cadastrar_tipevt():
    """POST: insere um novo tipo de evento em tbtipevt."""
    if request.method != "POST":
        return redirect(url_for("tipEvtCad"))

    nomTipEvt = (request.form.get("nomTipEvt") or "").strip()
    if not nomTipEvt:
        flash("❌ Informe o nome do Tipo de Evento.", "danger")
        return redirect(url_for("tipEvtCad"))

    conn = conectar_bd()
    if not conn:
        flash("❌ Erro de conexão com o banco.", "danger")
        return redirect(url_for("tipEvtCad"))

    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO "tbtipevt"("nomTipEvt") VALUES (%s)', (nomTipEvt,))
        conn.commit()
        flash("✅ Tipo de Evento cadastrado!", "success")
        return redirect(url_for("tipEvtCad"))
    except psycopg2.Error as e:
        try: conn.rollback()
        except: pass
        flash(f"❌ Erro ao gravar: {e.pgerror}", "danger")
        return redirect(url_for("tipEvtCad"))
    finally:
        try: conn.close()
        except: pass

def pagina_tipEvtAlt():
    """Lista + edição (carrega 1 registro se ?id=)."""
    itens = _listar_tipos_evento()
    registro = None
    sel_id = request.args.get("id")
    if sel_id:
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('SELECT "idTipEvt","nomTipEvt" FROM "tbtipevt" WHERE "idTipEvt"=%s', (int(sel_id),))
                row = cur.fetchone()
                if row:
                    registro = {"idTipEvt": row[0], "nomTipEvt": row[1]}
            finally:
                try: conn.close()
                except: pass
    return render_template("tipEvtAlt.html", itens=itens, registro=registro)

def alterar_tipevt():
    if request.method != "POST":
        return redirect(url_for("tipEvtAlt"))

    idTipEvt = request.form.get("idTipEvt")
    nomTipEvt = (request.form.get("nomTipEvt") or "").strip()
    if not idTipEvt or not nomTipEvt:
        flash("❌ Informe o registro e o nome do tipo.", "danger")
        return redirect(url_for("tipEvtAlt"))

    conn = conectar_bd()
    if not conn:
        flash("❌ Erro de conexão com o banco.", "danger")
        return redirect(url_for("tipEvtAlt"))

    try:
        cur = conn.cursor()
        cur.execute('UPDATE "tbtipevt" SET "nomTipEvt"=%s WHERE "idTipEvt"=%s',
                    (nomTipEvt, int(idTipEvt)))
        conn.commit()
        flash("✅ Tipo de Evento alterado!", "success")
        return redirect(url_for("tipEvtAlt", id=idTipEvt))
    except Exception as e:
        try: conn.rollback()
        except: pass
        flash("❌ Não foi possível alterar.", "danger")
        return redirect(url_for("tipEvtAlt", id=idTipEvt))
    finally:
        try: conn.close()
        except: pass

def pagina_tipEvtExc():
    """Lista + confirmação de exclusão (carrega 1 registro se ?id=)."""
    itens = _listar_tipos_evento()
    registro = None
    sel_id = request.args.get("id")
    if sel_id:
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('SELECT "idTipEvt","nomTipEvt" FROM "tbtipevt" WHERE "idTipEvt"=%s', (int(sel_id),))
                row = cur.fetchone()
                if row:
                    registro = {"idTipEvt": row[0], "nomTipEvt": row[1]}
            finally:
                try: conn.close()
                except: pass
    return render_template("tipEvtExc.html", itens=itens, registro=registro)

def excluir_tipevt():
    if request.method != "POST":
        return redirect(url_for("tipEvtExc"))

    idTipEvt = request.form.get("idTipEvt")
    if not idTipEvt:
        flash("❌ Registro não informado.", "danger")
        return redirect(url_for("tipEvtExc"))

    conn = conectar_bd()
    if not conn:
        flash("❌ Erro de conexão com o banco.", "danger")
        return redirect(url_for("tipEvtExc"))

    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "tbtipevt" WHERE "idTipEvt"=%s', (int(idTipEvt),))
        conn.commit()
        flash("✅ Tipo de Evento excluído!", "success")
        return redirect(url_for("tipEvtExc"))
    except psycopg2.Error as e:
        try: conn.rollback()
        except: pass
        # Em caso de FK em tbevento:
        flash("❌ Não foi possível excluir (possível uso em eventos).", "danger")
        return redirect(url_for("tipEvtExc", id=idTipEvt))
    finally:
        try: conn.close()
        except: pass


# ==========================
# ======= EVENTO ===========
# ==========================
def view_evtCad():
    """Tela de cadastro do Evento (notícia, reunião, etc.)."""
    tipos = _listar_tipos_evento()
    return render_template("evtCad.html", tipos=tipos)

def _parse_date(s: str):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except:
        return None

def cadastrar_evento():
    """
    POST: Cadastra um evento em tbevento.
      Campos sempre obrigatórios:
        - nomEvt
        - idTipEvt
      Regras:
        - idTipEvt == 1 (Notícia): capa 'S' ou 'N' + foto opcional (fotoCapa)
        - idTipEvt == 2 (Reunião): turno {M,T,N}, pauta, dtIniPer e dtFimPer + foto opcional (foto1)
    """
    if request.method != "POST":
        return redirect(url_for("evtCad_view"))

    # Básico
    nomEvt   = (request.form.get("nomEvt") or "").strip()
    idTipEvt = (request.form.get("idTipEvt") or "").strip()
    descricao = (request.form.get("descricao") or "").strip()  # <<< NOVO

    if not nomEvt:
        flash("❌ Informe o nome/título do evento.", "danger")
        return redirect(url_for("evtCad_view"))
    if not idTipEvt:
        flash("❌ Selecione o Tipo de Evento.", "danger")
        return redirect(url_for("evtCad_view"))

    try:
        idTipEvt = int(idTipEvt)
    except:
        flash("❌ Tipo de Evento inválido.", "danger")
        return redirect(url_for("evtCad_view"))

    # Campos gerais (opcionais)
    responsavel     = (request.form.get("responsavel") or "").strip()
    tippresenca     = (request.form.get("tippresenca") or "").strip()[:1] or None
    local           = (request.form.get("local") or "").strip()
    linkplatonline  = (request.form.get("linkplatonline") or "").strip()
    fones           = (request.form.get("fones") or "").strip()

    # Controle por tipo
    capa   = None
    turno  = None
    pauta  = None
    dtIniPer = None
    dtFimPer = None

    if idTipEvt == 1:
        # Notícia
        capa = (request.form.get("capa") or "").strip().upper()
        if capa not in ("S", "N"):
            flash("❌ Para Notícia, informe se é capa: 'S' ou 'N'.", "danger")
            return redirect(url_for("evtCad_view"))

    elif idTipEvt == 2:
        # Reunião
        turno = (request.form.get("turno") or "").strip().upper()
        if turno not in ("M", "T", "N"):
            flash("❌ Para Reunião, selecione Turno (M/T/N).", "danger")
            return redirect(url_for("evtCad_view"))

        pauta = (request.form.get("pauta") or "").strip()
        if not pauta:
            flash("❌ Para Reunião, informe a Pauta.", "danger")
            return redirect(url_for("evtCad_view"))

        # datas
        def _parse_date(s):
            from datetime import datetime
            try: return datetime.strptime(s, "%Y-%m-%d").date() if s else None
            except: return None

        dtIniPer = _parse_date(request.form.get("dtIniPer"))
        dtFimPer = _parse_date(request.form.get("dtFimPer"))
        if not dtIniPer or not dtFimPer:
            flash("❌ Para Reunião, informe as datas de Início e Fim.", "danger")
            return redirect(url_for("evtCad_view"))

    # Inserção inicial
    conn = conectar_bd()
    if not conn:
        flash("❌ Erro de conexão com o banco.", "danger")
        return redirect(url_for("evtCad_view"))

    new_id = None
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tbevento
              ("nomEvt","pauta","responsavel","dtIniPer","dtFimPer",
               tippresenca, local, linkplatonline, fones, turno,
               "idTipEvt", capa, "fotoCapa", foto1, foto2, foto3, descricao)
            VALUES (%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s, NULL, NULL, NULL, NULL, %s)
            RETURNING "idEvt"
        """, (nomEvt, pauta, responsavel, dtIniPer, dtFimPer,
              tippresenca, local, linkplatonline, fones, turno,
              idTipEvt, capa, descricao))  # <<< NOVO
        new_id = cur.fetchone()[0]
        conn.commit()
    except Exception:
        try: conn.rollback()
        except: pass
        flash("❌ Não foi possível cadastrar o evento.", "danger")
        return redirect(url_for("evtCad_view"))

    # Upload de foto (opcional)
    try:
        from werkzeug.utils import secure_filename
        foto = request.files.get("foto")
        if foto and foto.filename:
            folder = _pasta_img_eventos()
            filename = secure_filename(foto.filename)
            ext = filename.rsplit(".", 1)[1].lower() if "." in filename else "jpg"
            if ext not in ("jpg", "jpeg", "png", "gif", "webp"):
                ext = "jpg"

            if idTipEvt == 1:
                final_name = f"evt_{new_id}_capa.{ext}"
                foto.save(os.path.join(folder, final_name))
                rel = f"img/eventos/{final_name}"
                _evt_atualizar_foto(new_id, col="fotoCapa", valor=rel)
            else:
                final_name = f"evt_{new_id}_1.{ext}"
                foto.save(os.path.join(folder, final_name))
                rel = f"img/eventos/{final_name}"
                _evt_atualizar_foto(new_id, col="foto1", valor=rel)
    except Exception:
        flash("⚠️ Evento criado, mas houve falha ao salvar a imagem.", "warning")

    flash("✅ Evento cadastrado com sucesso!", "success")
    return redirect(url_for("evtCad_view"))

def _evt_atualizar_foto(idEvt: int, col: str, valor: str):
    """Atualiza fotoCapa/foto1/... do evento recém-criado."""
    if col not in ("fotoCapa", "foto1", "foto2", "foto3"):
        return
    conn = conectar_bd()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(f'UPDATE tbevento SET "{col}"=%s WHERE "idEvt"=%s', (valor, int(idEvt)))
        conn.commit()
    except:
        try: conn.rollback()
        except: pass
    finally:
        try: conn.close()
        except: pass
# --- Menu de Eventos (necessário para o import no BBC.py) ---
def view_menuEvento():
    # se quiser passar dados depois, adicione aqui (ex: tipos=_listar_tipos_evento())
    return render_template("menuEvento.html")

def view_evtAlt():
    """Lista + carrega 1 registro se ?id= para edição (inclui descricao)."""
    tipos = _listar_tipos_evento()
    itens = []     # lista para a tabela/lateral
    registro = None

    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT e."idEvt", e."nomEvt", e."idTipEvt", t."nomTipEvt",
                       e.capa, e.turno, e.pauta, e."dtIniPer", e."dtFimPer",
                       e.responsavel, e.tippresenca, e.local, e.linkplatonline, e.fones,
                       e."fotoCapa", e.foto1, e.foto2, e.foto3, e.descricao
                  FROM tbevento e
                  LEFT JOIN tbtipevt t ON t."idTipEvt" = e."idTipEvt"
                 ORDER BY e."idEvt" DESC
            """)
            itens = cur.fetchall()

            sel_id = request.args.get("id")
            if sel_id:
                cur.execute("""
                    SELECT e."idEvt", e."nomEvt", e."idTipEvt",
                           e.capa, e.turno, e.pauta, e."dtIniPer", e."dtFimPer",
                           e.responsavel, e.tippresenca, e.local, e.linkplatonline, e.fones,
                           e."fotoCapa", e.foto1, e.foto2, e.foto3, e.descricao
                      FROM tbevento e
                     WHERE e."idEvt"=%s
                """, (int(sel_id),))
                r = cur.fetchone()
                if r:
                    registro = {
                        "idEvt": r[0], "nomEvt": r[1], "idTipEvt": r[2],
                        "capa": r[3], "turno": r[4], "pauta": r[5],
                        "dtIniPer": r[6], "dtFimPer": r[7],
                        "responsavel": r[8], "tippresenca": r[9],
                        "local": r[10], "linkplatonline": r[11], "fones": r[12],
                        "fotoCapa": r[13], "foto1": r[14], "foto2": r[15], "foto3": r[16],
                        "descricao": r[17],  # <<< NOVO
                    }
        finally:
            try: conn.close()
            except: pass

    return render_template("evtAlt.html", tipos=tipos, itens=itens, registro=registro)


def alterar_evento():
    if request.method != "POST":
        return redirect(url_for("evtAlt"))

    idEvt = request.form.get("idEvt")
    if not idEvt:
        flash("❌ Registro não informado.", "danger")
        return redirect(url_for("evtAlt"))

    # Básico
    nomEvt   = (request.form.get("nomEvt") or "").strip()
    idTipEvt = (request.form.get("idTipEvt") or "").strip()
    descricao = (request.form.get("descricao") or "").strip()  # <<< NOVO

    if not nomEvt or not idTipEvt:
        flash("❌ Informe nome e tipo.", "danger")
        return redirect(url_for("evtAlt", id=idEvt))

    try:
        idTipEvt = int(idTipEvt)
    except:
        flash("❌ Tipo de Evento inválido.", "danger")
        return redirect(url_for("evtAlt", id=idEvt))

    # Campos gerais
    responsavel     = (request.form.get("responsavel") or "").strip()
    tippresenca     = (request.form.get("tippresenca") or "").strip()[:1] or None
    local           = (request.form.get("local") or "").strip()
    linkplatonline  = (request.form.get("linkplatonline") or "").strip()
    fones           = (request.form.get("fones") or "").strip()

    # Por tipo
    capa   = None
    turno  = None
    pauta  = None
    dtIniPer = None
    dtFimPer = None

    if idTipEvt == 1:
        capa = (request.form.get("capa") or "").strip().upper()
        if capa not in ("S", "N"):
            flash("❌ Para Notícia, informe 'S' ou 'N' para capa.", "danger")
            return redirect(url_for("evtAlt", id=idEvt))
    elif idTipEvt == 2:
        turno = (request.form.get("turno") or "").strip().upper()
        if turno not in ("M", "T", "N"):
            flash("❌ Para Reunião, selecione Turno (M/T/N).", "danger")
            return redirect(url_for("evtAlt", id=idEvt))
        pauta = (request.form.get("pauta") or "").strip()
        if not pauta:
            flash("❌ Para Reunião, informe a Pauta.", "danger")
            return redirect(url_for("evtAlt", id=idEvt))

        def _parse_date(s):
            from datetime import datetime
            try: return datetime.strptime(s, "%Y-%m-%d").date() if s else None
            except: return None

        dtIniPer = _parse_date(request.form.get("dtIniPer"))
        dtFimPer = _parse_date(request.form.get("dtFimPer"))
        if not dtIniPer or not dtFimPer:
            flash("❌ Para Reunião, informe Início e Fim.", "danger")
            return redirect(url_for("evtAlt", id=idEvt))

    # Update
    conn = conectar_bd()
    if not conn:
        flash("❌ Erro de conexão com o banco.", "danger")
        return redirect(url_for("evtAlt", id=idEvt))

    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE tbevento
               SET "nomEvt"=%s, "idTipEvt"=%s, capa=%s, turno=%s, pauta=%s,
                   "dtIniPer"=%s, "dtFimPer"=%s, responsavel=%s, tippresenca=%s,
                   local=%s, linkplatonline=%s, fones=%s, descricao=%s
             WHERE "idEvt"=%s
        """, (nomEvt, idTipEvt, capa, turno, pauta,
              dtIniPer, dtFimPer, responsavel, tippresenca,
              local, linkplatonline, fones, descricao, int(idEvt)))  # <<< NOVO
        conn.commit()
        flash("✅ Evento alterado com sucesso!", "success")
        return redirect(url_for("evtAlt", id=idEvt))
    except Exception:
        try: conn.rollback()
        except: pass
        flash("❌ Não foi possível alterar.", "danger")
        return redirect(url_for("evtAlt", id=idEvt))
    finally:
        try: conn.close()
        except: pass

def view_evtExc():
    """Lista + carrega 1 registro se ?id= para confirmação (inclui descricao)."""
    itens = []
    registro = None

    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT "idEvt","nomEvt","idTipEvt",capa,turno,pauta,"dtIniPer","dtFimPer",
                       responsavel,tippresenca,local,linkplatonline,fones,"fotoCapa",foto1,foto2,foto3,descricao
                  FROM tbevento
                 ORDER BY "idEvt" DESC
            """)
            itens = cur.fetchall()

            sel_id = request.args.get("id")
            if sel_id:
                cur.execute("""
                    SELECT "idEvt","nomEvt","idTipEvt",capa,turno,pauta,"dtIniPer","dtFimPer",
                           responsavel,tippresenca,local,linkplatonline,fones,"fotoCapa",foto1,foto2,foto3,descricao
                      FROM tbevento
                     WHERE "idEvt"=%s
                """, (int(sel_id),))
                r = cur.fetchone()
                if r:
                    registro = {
                        "idEvt": r[0], "nomEvt": r[1], "idTipEvt": r[2],
                        "capa": r[3], "turno": r[4], "pauta": r[5],
                        "dtIniPer": r[6], "dtFimPer": r[7],
                        "responsavel": r[8], "tippresenca": r[9],
                        "local": r[10], "linkplatonline": r[11], "fones": r[12],
                        "fotoCapa": r[13], "foto1": r[14], "foto2": r[15], "foto3": r[16],
                        "descricao": r[17],  # <<< NOVO
                    }
        finally:
            try: conn.close()
            except: pass

    return render_template("evtExc.html", itens=itens, registro=registro)


def excluir_evento():
    if request.method != "POST":
        return redirect(url_for("evtExc"))

    idEvt = request.form.get("idEvt")
    if not idEvt:
        flash("❌ Registro não informado.", "danger")
        return redirect(url_for("evtExc"))

    conn = conectar_bd()
    if not conn:
        flash("❌ Erro de conexão com o banco.", "danger")
        return redirect(url_for("evtExc"))

    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM tbevento WHERE "idEvt"=%s', (int(idEvt),))
        conn.commit()
        flash("✅ Evento excluído!", "success")
        return redirect(url_for("evtExc"))
    except psycopg2.Error:
        try: conn.rollback()
        except: pass
        flash("❌ Não foi possível excluir (verifique vínculos).", "danger")
        return redirect(url_for("evtExc", id=idEvt))
    finally:
        try: conn.close()
        except: pass

def pagina_evtCon():
    """Consulta simples/listagem com descricao disponível no template."""
    tipos = _listar_tipos_evento()
    rows = []

    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT e."idEvt", e."nomEvt", e."idTipEvt", t."nomTipEvt",
                       e.capa, e.turno, e.pauta, e."dtIniPer", e."dtFimPer",
                       e.responsavel, e.tippresenca, e.local, e.linkplatonline, e.fones,
                       e."fotoCapa", e.foto1, e.foto2, e.foto3, e.descricao
                  FROM tbevento e
                  LEFT JOIN tbtipevt t ON t."idTipEvt" = e."idTipEvt"
                 ORDER BY e."idEvt" DESC
            """)
            cols = [d[0] for d in cur.description]
            for r in cur.fetchall():
                rows.append({cols[i]: r[i] for i in range(len(cols))})
        finally:
            try: conn.close()
            except: pass

    return render_template("evtCon.html", tipos=tipos, rows=rows)

# --- ALIASES DE COMPATIBILIDADE (deixe no final do evento.py) ---

# Alguns arquivos importam esses nomes antigos:


def cadastrar_evt():
    return cadastrar_evento()

def view_menuEventos():
    """
    Lista últimos eventos (qualquer tipo) para o menu de eventos.
    Renderiza 'menuEvento.html' com a variável 'eventos'.
    """
    conn = conectar_bd()
    eventos = []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT e."idEvt",
                       e."nomEvt",
                       COALESCE(e.descricao, ''),
                       e."idTipEvt",
                       COALESCE(t."nomTipEvt",''),
                       COALESCE(e."fotoCapa", COALESCE(e.foto1,'')) AS foto,  -- usa capa se notícia, senão foto1
                       e."dtIniPer",
                       e."dtFimPer",
                       e.turno
                  FROM tbevento e
                  LEFT JOIN tbtipevt t ON t."idTipEvt" = e."idTipEvt"
                 ORDER BY e."idEvt" DESC
                 LIMIT 50
            """)
            for r in cur.fetchall():
                eventos.append({
                    "idEvt": r[0],
                    "titulo": r[1],
                    "descricao": r[2],
                    "idTipEvt": r[3],
                    "tipo": r[4],
                    "foto": r[5],  # relativo a /static/
                    "dtIniPer": r[6],
                    "dtFimPer": r[7],
                    "turno": r[8],
                })
        finally:
            try: conn.close()
            except: pass
    return render_template('menuEvento.html', eventos=eventos)

# ================
# LISTA DE PRESENÇA (Reuniões)
# ================

def _listar_reunioes():
    """Retorna [(idEvt, nomEvt, dtIniPer, turno, local)] apenas de reuniões (idTipEvt=2)."""
    conn = conectar_bd(); itens = []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT e."idEvt", e."nomEvt", e."dtIniPer", COALESCE(e.turno,''), COALESCE(e.local,'')
                  FROM tbevento e
                 WHERE e."idTipEvt" = 2
                 ORDER BY e."dtIniPer" DESC NULLS LAST, e."nomEvt" ASC
            """)
            itens = cur.fetchall()
        finally:
            try: conn.close()
            except: pass
    return itens

def view_evtPresencaSel():
    """Tela para escolher a reunião e gerar o PDF."""
    reunioes = _listar_reunioes()
    return render_template("evtPresencaSel.html", reunioes=reunioes)

def _pegar_evento(idEvt:int):
    """Dados do evento para o cabeçalho."""
    conn = conectar_bd(); reg=None
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT "nomEvt","dtIniPer","dtFimPer",COALESCE(turno,''),COALESCE(local,''),COALESCE(pauta,'')
                  FROM tbevento
                 WHERE "idEvt"=%s
            """, (int(idEvt),))
            row = cur.fetchone()
            if row:
                reg = {
                    "nomEvt": row[0],
                    "dtIniPer": row[1],
                    "dtFimPer": row[2],
                    "turno": (row[3] or '').strip(),
                    "local": row[4] or '',
                    "pauta": row[5] or '',
                }
        finally:
            try: conn.close()
            except: pass
    return reg

def _listar_assentados_ativos_alfabetico():
    """[(idAssent, nome)] — somente ATIVOS, ordenado por nome."""
    conn = conectar_bd(); itens=[]
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT "idAssent", nome
                  FROM tbassentado
                 WHERE COALESCE("idSitAssent",1)=1
                 ORDER BY lower(nome) ASC
            """)
            itens = cur.fetchall()
        finally:
            try: conn.close()
            except: pass
    return itens

def gerar_lista_presenca_pdf():
    """POST: recebe idEvt, gera PDF em memória e retorna."""
    if request.method != "POST":
        return redirect(url_for("evtPresenca"))

    idEvt = request.form.get("idEvt")
    if not idEvt:
        flash("Selecione uma reunião.", "warning")
        return redirect(url_for("evtPresenca"))

    try:
        idEvt = int(idEvt)
    except:
        flash("Reunião inválida.", "danger")
        return redirect(url_for("evtPresenca"))

    evt = _pegar_evento(idEvt)
    if not evt:
        flash("Evento não encontrado.", "danger")
        return redirect(url_for("evtPresenca"))

    assentados = _listar_assentados_ativos_alfabetico()

    # ---- Gera PDF em memória
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    left   = 15*mm
    right  = 15*mm
    top    = 15*mm
    bottom = 15*mm

    largura_util = W - left - right

    def _fmt_data(d):
        if not d: return ""
        try:
            return d.strftime("%d/%m/%Y")
        except: return str(d)

    data_str = _fmt_data(evt["dtIniPer"])
    turno_map = {"M":"Matutino","T":"Vespertino","N":"Noturno"}
    turno_str = turno_map.get((evt["turno"] or "").upper(), evt["turno"] or "-")

    # Config linhas
    linha_h = 9.5*mm
    y_start = H - top - 45*mm   # espaço para cabeçalho do evento
    rows_per_page = int((y_start - bottom) // linha_h) - 1
    if rows_per_page < 8:
        rows_per_page = 8

    # Colunas (larguras)
    col_nome = 70*mm
    col_matr = 32*mm
    col_ass  = largura_util - col_nome - col_matr - 18*mm  # assinatura ocupa o resto
    col_pres = 18*mm

    def cabecalho(pag_atual:int):
        # Linha 1
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left, H - top, "BBC - Banco do Bem Comum")
        c.setFont("Helvetica", 10)
        c.drawRightString(W - right, H - top, f"Data: {data_str or '-'}    Pág: {pag_atual:03d}")
        c.line(left, H - top - 3*mm, W - right, H - top - 3*mm)

        # Evento
        y = H - top - 10*mm
        c.setFont("Helvetica", 10)
        c.drawString(left, y, f"Evento:  {evt['nomEvt']}")
        c.drawRightString(W - right, y, f"Turno: {turno_str}")
        y -= 6*mm
        c.drawString(left, y, f"Local:   {evt['local']}")
        y -= 6*mm
        c.drawString(left, y, f"Pauta:   {evt['pauta']}")
        y -= 3*mm
        c.line(left, y, W - right, y)

        # Título da lista
        y -= 8*mm
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(W/2, y, "Lista de Presença")
        y -= 5*mm

        # Cabeçalho da tabela
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left, y, "Nome")
        c.drawString(left + col_nome, y, "( matrícula )")
        c.drawString(left + col_nome + col_matr, y, "Assinatura")
        c.drawRightString(W - right, y, "Presente (S/N)")
        y -= 2*mm
        c.line(left, y, W - right, y)
        return y - 4*mm  # primeira linha útil

    y = cabecalho(1)
    c.setFont("Helvetica", 10)
    pag = 1
    i_na_pagina = 0

    for idx, (idAssent, nome) in enumerate(assentados, start=1):
        # quebra de página
        if i_na_pagina >= rows_per_page:
            c.showPage()
            pag += 1
            y = cabecalho(pag)
            c.setFont("Helvetica", 10)
            i_na_pagina = 0

        # desenha a linha
        c.drawString(left, y, nome or "-")
        c.drawString(left + col_nome + 2*mm, y, f"({idAssent})")
        # linha de assinatura
        x_ass = left + col_nome + col_matr + 2*mm
        c.line(x_ass, y - 1*mm, x_ass + col_ass - 6*mm, y - 1*mm)
        # coluna presente
        c.rect(W - right - col_pres + 2*mm, y - 4*mm, 6*mm, 6*mm, stroke=1, fill=0)

        y -= linha_h
        i_na_pagina += 1

    c.showPage()
    c.save()
    buf.seek(0)

    filename = f"lista_presenca_evt_{idEvt}.pdf"
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True, download_name=filename)
