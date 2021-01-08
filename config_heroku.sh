#!/bin/bash
heroku config:set DJANGO_SETTINGS_MODULE=catello.settings.production SECRET=$SECRET TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN EMAIL_BACKEND=$EMAIL_BACKEND EMAIL_HOST=$EMAIL_HOST EMAIL_USE_TLS=$EMAIL_USE_TLS EMAIL_PORT=$EMAIL_PORT EMAIL_HOST_USER=$EMAIL_HOST_USER EMAIL_HOST_PASSWORD=$EMAIL_HOST_PASSWORD SHAREPOINT_URL=$SHAREPOINT_URL SHAREPOINT_USERNAME=$SHAREPOINT_USERNAME SHAREPOINT_PASSWORD=$SHAREPOINT_PASSWORD DOCUMENTS_URL=$DOCUMENTS_URL EMAIL_FROM=$EMAIL_FROM WEBHOOK_URL=$WEBHOOK_URL WEBHOOK_PREFIX=$WEBHOOK_PREFIX