from django.core.management import BaseCommand

from catello_bot.models import Iscritti


class Command(BaseCommand):
    def handle(self, *args, **options):
        codicesocio = input("Inserire il codice socio del nuovo superamministratore: \n")
        try:
            iscritto = Iscritti.objects.get(codice_socio__iexact=codicesocio)
            iscritto.role = 'SA'
            iscritto.save(force_update=True)
            print(f"L'utente {codicesocio} è ora Super Amministratore")
        except Iscritti.DoesNotExist:
            print(f"Non esiste un utente con codice {codicesocio}")
        except Iscritti.MultipleObjectsReturned:
            print(f"Si è verificato un errore con {codicesocio}")