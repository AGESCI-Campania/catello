import secrets

from django.core.management import BaseCommand
from django.db.models import Q

from catello_bot.models import Iscritti


class Command(BaseCommand):
    def handle(self, *args, **options):
        iscritti = Iscritti.objects.filter(
            Q(coca=True) &
            Q(authcode__isnull=True)
        )
        for iscritto in iscritti:
            authcode = secrets.token_urlsafe(6)
            iscritto.authcode = authcode
            iscritto.save(force_update=True)
            nome = f"{iscritto.nome} {iscritto.cognome}"
            authcode = authcode
            print(f"Authcode generato per {nome}: {authcode}")