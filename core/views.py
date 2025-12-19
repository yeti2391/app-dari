from django.shortcuts import render
from django.http import HttpResponse

# Mi vista de inicio
def home(request):
    return HttpResponse("Welcome to the Home Page!")