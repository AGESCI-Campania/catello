import re
from datetime import datetime
import locale

from catello_bot.models import Iscritti
from telegram.utils.helpers import escape_markdown
from django.core.mail import send_mail
from django.conf import settings
import logging
import os
import sys

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def clean_message(string: str) -> str:
    # cleaner = re.compile(r"([_\*\[\]\(\)~`>#\+\-=|{}\.!])", re.MULTILINE)
    # string = cleaner.sub(r"\\\1", string)
    return escape_markdown(string, version=2)


def parse_optional_string(string: str = None) -> str:
    return clean_message("-" if string is None else string)


def bool_to_str(input: bool) -> str:
    return clean_message("Si" if input else "No")


def format_date_field(data: datetime) -> str:
    try:
        locale.setlocale(locale.LC_TIME, "it_IT")
        return clean_message(data.strftime("%x"))
    except locale.Error:
        return clean_message(data.strftime("%d/%m/%Y"))


def format_address(iscritto: Iscritti) -> str:
    address = f"{iscritto.indirizzo} {iscritto.civico}, {iscritto.comune} ({iscritto.provincia})"
    return clean_message(address)


def get_telegram_link(iscritto: Iscritti):
    tid = iscritto.telegram_id
    if tid is None:
        return clean_message("-")
    tname = clean_message(f"{iscritto.nome} {iscritto.cognome}") if iscritto.telegram is None else iscritto.telegram
    return f"[@{tname}](tg://user?id={tid})"


def get_gendered_string(sesso: str, maschile: str, femminile: str) -> str:
    return maschile if sesso == 'M' else femminile


def send_authcode_email(iscritto: Iscritti):
    try:
        subject = "Accesso al bot telegram della Comunità Capi Avellino 1"
        message = f'Ciao {iscritto.nome} {iscritto.cognome},\n' \
                  f'Per accedere al bot devi essere autenticat{get_gendered_string(iscritto.sesso, "o", "a")}.\n' \
                  f'Il tuo codice autorizzazione e\' {iscritto.authcode}' \
                  f'Accedi al bot con telegram t.me/AV1CoCaBot e digita il comando "/registrami {iscritto.authcode}".\n' \
                  f'Fraternamente,\n' \
                  f'Il tuo amico bot di quartiere'
        message_html = f'<p>Ciao {iscritto.nome} {iscritto.cognome},</p>' \
                       f'<p>Per accedere al bot devi essere autenticat{get_gendered_string(iscritto.sesso, "o", "a")}.<br/>' \
                       f'Il tuo codice autorizzazione &egrave; <strong>{iscritto.authcode}</strong></p>' \
                       f'<p>Accedi al bot con telegram <a href="https://t.me/AV1CoCaBot">https://t.me/AV1CoCaBot</a> e digita il comando "/registrami {iscritto.authcode}".</p>' \
                       f'<p>Fraternamente,<br/>' \
                       f'Il tuo amico bot di quartiere</p>'
        email_from = settings.EMAIL_FROM
        recipient_list = iscritto.email.split(';')
        send_mail(subject, message, email_from, recipient_list, fail_silently=False, html_message=message_html)
        return True
    except Exception:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.error(f'{exc_type}, {fname}, {exc_tb.tb_lineno}')
        return False
