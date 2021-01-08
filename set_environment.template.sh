#!/bin/bash
export DJANGO_SETTINGS_MODULE="catello.settings.develop"
export SECRET='SECRET'
export TELEGRAM_BOT_TOKEN="TELEGRAM_BOT_TOKEN"
export EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
export EMAIL_HOST="EMAIL_HOST"
export EMAIL_USE_TLS="True"
export EMAIL_PORT="587"
export EMAIL_HOST_USER="EMAIL_HOST_USER"
export EMAIL_HOST_PASSWORD="@EMAIL_HOST_PASSWORD"
export SHAREPOINT_URL="SHAREPOINT_URL"
export SHAREPOINT_USERNAME="SHAREPOINT_USERNAME"
export SHAREPOINT_PASSWORD="SHAREPOINT_PASSWORD"
export DOCUMENTS_URL="/Documents/Censimenti/censiti.xlsx"
export EMAIL_FROM="EMAIL_FROM"
export WEBHOOK_URL="WEBHOOK_URL"
export WEBHOOK_PREFIX="catello"