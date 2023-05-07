from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render


def index(request):
    template = loader.get_template('compiler/index.html')
    context = {}
    return render(request, 'compiler/index.html', context)