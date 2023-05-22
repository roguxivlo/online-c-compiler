from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import User
# Create your models here.

class NamedEntity(models.Model):
    name = models.CharField(max_length=200)
    class Meta:
        abstract = True

    def __str__(self):
        return self.name

# class CustomUserManager(BaseUserManager):
#     def create_user(self, login, password=None):
#         if not login:
#             raise ValueError('The Login field must be set')
#         user = self.model(login=login)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, login, password):
#         user = self.create_user(login, password=password)
#         user.is_admin = True
#         user.save(using=self._db)
#         return user

# class CustomUser(AbstractBaseUser):
#     login = models.CharField(max_length=30, unique=True)
#     # password = models.CharField(max_length=128)

#     is_active = models.BooleanField(default=True)
#     is_admin = models.BooleanField(default=False)

#     objects = CustomUserManager()

#     USERNAME_FIELD = 'login'
#     REQUIRED_FIELDS = []

#     def __str__(self):
#         return self.login

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
    # optional
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, null=True, blank=True)
    # Set to false on delete
    accesible = models.BooleanField(default=True)
    deleted_date = models.DateTimeField(null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)

class SectionType(NamedEntity):
    can_be_nested = models.BooleanField(default=False)

class SectionStatus(NamedEntity):
    pass

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
    status_data = models.TextField(null=True, blank=True)
    body = models.TextField()