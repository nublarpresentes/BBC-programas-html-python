from selenium import webdriver
from selenium.webdriver.common.keys import keys

import pandas as pd
contatos = pd.read_html("templates/comentario.html")
display(contatos)
import time

navegador = webdriver.chrome()
navegador.get("https://web.whatsapp.com")

while len(navegador.find_elements_by_id("side")) < 1:
    time.sleep(1)

contatos = [  { "Pessoa": "Ana",  "Numero": 25,  "Mensagem": "olá" },
               { "Pessoa": "Pedro", "Numero": 35, "Mensagem": "oi" },
               { "Pessoa": "Maria", "Numero": 15, "Mensagem": "valew" },
               { "Pessoa": "José", "Numero": 32, "Mensagem": "sucesso !" } ]



#  ja estamos com o login feito no whastapp

for i, mensagem in enumerate(contatos['Mensagem']):
    pessoa = contatos.loc[i, 'Pessoa']
    numero = contatos.loc[i, 'Numero']
    texto = urllib.parse.quote(f'Oi {Pessoa} ! {mensagem})
    link = "https://we.whatsapp.com/send?phone={numero}&text={texto}"
    navegador.get(link)
    while len(navegador.find_elements_by_id("side")) < 1:
           time.sleep(1)