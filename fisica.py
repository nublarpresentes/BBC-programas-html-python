def calcular_aceleracao(massa, forca_aplicada, forca_atrito):

    # Calcula força resultante
    forca_resultante = forca_aplicada - forca_atrito

    # Calcula aceleração

    aceleracao = forca_resultante / massa
    return forca_resultante, aceleracao

# Exemplo de uso:
massa = 10      # kg
forca_aplicada = 60  # N
forca_atrito = 20    # N

F_res, a = calcular_aceleracao(massa, forca_aplicada, forca_atrito)

print(f"Força resultante: {F_res} N")
print(f"Aceleração: {a:.2f} m/s²")