import psycopg2
import calendar
from flask import Flask, request, render_template, redirect, url_for, session, make_response
from conexao_bd import conectar_bd
from datetime import datetime, time
from datetime import datetime, time as dt_time

import pandas as pd
import urllib
import locale

from  conexao_bd import conectar_bd

# Define o idioma local como português do Brasil
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
# cria instancia do framework flask  ( Flask é uma classe do framework )
app = Flask(__name__, template_folder='templates')

# --  ROTINAS BÁSICAS:  CONECTAR - INDEX - MENU - FICAM POSICIONADAS ANTES DE TODAS - MEU PADRÃO -----------------



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/consQTDdia', methods=['POST'])
def consQTDdia():
    if request.method == 'POST':
        turno = request.form['turno']
        datEntrg = request.form['datEntrg']
        dtEntrg = datetime.strptime(datEntrg, '%d/%m/%Y')

        # Extrair ano, mês e dia
        anoEntg = str(dtEntrg.year)
        mesEntg = str(dtEntrg.month).zfill(2)  # Zeros à esquerda se menor que 10
        diaEntg = str(dtEntrg.day).zfill(2)  # Zeros à esquerda se menor que 10

        # Montar a data no formato desejado
        datEntrgInv = anoEntg + mesEntg + diaEntg

        conn = conectar_bd()
        if conn:
            try:

                print(" @@@ 1111 consQTDdia ===>  data da entrega inva ", datEntrgInv)
                cur = conn.cursor()
                cur.execute('SELECT "qtdEntregue", "qtdTurM", "qtdTurT", "qtdTurN", "semana", "codAlim" ' +
                            'FROM tbmerctrl  WHERE "codCtrl" = %s', (datEntrgInv,))
                entrega = cur.fetchone()
                qtdEntregue, qtdTurM, qtdTurT, qtdTurN, semana, codAlim = entrega

                if entrega:

                    #  -----------  BUSCAR ALIMENTO NA TABELA  -----------------------
                    cur.execute('SELECT "nomAlim", "valUnitAlim" FROM tbalimento WHERE "codAlim" = %s', (codAlim,))
                    result = cur.fetchone()
                    if result:
                        nomAlim = result[0]
                        valUnitAlim = result[1]
                    else:
                        nomAlime = "Alimento não encontrado"

                    #  -----------  CALCULAR VALORES  ALIMENTO -----------------------
                    valEntregue =  qtdEntregue * valUnitAlim
                    valTurM = qtdTurM * valUnitAlim
                    valTurT = qtdTurT * valUnitAlim
                    valTurN = qtdTurN * valUnitAlim

                    return render_template('consQTDdia.html', qtdEntregue=qtdEntregue, qtdTurM=qtdTurM,
                             qtdTurT=qtdTurT, qtdTurN=qtdTurN, datEntrg=datEntrg, semana=semana, nomAlim=nomAlim,
                             valEntregue=valEntregue, valTurM=valTurM, valTurT=valTurT, valTurN=valTurN)

                else:
                  session['mensagem'] = f" Erro 0129 - ao Carregar Dados  ! "
                  return render_template('consQTDdia.html', mensagem=session['mensagem'])

            except Exception as e:
                  session['mensagem'] = f" Erro 0156 - ao Carregar Dados  ! {str(e)}"
                  return render_template('consQTDdia.html', mensagem=session['mensagem'])
            finally:
                conn.close()
        else:

            session['mensagem'] = f" Erro 222 - ao Carregar Dados  ! {str(e)}"
            return render_template('consQTDdia.html', mensagem=session['mensagem'])


@app.route('/consQTDsem', methods=['POST'])
def consQTDsem():
    if request.method == 'POST':
        ano = request.form['ano']
        mes = request.form['mes']
        semana = request.form['semana']
        data_atual = datetime.now().date()
        conn = conectar_bd()
        if conn:
            try:

                print(" @@@ 1111 consQTDsem ===>  data da entrega inva ", ano, mes)

                dtIni = f"{ano}{mes.zfill(2)}01"
                dtFim = f"{ano}{mes.zfill(2)}31"

                print(" @@@ 222 consQTDsem ===>  data da entrega inva ", ano, mes)

                cur = conn.cursor()
                cur.execute('SELECT "qtdEntregue", "qtdTurM", "qtdTurT", "qtdTurN", "codAlim", "diaSem" ' 
                            'FROM tbmerctrl WHERE "codCtrl" BETWEEN %s AND %s AND "semana" = %s',
                            (dtIni, dtFim, semana,))

                print(" @@@ 3333 consQTDsem ===>  data da entrega inva ", ano, mes)

                entregas = cur.fetchall()

                valEntregue = 0
                valTurM = 0
                valTurT = 0
                valTurN = 0
                qtdEntregueTot =0
                qtdTurMtot = 0
                qtdTurTtot = 0
                qtdTurNtot = 0
                print(" @@@ 4444 consQTDsem ===>  data da entrega inva ", ano, mes)

                if entregas:
                    nomAlims= []
                    valAlims = []
                    diaSems = []
                    print(" @@@ 5555 consQTDsem ===>  data da entrega inva ", ano, mes)

                    for entrega in entregas:

                        print(" @@@ 6666 consQTDsem ===>  data da entrega inva ", ano, mes)

                        #  -----------  BUSCAR ALIMENTO NA TABELA  -----------------------
                        qtdEntregue, qtdTurM, qtdTurT, qtdTurN, codAlim, diaSem = entrega

                        cur.execute('SELECT "nomAlim", "valUnitAlim" FROM tbalimento ' +
                                    'WHERE "codAlim" = %s', (codAlim,))
                        result = cur.fetchone()

                        print(" @@@ 7777 consQTDsem ===>  data da entrega inva ", ano, mes)

                        if result:
                           nomAlim = result[0]
                           valUnitAlim = result[1]

                           # Adicionar o nome do alimento e o valor unitário às listas
                           nomAlims.append(nomAlim)
                           valAlims.append(valUnitAlim)
                           diaSems.append(diaSem)
                        else:
                            nomAlime = "Alimento não encontrado"

                        print("###### SEMANA 11111111  ", qtdEntregue )
                        #  -----------  CALCULAR VALORES  ALIMENTO -----------------------
                        valEntregue += qtdEntregue * valUnitAlim
                        valTurM += qtdTurM * valUnitAlim
                        valTurT += qtdTurT * valUnitAlim
                        valTurN += qtdTurN * valUnitAlim

                        qtdEntregueTot += qtdEntregue
                        qtdTurMtot += qtdTurM
                        qtdTurTtot += qtdTurT
                        qtdTurNtot += qtdTurN


                    print("###### SEMANA 22222  ", qtdEntregue)

                    alimentos = list(zip(nomAlims, valAlims, diaSems))

                    data_atual = datetime.now().date()

                    return render_template('consQTDsem.html',
                                           qtdEntregueTot=qtdEntregueTot,
                                           qtdTurMtot=qtdTurMtot,
                                           qtdTurTtot=qtdTurTtot,
                                           qtdTurNtot=qtdTurNtot,
                                           ano=ano,
                                           mes=mes,
                                           semana=semana,
                                           alimentos=alimentos,
                                           valEntregue=valEntregue,
                                           valTurM=valTurM,
                                           valTurT=valTurT,
                                           valTurN=valTurN,
                                           data_atual=data_atual)

                else:
                  session['mensagem'] = f" Erro 0129 - ao Carregar Dados  ! "
                  data_atual = datetime.now().date()
                  return render_template('consQTDsem.html', data_atual=data_atual, mensagem=session['mensagem'])

            except Exception as e:
                  session['mensagem'] = f" Erro 0156 - ao Carregar Dados  ! {str(e)}"
                  data_atual = datetime.now().date()
                  return render_template('consQTDsem.html', data_atual=data_atual, mensagem=session['mensagem'])
            finally:
                conn.close()
        else:

            session['mensagem'] = f" Erro 222 - ao Carregar Dados  ! {str(e)}"
            return render_template('consQTDsem.html', mensagem=session['mensagem'])


#  aplicação Flask será acessível a partir de outros dispositivos na mesma rede, como o seu celular.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True )







