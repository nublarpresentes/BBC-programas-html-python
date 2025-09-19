import psycopg2

from flask import request, render_template, redirect, url_for, flash

from conexao_bd import conectar_bd
from datetime import datetime

# --------------------------------------
# Função: Cadastrar partilha
# --------------------------------------
def cadastrar_partlh():
    if request.method != 'POST':
        return redirect(url_for('partlhCad'))

    tipFinancCP   = request.form.get('tipFinancCP')  # fixo "2" - partilha - / 1 é contribuicao
    matricula     = request.form.get('matricula')    # FK tbassentado
    idCatgFinanc  = request.form.get('idCatgFinanc') # FK tbcatgfinanc
    idPolPub      = request.form.get('idPolPub')  # FK tbpolpub
    obs           = request.form.get('obs', '')

    # Ano/Mês
    anoFinanc     = request.form.get('anoFinanc') or None
    mesFinanc     = request.form.get('mesFinanc') or None

    # Parcelamento
    numParcela    = request.form.get('numParcela') or None

    # Valor livre (não usado se for Política Pública)
    valFinanc_raw = request.form.get('valFinanc')

    # Política pública (quando categoria = 1)
    #idPolPub      = request.form.get('idPolPub') or None
    valPolBase    = request.form.get('valPolBaseHidden') or None
    perctHidden   = request.form.get('perctHidden') or None
    valCalcHidden = request.form.get('valCalcHidden') or None

    # --------- valida mínimos
    if not tipFinancCP or tipFinancCP != '2' or not matricula or not idCatgFinanc:
        return redirect(url_for('partlhCad'))

    conn = conectar_bd()
    if not conn:
        return redirect(url_for('partlhCad'))

    try:
        cur = conn.cursor()

        # Descobrir se a categoria é parcelada e/ou se é política pública (=1)
        cur.execute('SELECT "catgParcdoSN" FROM "tbcatgfinanc" WHERE "idCatgFinanc"=%s', (idCatgFinanc,))
        row = cur.fetchone()
        catgParcdoSN = row[0] if row else 'N'

        # Se for política pública (idCatgFinanc == 1), força cálculo do valor
        if str(idCatgFinanc) == '1':
            # Exigir ano/mês
            if not anoFinanc or not mesFinanc:
                conn.close()
                return redirect(url_for('partlhCad'))

            # Se o front não trouxe, buscamos do BD para garantir
            if not idPolPub:
                conn.close()
                return redirect(url_for('partlhCad'))

            if not (valPolBase and perctHidden and valCalcHidden):
                # Busca na tabela tbpolitpub
                cur.execute('SELECT "valor","perct" FROM "tbpolitpub" WHERE "idPolPub"=%s', (idPolPub,))
                pol = cur.fetchone()
                if not pol:
                    conn.close()
                    return redirect(url_for('partlhCad'))
                base, perct = float(pol[0] or 0), float(pol[1] or 0)
                valFinanc = base * perct
            else:
                # Usa o que o front calculou
                try:
                    valFinanc = float(valCalcHidden)
                except:
                    valFinanc = None

            # valor é obrigatório
            if valFinanc is None:
                conn.close()
                return redirect(url_for('partlhCad'))

        else:
            # Categoria comum: valor vem do campo livre
            valFinanc = None
            if valFinanc_raw not in (None, ''):
                try:
                    valFinanc = float(valFinanc_raw)
                except:
                    valFinanc = None
            if valFinanc is None:
                conn.close()
                return redirect(url_for('partlhCad'))

        # Se não for parcelada, ignora numParcela
        if catgParcdoSN != 'S':
            numParcela = None

        # Monta INSERT básico (ajuste nomes da sua tabela, se necessário)
        cur.execute("""
            INSERT INTO "tbfinanc"
            ("tipFinancCP","matricula","idCatgFinanc",
             "anoFinanc","mesFinanc","numParcela",
             "valFinanc","obs","dtPag", "idPolPub")
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            2,                           # tipFinancCP fixo partilha
            matricula,
            int(idCatgFinanc),
            int(anoFinanc) if anoFinanc else None,
            int(mesFinanc) if mesFinanc else None,
            int(numParcela) if numParcela else None,
            valFinanc,
            obs,
            datetime.now(),
            int(idPolPub) if idPolPub else None
        ))

        conn.commit()
        flash("✅ Partilha cadastrada com sucesso!")
        return redirect(url_for('partlhCad'))
    except Exception as e:
        try:
            if conn and not conn.closed:
                conn.rollback()
        except Exception:
            pass

        print("Erro ao cadastrar partilha:", e)
        return redirect(url_for('partlhCad'))
    finally:
        if conn and not conn.closed:
           conn.close()


# --------------------------------------
# Função: Alterar partilha (básica)
# --------------------------------------
def alterar_partlh():
    if request.method != 'POST':
        return redirect(url_for('partlhAlt'))

    # Você precisará enviar o idSeqFinanc no form de alteração
    idSeqFinanc   = request.form.get('idSeqFinanc')
    tipFinancCP   = request.form.get('tipFinancCP')
    matricula     = request.form.get('matricula')
    idCatgFinanc  = request.form.get('idCatgFinanc')
    anoFinanc     = request.form.get('anoFinanc') or None
    mesFinanc     = request.form.get('mesFinanc') or None
    numParcela    = request.form.get('numParcela') or None
    valFinanc_raw = request.form.get('valFinanc')
    obs           = request.form.get('obs', '')

    if not idSeqFinanc:
        return redirect(url_for('partlhAlt'))

    valFinanc = None
    if valFinanc_raw not in (None, ''):
        try:
            valFinanc = float(valFinanc_raw)
        except ValueError:
            valFinanc = None

    conn = conectar_bd()
    if not conn:
        return redirect(url_for('partlhAlt'))

    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE "tbfinanc"
               SET "tipFinancCP"=%s,
                   "matricula"=%s,
                   "idCatgFinanc"=%s,
                   "anoFinanc"=%s,
                   "mesFinanc"=%s,
                   "numParcela"=%s,
                   "valFinanc"=%s,
                   "obs"=%s
             WHERE "idSeqFinanc"=%s
        """, (
            int(tipFinancCP) if tipFinancCP else None,
            matricula,
            int(idCatgFinanc) if idCatgFinanc else None,
            int(anoFinanc) if anoFinanc else None,
            int(mesFinanc) if mesFinanc else None,
            int(numParcela) if numParcela else None,
            valFinanc,
            obs,
            int(idSeqFinanc)
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('partlhAlt'))
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Erro ao alterar partilha:", e)
        return redirect(url_for('partlhAlt'))
