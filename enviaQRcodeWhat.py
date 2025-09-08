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
navegador.get("https://web.whatsapp.com/")

contatos = [
    {"Pessoa": "Tamiel",  "Numero": 5591980800516,  "Mensagem": "olá teste"},
    {"Pessoa": "Paulo Talharim", "Numero": 5591982528434, "Mensagem": "vai tu talharim"},
]

#while len(navegador.find_elements_by_class_name("side")) < 1:
#    time.sleep(1)

for i, mensagem in enumerate(contatos):
    pessoa = contatos[i]['Pessoa']
    numero = contatos[i]['Numero']
    texto = urllib.parse.quote(f'{contatos[i]["Mensagem"]}')
    print(f'Pessoa => {pessoa} - numero => {numero} - textoUrl => {texto}')
    # link = f"https://wa.me/{numero}?text={texto}"
    texto = f"Oi {pessoa} - {texto}"
    link = f"https://web.whatsapp.com/send?phone={numero}&text={texto}"
    navegador.get(link)

  #  while len(navegador.find_elements_by_class_name("side")) < 1:
  #      time.sleep(1)
    # Esperar até que o elemento com a classe "side" esteja presente na página

    timeout_maximo = 90
    try:
      elemento_side = WebDriverWait(navegador, timeout_maximo).until(
            EC.presence_of_element_located((By.CLASS_NAME, "side")))

      navegador.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div/p').send_keys(Keys.ENTER)

    except TimeoutException:
        print(f"Tempo limite atingido. O elemento 'side' não foi encontrado para o contato {pessoa}.")
        # Lidar com a situação em que o elemento não foi encontrado dentro do tempo limite
        continue



# Fechar o navegador ao final
navegador.quit()
