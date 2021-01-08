from django.shortcuts import render

# Create your views here.
from django.views import View
from django.http import JsonResponse


class CatelloView(View):
    def post(self, request, *args, **kwargs):
        return JsonResponse({"ok": "POST request processed"})

    def get(self, request, *args, **kwargs):
        return JsonResponse({"ok": "POST request processed"})