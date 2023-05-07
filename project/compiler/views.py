from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from .models import *


def index(request):
    template = loader.get_template('compiler/index.html')

    # get all directories from directory table
    directories = Directory.objects.all()
    context = {'directories': directories}

    return render(request, 'compiler/index.html', context)