from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

def es_drbpa(user):
    return user.groups.filter(name='DRBPA').exists() or user.is_superuser

@login_required
@user_passes_test(es_drbpa)
def drbpa_home(request):
    return render(request, 'drbpa/drbpa.html')