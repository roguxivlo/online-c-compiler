from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class LoginFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = "/compiler/login/"
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_valid_login(self):
        response = self.client.post(self.login_url, {'username': self.username, 'password': self.password})
        self.assertRedirects(response, '/compiler/editor/show_file')  # Assuming successful login redirects to the home page

    def test_invalid_username(self):
        response = self.client.post(self.login_url, {'username': 'invaliduser', 'password': self.password})
        self.assertEqual(response.status_code, 200)  # Login page should be rendered again
        self.assertContains(response, 'Invalid login credentials')  # Assuming error message is displayed

    def test_invalid_password(self):
        response = self.client.post(self.login_url, {'username': self.username, 'password': 'invalidpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid login credentials')

    def test_empty_fields(self):
        response = self.client.post(self.login_url, {'username': '', 'password': ''})
        self.assertEqual(response.status_code, 200)

    def test_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.login_url, {'username': self.username, 'password': self.password})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid login credentials')  # Assuming inactive account error message is displayed


from .models import File

class IndexViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.index_url = '/compiler/editor/show_file'
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.item1 = File.objects.create(name='File 1', description='Description 1', owner=self.user)
        self.item2 = File.objects.create(name='File 2', description='Description 2', owner=self.user)

    def test_view_accessible_by_authenticated_user(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'compiler/index.html')

    def test_view_displays_items(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item1.name)
        self.assertContains(response, self.item2.name)

    def test_view_filters_items_by_user(self):
        other_user = User.objects.create_user(username='otheruser', password='otherpassword')
        File.objects.create(name='Other User File', description='Description', owner=other_user)

        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item1.name)
        self.assertContains(response, self.item2.name)
        self.assertNotContains(response, 'Other User File')

from .models import NamedEntity, Directory, File, SectionType, SectionStatus, Section

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_directory_creation(self):
        directory = Directory.objects.create(name='Test Directory', owner=self.user)
        self.assertEqual(directory.name, 'Test Directory')
        self.assertEqual(directory.owner, self.user)
        self.assertIsNotNone(directory.created)
        self.assertEqual(directory.accesible, True)
        self.assertIsNone(directory.deleted_date)
        self.assertIsNotNone(directory.last_modified)

    def test_file_creation(self):
        file = File.objects.create(name='Test File', owner=self.user)
        self.assertEqual(file.name, 'Test File')
        self.assertEqual(file.owner, self.user)
        self.assertIsNotNone(file.created)
        self.assertEqual(file.accesible, True)
        self.assertIsNone(file.deleted_date)
        self.assertIsNotNone(file.last_modified)

    def test_section_type_creation(self):
        section_type = SectionType.objects.create(name='Test Type', can_be_nested=True)
        self.assertEqual(section_type.name, 'Test Type')
        self.assertEqual(section_type.can_be_nested, True)

    def test_section_status_creation(self):
        section_status = SectionStatus.objects.create(name='Test Status')
        self.assertEqual(section_status.name, 'Test Status')

    def test_section_creation(self):
        file = File.objects.create(name='Test File', owner=self.user)
        section_type = SectionType.objects.create(name='Test Type', can_be_nested=True)
        section_status = SectionStatus.objects.create(name='Test Status')

        section = Section.objects.create(
            name='Test Section',
            file=file,
            begin=1,
            end=10,
            section_type=section_type,
            status=section_status,
            body='Section Body'
        )

        self.assertEqual(section.name, 'Test Section')
        self.assertEqual(section.file, file)
        self.assertIsNotNone(section.created)
        self.assertEqual(section.begin, 1)
        self.assertEqual(section.end, 10)
        self.assertEqual(section.section_type, section_type)
        self.assertEqual(section.status, section_status)
        self.assertIsNone(section.status_data)
        self.assertEqual(section.body, 'Section Body')

