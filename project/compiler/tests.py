from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from .views import *

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
        # create temp directory
        tmp = Directory.objects.create(name='tmp', description='tmp directory', owner=self.user)
        
    def test_compile(self):
        context = {}
        request = RequestFactory().get('/')
        request.session = {}
        # create empty file object and save it to database:
        files = File.objects.all()
        file_pk = files[0].pk
        compile(context, request, file_pk)
        self.assertGreater(len(context['fail']), 0)

    def test_compile_bad_std_proc(self):
        context = {'STD': 'example', 'PROC': 'badproc'}
        request = RequestFactory().get('/')
        request.session = context
        # create empty file object and save it to database:
        files = File.objects.all()
        file_pk = files[0].pk
        compile(context, request, file_pk)
        self.assertGreater(len(context['fail']), 0)

    def test_compile_bad_std_proc_bad_deps(self):
        context = {'STD': 'example', 'PROC': 'badproc', 'DEP': 'somedeps'}
        request = RequestFactory().get('/')
        request.session = context
        # create empty file object and save it to database:
        files = File.objects.all()
        file_pk = files[0].pk
        compile(context, request, file_pk)
        self.assertGreater(len(context['fail']), 0)
        context = {'STD': 'example', 'PROC': 'badproc', 'OPT': 'somedeps'}
        compile(context, request, file_pk)

    def test_compile_bad_std_proc_bad_deps_opts(self):
        context = {'STD': 'example', 'PROC': 'badproc', 'DEP': 'somedeps', 'OPT': 'something'}
        request = RequestFactory().get('/')
        request.session = context
        # create empty file object and save it to database:
        files = File.objects.all()
        file_pk = files[0].pk
        compile(context, request, file_pk)
        self.assertGreater(len(context['fail']), 0)

    def test_parse_file_to_sections(self):
        parse_file_to_sections("", self.item1)
        # if no exception thrown, then pass
        self.assertTrue(True)
        # create SectionType object with name 'other'
        a = SectionType.objects.create(name='other', can_be_nested=False)
        b = SectionStatus.objects.create(name='default')
        # save SectionType object to database
        a.save()
        b.save()
        parse_file_to_sections("some\nline\nseparated\nby\nnewline", self.item1)

    def test_view_accessible_by_authenticated_user(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'compiler/index.html')
        # create request with request.method=POST
        request = RequestFactory().post(self.index_url)
        # add user to request
        request.user = self.user
        # add POST data to request
        request.POST = {'STD': 'test', 'PROC': 'test description', 'parent_directory_pk': '123'}
        # add file to request.FILES
        request.FILES['file'] = self.item1
        # add session to request
        request.session = {}
        # pass request to index view
        response = index(request, 'add_file')
        response = index(request, 'add_dir')
        response = index(request, 'show_file', self.item1.pk)
        response = compile_file(request, self.item1.pk)
        response = show_file(request, self.item1.pk)
        response = delete_file(request, self.item1.pk)
        self.item1.accesible = False
        self.item1.save()
        response = delete_file(request, self.item1.pk)

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

    def test_generate_file_tree_html(self):
        request = RequestFactory().get('/')
        request.session = {}
        # set request.user:
        request.user = self.user
        generate_file_tree_html(request)
        generate_file_form_html(request)
        generate_directory_form_html(request)
        try:
            # delete tmp directory
            # get tmp pk
            tmp = Directory.objects.get(name='tmp')
            delete_directory(request, tmp.pk)
        except:
            pass
        # if no exception thrown, then pass
        self.assertTrue(True)

from .models import NamedEntity, Directory, File, SectionType, SectionStatus, Section

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_Get_file_layout(self):
        context = get_file_layout(self.user)
        # assert that context['parent_dir_list'] and context['free_files'] exist and are empty:
        self.assertEqual(len(context['parent_dir_list']), 0)
        self.assertEqual(len(context['free_files']), 0)

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

    def test_get_text_from_section(self):
        file = File.objects.create(name='Test File', owner=self.user)
        section_type = SectionType.objects.create(name='Test Type', can_be_nested=False)
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
        self.assertEqual(get_text_from_section(section), 'Section Body\n')

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

class TestGet_Flags_string(TestCase):
    def setUp(self):
        self.flags = ["none"]

    def test_get_flags_string(self):
        self.assertEqual(get_flags_string(self.flags), "")

class TestProcess_Asm(TestCase):
    def test_Process_Asm(self):
        context = {}
        process_asm(context, "line\nline")
        self.assertEqual(len(context['asmLines']), 2)
        context = {}
        process_asm(context, "line\nline\n/tmp/ in line: :12:)\n;-costam\n;costam\n;-costam")
        self.assertEqual(len(context['asmLines']), 6)


class TestDirClass(TestCase):
    def test_1(self):
        dir = Dir("name", "children", "files", 12)
        self.assertEqual(dir.name, "name")
        self.assertEqual(dir.children, "children")
        self.assertEqual(dir.files, "files")
        self.assertEqual(dir.pk, 12)

