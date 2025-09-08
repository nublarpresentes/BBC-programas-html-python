import cv2

# Carrega a imagem contendo o QR code
imagem_qrcode = cv2.imread("static/img/QR20182043271.jpg")

# Inicializa um leitor QR code
leitor_qrcode = cv2.QRCodeDetector()

# Detecta e decodifica o QR code na imagem
retval, pontos_qrcode, qr_code_info = leitor_qrcode.detectAndDecode(imagem_qrcode)

# Verifica se um QR code foi detectado
if retval:
    # Imprime o conteúdo do QR code
    print("Conteúdo do QR code:", qr_code_info)
else:
    print("Nenhum QR code foi detectado na imagem.")
