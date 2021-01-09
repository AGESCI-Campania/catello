# -*- coding: utf-8 -*-
# Example code for telegrambot.py module
from enum import Enum
from re import Match

from django.db.models import Q
from django.conf import settings
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, TelegramError
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from django_telegrambot.apps import DjangoTelegramBot

from catello_bot.models import Iscritti
from utils import dbmanager
from utils import Utils
import os
import sys
import re
import secrets

import logging

from utils.DataLoader import DataLoader


class Conversations(Enum):
    INFO = 1
    CODICE = 2


log_level = logging.DEBUG if settings.DEBUG else logging.WARNING
logging.basicConfig(level=log_level,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

CONVERSATIONEND = 0
INFOSELECTDETAIL, INFOONLYACTIVE, INFOFULL, CONVERSATIONEND = range(CONVERSATIONEND, 4 + CONVERSATIONEND)
CODICESELECTDETAIL, CODICEONLYACTIVE, CODICEFULL, CONVERSATIONEND = range(CONVERSATIONEND, 4 + CONVERSATIONEND)
GENERACODICE, CONVERSATIONEND = range(CONVERSATIONEND, 2 + CONVERSATIONEND)
INVIACODICE, CONVERSATIONEND = range(CONVERSATIONEND, 2 + CONVERSATIONEND)


def create_regex(regexstr: str) -> re:
    return re.compile(regexstr, re.IGNORECASE)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_markdown_v2(f"Benvenuto sul bot della *Comunità Capi AGESCI Avellino 1*\n"
                                     f"Se sei un membro di questa Comunità Capi usa il codice ricevuto "
                                     f"per email per registrarti\!\n"
                                     f"Se non lo hai ricevuto, chiedimi _\"invia codice\"_ seguito dal tuo codice socio "
                                     f"o codice fiscale e riceverai il codice di autorizzazioni e le istruzioni"
                                     f"per usarlo sulla tua mail\.",
                                     reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def help(update: Update, context: CallbackContext) -> int:
    help_text = ""
    help_text += f"/info \- Ottiene le info di un socio del gruppo, si può cercare per cognome, nome, codice socio, " \
                 "codice fiscale o unità [L/C, E/G, R/S, Co\.Ca\.] "
    help_text += f"/socio \- Ottiene le info di un socio del gruppo, si può cercare per cognome, nome, codice socio, " \
                 "codice fiscale o unità [L/C, E/G, R/S, Co\.Ca\.] "
    help_text += f"/codice \- Ottiene il codice socio di un socio del gruppo, si può cercare per cognome, nome, " \
                 "codice socio, codice fiscale o unità [L/C, E/G, R/S, Co\.Ca\.] "
    help_text += f"/codicesocio \- Ottiene il codice socio di un socio del gruppo, si può cercare per cognome, nome, " \
                 "codice socio, codice fiscale o unità [L/C, E/G, R/S, Co\.Ca\.] "
    help_text += f"/generacodice \- Genera il codice di autorizzazione per potersi abilitare all'uso del bot"
    help_text += f"/inviacodice \- Invia il codice di autorizzazione per potersi abilitare all'uso del bot " \
                 "all'indirizzo email registrato su Buonastrada, si può cercare per codice socio, codice fiscale "
    help_text += f"/registrami \- Registra l'account telegram al bot\. *Richiede codice di autorizzazione*"
    help_text += f"/aggiungiadmin \- Aggiunge un amministratore del bot\. *Solo per amministratori*"
    help_text += f"/aggiungicapo \- Aggiunge un un capo del gruppo\. *Solo per amministratori*"
    help_text += f"/rimuoviadmin \- Rimuove un amministratore del bot\. *Solo per amministratori*"
    help_text += f"/rimuovicapo \- Rimuove un un capo del gruppo\. *Solo per amministratori*"
    help_text += f"/aggiorna \- Aggiorna la lista soci dal file excel su onedrive\. *Solo per amministratori*"
    help_text += f"/attiva \- Attiva un iscritto\. *Solo per amministratori*"
    help_text += f"/disattiva \- Disattiva un iscritto\. *Solo per amministratori*"
    help_text += f"/abilitati \- Lista abilitati\. *Solo per amministratori*"
    help_text += f"/help \- Mostra questa lista dei comandi"
    update.message.reply_markdown_v2(help_text)
    return ConversationHandler.END


def unknowncommand(update: Update, context: CallbackContext) -> int:
    update.message.reply_markdown_v2(Utils.clean_message(f"Non so cosa significa {update.message.text}. "
                                                         f"Non sono così intelligente!"),
                                     reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def startinfo(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Tutti'], ['Censiti'], ['annulla']]
    if dbmanager.check_user(update.message.from_user.id):
        update.message.reply_text(
            "Vuoi visualizzare tutti o solo soci (censiti nell'anno)?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        if update.message.text.lstrip("/").startswith("codice"):
            return CODICESELECTDETAIL
        return INFOSELECTDETAIL
    else:
        update.message.reply_text('Non sei autorizzato!')
        return ConversationHandler.END


def infoselectdetaillevel(update: Update, context: CallbackContext) -> int:
    return selectdetaillevel(update, context, Conversations.INFO)


def codiceselectdetaillevel(update: Update, context: CallbackContext) -> int:
    return selectdetaillevel(update, context, Conversations.CODICE)


def selectdetaillevel(update: Update, context: CallbackContext, conv: Conversations) -> int:
    if not (conv in [Conversations.INFO, Conversations.CODICE]):
        answer_error_message(update, context)
        return ConversationHandler.END

    reply_keyboard = [['Branca L/C', 'Branca E/G'], ['Branca R/S', 'Co.Ca.'], ['Tutti', 'annulla']]
    user_choice = update.message.text
    if user_choice == 'Tutti':
        resp = INFOFULL if conv == Conversations.INFO else CODICEFULL
    else:
        resp = INFOONLYACTIVE if conv == Conversations.INFO else CODICEONLYACTIVE

    update.message.reply_text("Ok, adesso dimmi cosa vuoi cercare. Seleziona una opzione\n"
                              "Oppure scrivi il nome o cognome o codice socio o codice fiscale",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
                              )
    return resp


def inforesponseall(update: Update, context: CallbackContext) -> int:
    return inforesponse(update, context, showall=True)


def inforesponseactive(update: Update, context: CallbackContext) -> int:
    return inforesponse(update, context, showall=False)


def inforesponse(update: Update, context: CallbackContext, showall: bool) -> int:
    return iscrittiresponse(update, context, showall=showall, conv=Conversations.INFO)


def codiceresponseall(update: Update, context: CallbackContext) -> int:
    return codiceresponse(update, context, showall=True)


def codiceresponseactive(update: Update, context: CallbackContext) -> int:
    return codiceresponse(update, context, showall=False)


def codiceresponse(update: Update, context: CallbackContext, showall: bool) -> int:
    return iscrittiresponse(update, context, showall=showall, conv=Conversations.CODICE)


def iscrittiresponse(update: Update, context: CallbackContext, showall: bool, conv: Conversations) -> int:
    search_str = update.message.text.strip()
    if (search_str.lower() == 'tutti') | (search_str == ''):
        iscritti_set = dbmanager.get_iscritti('*', show_only_active=(not showall), show_all=True)
    else:
        if search_str.lower() == 'co.ca.':
            search_str = "adulti"
        iscritti_set = dbmanager.get_iscritti(search_str, show_only_active=(not showall))

    counter = 0
    try:
        for iscritto in iscritti_set:
            counter += 1
            nome = Utils.clean_message(f"{iscritto.nome} {iscritto.cognome} ({iscritto.sesso})")
            if conv == Conversations.INFO:
                messagge_text = f"*Nome:* {nome}\n"
                messagge_text += f"*Codice Fiscale:* {Utils.clean_message(iscritto.codice_fiscale)}\n"
                messagge_text += f"*Codice Socio:* {iscritto.codice_socio}\n"
                messagge_text += f"*Data e luogo di nascita:* {Utils.format_date_field(iscritto.data_di_nascita)}\n"
                messagge_text += f"*Residenza:* {Utils.format_address(iscritto)}\n"
                messagge_text += f"*Privacy:* *_2\.a:_* {Utils.bool_to_str(iscritto.informativa2a)} \- *_2\.b:_* " \
                                 f"{Utils.bool_to_str(iscritto.informativa2b)} \- *_2\.c:_* " \
                                 f"{Utils.bool_to_str(iscritto.consenso_immagini)}\n"
                messagge_text += f"*Branca:* {Utils.clean_message(iscritto.branca)}\n"
                messagge_text += f"*Cellulare:* {Utils.parse_optional_string(str(iscritto.cellulare))}\n"
                messagge_text += f"*Email:* {Utils.parse_optional_string(iscritto.email)}\n"
                messagge_text += f"*Fo\.Ca\.:* {Utils.clean_message(iscritto.livello_foca)}\n"
                if dbmanager.check_admin(update.message.from_user.id):
                    messagge_text += f"*Ruolo:* {Utils.clean_message(iscritto.get_role_display())}\n"
                    messagge_text += f"*Telegram:* {Utils.get_telegram_link(iscritto)}\n"
                    messagge_text += f"*AuthCode:* {Utils.parse_optional_string(iscritto.authcode)}\n"
                    messagge_text += f"*Attivo:* {Utils.bool_to_str(iscritto.active)}\n"
            elif conv == Conversations.CODICE:
                messagge_text = f"*{nome}:* {iscritto.codice_socio}"
            else:
                return ConversationHandler.END
            update.message.reply_markdown_v2(messagge_text, reply_markup=ReplyKeyboardRemove())
    except Exception:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.error(str(sys.exc_info()))
        logger.error(f'{exc_type}, {fname}, {exc_tb.tb_lineno}')
        # update.message.reply_text("Ooops, si è verificato un errore :(", reply_markup=ReplyKeyboardRemove())
        answer_error_message(update, context)
        return ConversationHandler.END

    messagge_text = Utils.clean_message(f"Ci sono {counter} iscritti!")
    logger.debug(messagge_text)
    update.message.reply_markdown_v2(messagge_text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def start_generacodice(update: Update, context: CallbackContext) -> int:
    if dbmanager.check_admin(update.message.from_user.id):
        reply_keyboard = [['Nuovi', 'Tutti'], ['Annulla']]
        update.message.reply_text("Bene, per chi devo generare i codici, scegli una opzione o scrivi il codice socio o "
                                  "il codice fiscale del\la capo per ui generare il codice.",
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
                                  )
        return GENERACODICE
    else:
        update.message.reply_text('Non sei autorizzato!')

    return ConversationHandler.END


def generacodice(update: Update, context: CallbackContext) -> int:
    command = update.message.text.lower()
    if command == 'tutti':
        iscritti = Iscritti.objects.filter(
            Q(coca=True)
        )
    elif command == 'nuovi':
        iscritti = Iscritti.objects.filter(
            Q(coca=True) &
            Q(authcode__isnull=True)
        )
    else:
        iscritti = dbmanager.get_iscritti(command).filter(
            Q(coca=True)
        )

    for iscritto in iscritti:
        authcode = secrets.token_urlsafe(6)
        iscritto.authcode = authcode
        iscritto.save(force_update=True)
        nome = Utils.clean_message(f"{iscritto.nome} {iscritto.cognome}")
        authcode = Utils.clean_message(authcode)
        update.message.reply_markdown_v2(f"Authcode generato per *{nome}*: *_{authcode}_*")
    return ConversationHandler.END


def answer_error_message(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Ooops, si è verificato un errore :(', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Ciao! Torna a trovarmi presto.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def listabilitati(update: Update, context: CallbackContext) -> int:
    if dbmanager.check_admin(update.message.from_user.id):
        abilitati = dbmanager.get_enabled()
        for abilitato in abilitati:
            try:
                nome = Utils.clean_message(f"{abilitato.nome} {abilitato.cognome}")
                tid = Utils.get_telegram_link(abilitato)
                update.message.reply_markdown_v2(f"*{nome}:* _{tid}_")
            except TelegramError:
                send_error_message(update, context)
    return ConversationHandler.END


def start_invia_codice(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Annulla']]
    try:
        update.message.reply_markdown_v2("Inserisci il *Codice Socio o il Codice Fiscale* del capo a cui "
                                         "mandare il codice di autorizzazione\.  \n"
                                         "Scrivi annulla per annullare la richiesta\.",
                                         reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True), )
        return INVIACODICE
    except TelegramError:
        send_error_message(update, context)
        return ConversationHandler.END


def invia_codice(update: Update, context: CallbackContext) -> int:
    try:
        iscritto = dbmanager.get_iscritto_by_codice(update.message.text)
        if iscritto.email is None:
            update.message.reply_text(f"{update.message.text} non ha un indirizzo mail a cui mandare il codice!",
                                      reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        if iscritto.authcode is None:
            iscritto.authcode = secrets.token_urlsafe(6)
            iscritto.save(force_update="True")

        Utils.send_authcode_email(iscritto)
        update.message.reply_text(f"Il codice di autorizzazione è stato inviato all'indirizzo mail registrato "
                                  f"su BuonaStrada!",
                                  reply_markup=ReplyKeyboardRemove())
    except Iscritti.DoesNotExist:
        update.message.reply_text(f"Non ho trovato un iscritto che risponde a {update.message.text}")
    except Iscritti.MultipleObjectsReturned:
        update.message.reply_text(f"Si è verificato un errore per il codice {update.message.text}")
    finally:
        return ConversationHandler.END


def registrami(update: Update, context: CallbackContext) -> int:
    inputstr = update.message.text
    regexp = create_regex(r"/?(registrami|abilitami) ([A-Za-z0-9\-_ \.~]+)")
    if regexp.match(inputstr):
        res = list(filter(None, regexp.split(inputstr)))
        authcode = res[1]
        try:
            logger.debug("Getting user")
            iscritto = dbmanager.get_iscritto_by_authcode(authcode)
            logger.debug("Got user")
            if ((iscritto.telegram is None) | (iscritto.telegram == '')) & \
                    ((iscritto.telegram_id is None) | (iscritto.telegram_id == '')):
                logger.debug("Valid user")
                if update.message.from_user.username is None:
                    username = f"User{update.message.from_user.id}"
                else:
                    username = update.message.from_user.username

                logger.debug("Prepared username")
                iscritto.telegram_id = update.message.from_user.id
                iscritto.telegram = username
                iscritto.save(force_update="True")
                logger.debug("Saved user")
                update.message.reply_text(f"Sei stato registrato correttamente! Ora comincia a chiedermi informazioni")
                return ConversationHandler.END
            else:
                update.message.reply_text(f"Questo utente ha già un telegram associato")
                return ConversationHandler.END
        except Iscritti.DoesNotExist:
            update.message.reply_text(f"Non esiste alcun utente con authcode {authcode}")
        except Iscritti.MultipleObjectsReturned:
            update.message.reply_text(f"Si è verificato un errore per l'authcode {authcode}")
        except Exception:
            send_error_message(update, context)
        finally:
            return ConversationHandler.END
    else:
        update.message.reply_text("Non hai inserito il codice autorizzazione")
    return ConversationHandler.END


def aggiungiadmin(update: Update, context: CallbackContext) -> int:
    if dbmanager.check_super_admin(update.message.from_user.id):
        regexp = create_regex(
            r"^(?P<command>/?aggiungi ?admin) (?P<searchstr>(?:[0-9]+)|(?:[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]))$")
        m = regexp.match(update.message.text)
        if m:
            searchstr = m.group("searchstr")
            try:
                iscritto = dbmanager.get_iscritto_by_codice(searchstr)
                if iscritto.role == 'SA':
                    update.message.reply_text(f"L'utente {searchstr} è già super admin!")
                    return ConversationHandler.END

                if iscritto.telegram_id == update.message.from_user.id:
                    update.message.reply_text(f"Non puoi cambiare il tuo stesso ruolo!")
                    return ConversationHandler.END

                iscritto.role = 'AD'
                iscritto.save(force_update=True)
                nome = Utils.clean_message(f"{iscritto.nome} {iscritto.cognome}")
                update.message.reply_markdown_v2(f"L'utente *{nome}* è ora amministratore")
            except Iscritti.DoesNotExist:
                update.message.reply_text(f"Non esiste alcun utente con codice {searchstr}")
            except Iscritti.MultipleObjectsReturned:
                update.message.reply_text(f"Si è verificato un errore per il codice {searchstr}")
            finally:
                return ConversationHandler.END
        else:
            update.message.reply_text(f"Non mi hai detto chi nominare amministratore")
            return ConversationHandler.END
    else:
        update.message.reply_text("Non hai sei autorizzato!")
        return ConversationHandler.END


def aggiungicapo(update: Update, context: CallbackContext) -> int:
    if dbmanager.check_admin(update.message.from_user.id):
        regexp = create_regex(
            r"^(?P<command>/?aggiungi ?capo) (?P<searchstr>(?:[0-9]+)|(?:[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]))$")
        m = regexp.match(update.message.text)
        if m:
            searchstr = m.group("searchstr")
            try:
                iscritto = dbmanager.get_iscritto_by_codice(searchstr)
                if (iscritto.role == 'SA') | (iscritto.role == 'AD'):
                    update.message.reply_text(f"L'utente {searchstr} è già {iscritto.get_role_display()}")
                    return ConversationHandler.END

                if iscritto.telegram_id == update.message.from_user.id:
                    update.message.reply_text(f"Non puoi cambiare il tuo stesso ruolo!")
                    return ConversationHandler.END

                iscritto.role = 'CA'
                iscritto.save(force_update=True)
                nome = Utils.clean_message(f"{iscritto.nome} {iscritto.cognome}")
                update.message.reply_markdown_v2(f"L'utente *{nome}* è ora inserito in Co\.Ca\.")
            except Iscritti.DoesNotExist:
                update.message.reply_text(f"Non esiste alcun utente con codice {searchstr}")
            except Iscritti.MultipleObjectsReturned:
                update.message.reply_text(f"Si è verificato un errore per il codice {searchstr}")
            finally:
                return ConversationHandler.END
        else:
            update.message.reply_text(f"Non mi hai detto chi inserire nella Co.Ca.")
            return ConversationHandler.END
    else:
        update.message.reply_text("Non hai sei autorizzato!")
        return ConversationHandler.END


def rimuoviadmin(update: Update, context: CallbackContext) -> int:
    if dbmanager.check_super_admin(update.message.from_user.id):
        regexp = create_regex(
            r"^(?P<command>/?rimuovi ?admin) (?P<searchstr>(?:[0-9]+)|(?:[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]))$")
        m = regexp.match(update.message.text)
        if m:
            searchstr = m.group("searchstr")
            try:
                iscritto = dbmanager.get_iscritto_by_codice(searchstr)
                if iscritto.role == 'SA':
                    update.message.reply_text(f"L'utente {searchstr} è {iscritto.get_role_display()}! Non puoi toccarlo")
                    return ConversationHandler.END

                if iscritto.telegram_id == update.message.from_user.id:
                    update.message.reply_text(f"Non puoi cambiare il tuo stesso ruolo!")
                    return ConversationHandler.END

                iscritto.role = 'IS'
                iscritto.save(force_update=True)
                nome = Utils.clean_message(f"{iscritto.nome} {iscritto.cognome}")
                update.message.reply_markdown_v2(f"L'utente *{nome}* è ora amministratore")
            except Iscritti.DoesNotExist:
                update.message.reply_text(f"Non esiste alcun utente con codice {searchstr}")
            except Iscritti.MultipleObjectsReturned:
                update.message.reply_text(f"Si è verificato un errore per il codice {searchstr}")
            finally:
                return ConversationHandler.END
        else:
            update.message.reply_text(f"Non mi hai detto chi eliminare da amministratore")
            return ConversationHandler.END
    else:
        update.message.reply_text("Non hai sei autorizzato!")
        return ConversationHandler.END


def rimuovicapo(update: Update, context: CallbackContext) -> int:
    if dbmanager.check_admin(update.message.from_user.id):
        regexp = create_regex(
            r"^(?P<command>/?rimuovi ?capo) (?P<searchstr>(?:[0-9]+)|(?:[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]))$")
        m = regexp.match(update.message.text)
        if m:
            searchstr = m.group("searchstr")
            try:
                iscritto = dbmanager.get_iscritto_by_codice(searchstr)
                if iscritto.role == 'SA':
                    update.message.reply_text(f"L'utente {searchstr} è un {iscritto.get_role_display()}. Non puoi modificarlo.")
                    return ConversationHandler.END
                if iscritto.telegram_id == update.message.from_user.id:
                    update.message.reply_text(f"Non puoi cambiare il tuo stesso ruolo!")
                    return ConversationHandler.END

                iscritto.role = 'IS'
                iscritto.save(force_update=True)
                nome = Utils.clean_message(f"{iscritto.nome} {iscritto.cognome}")
                update.message.reply_markdown_v2(f"L'utente *{nome}* è ora rimosso dalla Co\.Ca\.")
            except Iscritti.DoesNotExist:
                update.message.reply_text(f"Non esiste alcun utente con codice {searchstr}")
            except Iscritti.MultipleObjectsReturned:
                update.message.reply_text(f"Si è verificato un errore per il codice {searchstr}")
            finally:
                return ConversationHandler.END
        else:
            update.message.reply_text(f"Non mi hai detto chi eliminare dalla Co.Ca.")
            return ConversationHandler.END
    else:
        update.message.reply_text("Non hai sei autorizzato!")
        return ConversationHandler.END


def aggiorna(update: Update, context: CallbackContext) -> int:
    if dbmanager.check_admin(update.message.from_user.id):
        url = settings.SHAREPOINT_URL
        username = settings.SHAREPOINT_USERNAME
        password = settings.SHAREPOINT_PASSWORD
        documents = settings.DOCUMENTS_URL
        update.message.reply_markdown_v2(
            Utils.clean_message(f"Sto caricando il file excel. Ti avviso io quando ho finito!"))
        loader = DataLoader(url, username, password, documents)
        (nuovi, aggiornati) = loader.load_remote_into_db()
        update.message.reply_markdown_v2(
            Utils.clean_message(f"Fatto, ho caricato {nuovi} soci e ne ho aggiornati altri {aggiornati}"))
    else:
        update.message.reply_text("Non hai sei autorizzato!")

    return ConversationHandler.END


def imposta_status(update: Update, context: CallbackContext) -> int:
    if dbmanager.check_admin(update.message.from_user.id):
        regexp = create_regex(
            r"^(?P<command>/?(dis)?attiva) (?P<searchstr>(?:[0-9]+)|(?:[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]))$")
        m = regexp.match(update.message.text)
        if m:
            command = m.group("command")
            searchstr = m.group("searchstr")
            active = not (command.startswith("/dis") | command.startswith("dis"))
            try:
                iscritto = dbmanager.get_iscritto_by_codice(searchstr)

                if iscritto.role == 'SA':
                    update.message.reply_text(
                        f"L'utente {searchstr} è un {iscritto.get_role_display()}. Non puoi modificarlo.")
                    return ConversationHandler.END

                if iscritto.telegram_id == update.message.from_user.id:
                    update.message.reply_text(f"Non puoi modificare le tue abilitazioni!")
                    return ConversationHandler.END

                iscritto.active = active
                iscritto.save(force_update=True)
                nome = Utils.clean_message(f"{iscritto.nome} {iscritto.cognome}")
                update.message.reply_markdown_v2(f"L'utente *{nome}* è stato *{'' if active else 'dis'}attivato*")
            except Iscritti.DoesNotExist:
                update.message.reply_text(f"Non esiste alcun utente con codice {searchstr}")
            except Iscritti.MultipleObjectsReturned:
                update.message.reply_text(f"Si è verificato un errore per il codice {searchstr}")
            finally:
                return ConversationHandler.END
        else:
            update.message.reply_text(f"Non mi hai detto chi chi devo modificare")
    else:
        update.message.reply_text("Non hai sei autorizzato!")
    return ConversationHandler.END


def send_error_message(update: Update, context: CallbackContext) -> int:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    logger.error(f'{exc_type}, {fname}, {exc_tb.tb_lineno}')
    logger.error(str(sys.exc_info()))
    update.message.reply_text("Ooops si è verificato un errore!")
    return ConversationHandler.END


def error(update: Update, context: CallbackContext) -> int:
    logger.error(str(sys.exc_info()))
    logger.error('Update "%s" caused error "%s"' % (update, context.error))
    update.message.reply_text("Ooops si è verificato un errore!")
    return ConversationHandler.END


def main():
    logger.setLevel(logging.DEBUG)
    logger.info("Loading handlers for telegram bot")

    dp = DjangoTelegramBot.dispatcher

    # Handler for start command
    dp.add_handler(CommandHandler("start", start))

    # Handler for help command
    dp.add_handler(CommandHandler("help", help))

    # Handler for info command
    info_handler = ConversationHandler(
        entry_points=[CommandHandler('info', startinfo),
                      CommandHandler('socio', startinfo),
                      MessageHandler(Filters.regex(create_regex(r'^(info|socio)$')), startinfo)],
        states={
            INFOSELECTDETAIL: [
                MessageHandler(Filters.regex(create_regex(r'^(Tutti|Censiti)$')), infoselectdetaillevel)],
            INFOFULL: [MessageHandler(Filters.text & ~Filters.command, inforesponseall)],
            INFOONLYACTIVE: [MessageHandler(Filters.text & ~Filters.command, inforesponseactive)],
        },
        fallbacks=[CommandHandler('annulla', cancel),
                   MessageHandler(Filters.regex(create_regex(r'^(annulla)$')), cancel)]
    )

    dp.add_handler(info_handler)

    # Handler for codicesocio command
    codice_handler = ConversationHandler(
        entry_points=[CommandHandler('codice', startinfo),
                      CommandHandler('codicesocio', startinfo),
                      MessageHandler(Filters.regex(create_regex(r'^(codice ?(socio)?)$')), startinfo)],
        states={
            CODICESELECTDETAIL: [
                MessageHandler(Filters.regex(create_regex(r'^(Tutti|Censiti)$')), codiceselectdetaillevel)],
            CODICEFULL: [MessageHandler(Filters.text & ~Filters.command, codiceresponseall)],
            CODICEONLYACTIVE: [MessageHandler(Filters.text & ~Filters.command, codiceresponseactive)],
        },
        fallbacks=[CommandHandler('annulla', cancel),
                   MessageHandler(Filters.regex(create_regex(r'^(annulla)$')), cancel)]
    )

    dp.add_handler(codice_handler)

    # Handler for generacodice command
    authcode_handler = ConversationHandler(
        entry_points=[CommandHandler('generacodice', start_generacodice),
                      MessageHandler(Filters.regex(create_regex(r'^(genera ?codice)$')), start_generacodice)],
        states={
            GENERACODICE: [MessageHandler(Filters.text & ~Filters.command, generacodice)],
        },
        fallbacks=[CommandHandler('annulla', cancel),
                   MessageHandler(Filters.regex(create_regex(r'^(annulla)$')), cancel)]
    )

    dp.add_handler(authcode_handler)

    # Handler for inviacodice command
    send_code_handler = ConversationHandler(
        entry_points=[CommandHandler('inviacodice', start_invia_codice),
                      MessageHandler(Filters.regex(create_regex(r'^(invia ?codice)$')), start_invia_codice)],
        states={
            INVIACODICE: [MessageHandler(Filters.text & ~Filters.command, invia_codice)],
        },
        fallbacks=[CommandHandler('annulla', cancel),
                   MessageHandler(Filters.regex(create_regex(r'^(annulla)$')), cancel)]
    )

    dp.add_handler(send_code_handler)

    # Handler for abilitati command
    dp.add_handler(MessageHandler(Filters.regex(create_regex(r'^((lista)? ?abilitati)$')), listabilitati))
    dp.add_handler(CommandHandler('abilitati', listabilitati))

    # Handler for registrami command
    dp.add_handler(MessageHandler(Filters.regex(create_regex(r'^(registrami|abilitami).*$')), registrami))
    dp.add_handler(CommandHandler('abilitami', registrami))
    dp.add_handler(CommandHandler('registrami', registrami))

    # Handler for aggiungiadmin command
    dp.add_handler(MessageHandler(Filters.regex(create_regex(r'^(aggiungi ?admin) .+$')), aggiungiadmin))
    dp.add_handler(CommandHandler('aggiungiadmin', aggiungiadmin))

    # Handler for aggiungicapo command
    dp.add_handler(MessageHandler(Filters.regex(create_regex(r'^(aggiungi ?capo) .+$')), aggiungicapo))
    dp.add_handler(CommandHandler('aggiungicapo', aggiungicapo))

    # Handler for rimuoviadmin command
    dp.add_handler(MessageHandler(Filters.regex(create_regex(r'^(rimuovi ?admin) .+$')), rimuoviadmin))
    dp.add_handler(CommandHandler('rimuoviadmin', rimuoviadmin))

    # Handler for rimuovicapo command
    dp.add_handler(MessageHandler(Filters.regex(create_regex(r'^(rimuovi ?capo) .+$')), rimuovicapo))
    dp.add_handler(CommandHandler('rimuovicapo', rimuovicapo))

    # Handler for attiva/disattiva command
    dp.add_handler(MessageHandler(Filters.regex(create_regex(r'^((dis)?attiva) .+$')), imposta_status))
    dp.add_handler(CommandHandler('attiva', imposta_status))
    dp.add_handler(CommandHandler('disattiva', imposta_status))

    # Handler for aggiorna command
    dp.add_handler(MessageHandler(Filters.regex(create_regex(r'^(aggiorna)$')), aggiorna))
    dp.add_handler(CommandHandler('aggiorna', aggiorna))

    # Handler for unknown command
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, unknowncommand))

    # Error logging
    dp.add_error_handler(error)
