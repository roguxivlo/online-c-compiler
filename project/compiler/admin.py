from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(User)

admin.site.register(Directory)

admin.site.register(File)

admin.site.register(SectionType)

admin.site.register(SectionStatus)

admin.site.register(SectionStatusData)

admin.site.register(Section)