# evento.py
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import (
    request, render_template, redirect, url_for, flash, current_app
)
import psycopg2

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

def cadastrar_evt():
    """
    POST: Cadastra um evento em tbevento.
      Campos sempre obrigatórios:
        - nomEvt
        - idTipEvt
      Regras:
        - idTipEvt == 1 (Notícia):
            * capa 'S' ou 'N'
            * upload de foto opcional => salva em fotoCapa
        - idTipEvt == 2 (Reunião):
            * turno em {'M','T','N'}
            * pauta texto
            * datas dtIniPer e dtFimPer obrigatórias
            * upload de foto opcional => foto1
    """
    if request.method != "POST":
        return redirect(url_for("evtCad"))

    # Básico
    nomEvt   = (request.form.get("nomEvt") or "").strip()
    idTipEvt = (request.form.get("idTipEvt") or "").strip()

    if not nomEvt:
        flash("❌ Informe o nome/título do evento.", "danger")
        return redirect(url_for("evtCad"))
    if not idTipEvt:
        flash("❌ Selecione o Tipo de Evento.", "danger")
        return redirect(url_for("evtCad"))

    try:
        idTipEvt = int(idTipEvt)
    except:
        flash("❌ Tipo de Evento inválido.", "danger")
        return redirect(url_for("evtCad"))

    # Campos comuns/gerais (opcionais)
    responsavel     = (request.form.get("responsavel") or "").strip()
    tippresenca     = (request.form.get("tippresenca") or "").strip()[:1] or None  # 'P'/'O' etc (se for usar)
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
            return redirect(url_for("evtCad"))

    elif idTipEvt == 2:
        # Reunião
        turno = (request.form.get("turno") or "").strip().upper()
        if turno not in ("M", "T", "N"):
            flash("❌ Para Reunião, selecione Turno (M/T/N).", "danger")
            return redirect(url_for("evtCad"))

        pauta = (request.form.get("pauta") or "").strip()
        if not pauta:
            flash("❌ Para Reunião, informe a Pauta.", "danger")
            return redirect(url_for("evtCad"))

        dtIniPer = _parse_date(request.form.get("dtIniPer"))
        dtFimPer = _parse_date(request.form.get("dtFimPer"))
        if not dtIniPer or not dtFimPer:
            flash("❌ Para Reunião, informe as datas de Início e Fim.", "danger")
            return redirect(url_for("evtCad"))

    # Inserção inicial (sem fotos) para obter idEvt
    conn = conectar_bd()
    if not conn:
        flash("❌ Erro de conexão com o banco.", "danger")
        return redirect(url_for("evtCad"))

    new_id = None
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tbevento
              ("nomEvt","pauta","responsavel","dtIniPer","dtFimPer",
               tippresenca, local, linkplatonline, fones, turno,
               "idTipEvt", capa, "fotoCapa", foto1, foto2, foto3)
            VALUES (%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s, NULL, NULL, NULL, NULL)
            RETURNING "idEvt"
        """, (nomEvt, pauta, responsavel, dtIniPer, dtFimPer,
              tippresenca, local, linkplatonline, fones, turno,
              idTipEvt, capa))
        new_id = cur.fetchone()[0]
        conn.commit()
    except Exception as e:
        try: conn.rollback()
        except: pass
        flash("❌ Não foi possível cadastrar o evento.", "danger")
        return redirect(url_for("evtCad"))

    # Upload de foto (opcional)
    try:
        foto = request.files.get("foto")  # input name="foto"
        if foto and foto.filename:
            folder = _pasta_img_eventos()
            filename = secure_filename(foto.filename)
            # preserva extensão
            ext = ""
            if "." in filename:
                ext = filename.rsplit(".", 1)[1].lower()
            if ext not in ("jpg", "jpeg", "png", "gif", "webp"):
                ext = "jpg"  # fallback

            # Define destino/coluna por tipo
            if idTipEvt == 1:
                # notícia -> fotoCapa
                final_name = f"evt_{new_id}_capa.{ext}"
                foto.save(os.path.join(folder, final_name))
                rel = f"img/eventos/{final_name}"
                _evt_atualizar_foto(new_id, col="fotoCapa", valor=rel)
            else:
                # demais -> foto1
                final_name = f"evt_{new_id}_1.{ext}"
                foto.save(os.path.join(folder, final_name))
                rel = f"img/eventos/{final_name}"
                _evt_atualizar_foto(new_id, col="foto1", valor=rel)
    except Exception as e:
        # Sem travar o cadastro por causa de imagem
        flash("⚠️ Evento criado, mas houve falha ao salvar a imagem.", "warning")

    flash("✅ Evento cadastrado com sucesso!", "success")
    return redirect(url_for("evtCad"))


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
