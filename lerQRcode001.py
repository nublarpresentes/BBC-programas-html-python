import cv2

# Ler a imagem do QR Code
img = cv2.imread('static/img/QR20202203009.jpg')

# Inicializar o detector QR Code
detector = cv2.QRCodeDetector()

# Detectar e decodificar o QR Code
data, bbox, _ = detector.detectAndDecode(img)

# Verificar se a detecção foi bem-sucedida
if bbox is not None:
    print("Conteúdo do QR code:", data)
else:
    print("Nenhum QR code encontrado.")
