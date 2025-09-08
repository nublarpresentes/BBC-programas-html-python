from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # Adicionado
from selenium.webdriver.common.by import By

import time
import pandas as pd
import urllib

# Definir o caminho para o executável do Chrome WebDriver
chromedriver_path = '../intranet/chromedriver-win64/chromedriver.exe'

# Definir o tempo limite de conexão
timeout_value = 90  # Definir o tempo limite em segundos

# Inicializar o navegador Chrome com as opções configuradas
navegador = webdriver.Chrome(executable_path=chromedriver_path)
navegador.set_page_load_timeout(timeout_value)

# Abrir o WhatsApp Web
navegador.get("https://localhost:5000/merenda3")

#while len(navegador.find_elements_by_class_name("side")) < 1:
#    time.sleep(1)

for i, mensagem in enumerate(contatos):
    link = f"https://localhost:5000/merenda3"
    navegador.get(link)
    timeout_maximo = 90
    try:
      elemento_side = WebDriverWait(navegador, timeout_maximo).until(
            EC.presence_of_element_located((By.CLASS_NAME, "side")))

      navegador.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div/p').send_keys(Keys.ENTER)

   #   campo_matricula = WebDriverWait(driver, tempo_espera).until(
   #          EC.presence_of_element_located((By.ID, 'matricula'))#


    except TimeoutException:
        print(f"Tempo limite atingido. O elemento 'side' não foi encontrado para o contato {pessoa}.")
        # Lidar com a situação em que o elemento não foi encontrado dentro do tempo limite
        continue



# Fechar o navegador ao final
navegador.quit()




def enviar_matricula(matricula):
    driver.get('http://192.168.0.7:5000/merenda3')
    campo_matricula = driver.find_element_by_id('matricula')
    campo_matricula.send_keys(matricula)
    botao_enviar = driver.find_element_by_xpath('//input[@type="submit"]')
    botao_enviar.click()


# Rota para receber a matrícula
@app.route('/receber_matricula', methods=['POST'])
def testeCnxQR():

    return render_template('testeCnxQR.html')


@app.route('/enviar_matricula', methods=['POST', 'GET'])
def testar():
    matricula = request.args.get("matricula")
    url = 'http://localhost:5000/receber_matricula'
    data = {'matricula': matricula}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print('Matrícula enviada com sucesso')
    else:
        print('Erro ao enviar matrícula')


def obter_matricula(matricula):
    driver.get('http://192.168.0.7:5000/merenda')
    campo_matricula = driver.find_element_by_id('matricula')
    campo_matricula.send_keys(matricula)
    botao_enviar = driver.find_element_by_xpath('//input[@type="submit"]')
    botao_enviar.click()