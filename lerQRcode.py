from zxing import BarCodeReader
from PIL import Image

# Caminho da imagem do QR Code
caminho_imagem_qrcode = "static/img/QR20202203009.jpg"

# Criando uma instância do leitor de código de barras
leitor_qrcode = BarCodeReader()

# Ler o conteúdo do QR Code na imagem especificada
conteudo_qrcode = leitor_qrcode.decode(Image.open(caminho_imagem_qrcode))

# Verificar se o QR Code foi decodificado com sucesso
if conteudo_qrcode:
    # Exibir o conteúdo decodificado
    print("Conteúdo do QR Code:", conteudo_qrcode[0].data.decode("utf-8"))
else:
    print("Nenhum QR Code encontrado ou não foi possível decodificar.")
