import psycopg2
from flask import request, render_template, redirect, url_for
from conexao_bd import conectar_bd
from datetime import datetime

# ------------------------------
# Função: Cadastrar finança
# ------------------------------
def cadastrar_financ():
    if request.method != 'POST':
        return redirect(url_for('financCad'))

    tipFinancCR   = request.form.get('tipFinancCR')         # 1 ou 2
    idAssent     = request.form.get('idAssent')           # FK tbassentado
    idCatgFinanc  = request.form.get('idCatgFinanc')        # FK tbtipfinanc
    valFinanc_raw = request.form.get('valFinanc')
    obs           = request.form.get('obs', '')

    # Campos de parcelas (opcionais)
    anoFinanc     = request.form.get('anoFinanc') or None
    mesFinanc     = request.form.get('mesFinanc') or None
    numParcela    = request.form.get('numParcela') or None

    # Normaliza valor
    valFinanc = None
    if valFinanc_raw not in (None, ''):
        try:
            valFinanc = float(valFinanc_raw)
        except ValueError:
            valFinanc = None

    # Valida mínimos
    if not tipFinancCR or not idAssent or not idCatgFinanc or valFinanc is None:
        # Poderia renderizar com mensagem, mas vamos voltar para o form
        return redirect(url_for('financCad'))

    conn = conectar_bd()
    if not conn:
        return redirect(url_for('financCad'))

    try:
        cur = conn.cursor()
        # Assumindo a tabela "tbfinanc" com PK serial "idSeqFinanc"
        # e colunas compatíveis com estes campos (ajuste nomes se necessário):
        # idSeqFinanc (serial), tipFinancCR, idAssent, idCatgFinanc,
        # anoFinanc, mesFinanc, numParcela, valFinanc, obs, datCad
        cur.execute("""
            INSERT INTO "tbfinanc"
            ("tipFinancCR","idAssent","idCatgFinanc",
             "anoFinanc","mesFinanc","numParcela",
             "valFinanc","obs","datCad")
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            int(tipFinancCR), idAssent, int(idCatgFinanc),
            int(anoFinanc) if anoFinanc else None,
            int(mesFinanc) if mesFinanc else None,
            int(numParcela) if numParcela else None,
            valFinanc, obs, datetime.now()
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('financCad'))
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Erro ao cadastrar retribuição:", e)
        return redirect(url_for('financCad'))


# ------------------------------
# Função: Alterar finança (básica)
# ------------------------------
def alterar_financ():
    if request.method != 'POST':
        return redirect(url_for('financCad'))

    # Você precisará enviar o idSeqFinanc no form de alteração
    idSeqFinanc   = request.form.get('idSeqFinanc')
    tipFinancCR   = request.form.get('tipFinancCR')
    idAssent     = request.form.get('idAssent')
    idCatgFinanc  = request.form.get('idCatgFinanc')
    anoFinanc     = request.form.get('anoFinanc') or None
    mesFinanc     = request.form.get('mesFinanc') or None
    numParcela    = request.form.get('numParcela') or None
    valFinanc_raw = request.form.get('valFinanc')
    obs           = request.form.get('obs', '')

    if not idSeqFinanc:
        return redirect(url_for('financCad'))

    valFinanc = None
    if valFinanc_raw not in (None, ''):
        try:
            valFinanc = float(valFinanc_raw)
        except ValueError:
            valFinanc = None

    conn = conectar_bd()
    if not conn:
        return redirect(url_for('financCad'))

    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE "tbfinanc"
               SET "tipFinancCR"=%s,
                   "idAssent"=%s,
                   "idCatgFinanc"=%s,
                   "anoFinanc"=%s,
                   "mesFinanc"=%s,
                   "numParcela"=%s,
                   "valFinanc"=%s,
                   "obs"=%s
             WHERE "idSeqFinanc"=%s
        """, (
            int(tipFinancCR) if tipFinancCR else None,
            idAssent,
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
        return redirect(url_for('financCad'))
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Erro ao alterar retribuição:", e)
        return redirect(url_for('financCad'))
