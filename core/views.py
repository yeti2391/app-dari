from django.shortcuts import render


# Mi vista de inicio
def home(request):
    return render(request, 'core/home.html')