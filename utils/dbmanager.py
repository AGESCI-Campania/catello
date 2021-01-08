from datetime import datetime, timedelta

from django.db.models import QuerySet, Q

from catello_bot.models import AppLogs, Iscritti
import logging
import re

logger = logging.getLogger(__name__)


def get_iscritti(search_string: str, show_only_active: bool = False, show_all: bool = False) -> QuerySet:
    if show_all:
        if show_only_active:
            iscritti_set = Iscritti.objects.filter(
                Q(active=True)
            )
        else:
            iscritti_set = Iscritti.objects.all()
        return iscritti_set
    else:
        iscritti_set = Iscritti.objects.filter(
            Q(cognome__icontains=search_string) |
            Q(nome__icontains=search_string) |
            Q(codice_socio__icontains=search_string) |
            Q(codice_fiscale__icontains=search_string) |
            Q(branca__icontains=search_string)
        )

        if show_only_active:
            iscritti_set = Iscritti.objects.filter(
                Q(cognome__icontains=search_string) |
                Q(nome__icontains=search_string) |
                Q(codice_socio__icontains=search_string) |
                Q(codice_fiscale__icontains=search_string) |
                Q(branca__icontains=search_string)
            ).filter(
                Q(active=True)
            )
        return iscritti_set.order_by('cognome', 'nome')


def get_iscritto_by_codice(search_string: str, show_only_active: bool = False) -> Iscritti:
    iscritto = Iscritti.objects.get(
        Q(codice_socio__iexact=search_string) |
        Q(codice_fiscale__iexact=search_string)
    )
    if show_only_active:
        iscritto = Iscritti.objects.get(
            Q(active=True) &
            (Q(codice_socio__iexact=search_string) |
             Q(codice_fiscale__iexact=search_string))
        )
    return iscritto


def get_iscritto_by_telegram(t_user: str) -> QuerySet:
    return Iscritti.objects.filter(
        Q(telegram_id__iexact=str(t_user)) |
        Q(telegram__iexact=str(t_user))
    )


def get_enabled() -> QuerySet:
    return Iscritti.objects.filter(
        Q(telegram_id__isnull=False)
    ).exclude(
        Q(telegram_id__iexact='') &
        Q(active=False)
    )


def get_iscritto_by_authcode(authcode: str) -> Iscritti:
    return Iscritti.objects.get(
        Q(authcode__iexact=authcode)
    )


def get_logs_by_date(days: int) -> QuerySet:
    date_to = datetime.now() - timedelta(days=7)
    return AppLogs.objects.filter(log_time__date__gte=date_to)


def get_logs_by_date_gte(days: int) -> QuerySet:
    date_to = datetime.now() - timedelta(days=7)
    return AppLogs.objects.filter(
        Q(log_time__date__gte=date_to)
    ).order_by('log_time')[:20]


def get_logs_by_date_lt(days: int) -> QuerySet:
    date_to = datetime.now() - timedelta(days=7)
    return AppLogs.objects.filter(
        Q(log_time__date__lt=date_to)
    )


def check_user(t_user):
    return check_role(t_user, ['SA', 'AD', 'CA'])


def check_admin(t_user):
    return check_role(t_user, ['SA', 'AD'])


def check_super_admin(t_user):
    return check_role(t_user, ['SA'])


def check_role(t_user: str, roles: list):
    if t_user is None:
        return False
    try:
        t_user = str(t_user)
        user: Iscritti = Iscritti.objects.get(telegram_id__iexact=t_user)
    except Iscritti.DoesNotExist:
        return False
    except Iscritti.MultipleObjectsReturned:
        return False
    except:
        return False

    if user.role in roles:
        return user.active
    else:
        return False
