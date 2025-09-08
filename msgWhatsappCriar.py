import pandas as pd
import urllib.parse
import time

# Supondo que você já tenha uma lista de contatos
contatos = [
    {"Pessoa": "Ana",  "Numero": 25,  "Mensagem": "olá"},
    {"Pessoa": "Pedro", "Numero": 35, "Mensagem": "oi"},
    {"Pessoa": "Maria", "Numero": 15, "Mensagem": "valew"},
    {"Pessoa": "José", "Numero": 32, "Mensagem": "sucesso !"}
]

# Inicialize listas vazias para cada coluna
pessoas = []
numeros = []
mensagens = []

# Execute o loop fornecido
for i, mensagem in enumerate(contatos):
    pessoa = contatos[i]['Pessoa']
    numero = contatos[i]['Numero']
    texto = urllib.parse.quote(f'Oi {pessoa} ! {contatos[i]["Mensagem"]}')
    print(f'Pessoa => {pessoa} - numero => {numero} - textoUrl => {texto}')
    link = f"https://wa.me/{numero}?text={texto}"


    # Simule o comportamento esperado, mas isso pode não ser necessário
    time.sleep(1)

# Crie o DataFrame com as listas de dados
df = pd.DataFrame({
    'Pessoa': pessoas,
    'Número': numeros,
    'Mensagem': mensagens
})
print("*"*50)
# Exibir o DataFrame
print(df)
# --------------------------------------------

print("*"*50)
import pandas as pd

data = {'Nome': ['Ana', 'Pedro', 'Maria'],
        'Idade': [25, 30, 35],
        'Cidade': ['Belém', 'Marudá', 'Mosqueiro']}

df = pd.DataFrame(data)
print(df)


#  2 ) A partir de uma lista de listas:


print("*"*50)
import pandas as pd

data = [['Ana', 25, 'São Paulo'],
        ['Pedro', 30, 'Rio de Janeiro'],
        ['Maria', 35, 'Belo Horizonte']]

df = pd.DataFrame(data, columns=['Nome', 'Idade', 'Cidade'])
print(df)

