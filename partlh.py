# partlh.py
from datetime import datetime, date
from flask import request, render_template, redirect, url_for, flash
from conexao_bd import conectar_bd

# =========================================
# HELPERS / SELECTS
# =========================================
def _selecoes_partlh():
    """
    Para as telas de Partilha:
      - Assentados (matrícula, nome)
      - Grupos (id,nome)
      - Tipos (tbtipfinanc) EXCLUINDO categorias 1=Política e 3=Mensalidade
        (idTipFinanc, nomFinanc, idCatgFinanc, idTipUnEqv, valEqv, nomCatg, catgParcdoSN, nomUnEqv)
    """
    conn = conectar_bd()
    assentados, grupos, tipos = [], [], []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT "matricula","nome" FROM "tbassentado" ORDER BY "nome"')
        assentados = cur.fetchall()

        cur.execute('SELECT "idGrpPartlh","nomGrpParth" FROM "tbgrppartlh" ORDER BY "nomGrpParth"')
        grupos = cur.fetchall()

        cur.execute("""
          SELECT
            t."idTipFinanc",
            t."nomFinanc",
            t."idCatgFinanc",
            t."idTipUnEqv",
            COALESCE(t."valEqv",0) AS valEqv,
            c."nomCatgFinanc",
            c."catgParcdoSN",
            u."nomUnEqv"
          FROM "tbtipfinanc" t
          LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc" = t."idCatgFinanc"
          LEFT JOIN "tbtipuneqv"  u ON u."idTipUnEqv"   = t."idTipUnEqv"
          WHERE t."idCatgFinanc" NOT IN (1,3)
          ORDER BY t."nomFinanc"
        """)
        tipos = cur.fetchall()
        conn.close()
    return assentados, grupos, tipos


# =========================================
# CADASTRO
# =========================================
def view_partlhCad():
    assentados, grupos, tipos = _selecoes_partlh()
    return render_template('partlhCad.html',
                           assentados=assentados, grupos=grupos, tipos=tipos)

def cadastrar_partlh():
    """
    Grava em tbfinanc com tipFinancCP=2 (PARTILHA).
    Em Partilha NÃO existe Política Pública/Mensalidade -> valor = valEqv do tipo.
    Suporta categoria parcelada (máx 12 parcelas/ano).
    """
    if request.method != 'POST':
        return redirect(url_for('partlhCad'))

    # fixo p/ partilha
    tipFinancCP = request.form.get('tipFinancCP')
    if tipFinancCP != '2':
        flash('❌ Operação inválida (tipFinancCP deve ser 2).')
        return redirect(url_for('partlhCad'))

    matricula    = request.form.get('matricula')
    idTipFinanc  = request.form.get('idTipFinanc')
    idCatgFinanc = request.form.get('idCatgFinanc')
    idGrpPartlh  = request.form.get('idGrpPartlh')
    catgParcdoSN = request.form.get('catgParcdoSN') or 'N'
    obs          = request.form.get('obs','').strip()

    # valor recebido do front (valEqv)
    try:
        valFinanc = float((request.form.get('valFinanc') or '0').replace(',','.'))
    except:
        valFinanc = 0.0

    if not (matricula and idTipFinanc and idCatgFinanc and idGrpPartlh):
        flash('❌ Preencha assentado, tipo e grupo de partilha.')
        return redirect(url_for('partlhCad'))
    if valFinanc <= 0:
        flash('❌ Valor inválido.')
        return redirect(url_for('partlhCad'))

    ano_atual = datetime.now().year
    conn = conectar_bd()
    if not conn:
        flash('❌ Erro ao conectar no BD.')
        return redirect(url_for('partlhCad'))

    try:
        cur = conn.cursor()
        inseridos = 0

        if catgParcdoSN == 'S':
            try:
                qtd = int(request.form.get('qtdParcelas') or '0')
            except:
                qtd = 0
            if qtd <= 0:
                conn.close()
                flash('❌ Informe o nº de parcelas a pagar.')
                return redirect(url_for('partlhCad'))

            cur.execute("""
                SELECT COALESCE(MAX("numParcela"),0), COUNT(*)
                  FROM "tbfinanc"
                 WHERE "matricula"=%s
                   AND "idCatgFinanc"=%s
                   AND "tipFinancCP"=2
                   AND "anoFinanc"=%s
            """, (matricula, int(idCatgFinanc), ano_atual))
            mx, cnt = cur.fetchone() or (0,0)

            prox = mx + 1
            restantes = max(0, 12 - cnt)
            if restantes <= 0:
                flash('⚠️ Limite de 12 parcelas já alcançado neste ano.')
                conn.close()
                return redirect(url_for('partlhCad'))

            pagar = min(restantes, qtd)
            if pagar < qtd:
                flash(f'⚠️ Só havia espaço para {pagar} parcela(s) neste ano (máx 12).')

            for i in range(pagar):
                par = prox + i
                cur.execute("""
                    INSERT INTO "tbfinanc"
                    ("matricula","anoFinanc","mesFinanc","valFinanc",
                     "idCatgFinanc","dtPagto","obs","horario",
                     "tipFinancCP","numParcela","catgParcdoSN","idPolPub","idGrpPartlh")
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,%s)
                """, (
                    matricula, ano_atual, par, valFinanc,
                    int(idCatgFinanc), date.today(), obs, datetime.now().time(),
                    2, par, 'S', int(idGrpPartlh)
                ))
                inseridos += 1
        else:
            cur.execute("""
                INSERT INTO "tbfinanc"
                ("matricula","anoFinanc","mesFinanc","valFinanc",
                 "idCatgFinanc","dtPagto","obs","horario",
                 "tipFinancCP","numParcela","catgParcdoSN","idPolPub","idGrpPartlh")
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,%s)
            """, (
                matricula, ano_atual, None, valFinanc,
                int(idCatgFinanc), date.today(), obs, datetime.now().time(),
                2, 0, 'N', int(idGrpPartlh)
            ))
            inseridos = 1

        conn.commit()
        flash(f"✅ Partilha registrada ({inseridos} registro(s)).")
        return redirect(url_for('partlhCad'))

    except Exception as e:
        try:
            if conn and not conn.closed: conn.rollback()
        except: pass
        print("Erro ao cadastrar partilha:", e)
        flash("❌ Erro ao cadastrar Partilha.")
        return redirect(url_for('partlhCad'))
    finally:
        if conn and not conn.closed: conn.close()


# =========================================
# ALTERAÇÃO (lista + painel de edição)
# =========================================
def _ler_filtros_alt():
    src = request.args
    f = type('F', (), {})()
    f.matricula   = src.get('matricula') or ''
    f.idGrpPartlh = src.get('idGrpPartlh') or ''
    f.idTipFinanc = src.get('idTipFinanc') or ''
    sel_id        = src.get('id') or ''
    return f, sel_id

def view_partlhAlt():
    filtros, sel_id = _ler_filtros_alt()
    assentados, grupos, tipos = _selecoes_partlh()

    conn = conectar_bd()
    itens, registro = [], None
    if conn:
        cur = conn.cursor()

        where = ['f."tipFinancCP"=2']
        params = []
        if filtros.matricula:
            where.append('f."matricula"=%s'); params.append(filtros.matricula)
        if filtros.idGrpPartlh:
            where.append('f."idGrpPartlh"=%s'); params.append(int(filtros.idGrpPartlh))
        if filtros.idTipFinanc:
            where.append('t."idTipFinanc"=%s'); params.append(int(filtros.idTipFinanc))

        cur.execute(f"""
          SELECT
            f."idSeqFinanc" AS idseq,
            f."matricula",
            a."nome"         AS nome_assent,
            t."nomFinanc"    AS nomtip,
            c."nomCatgFinanc" AS nomcatg,
            g."nomGrpParth"  AS nomgrp,
            f."anoFinanc"    AS ano,
            f."mesFinanc"    AS mes,
            f."numParcela"   AS numparc,
            f."valFinanc"    AS valor,
            f."obs"          AS obs
          FROM "tbfinanc" f
          LEFT JOIN "tbassentado"  a ON a."matricula"=f."matricula"
          LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc"=f."idCatgFinanc"
          LEFT JOIN "tbgrppartlh"  g ON g."idGrpPartlh"=f."idGrpPartlh"
          LEFT JOIN "tbtipfinanc"  t ON t."idCatgFinanc"=f."idCatgFinanc"
          WHERE {" AND ".join(where)}
          ORDER BY f."anoFinanc" DESC, COALESCE(f."numParcela",0) DESC, a."nome" ASC, f."idSeqFinanc" DESC
          LIMIT 200
        """, params)
        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            itens.append({cols[i]: r[i] for i in range(len(cols))})

        if sel_id:
            cur.execute("""
              SELECT
                f."idSeqFinanc" AS idseq,
                f."matricula",
                a."nome"         AS nome_assent,
                t."nomFinanc"    AS nomtip,
                c."nomCatgFinanc" AS nomcatg,
                g."nomGrpParth"  AS nomgrp,
                f."anoFinanc"    AS ano,
                f."mesFinanc"    AS mes,
                f."numParcela"   AS numparc,
                f."valFinanc"    AS valor,
                f."obs"          AS obs
              FROM "tbfinanc" f
              LEFT JOIN "tbassentado"  a ON a."matricula"=f."matricula"
              LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc"=f."idCatgFinanc"
              LEFT JOIN "tbgrppartlh"  g ON g."idGrpPartlh"=f."idGrpPartlh"
              LEFT JOIN "tbtipfinanc"  t ON t."idCatgFinanc"=f."idCatgFinanc"
             WHERE f."idSeqFinanc"=%s
            """, (int(sel_id),))
            row = cur.fetchone()
            if row:
                registro = {cols[i]: row[i] for i in range(len(cols))}
        conn.close()

    return render_template('partlhAlt.html',
                           assentados=assentados, grupos=grupos, tipos=tipos,
                           filtros=filtros, itens=itens, registro=registro)

def alterar_partlh():
    if request.method != 'POST':
        return redirect(url_for('route_partlhAlt') if 'route_partlhAlt' in globals() else url_for('partlhAlt'))

    idSeqFinanc = request.form.get('idSeqFinanc')
    obs = request.form.get('obs','').strip()
    if not idSeqFinanc:
        return redirect(url_for('partlhAlt'))

    conn = conectar_bd()
    if not conn:
        return redirect(url_for('partlhAlt'))

    try:
        cur = conn.cursor()
        cur.execute('UPDATE "tbfinanc" SET "obs"=%s WHERE "idSeqFinanc"=%s', (obs, int(idSeqFinanc)))
        conn.commit()
        flash("✅ Partilha alterada com sucesso!")
        return redirect(url_for('partlhAlt'))
    except Exception as e:
        try:
            if conn and not conn.closed: conn.rollback()
        except: pass
        print("Erro ao alterar partilha:", e)
        return redirect(url_for('partlhAlt'))
    finally:
        if conn and not conn.closed: conn.close()


# =========================================
# EXCLUSÃO (lista + confirmação)
# =========================================
def view_partlhExc():
    # Reaproveita a listagem da ALT (sem painel de edição)
    filtros, _ = _ler_filtros_alt()
    assentados, grupos, tipos = _selecoes_partlh()

    conn = conectar_bd()
    itens = []
    if conn:
        cur = conn.cursor()
        where = ['f."tipFinancCP"=2']
        params = []
        if filtros.matricula:
            where.append('f."matricula"=%s'); params.append(filtros.matricula)
        if filtros.idGrpPartlh:
            where.append('f."idGrpPartlh"=%s'); params.append(int(filtros.idGrpPartlh))
        if filtros.idTipFinanc:
            where.append('t."idTipFinanc"=%s'); params.append(int(filtros.idTipFinanc))

        cur.execute(f"""
          SELECT
            f."idSeqFinanc" AS idseq,
            a."nome"         AS nome_assent,
            g."nomGrpParth"  AS nomgrp,
            t."nomFinanc"    AS nomtip,
            c."nomCatgFinanc" AS nomcatg,
            f."anoFinanc"    AS ano,
            f."mesFinanc"    AS mes,
            f."numParcela"   AS numparc,
            f."valFinanc"    AS valor,
            f."obs"          AS obs
          FROM "tbfinanc" f
          LEFT JOIN "tbassentado"  a ON a."matricula"=f."matricula"
          LEFT JOIN "tbcatgfinanc" c ON c."idCatgFinanc"=f."idCatgFinanc"
          LEFT JOIN "tbgrppartlh"  g ON g."idGrpPartlh"=f."idGrpPartlh"
          LEFT JOIN "tbtipfinanc"  t ON t."idCatgFinanc"=f."idCatgFinanc"
          WHERE {" AND ".join(where)}
          ORDER BY f."anoFinanc" DESC, COALESCE(f."numParcela",0) DESC, a."nome" ASC, f."idSeqFinanc" DESC
          LIMIT 200
        """, params)
        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            itens.append({cols[i]: r[i] for i in range(len(cols))})
        conn.close()

    return render_template('partlhExc.html',
                           assentados=assentados, grupos=grupos, tipos=tipos,
                           filtros=filtros, itens=itens)

def excluir_partlh():
    if request.method != 'POST':
        return redirect(url_for('partlhExc'))

    idSeqFinanc = request.form.get('idSeqFinanc')
    if not idSeqFinanc:
        flash('❌ Registro não informado.')
        return redirect(url_for('partlhExc'))

    conn = conectar_bd()
    if not conn:
        flash('❌ Erro ao conectar no BD.')
        return redirect(url_for('partlhExc'))

    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "tbfinanc" WHERE "idSeqFinanc"=%s', (int(idSeqFinanc),))
        conn.commit()
        flash('✅ Partilha excluída.')
        return redirect(url_for('partlhExc'))
    except Exception as e:
        try:
            if conn and not conn.closed: conn.rollback()
        except: pass
        print("Erro ao excluir partilha:", e)
        flash('❌ Erro ao excluir.')
        return redirect(url_for('partlhExc'))
    finally:
        if conn and not conn.closed: conn.close()
