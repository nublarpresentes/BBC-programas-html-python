import smtplib
from random import random

from email_mod.mime.text import MIMEText



import bcrypt

import os
from flask.helpers import send_file


from email_mod import enviar_email

import os
from flask.helpers import send_file

import os
from flask.helpers import send_file


def enviar_email(usuario, email):
    # Gerar uma senha temporária
    senha_temporaria = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_-+=', k=12))

    # Configurar os detalhes do e-mail
    remetente = 'marco.cordovil2025@gmail.com'  # Insira o seu e-mail aqui
    destinatario = email
    assunto = 'Recuperação de Senha'
    mensagem = f'Olá {usuario},\n\nSua senha temporária é: {senha_temporaria}\n\nAtenciosamente,\nSua Aplicação Web'

    # Configurar o servidor SMTP
    servidor_smtp = 'smtp.gmail.com'
    porta = 587
    usuario_smtp = 'marco.cordovil2025@gmail.com'  # Insira o seu e-mail aqui
    senha_smtp = '@Sigma4321'  # Insira a sua senha aqui

    # Criar o objeto MIMEText
    msg = MIMEText(mensagem)
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto

    # Enviar o e-mail usando o servidor SMTP
    try:
        with smtplib.SMTP(servidor_smtp, porta) as servidor:
            servidor.starttls()
            servidor.login(usuario_smtp, senha_smtp)
            servidor.sendmail(remetente, destinatario, msg.as_string())
        print('E-mail enviado com sucesso.')
    except Exception as e:
        print(f'Erro ao enviar e-mail: {e}')


def mime():
    return None