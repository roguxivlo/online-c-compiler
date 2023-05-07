from django.db import models

# Create your models here.

class NamedEntity(models.Model):
    name = models.CharField(max_length=200)
    class Meta:
        abstract = True

    def __str__(self):
        return self.name

class User(NamedEntity):
    login = models.CharField(max_length=200)
    password = models.CharField(max_length=200)

class Directory(NamedEntity):
    # optional
    description = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    # optional
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name='parent directory')
    # Set to false on delete
    accesible = models.BooleanField(default=True)
    deleted_date = models.DateTimeField(null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)

class File(NamedEntity):
    # optional
    description = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE)
    # Set to false on delete
    accesible = models.BooleanField(default=True)
    deleted_date = models.DateTimeField(null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)

class SectionType(NamedEntity):
    pass

class SectionStatus(NamedEntity):
    pass

class SectionStatusData(models.Model):
    info = models.TextField()

class Section(models.Model):
    # optional
    name = models.CharField(max_length=200, blank=True)
    # optional
    description = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name='parent section')
    begin = models.IntegerField(verbose_name='first row of section')
    end = models.IntegerField(verbose_name='last row of section')
    section_type = models.ForeignKey(SectionType, on_delete=models.PROTECT)
    status = models.ForeignKey(SectionStatus, on_delete=models.PROTECT)
    status_data = models.ForeignKey(SectionStatusData, on_delete=models.PROTECT, null=True, blank=True)
    body = models.TextField()