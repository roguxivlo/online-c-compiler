from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from .models import *
from datetime import datetime



class Dir:
    def __init__(self, name, children, files, pk):
        self.name = name
        self.children = children
        self.files = files
        self.pk = pk

def get_file_layout():
    # get all parent directories and files without a parent directory
    parent_dirs = Directory.objects.filter(parent=None, accesible=True)
    free_files = File.objects.filter(directory=None, accesible=True)

    def generate_subtree(dir: Directory):
        children = Directory.objects.filter(parent=dir, accesible=True)
        files = File.objects.filter(directory=dir, accesible=True)
        children_list = []
        for child in children:
            children_list.append(generate_subtree(child))
        
        return Dir(dir.name, children_list, files, dir.pk)
    
    parent_dir_list = []

    for dir in parent_dirs:
        parent_dir_list.append(generate_subtree(dir))

    return {"parent_dir_list": parent_dir_list, "free_files": free_files}

def parse_file_to_sections(code, file: File):
    lines = code.count('\n')
    section_type = SectionType.objects.get(name="other")
    section_status = SectionStatus.objects.get(name="default")
    section = Section(name="", description="", file=file, parent=None, begin=0,
                      end=lines, section_type=section_type, status=section_status,
                      status_data="", body=code)
    section.save()


def index(request):
    # template = loader.get_template('compiler/index.html')

    context = get_file_layout()

    file_pk = request.POST.get('file_pk')
    print(request.POST)
    if (file_pk == None):
        return render(request, 'compiler/index.html', context)
    
    try:
        file_to_display = File.objects.get(pk=file_pk)
    except File.DoesNotExist:
        return render(request, 'compiler/index.html', context)
    
    source_code = ""

    def get_text_from_section(section: Section):
        s_type = section.section_type
        if (s_type.can_be_nested == False):
            return section.body + "\n"
        else:
            sections = Section.objects.filter(parent=section).order_by('begin')
            text = ""
            for section in sections:
                text += get_text_from_section(section)
            return text


    if (file_to_display):
        sections = Section.objects.filter(file=file_to_display).order_by('begin')
        for section in sections:
            source_code += get_text_from_section(section)

    context["source_code"] = source_code
    return render(request, 'compiler/index.html', context)

def file_upload(request):
    context = get_file_layout()
    directories = Directory.objects.filter(accesible=True)
    users = User.objects.all()
    context['users'] = users
    context['directories'] = directories

    if request.method == 'POST':
        filename = request.FILES['file'].name
        print(filename)
        print(request.POST)
        owner_pk = request.POST.get('owner_pk')
        try:
            owner = User.objects.get(pk=owner_pk)
        except User.DoesNotExist:
            context['failure'] = 'Właściciel nie istnieje'
            return render(request, 'compiler/file_upload.html', context)
        
        directory_pk = request.POST.get('parent_directory_pk')
        if directory_pk == "":
            directory_pk = None
            directory = None
        else:
            try:
                directory = Directory.objects.get(pk=directory_pk)
            except Directory.DoesNotExist:
                context['failure'] = 'Folder nie istnieje'
                return render(request, 'compiler/file_upload.html', context)
        
        if directory_pk != None and Directory.objects.get(pk=directory_pk).owner != owner:
            context['failure'] = 'Folder nie należy do właściciela'
            return render(request, 'compiler/file_upload.html', context)
        
        neighbour_files = File.objects.filter(directory=directory)
        # check if file already exists in directory:
        if (File.objects.filter(directory=directory, name=filename, accesible = True).exists()):
            context['failure'] = 'Plik o podanej nazwie już istnieje w tym folderze'
            return render(request, 'compiler/file_upload.html', context)
        
        description = request.POST.get('file_description')
        if description == None:
            description = ""

        file = File(name=filename, owner=owner, directory=directory, description=description)
        file.save()
        parse_file_to_sections(request.FILES['file'].read().decode('utf-8'), file)
    return render(request, 'compiler/file_upload.html', context)

def create_directory(request):
    context = get_file_layout()
    # get all directories:
    directories = Directory.objects.filter(accesible=True)
    context['directories'] = directories
    users = User.objects.all()
    context['users'] = users

    if request.method == 'POST':
        print(request.POST)
        directory_name = request.POST.get('directory_name')
        parent_directory_pk = request.POST.get('parent_directory_pk')
        if (parent_directory_pk == ""):
            parent_directory = None
        else:
            try:
                parent_directory = Directory.objects.get(pk=parent_directory_pk)
            except Directory.DoesNotExist:
                context['failure'] = 'Lokalizacja nie istnieje'
                return render(request, 'compiler/create_directory.html', context)
        
        # check if directory already exists in parent:
        if (Directory.objects.filter(parent=parent_directory, name=directory_name, accesible=True).exists()):
            context['failure'] = 'Folder o podanej nazwie już istnieje w tym folderze'
            return render(request, 'compiler/create_directory.html', context)
        
        owner_pk = request.POST.get('owner_pk')
        try:
            owner = User.objects.get(pk=owner_pk)
        except User.DoesNotExist:
            context['failure'] = 'Właściciel nie istnieje'
            return render(request, 'compiler/create_directory.html', context)
        
        neighbour_directories = Directory.objects.filter(parent=parent_directory)
        
        description = request.POST.get('description')
        if description == None:
            description = ""
        
        # create directory:
        new_directory = Directory(name=directory_name, parent=parent_directory, owner=owner, description=description)
        new_directory.save()
        context = get_file_layout()
        # get all directories:
        directories = Directory.objects.filter(accesible=True)
        context['directories'] = directories
        context['users'] = users
        context['success'] = 'Folder dodany'
        return render(request, 'compiler/create_directory.html', context)
    else:
        return render(request, 'compiler/create_directory.html', context)
    
def file_delete(request):
    context = get_file_layout()
    context['source_code'] = 'Wybierz plik do usunięcia po lewej'
    if request.method == 'POST':
        print(request.POST)
        file_to_delete_pk = request.POST.get('file_pk')
        
        if (file_to_delete_pk == None):
            return render(request, 'compiler/file_delete.html', context)
        
        try:
            file_to_delete = File.objects.filter(pk = file_to_delete_pk, accesible = True)
        except File.DoesNotExist:
            context['failure'] = 'Wybrany plik nie istnieje lub został usunięty'
            return render(request, 'compiler/file_delete.html', context)
        
        file_to_delete = file_to_delete[0]

        file_to_delete.accesible = False
        file_to_delete.deleted_date = datetime.now()
        file_to_delete.save()
        context = get_file_layout()
        return render(request, 'compiler/file_delete.html', context)
    else:
        return render(request, 'compiler/file_delete.html', context)

def clean(dir:Directory):
    files=File.objects.filter(directory=dir)
    for f in files:
        f.accesible=False
        f.deleted_date=datetime.now()
        f.save()

    subdirs=Directory.objects.filter(parent=dir)
    for subdir in subdirs:
        clean(subdir)

    dir.accesible=False
    dir.deleted_date=datetime.now()
    dir.save()

def delete_directory(request):
    context = get_file_layout()
    context['source_code'] = 'Wybierz folder do usunięcia po lewej'
    if request.method == 'POST':
        dir_pk = request.POST.get('dir_pk')
        dir_to_delete = Directory.objects.get(pk=dir_pk)
        print(dir_to_delete.name)
        # Recursively set all subdirectories and files to inaccessible:
        clean(dir_to_delete)
        context['success']='Usunięto folder'
        return render(request, 'compiler/delete_directory.html', context)
    else:
        return render(request, 'compiler/delete_directory.html', context)
