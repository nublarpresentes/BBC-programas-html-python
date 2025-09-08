from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Configurando as opções do Chrome para simular um dispositivo móvel
mobile_emulation = {
    "deviceName": "iPhone X"
}
chrome_options = Options()
chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

# Inicializando o driver do Chrome com as opções configuradas
driver = webdriver.Chrome(options=chrome_options)

# Navegando para uma página da web no celular
driver.get("https://www.mercadolivre.com.br")

# Extraindo o texto de um elemento na página
element = driver.find_element_by_xpath("//h1")
print("Texto extraído do elemento:", element.text)

# Fechando o navegador
# driver.quit()
