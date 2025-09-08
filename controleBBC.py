import psycopg2
import calendar
from flask import Flask, request, render_template, redirect, url_for, session, make_response
from conexao_bd import conectar_bd
from datetime import datetime, time
from datetime import datetime, time as dt_time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # Adicionado
from selenium.webdriver.common.by import By
import pandas as pd
import urllib
import locale

# Define o idioma local como português do Brasil
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

app = Flask(__name__, template_folder='templates')

# --  ROTINAS BÁSICAS:  CONECTAR - INDEX - MENU - FICAM POSICIONADAS ANTES DE TODAS - MEU PADRÃO -----------------


def conectar_bd():
    try:
        conn = psycopg2.connect(
            dbname="BBC",
            user="postgres",
            password="admin",
            host="localhost"
        )
       # session['mensagem'] = "Conexão Banco de Dados Com sucesso...!"
        print(" ==> CONTROLE ==>Conexão com o banco de dados estabelecida com sucesso!")
        return conn
    except psycopg2.Error as e:
        session['mensagem'] = f" ==> ERRO 001 AO CONECTAR BANCO DE DADOS !  {e},"
        return None


@app.route('/buscacontrole', methods=['GET', 'POST'])
def busca_controle():
    data_atual = datetime.now()  # Importe datetime no topo do seu arquivo
    ano_sistema = datetime.now().year
    return render_template('buscaControle.html', ano_sistema=ano_sistema, data_atual=data_atual)


def bip():

    return


@app.route('/cadcontrole', methods=['GET', 'POST'])
def cadastrar_controle():
    print(" ==> CONTROLE ==>#################11111####### CADASTRAR CONTROLE () ###########################  ")
    session['mensagem'] = " "

    if request.method == 'POST':
        print(" ==> CONTROLE ==>#################2222####### CADASTRAR CONTROLE () ###########################  ")

        hrCtrl = datetime.now()
        hrCtrl_str = hrCtrl.strftime('%H:%M:%S')  # Formato HH:MM:SS
        ano_sistema = datetime.now().year
        mes_sistema = str(request.form['mes']).zfill(2)
        nome_mes = calendar.month_name[int(mes_sistema)]
        semanaStr = str(request.form['semana']).zfill(2)
        diaSemStr = str(request.form['dia']).zfill(2)
        codAlim = str(request.form['codAlim']).zfill(2)
        diaSem = request.form['dia']
        semana = request.form['semana']
        usuario = request.form['usuario']
        codCtrl = str(ano_sistema) + mes_sistema + diaSemStr
        qtdTotal = request.form['qtdTotal']
        dtEntCtrl = request.form['dtEntCtrl']
        codFornec = request.form['codFornec']
        status = request.form['status']
        conn = conectar_bd()
        if conn:
             try:
                #  --------  VERIFICA SE O  CONTROLE EXISTE   -------------
                print(" ==> CONTROLE ==>#################33333####### CADASTRAR CONTROLE () #######  ", codCtrl)

                cur = conn.cursor()
                cur.execute('SELECT * FROM tbmerctrl WHERE "codCtrl" = %s', (codCtrl,))
                controle_existente = cur.fetchone()

                if controle_existente:
                    print(" ==> CONTROLE ==>#################44444####### CADASTRAR CONTROLE () ###########################  ")

                    #  --------  VERIFICA SE O STATUS CONTROLE = 1  , OU SEJA , ABERTO  -------------

                    if controle_existente[9] == 1:
                        print(" ==> CONTROLE ==>#################5555####### CADASTRAR CONTROLE () ###########################  ")

                        #  --------  ATUALIZAR  CONTROLE CASO JA ESTEJA CADASTRADO O DIA -------------

                        cur.execute('UPDATE tbmerctrl SET "qtdTotal" = %s, "codAlim" = %s, "codFornec" = %s '
                                    'WHERE "codCtrl" = %s',
                                    (qtdTotal, codAlim, codFornec, codCtrl))
                        conn.commit()

                        #  -----------  BUSCAR ALIMENTO NA TABELA  -----------------------

                        cur.execute('SELECT "nomAlim" FROM tbalimento WHERE "codAlim" = %s', (codAlim,))
                        result = cur.fetchone()

                        if result:
                            nomAlimento = result[0]
                        else:
                            nomAlimento = "Alimento não encontrado"

                        session['mensagem'] = f"CONTROLE ATUALIZADO ! Mês: {mes_sistema} / Semana:{semana} / Dia: {diaSem} / Alimento: {nomAlimento}," \
                                          f"Quantidade: {qtdTotal}"
                    else:
                         session['mensagem'] = "CONTROLE JÁ FECHADO -NÃO PODE MAIS ATUALIZAR !"

                else:
                    status = 1
                    print(" ==> CONTROLE ==>#################66666####### CADASTRAR CONTROLE () ###########################  ")

                    #  -------  INSERIR REGISTRO DE CONTROLE NA TBMERCTRL -------------

                    qtdEntregue = 0
                    qtdTurM = 0
                    qtdTurT = 0
                    qtdTurN = 0
                    cur.execute('INSERT INTO tbmerctrl ("codCtrl", "matRespCad", "status", "codAlim", '
                                '"semana", "diaSem", "qtdTotal", "qtdEntregue", "dtEntContrl", "codFornec", '
                                ' "qtdTurM", "qtdTurT", "qtdTurN") '
                                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s , %s, %s, %s)',
                                (codCtrl, usuario, status, codAlim, semana, diaSem, qtdTotal, qtdEntregue,
                                 dtEntCtrl, codFornec, qtdTurM, qtdTurT, qtdTurN))

                    conn.commit()
                    print(" ==> CONTROLE ==>@@ 2222-999 INSERT calim ", codAlim)
                    cur.execute('SELECT "nomAlim" FROM tbalimento WHERE "codAlim" = %s', (codAlim,))
                    result = cur.fetchone()
                    print(" ==> CONTROLE ==>@@ 2222-888 INSERT result ", result)
                    if result:
                        nomAlim = result[0]
                    else:
                        nomAlim= "Alimento não encontrado"

                    print(" ==> CONTROLE ==>@@ 2222-777 INSERT nomAlim ", nomAlim)
                    session['mensagem'] = f"CONTROLE CADASTRADO ! Mês: {mes_sistema} /Semana: {semana} /Dia: {diaSem} / Alimento: {nomAlim}" \
                                      f" / Quantidade: {qtdTotal},"

                    return dados_controle()

             except Exception as e:
                    app.logger.error(f"Erro inesperado durante a execução do cadastro de controle: {str(e)}")
        return dados_controle()


@app.route('/cadastro_merenda', methods=['GET', 'POST'])
def cadastro_merenda():
    print(" ==> CONTROLE ==>##################   CADASTRO _ MERENDA() ########################")
    contrDiario = request.form.get('contrDiario')
    print(" ==> CONTROLE ==>@@@@@@@@@@  CADASTRO_MERENDA() ==>", contrDiario)
    assentado = request.form.get('assentado')
    nomAlu = request.form.get('nome')
    codCtrl = request.form.get('codCtrl')

    matricula = request.form.get('matricula')
    nomAlu = request.form.get('nomAlu')
    ano = request.form.get('ano')
    mes = request.form.get('mes')
    semana = request.form.get('semana')
    dia = request.form.get('dia')
    # turno = request.form.get('turno')
    qtdTotal = request.form.get('qtdTotal')
    qtdEntregue = request.form.get('qtdEntregue')
    qtdTurnos = request.form.get('qtdTurnos')

    if request.form.get('qtdTurM') is None:
        qtdTurM = 0
    else:
        qtdTurM = request.form.get('qtdTurM')

    if request.form.get('qtdTurT') is None:
        qtdTurT = 0
    else:
        qtdTurT = request.form.get('qtdTurT')

    if request.form.get('qtdTurN') is None:
        qtdTurN = 0
    else:
        qtdTurN = request.form.get('qtdTurN')

   # qtdTurnos = qtdTurM + qtdTurT + qtdTurN
    qtdDisp = request.form.get('qtdDisp')

    # -----------------  PEGAR TURNO PELO HORARIO -------------------------
    turno = ' '
    turno, turnodes = obter_turno()

    print(" ==> CONTROLE ==>#######  CAD MERENDA -  TURNO ", turno)

    semana = request.form.get('semana')

    data_atual = datetime.now().date()
    dtMerenda = datetime.now().date()
    hrMerenda = datetime.now()

    # Formata a data e hora para strings no formato desejado
    dtMerenda_str = dtMerenda.strftime('%Y-%m-%d')  # Formato YYYY-MM-DD
    hrMerenda_str = hrMerenda.strftime('%H:%M:%S')  # Formato HH:MM:SS
    # print(" ==> CONTROLE ==>@@@@@***********  11111111111====>  CAD MERENDA HORA => ", hrMerenda_str)

    #  -------  ACESSAR TABELA CONTROLE TBMERCTRL E OBTER QTD TOTAL E QTD ENTREGUE -----------------------------------

    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('SELECT "qtdTotal", "qtdEntregue", "qtdTurM", "qtdTurT", "qtdTurN" FROM tbmerctrl '
                   'WHERE "codCtrl" = %s', (codCtrl,))
    regCtrl = cursor.fetchone()
    # print(" ==> CONTROLE ==>@@@@@***********  2222222 ====>  CAD MERENDA HORA => ", regCtrl)

    if regCtrl:

        #  -------  CALCULAR DIFERENCA ENTRE QTD TOTAL E QTD ENTREGUE => QTD DISPONIVEL-------------
        qtdTotal = regCtrl[0]
        qtdEntregue = regCtrl[1]

        # print(" ==> CONTROLE ==>@@@@@***********  33333 ====>  CAD MERENDA HORA => ", qtdTotal, " - ", qtdEntregue )

        qtdTurnos = (regCtrl[2] + regCtrl[3] + regCtrl[4])
        qtdDisp = int(qtdTotal) - (int(qtdEntregue) + int(qtdTurnos))

        # print(" ==> CONTROLE ==>@@@@@***********  444444 ====>  CAD MERENDA HORA => ", qtdDisp)

        # print(" ==> CONTROLE ==> @@@@@***********  55555  CALCULAR DISP = TOT - ENTR", qtdTotal, " - ", qtdEntregue, " = ", qtdDisp)

        cursor.close()
        conn.close()

    if qtdDisp > 0:
        try:

            conn = conectar_bd()
            cur = conn.cursor()

            #  -------  VERIFICAR SE JÁ EXISTE REGISTRO NA TABELA TBMERCTRL ------------
            # print(" ==> CONTROLE ==> @@@  # print XXXXXXXX 1111 nome ", nome, " matr =>", matricula, " codctrl ", codCtrl)
            cur.execute('SELECT * FROM tbmerenda WHERE "matricula" = %s AND "codCtrl" = %s', (matricula, codCtrl))

            # print(" ==> CONTROLE ==>  @@@  # print XXXXXXXX 2222 cur.fetchone ", cur.fetchone())
            if not cur.fetchone():

                cur.execute('INSERT INTO tbmerenda ("matricula", "codCtrl", "dtMerenda", "hrMerenda", '
                            '"turno", "semana", "dia")'
                            'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                            (matricula, codCtrl, dtMerenda_str, hrMerenda_str, turno, semana, dia))
                conn.commit()


                #  -------  DIMINUINDO MERENDA BANCO DE DADOS -----------------------------------

                cur.execute('UPDATE tbmerctrl SET "qtdEntregue" = "qtdEntregue" + 1 WHERE "codCtrl" = %s', (codCtrl,))
                conn.commit()
                # print(" ==> CONTROLE ==> ####>  4444 ENTREGANDO  ===> matricula ", matricula, " codCtrl ", codCtrl)
                cur.close()
                conn.close()

                qtdEntregue = qtdEntregue + 1

                qtdDisp = int(qtdTotal) - (int(qtdEntregue) + int(qtdTurnos))

                #  -------  RETORNADO PARA MARENDA.HTML -----------------------------------

                print(" ==> CONTROLE ==>$ MERENDA ENTREGUE ", nomAlu)

                session['mensagem'] = f" ( MERENDA ENTREGUE ! ) {nomAlu}  [ Matricula: {matricula} ]"

                return render_template('merendaQC.html', contrDiario=contrDiario, ano=ano, mes=mes, assentado=assentado,
                                       turno=turno, data_atual=data_atual, matricula=matricula,
                                       qtdTotal=qtdTotal, qtdDisp=qtdDisp, nomAlu=nomAlu, qtdEntregue=qtdEntregue,
                                       semana=semana, dia=dia, qtdTurnos=qtdTurnos)
            else:
                #  -------  assentado JA MERENDOU - NÃO INCLUI -----------------------------------
                qtdDisp = int(qtdTotal) - (int(qtdEntregue) + int(qtdTurnos))
                print(" ==> CONTROLE ==> 11111 JA MEREDNOU", nomAlu)
                session['mensagem'] = f" ( JÁ MERENDOU ! ) {nomAlu}  [ Matricula: {matricula} ]"
                return render_template('merendaQC.html', contrDiario=contrDiario, ano=ano, mes=mes, assentado=assentado,
                                       turno=turno, data_atual=data_atual, matricula=matricula,
                                       qtdTotal=qtdTotal, qtdDisp=qtdDisp, nomAlu=nomAlu, qtdEntregue=qtdEntregue,
                                       semana=semana, dia=dia, qtdTurnos=qtdTurnos)

        except  Exception as e:
                #  session['mensagem'] = f"Erro 020 ao entregar merenda: {str(e)}"
                print(" ==> CONTROLE ==> 22222 ERRO 087", nomAlu)
                session['mensagem'] = f" ( ERRO  087  ! ){nomAlu}  [ Matricula:{matricula} ]"
                return render_template('merendaQC.html', contrDiario=contrDiario, ano=ano, mes=mes, assentado=assentado,
                               turno=turno, data_atual=data_atual,
                               qtdTotal=qtdTotal, qtddisp=qtdDisp, nomAlu=nomAlu, matricula=matricula,
                               qtdEntregue=qtdEntregue, semana=semana, dia=dia, qtdTurnos=qtdTurnos)

    else:
        conn = conectar_bd()
        cur = conn.cursor()
        status = 2
        cur.execute('UPDATE tbmerctrl SET "status" = %s', (status,))
        conn.commit()
        session['mensagem'] = "TODAS MERENDAS JÁ FORAM ENTREGUES ! - CONTROLE FECHADO"

    #  -------  RETORNAR PARA PAGINA DE MERENDA RENDERIZANDO    -----------------------------------

    return render_template('merendaQC.html', contrDiario=contrDiario, ano=ano, mes=mes, assentado=assentado,
                           turno=turno, data_atual=data_atual,
                           qtdTotal=qtdTotal, qtddisp=qtdDisp, nomAlu=nomAlu, matricula=matricula,
                           qtdEntregue=qtdEntregue, semana=semana, dia=dia, qtdTurnos=qtdTurnos)


@app.route('/cadMerendaExced', methods=['GET', 'POST'])
def cadastro_merenda_exced():
    # print(" ==> CONTROLE ==>##################   CADASTRO _ MERENDA() ########################")
    contrDiario = request.form.get('contrDiario')
    # print(" ==> CONTROLE ==>@@@@@@@@@@  CADASTRO_MERENDA() ==>", contrDiario)
    codCtrl = request.form.get('codCtrl')
    matricula = request.form.get('matricula')
    ano = request.form.get('ano')
    mes = request.form.get('mes')
    semana = request.form.get('semana')
    dia = request.form.get('dia')
    turno = request.form.get('turno')
    qtdTotal = int(request.form.get('qtdTotal'))
    qtdEntregue = int(request.form.get('qtdEntregue'))
    qtdDisp = int(request.form.get('qtdDisp'))

    qtdTurM = int(request.form.get('qtdTurM'))
    qtdTurT = int(request.form.get('qtdTurT'))
    qtdTurN = int(request.form.get('qtdTurN'))

    # print(" ==> CONTROLE ==> m - t - n - ", qtdTurM, " - ", qtdTurT, " - ", qtdTurN)
    # print(" ==> CONTROLE ==> mi - ti - ni - ", request.form.get('qtdTurMInp'), " - ", request.form.get('qtdTurTInp'),
    #      " - ", request.form.get('qtdTurNInp'))

    if request.form.get('qtdTurMInp') is None:
        qtdTurMInp = 0
    else:
        qtdTurMInp = int(request.form.get('qtdTurMInp'))

    if request.form.get('qtdTurTInp') is None:
        qtdTurTInp = 0
    else:
        qtdTurTInp = int(request.form.get('qtdTurTInp'))

    if request.form.get('qtdTurNInp') is None:
        qtdTurNInp = 0
    else:
        qtdTurNInp = int(request.form.get('qtdTurNInp'))


    # -----------------  PEGAR TURNO PELO HORARIO -------------------------

    # turno, turnodes = obter_turno()

    # print(" ==> CONTROLE ==>#######  CAD MERENDA -  TURNO ", turno)

    semana = request.form.get('semana')

    data_atual = datetime.now().date()
    dtMerenda = datetime.now().date()
    hrMerenda = datetime.now()

    # Formata a data e hora para strings no formato desejado
    dtMerenda_str = dtMerenda.strftime('%Y-%m-%d')  # Formato YYYY-MM-DD
    hrMerenda_str = hrMerenda.strftime('%H:%M:%S')  # Formato HH:MM:SS
    # print(" ==> CONTROLE ==>@@@@@====>  CAD MERENDA HORA => ", hrMerenda_str)

    #  -------  ACESSAR TABELA CONTROLE TBMERCTRL E OBTER QTD TOTAL E QTD ENTREGUE -----------------------------------

    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('SELECT "qtdTotal", "qtdEntregue", "qtdTurM", "qtdTurT", "qtdTurN" '
                   'FROM tbmerctrl WHERE "codCtrl" = %s', (codCtrl,))
    regCtrl = cursor.fetchone()

    if regCtrl:

        #  -------  CALCULAR DIFERENCA ENTRE QTD TOTAL E QTD QTD-TOT-ENTREGUE => QTD DISPONIVEL-------------
        qtdTotal = int(regCtrl[0])
        qtdEntregue = int(regCtrl[1])
        qtdTurM = int(regCtrl[2])
        qtdTurT = int(regCtrl[3])
        qtdTurN = int(regCtrl[4])
        qtdTotalEntregue = int(qtdEntregue) + int(qtdTurM) + int(qtdTurT) + int(qtdTurN)

        qtdTotalEntregueInp = int(qtdTurMInp) + int(qtdTurTInp) + int(qtdTurNInp)

        qtdDisp = int(qtdTotal) - (int(qtdTotalEntregue) + int(qtdTotalEntregueInp))

        # print(" ==> CONTROLE ==> @@@@@@@@@@@@@@@@@ CALCULAR DISP = TOTAL - ENTRG", qtdTotalEntregue, " - ", qtdDisp)


    if qtdDisp > 0 and qtdEntregue > 0:
        try:
            conn = conectar_bd()
            cur = conn.cursor()

            #  -------  VERIFICAR SE JÁ EXISTE REGISTRO NA TABELA TBMERCTRL ------------
            matricula = 99999999999

            #  -------  ATUALIZANDO CONTROLE DE  MERENDA    -----------------------------------

            qtdTurMTo = int(qtdTurM) + int(qtdTurMInp)
            qtdTurTTo = int(qtdTurT) + int(qtdTurTInp)
            qtdTurNTo = int(qtdTurN) + int(qtdTurNInp)

            cur.execute('UPDATE tbmerctrl SET "qtdTurM" = %s, "qtdTurT" = %s, "qtdTurN" = %s '
                        'WHERE "codCtrl" = %s',
                        (qtdTurMTo, qtdTurTTo, qtdTurNTo, codCtrl))

            conn.commit()


            #  -------  RETORNADO PARA MEREXCEDENTE.HTML -----------------------------------

            session['mensagem'] = f" ( MERENDA EXCEDENTE CADASTRADA ! {codCtrl})"

            # Retornar para a página merendaQC.html renderizando-a novamente
            return render_template('merexcedente.html', contrDiario=contrDiario, ano=ano, mes=mes,
                                       turno=turno, data_atual=data_atual,
                                       qtdTotal=qtdTotal, qtddisp=qtdDisp,
                                       qtdEntregue=qtdEntregue, semana=semana, dia=dia, matricula=matricula,
                                       qtdTurM=qtdTurM, qtdTurT=qtdTurT, qtdTurN=qtdTurN)

        except Exception as e:
                session['mensagem'] = f"Erro 020 ao cadastrar merenda excedente: {str(e)}"

    else:
        if qtdDisp == 0:
            conn = conectar_bd()
            cur = conn.cursor()
            status = 2
            cur.execute('UPDATE tbmerctrl SET "status" = %s '
                        'WHERE "codCtrl" = %s',
                        (status, codCtrl))

            conn.commit()
            session['mensagem'] = "TODAS MERENDAS JÁ FORAM ENTREGUES ! - CONTROLE FECHADO"
        if qtdEntregue == 0:
            session['mensagem'] = "EXCEDENTE SOMENTE APÓS ENTREGA PARA ALUNOS !"


    #  -------  RETORNAR PARA PAGINA DE MERENDA RENDERIZANDO    -----------------------------------

    return render_template('merexcedente.html', contrDiario=contrDiario, ano=ano, mes=mes,
                           turno=turno, data_atual=data_atual,
                           qtdTotal=qtdTotal, qtddisp=qtdDisp,
                           qtdEntregue=qtdEntregue, semana=semana, dia=dia, matricula=matricula,
                           qtdTurM=qtdTurM, qtdTurT=qtdTurT, qtdTurN=qtdTurN)


@app.route('/dados_controle', methods=['POST'])
def dados_controle():
    # print ('######################   DADOS CONTROLE () ##########################')
    data_atual = datetime.now()  # Importe datetime no topo do seu arquivo
    conn = conectar_bd()
    # print('######################   DADOS CONTROLE () conn###########  ', conn)
    if conn:
        try:
            # print(" ==> CONTROLE ==> 2222 dados - contole() - controle.py")
            alimentos = obter_dados_alimento()
            usuarios = obter_dados_usuario()
            fornecedores = obter_dados_fornecedor()
            conn.close()
          # # print(f" 333 dados - contole() - controle.py", {alimentos}, " fornecedores ", {fornecedores})

            return render_template('controle.html', alimentos=alimentos, usuarios=usuarios, fornecedores=fornecedores,
                                   data_atual=data_atual)
        except Exception as e:
            session['mensagem'] = f" Erro 012 - ao Carregar Dados ! {str(e)}"
            return render_template('controle.html', mensagem=session['mensagem'])
        finally:

            conn.close()
    else:
        session['mensagem'] = " Erro 013 - ao conectar ao banco de dados !"
        return "Erro ao conectar ao banco de dados."


@app.route('/dados_merenda', methods=['POST'])
def dados_merenda(matricula):
    # print(" ==> CONTROLE ==>##################### DADOS MERENDA(matricula)   ############################### ", matricula)
    data_atual = datetime.now()  # Importe datetime no topo do seu arquivo
    # Obter a hora atual
    hora_atual = data_atual.time()
    ano_sistema = datetime.now().year
    mes_sistema = datetime.now().month
    dia_sistema = datetime.now().day
    codCtrl = str(ano_sistema) + str(mes_sistema).zfill(2) + str(dia_sistema).zfill(2)

    turno, turnodes = obter_turno()
    # print(" ==> CONTROLE ==>########  1111  DADOS _ MERENDA turno e matricula ======>", turno, " - ", matricula)
    contrDiario = obter_controle_diario(codCtrl)
    # print(" ==> CONTROLE ==>########  1111  DADOS _ MERENDA CONTRDIARIO======>", contrDiario)
    if contrDiario is not None:

        if contrDiario[9] == 1:            # CONTROLE DIÁRIO ABERTO
            codcontrole = contrDiario[4]
            ano = int(codcontrole[:4])
            mes = int(codcontrole[4:6])
            semana = contrDiario[15]
            diaSem = contrDiario[8]
            codAlim = contrDiario[0]
            qtdTotal = contrDiario[1]
            qtdEntregue = contrDiario[2]
            qtTurM = contrDiario[12]
            qtTurT = contrDiario[13]
            qtTurN = contrDiario[14]
            qtdTurnos = qtTurM + qtTurT + qtTurN

            qtdDisp = int(qtdTotal) - (int(qtdEntregue) + int(qtdTurnos))

           # busca alimento por codigo
            conn = conectar_bd()

            if conn:
               try:
                   cur = conn.cursor()
                   cur.execute('SELECT "nomAlim" FROM tbalimento WHERE "codAlim" = %s', (codAlim,))

                   alimento = cur.fetchone()

                   nomAlim = alimento[0]

                   if alimento is not None:
                       nomAlim = alimento[0]
                   else:
                       nomAlim ='alimento não cadastrado '


                   conn.close()

               except Exception as e:
                   session['mensagem'] = " Erro 015 -  obter_dados_alimento() !"
                   return render_template('mensagem.html', mensagem="==> Erro 015 -  obter_dados_alimento() !")
            else:
                session['mensagem'] = " Erro 017 - ACESSO A BANCO DE DADOS ! !"
                return render_template('mensagem.html', mensagem="==> BASE assentado - SEM PRIMEIRO assentado !")

            # OBTER 1o assentado DO TURNO -  obter_aluno()
            if matricula == '999':
                matricula = '001'

            # print(" ==> CONTROLE ==> @@@@@@ 11111  DADOS-MERENDA -> OBTER-assentado(turno, matricula) ==> ", turno, " - ", matricula)
            assentado = obter_aluno(turno=turno, matricula=matricula)
           #  chave_pesquisa = turno + matricula.zfill(3)
           #  codMer = chave_pesquisa
            # print(" ==> CONTROLE ==> @@@@@@ ....2222 DADOS-MERENDA -> OBTER-assentado -> OBTER-assentado(turno, matricula) ==> ", turno, " - ", matricula)

            if assentado is None:
               session['mensagem'] = " Erro 012 - BASE assentado - SEM PRIMEIRO assentado !"
               return render_template('mensagem.html', mensagem="==> BASE assentado SEM PRIMEIRO assentado !")

          #  matricula = request.form.get('dados_qrcode')

            nomAlu = assentado[0]
            bbb = assentado[1]

            # print( " @@@ # print  22222222222 CONTROLE DIARIO => ", contrDiario)

            return render_template('merendaQC.html', contrDiario=contrDiario, assentado=assentado, ano=ano, mes=mes,
                                data_atual=data_atual, semana=semana, diaSem=diaSem,nomAlim=nomAlim,
                                qtdTotal=qtdTotal, qtdEntregue=qtdEntregue, qtdDisp=qtdDisp,
                                turno=turno, turnodes=turnodes, matricula=matricula, nomAlu=nomAlu, qtdTurnos=qtdTurnos)
        else:
            session['mensagem'] = f"  CONTROLE DIÁRIO FECHADO ! {dia_sistema}/{mes_sistema}/{ano_sistema} "
            return render_template('mensagem.html', mensagem="==>  CONTROLE DIÁRIO FECHADO !")

    else:
        session['mensagem'] = f" ERRO 034 - CONTROLE NÃO CADASTRADO ! {dia_sistema}/{mes_sistema}/{ano_sistema} "
        return render_template('mensagem.html', mensagem="==> ERRO 014 - ao Carregar Dados Controle !")


@app.route('/dados_merenda_exced', methods=['POST'])
def dados_merenda_exced():
    # print(" ==> CONTROLE ==>##################### DADOS MERENDA EXCED   ############################### ")
    data_atual = datetime.now()  # Importe datetime no topo do seu arquivo
    # Obter a hora atual
    hora_atual = data_atual.time()
    ano_sistema = datetime.now().year
    mes_sistema = datetime.now().month
    dia_sistema = datetime.now().day
    codCtrl = str(ano_sistema) + str(mes_sistema).zfill(2) + str(dia_sistema).zfill(2)

    # print(" ==> CONTROLE ==>####### 11111 DADOS MERENDA obter_turno()  ==> ")
    turno, turnodes = obter_turno()
    # print(" ==> CONTROLE ==>####### 11111 DADOS MERENDA(matricula)  ==> ", turno, " - ", turnodes)

    contrDiario = obter_controle_diario(codCtrl)

    if contrDiario is not None:
        if contrDiario[9] == 1:            # CONTROLE DIÁRIO ABERTO
            codcontrole = contrDiario[4]
            ano = int(codcontrole[:4])
            mes = int(codcontrole[4:6])
            semana = contrDiario[15]
            diaSem = contrDiario[8]
            codAlim = contrDiario[0]
            qtdTotal = contrDiario[1]
            qtdEntregue = contrDiario[2]

            qtdTurM = contrDiario[12]
            qtdTurT = contrDiario[13]
            qtdTurN = contrDiario[14]

            # print(" ==> CONTROLE ==> @@@@ 1111  DADOS MERENDA-EXCED ", qtdTurM)
            qtdTotalEntreg = int(qtdEntregue) + int(qtdTurM) + int(qtdTurT) + int(qtdTurN)
            qtdDisp = int(qtdTotal) - int(qtdTotalEntreg)
            # print(" ==> CONTROLE ==> @@@@ 2222  DADOS MERENDA-EXCED ", qtdDisp)

           # busca alimento por codigo
            conn = conectar_bd()

            if conn:
               try:
                   cur = conn.cursor()
                   cur.execute('SELECT "nomAlim" FROM tbalimento WHERE "codAlim" = %s', (codAlim,))

                   alimento = cur.fetchone()

                   nomAlim = alimento[0]

                   if alimento is not None:
                       nomAlim = alimento[0]
                   else:
                       nomAlim ='alimento não cadastrado '

                   conn.close()
                   # print(" ==> CONTROLE ==> @@@@ 333  DADOS MERENDA-EXCED alimento cadastraso ", nomAlim)
               except Exception as e:
                   session['mensagem'] = " Erro 015 -  obter_dados_alimento() !"
                   return render_template('mensagem.html', mensagem="==> Erro 015 -  obter_dados_alimento() !")
            else:
                session['mensagem'] = " Erro 017 - ACESSO A BANCO DE DADOS ! !"
                return render_template('mensagem.html', mensagem="==> BASE assentado SEM PRIMEIRO assentado !")

            matricula = turno + '999'

            return render_template('merexcedente.html', contrDiario=contrDiario, ano=ano, mes=mes,
                                data_atual=data_atual, semana=semana, diaSem=diaSem,nomAlim=nomAlim,
                                qtdTotal=qtdTotal, qtdEntregue=qtdEntregue, qtdDisp=qtdDisp,
                                turno=turno, matricula=matricula, qtdTurM=qtdTurM, qtdTurT=qtdTurT, qtdTurN=qtdTurN)


        else:
            session['mensagem'] = f"  CONTROLE DIÁRIO FECHADO ! {dia_sistema}/{mes_sistema}/{ano_sistema} "
            return render_template('mensagem.html', mensagem="==>  CONTROLE DIÁRIO FECHADO !")

    else:
        session['mensagem'] = f" ERRO 014 - CONTROLE NÃO CADASTRADO !"
        return render_template('mensagem.html', mensagem="==> ERRO 014 - ao Carregar Dados Controle !")


@app.route('/obter_turno', methods=['GET', 'POST'])
def obter_turno():
    # -----------------  PEGAR TURNO PELO HORARIO -------

    data_atual = datetime.now()
    hora_atual = data_atual.time()

    if time(6, 0) <= hora_atual < time(15, 50):
       turno = 'M'
       turnodes = 'Manhã'
    elif time(15, 50) <= hora_atual < time(19, 0):
       turno = 'T'
       turnodes = 'Tarde'
    else:
       turno = 'N'
       turnodes = 'Noite'

    # print(" ==> CONTROLE ==> 11111 ====>>>>>>>>>>>  OBTER TURNO ", turno, " - " ,  turnodes)

    return turno, turnodes


@app.route('/obter_aluno', methods=['GET','POST'])
def obter_aluno(turno, matricula):
    # print(" ==> CONTROLE ==>######################## OBTER-assentado(turno,matricula) #################  ", turno," - ", matricula)

    # matricula = request.form.get('matricula')
   # turno = request.form.get('turno')
    # print(" ==> CONTROLE ==>@@ 111 porraaaaa.... OBTER-assentado  turno=> ", turno, " numero ", matricula)

    assentado = obter_dados_aluno_cod_merenda(matricula, turno)
    # print(" ==> CONTROLE ==>@@ 333  porraaaaa PESQUISAR-assentado (SIGMA.py) - matricula=> e turno ", assentado,
        #  " matricula => ", matricula, turno)

    session['mensagem'] = "  "
    if assentado is not None:
        print(" ==> CONTROLE ==> @@ 666  OBTER-assentado (SIGMA_OLD.py) ==>  ", assentado[0])
        return assentado
    else:
        if matricula != '001':
            session['mensagem'] = f"  CÓDIGO DE assentado NÃO CADASTRADO ........! {matricula} "
            return render_template('mensagem.html', mensagem="==> CÓDIGO DE assentado NÃO CADASTRADO")
        else:
           session['mensagem'] = "   "
           return render_template('mensagem.html', mensagem=" ")


@app.route('/obter_dados_alimento', methods=['POST'])
def obter_dados_alimento():
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT  * FROM tbalimento order by "nomAlim"')
            alimentos = cur.fetchall()
            if alimentos is not None:
                conn.close()
                return alimentos
            else:
                return None
        except Exception as e:
            session['mensagem'] = " Erro 015 -  obter_dados_alimento() !"
            return None
    else:
        return None

@app.route('/obter_dados_curso', methods=['POST'])
def obter_dados_curso():
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT  * FROM tbcurso order by "nomCur"')
            cursos = cur.fetchall()
            if cursos is not None:
                conn.close()
                return cursos
            else:
                return None
        except Exception as e:
            session['mensagem'] = " Erro 015 -  obter_dados_cursos() !"
            return None
    else:
        return None

@app.route('/obter_nome_curso', methods=['POST'])
def obter_dados_parmto_curso(curso):
    conn = conectar_bd()
    if conn:
        try:
            print(" ==> CONTROLE ==>55555555555555 obter parmto curso ", curso)
            cur = conn.cursor()
            cur.execute('SELECT "nomCur", "codCurso" FROM tbcurso WHERE "idCurso" = %s', (curso,))
            print(" ==> CONTROLE ==>5555555555  1111111115 obter parmto curso ", curso)
            curso = cur.fetchone()
            nomCur, codCurso = curso
            print(" ==> CONTROLE ==>55555555555555 2222 obter parmto curso ", nomCur)
            if curso is not None:
                conn.close()
                return nomCur, codCurso
            else:
                return None
        except Exception as e:
            session['mensagem'] = " Erro 015 -  obter_dados_parmto_curso() !"
            return None
    else:
        return None



@app.route('/obter_controle_diario', methods=['POST'])
def obter_controle_diario(codCtrl):
    print(" ==> CONTROLE ==>######################## OBTER-CONTROLE- DIARIO(codcrtl) ########################  ", codCtrl)

    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            # Obtém a data atual
            data_atual = datetime.now().date()
            # Busca o registro de controle diário para a data atual
            print(" ==> CONTROLE ==>#### 11111 OBTER-CONTREOLE-DIARIO codCtrl  =>", codCtrl)
            cur.execute('SELECT * FROM tbmerctrl WHERE "codCtrl" = %s', (codCtrl,))
            contrDiario = cur.fetchone()
            print(" ==> CONTROLE ==>#### 222222   OBTER-CONTRol-DIARIO contrDiario ======>", contrDiario)
            if contrDiario is not None:
                print(" ==> CONTROLE ==>#### 33333   OBTER-CONTRol-DIARIO contrDiario ======>", contrDiario)
                # Verifica o status do controle diário

                print(" ==> CONTROLE ==>#### 4444   OBTER-CONTRol-DIARIO contrDiario[9] ======>", contrDiario[9] )
                if contrDiario[9] == 1:
                    conn.close()
                    return contrDiario
                else:
                    conn.close()
                    session['mensagem'] = " Erro 025 - ==> => CONTROLE FECHADO !"
            else:
                print(" ==> CONTROLE ==>#### 5555   OBTER-CONTRol-DIARIO contrDiario ======>", contrDiario)
                conn.close()
                session['mensagem'] = " Erro 015 - ==> CONTROLE DIÁRIO NÃO CADASTRADO !"

        except Exception as e:
            session['mensagem'] = " Erro 022 - ==> CONTROLE DIÁRIO NÃO CADASTRADO !"

    else:
        session['mensagem'] = " Erro 043 - ==> CONTROLE DIÁRIO NÃO CADASTRADO !"


def obter_dados_aluno_cod_merenda(matricula, turno):
    print(" ==> CONTROLE ==>###########  OBTER DADOS assentado CAD MERENDA(matricula) ############  ", matricula)

    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()

            if matricula == '001':
                cur.execute('SELECT "matricula", "nome", "foto" FROM tbassentado WHERE turno = %s ORDER BY "nome" '
                            'LIMIT 1', (turno,))
            else:

               print(" ==> CONTROLE ==> @@@  PRINT 77777  matricula , turno ==> ", matricula, " - turno " , turno)

               cur.execute('SELECT "nome", "foto" FROM tbassentado WHERE "matricula" = %s and turno = %s', (matricula, turno))

            assentado = cur.fetchone()
            nome, foto = assentado
            if assentado:
                print(" ==> CONTROLE ==>@@@ PRINT 888888   ", nome)
                aluno_corrigido = list(assentado)
                aluno_corrigido[1] = url_for('static', filename='img/' + foto)  # Corrigir o caminho da imagem
                print(" ==> CONTROLE ==>@@@ PRINT 999999...   ", aluno_corrigido)
                conn.close()
                return aluno_corrigido
            else:
                session['mensagem'] = "ERRO 005- assentado NÃO CADASTRADO ! "
                print(" ==> CONTROLE ==> @@@ PRINT 10  10  10  assentado NAO CADASTRADO ! obter_dados_aluno_cod_merenda()  assentado ", assentado)
                return None
        except Exception as e:
               session['mensagem'] = "ERRO 005- ACESSO BANCO DE DADOS !"
               return None
    else:
        session['mensagem'] = "ERRO 08- SEM CONEXÃO BANCO DE DADOS !"
        return None


@app.route('/obter_dados_busca_controle', methods=['POST'])
def obter_dados_busca_controle(codCtrl):
    print(" ==> CONTROLE ==>########################  OBTER DADOS BUSCA CONTROLE(codCtrl)  ################  ", codCtrl)

    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT  * FROM tbmerctrl WHERE "codCtrl" = %s', (codCtrl,))
            alimentos = cur.fetchall()
            if alimentos is not None:
                session['mensagem'] = "ALIMENTO NÃO ENCONTRADO !"
                conn.close()
                return alimentos
            else:
                return None
        except Exception as e:
            session['mensagem'] = " Erro 017 -  ao obter dados do alimento !"
            return None
    else:
        return None


@app.route('/obter_dados_fornecedor', methods=['POST'])
def obter_dados_fornecedor():
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT  * FROM tbfornec order by "nomFornec"')
            fornecedores = cur.fetchall()
            if fornecedores is not None:
                conn.close()
                return fornecedores
            else:
                return None
        except Exception as e:
            session['mensagem'] = " Erro 018 -  dados do fornecedor !"
            return None
    else:
        return None


@app.route('/obter_dados_usuario', methods=['POST'])
def obter_dados_usuario():
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT  * FROM tbusuario order by "nome"')
            usuarios = cur.fetchall()
            if usuarios is not None:
                conn.close()
                return usuarios
            else:
                return None
        except Exception as e:
            session['mensagem'] = f"ERRO 007 - ACESSO BANCO DE DADOS - USUÁRIO: {usuarios},"
            return None
    else:
        return None


@app.route('/dados_whatsapp', methods=['POST'])
def dados_whatsapp():
    print('######################   DADOS whatsapp () ##########################')
    data_atual = datetime.now()  # Importe datetime no topo do seu arquivo
    conn = conectar_bd()
    print('######################   DADOS WHATSAPP () conn###########  ', conn)
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT "nome", "foto", "noWhatsapp"  FROM tbassentado ORDER BY "nome" ')
            alunos = cur.fetchall()
            conn.close()
            return render_template('enviarWhatsapp.html', alunos=alunos)
        except Exception as e:
            session['mensagem'] = f" Erro 018 - ao Carregar Dados Whatsapp ! {str(e)}"
            return render_template('enviarWhatsapp.html', mensagem=session['mensagem'])
        finally:

            conn.close()
    else:
        session['mensagem'] = " Erro 013 - ao conectar ao banco de dados !"
        return "Erro ao conectar ao banco de dados."

@app.route('/env_whatsapp', methods=['POST', 'GET'])
def enviar_whatsapp():
    noWhatsapp = request.form.get('noWhatsapp')

    print(" ==> CONTROLE ==>################ ENVIAR WHATSAPP ###########################  ")

    nome = request.form['nome']
    mensagem = request.form['mensagem']

    # Definir o caminho para o executável do Chrome WebDriver
    chromedriver_path = '../intranet/chromedriver-win64/chromedriver.exe'

    # Definir o tempo limite de conexão
    timeout_value = 90  # Definir o tempo limite em segundos

    # Inicializar o navegador Chrome com as opções configuradas
    navegador = webdriver.Chrome(executable_path=chromedriver_path)
    navegador.set_page_load_timeout(timeout_value)

    # Abrir o WhatsApp Web
    navegador.get("https://web.whatsapp.com/")


    #while len(navegador.find_elements_by_class_name("side")) < 1:
    #    time.sleep(1)

    texto = urllib.parse.quote(f'{mensagem}')
    print(f'Pessoa => {nome} - numero => {noWhatsapp} - textoUrl => {texto}')
    # link = f"https://wa.me/{numero}?text={texto}"
    texto = f"Oi {nome} - {texto}"
    link = f"https://web.whatsapp.com/send?phone={noWhatsapp}&text={texto}"
    navegador.get(link)

      #  while len(navegador.find_elements_by_class_name("side")) < 1:
      #      time.sleep(1)
        # Esperar até que o elemento com a classe "side" esteja presente na página

    timeout_maximo = 90
    try:
           elemento_side = WebDriverWait(navegador, timeout_maximo).until(
           EC.presence_of_element_located((By.CLASS_NAME, "side")))
           # navegador abaixo é para dar enter
           navegador.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div/p').send_keys(Keys.ENTER)

    except TimeoutException:
           print(f"Tempo limite atingido. O elemento 'side' não foi encontrado para o contato {pessoa}.")
           # Lidar com a situação em que o elemento não foi encontrado dentro do tempo limite


    # Fechar o navegador ao final
    navegador.quit()

    return dados_whatsapp()


@app.route('/AtlzMatricula', methods=['POST'])
def atualizar_matricula():
    matricula = request.form['matricula']

    return render_template('merendaQC.html', matricula=matricula)

@app.route('/cartaoQRalu', methods=['POST'])
def cartaoQR_old():
            conn = conectar_bd()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT matricula, nome FROM tbassentado ORDER BY nome LIMIT 5")
                    alunos = cur.fetchall()
                    alunos_formatados = []
                    for assentado in alunos:
                        matricula, nome = assentado  # Desempacotando os dados do assentado
                        linha1 = "!_______________!________________________________!_____________________!"
                        linha2 = f" !   IFPA       ! {matricula} - {nome:<20}!"
                        linha3 = f"!_______________!________________________________!_____________________!"
                        caminho_qrcode = url_for('static', filename=f'img/QR{matricula}.jpg')
                        alunos_formatados.extend([linha1, linha2, linha3])
                    conn.close()
                    return alunos_formatados
                except Exception as e:
                    app.logger.error("Erro ao obter dados dos alunos: %s", e)
                    return []
            else:
                return []


from flask import render_template

@app.route('/cartaoQRAlun', methods=['GET', 'POST'])
def cartaoQR():

    if request.method == 'POST':
        session['mensagem'] = ""
        return cartaoQR()
    else:
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT matricula, nome, turno FROM tbassentado ORDER BY nome LIMIT 5")
                alunos = cur.fetchall()
                alunos_formatados = []
                for assentado in alunos:
                    matricula, nome, turno = assentado
                    caminho_qrcode = url_for('static', filename=f'img/QR{matricula}.jpg')
                    alunos_formatados.append({
                        'matricula': matricula,
                        'nome': nome,
                        'qrcode': caminho_qrcode,
                        'turno': turno,
                    })
                conn.close()
                mes_atual = datetime.now().strftime('%B').upper()
                return render_template('cartaoQR.html', alunos=alunos_formatados, mes_atual=mes_atual)
            except Exception as e:
                app.logger.error("Erro ao obter dados dos alunos: %s", e)
                return "Erro ao obter dados dos alunos"
        else:
            return "Erro de conexão com o banco de dados"

@app.route('/gerar_pdf', methods=['GET'])
def gerar_pdf_Cartao():

   if request.method == 'POST':
      session['mensagem'] = ""
      return cartaoQR()
   else:
      conn = conectar_bd()
      if conn:
         try:
            cur = conn.cursor()
            cur.execute("SELECT matricula, nome FROM tbassentado ORDER BY nome LIMIT 5")
            alunos = cur.fetchall()
            alunos_formatados = []
            for assentado in alunos:
                matricula, nome = assentado
                caminho_qrcode = url_for('static', filename=f'img/QR{matricula}.jpg')
                alunos_formatados.append({'matricula': matricula, 'nome': nome, 'qrcode': caminho_qrcode})


            conn.close()
            mes_atual = datetime.now().strftime('%B').upper()
            html = render_template('cartaoQR.html', alunos=alunos_formatados, mes_atual=mes_atual)
          #  pdf = HTML(string=html).write_pdf()

          #  response = make_response(pdf)
          #  response.headers['Content-Type'] = 'application/pdf'
          #  response.headers['Content-Disposition'] = 'inline; filename=cartao_Assentado.pdf'

            return " ===> RETORNO"

         except Exception as e:
            app.logger.error("Erro ao obter dados dos alunos: %s", e)
            return "Erro ao obter dados dos alunos"

@app.route('/dados_cartao', methods=['GET', 'POST'])
def dados_cartao(matricula):
    print('######################   DADOS CARTAO MATR () ######################## ', matricula)
    data_atual = datetime.now()  # Importe datetime no topo do seu arquivo
    conn = conectar_bd()
    print('######################   DADOS CARTAO () conn###########  ', conn)
    if conn:
        try:
            print(" ==> CONTROLE ==> =====> 9999999911111111  matricula nome ", matricula)
            cur = conn.cursor()
            cur.execute('SELECT "nome", "matricula", "qrcode", "foto", "turno", "idCurso" ' +
                        ' FROM tbassentado  WHERE "matricula" = %s', (matricula,))

            print(" ==> CONTROLE ==> =====> 9999999999 2222222  matricula nome ", matricula)
            assentado = cur.fetchone()

            if assentado:
                nome, matricula, qrcode, foto, turno, idCurso = assentado
                print(" ==> CONTROLE ==> =====> 9999999999 3333 Nome do assentado:", nome)
            else:
                print(" ==> CONTROLE ==>assentado não encontrado.")
                session['mensagem'] = f" Erro 019 - Discente nao encontrado "
                return render_template('cartaoAssent.html', mensagem=session['mensagem'])

            qrcode = url_for('static', filename=f'img/QR{matricula}.jpg')
            foto = url_for('static', filename=f'img/{foto}.jpg')
            conn.close()
            mes_atual = datetime.now().strftime('%B').upper()
          #  html = render_template('emitirCartaoAlu.html', assentado=assentado, mes_atual=mes_atual, qrcode=qrcode, foto=foto)

            nomCur, codCurso = obter_dados_parmto_curso(idCurso)

            conn.close()
            return render_template('emitirCartaoAlu.html',
                                   matricula=matricula,
                                   nome=nome,
                                   qrcode=qrcode,
                                   mes_atual=mes_atual,
                                   codCurso=codCurso,
                                   nomCur=nomCur,
                                   turno=turno)

        except Exception as e:
            session['mensagem'] = f" Erro 019 - ao Carregar Dados cartao ! {str(e)}"
            return render_template('emitirCartaoAlu.html', mensagem=session['mensagem'])
        finally:

            conn.close()
    else:
        session['mensagem'] = " Erro 013 - ao conectar ao banco de dados !"
        return "Erro ao conectar ao banco de dados."


@app.route('/dados_cartao_turno', methods=['GET', 'POST'])
def dados_cartao_turno(turno):

    print(" ==> CONTROLE ==>@@@@@@@@@  1111111   dados_cartao_turno(turno):", turno)
    if request.method == 'POST':
        session['mensagem'] = ""
        print(" ==> CONTROLE ==>@@@@@@@@@  222222   dados_cartao_curso(curso):", turno)
        conn = conectar_bd()
        if conn:
            try:
                print(" ==> CONTROLE ==>@@@@@@@@@  333333   dados_cartao_turno(turno):", turno)
                cur = conn.cursor()
                cur.execute('SELECT "nome", "matricula", "qrcode", "foto", "idCurso" ' +
                            ' FROM tbassentado  WHERE "turno" = %s ORDER BY "nome" ', (turno,))

                alunos = cur.fetchall()
                alunos_formatados = []
                for assentado in alunos:
                    nome, matricula, qrcode, foto, idCurso = assentado

                   # busca codigo e nome do curso
                   # nomCur, codCurso = obter_dados_parmto_curso(idCurso)

                    caminho_qrcode = url_for('static', filename=f'img/QR{matricula}.jpg')
                    alunos_formatados.append({
                        'matricula': matricula,
                        'nome': nome,
                        'qrcode': caminho_qrcode,
                        'turno': turno,
                    })
                conn.close()
                mes_atual = datetime.now().strftime('%B').upper()

                print(" ==> CONTROLE ==>@@@@@@@@@  44444   dados_cartao_turno(turno):", turno)
                return render_template('emitirCartaoTurno.html', alunos=alunos_formatados,
                                            mes_atual=mes_atual)
              #  return render_template('emitirCartao.html', alunos=alunos_formatados,
              #                         nomCur=nomCur, codCurso=codCurso,
              #                         mes_atual=mes_atual)

            except Exception as e:
                app.logger.error("Erro ao obter dados dos alunos: %s", e)
                return "Erro ao obter dados dos alunos"
        else:
            return "Erro de conexão com o banco de dados"


@app.route('/dados_cartao_curso', methods=['GET', 'POST'])
def dados_cartao_curso(curso):
    print(" ==> CONTROLE ==>@@@@@@@@@##########  1111111   dados_cartao_curso(curso):", curso)
    if request.method == 'POST':
        session['mensagem'] = ""
        print(" ==> CONTROLE ==>@@@@@@@@@  222222   dados_cartao_curso(curso):", curso)

        conn = conectar_bd()
        if conn:
            try:
                print(" ==> CONTROLE ==>@@@@@@@@@  333333   dados_cartao_curso:", curso)
                cur = conn.cursor()
                cur.execute('SELECT "nome", "matricula", "qrcode", "foto", "turno" ' +
                            ' FROM tbassentado  WHERE "idCurso" = %s', (curso,))
                print(" ==> CONTROLE ==>@@@@@@@@@  333333 -  000000  dados_cartao_curso:", curso)
                nomCur, codCurso = obter_dados_parmto_curso(curso)

                print(" ==> CONTROLE ==>@@@@@@@@@  333333 -  111111  dados_cartao_curso:", curso)
                alunos = cur.fetchall()
                alunos_formatados = []
                for assentado in alunos:
                    nome, matricula, qrcode, foto, turno = assentado
                    caminho_qrcode = url_for('static', filename=f'img/QR{matricula}.jpg')
                    foto = url_for('static', filename=f'img/{foto}.jpg')
                    alunos_formatados.append({
                        'matricula': matricula,
                        'nome': nome,
                        'qrcode': caminho_qrcode,
                        'foto': foto,
                        'turno': turno,
                       })
                conn.close()
                mes_atual = datetime.now().strftime('%B').upper()

                print(" ==> CONTROLE ==>@@@@@@@@@  44444   dados_cartao_turno(turno):", nomCur)
                return render_template('emitirCartao.html', alunos=alunos_formatados,
                                       nomCur=nomCur, codCurso=codCurso,
                                       mes_atual=mes_atual)
            except Exception as e:
                app.logger.error("Erro ao obter dados dos "
                                 "alunos: %s", e)
                return "Erro ao obter dados dos alunos"

        else:
            return "Erro de conexão com o banco de dados"


def cartao_Assentado():
    return render_template('cartaoAssent.html')


def cartao_turno():
    return render_template('cartaoTurno.html')


def cartao_curso():

    cursos = obter_dados_curso()
    return render_template('cartaoCurso.html', cursos=cursos)


# aplicação Flask será acessível a partir de outros dispositivos na mesma rede, como o seu celular.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True )
