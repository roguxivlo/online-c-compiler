from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.shortcuts import render, redirect
from .models import *
from datetime import datetime
import subprocess
import tempfile
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
import os
import json
import re 

def get_flags_string(flags):
    if 'none' not in flags:
        return " ".join(str(x) for x in flags)
    return ""

class asmLine:
    def __init__(self, line, refCLine, section, isParent) -> None:
        self.line = line
        self.refCLine = refCLine
        self.section = section
        self.isParent = isParent

def process_asm(context, asm_code):
    asm_lines = asm_code.split('\n')
    context['asmLines'] = []
    current_C_line = 0
    current_section = 0
    for line in asm_lines:
        # check if line contains substring "/tmp/" and if it does,
        # extract first integer after ':' sign in line:
        if '/tmp/' in line:
            match = re.search(r'(?<=:)\d+', line)
            if match:
                current_C_line = int(match.group())
        # check if the preceeding line and the next line start with ;-
        # if they do, then the current line is a parent line

        preceeding_line = asm_lines[asm_lines.index(line) - 1]
        next_line = asm_lines[asm_lines.index(line) + 1]
        if preceeding_line.startswith(';-') and next_line.startswith(';-') and line.startswith(';'):
            current_section = current_section + 1
            context['asmLines'].append(asmLine(line, current_C_line, current_section, True))
        else:
            context['asmLines'].append(asmLine(line, current_C_line, current_section, False))
        # if line.startswith(';-') and asm_lines[asm_lines.index(line) + 1].startswith(';-'):
        #     current_section = current_section + 1
        #     context['asmLines'].append(asmLine(line, current_C_line, current_section, True))
        # else:
        #     context['asmLines'].append(asmLine(line, current_C_line, current_section, False))


def compile(context, request, file_pk):
    file_to_display = File.objects.get(pk=file_pk)
    sections = file_to_display.section_set.all().order_by('begin')
    temp_file = tempfile.NamedTemporaryFile(suffix='.c', delete=False)
    with open(temp_file.name, 'w') as f:
        for section in sections:
            f.write(section.body + '\n')
    
    if 'STD' not in request.session or 'PROC' not in request.session:
        context['fail'] = "Nie wybrano standardu C lub procesora"
        return
    c_standard = request.session['STD']
    procesor = request.session['PROC']
    procesor=procesor.lower()
    c_standard=c_standard.lower()
    if 'OPT' in request.session:
        opt_string = get_flags_string(request.session['OPT'])
    else:
        opt_string = ""
    if 'DEP' in request.session:
        dep_string = get_flags_string(request.session['DEP'])
    else:
        dep_string = ""


    try:
        if opt_string:
            if dep_string:
                subprocess.check_output(['sdcc', f'-m{procesor}','-S', opt_string, dep_string, f'--std-{c_standard}', temp_file.name], stderr=subprocess.STDOUT)
            else:
                subprocess.check_output(['sdcc', f'-m{procesor}','-S', opt_string, f'--std-{c_standard}', temp_file.name], stderr=subprocess.STDOUT)
        else:
            if dep_string:
                subprocess.check_output(['sdcc', f'-m{procesor}','-S', dep_string, f'--std-{c_standard}', temp_file.name], stderr=subprocess.STDOUT)
            else:
                subprocess.check_output(['sdcc', f'-m{procesor}','-S',  f'--std-{c_standard}', temp_file.name], stderr=subprocess.STDOUT)
        # return result.decode('utf-8')
    except subprocess.CalledProcessError as e:
        context['fail'] = e.output.decode('utf-8')
        return
    # Read and print the .asm file
    with open(temp_file.name[5:-2] + '.asm', 'r') as asm_file:
        asm_code = asm_file.read()
    # delete temp_file.name[5:-2] + '.asm' file
    subprocess.check_output(['rm', temp_file.name[5:-2] + '.asm'])
    process_asm(context, asm_code)

class Dir:
    def __init__(self, name, children, files, pk):
        self.name = name
        self.children = children
        self.files = files
        self.pk = pk

def get_file_layout(user):
    # get all parent directories and files without a parent directory
    parent_dirs = Directory.objects.filter(parent=None, accesible=True, owner=user)
    free_files = File.objects.filter(directory=None, accesible=True, owner=user)

    def generate_subtree(dir: Directory):
        children = Directory.objects.filter(parent=dir, accesible=True, owner=user)
        files = File.objects.filter(directory=dir, accesible=True, owner=user)
        children_list = []
        for child in children:
            children_list.append(generate_subtree(child))
        
        return Dir(dir.name, children_list, files, dir.pk)
    
    parent_dir_list = []

    for dir in parent_dirs:
        parent_dir_list.append(generate_subtree(dir))

    return {"parent_dir_list": parent_dir_list, "free_files": free_files}

def parse_file_to_sections(code, file: File):
    linesByNewLine = code.split('\n')
    lines = []
    for line in linesByNewLine:
        if line != '':
            lines.append(line)

    # Each nonempty line is a separate section:
    for i in range(len(lines)):
        section_type = SectionType.objects.get(name="other")
        section_status = SectionStatus.objects.get(name="default")
        section = Section(name="", description="", file=file, parent=None, begin=i,
                          end=i+1, section_type=section_type, status=section_status,
                          status_data="", body=lines[i])
        section.save()

def get_text_from_section(section: Section):
    # s_type = section.section_type
    # if (s_type.can_be_nested == False):
    return section.body + "\n"
    # else:
    #     sections = Section.objects.filter(parent=section).order_by('begin')
    #     text = ""
    #     for section in sections:
    #         text += get_text_from_section(section)
    #     return text

"""
mode: "show_file" or "add_file" or "add_dir"
file_pk: pk of file to show
"""
def index(request, mode='show_file', file_pk=None):
    if not request.user.is_authenticated:
        return redirect('/compiler/login')
    user = request.user
    
    context=get_file_layout(user)
    context['mode'] = mode
    context['file_pk'] = file_pk
    context['user'] = user

    # Handle Post requests:
    if request.method == 'POST':
        if 'STD' in request.POST:
            request.session['STD'] = request.POST['STD']
        if 'OPT' in request.POST:
            request.session['OPT'] = request.POST.getlist('OPT')
        if 'PROC' in request.POST:
            request.session['PROC'] = request.POST['PROC']
        if 'DEP' in request.POST:
            request.session['DEP'] = request.POST.getlist('DEP')

    # get session variables and save them to context:
    try:
        context['STD'] = request.session['STD']
    except:
        pass
    try:
        context['OPT'] = request.session['OPT']
    except:
        pass
    try:
        context['PROC'] = request.session['PROC']
    except:
        pass
    try:
        context['DEP'] = request.session['DEP']
    except:
        pass

    if (mode == 'add_file'):
        directories = Directory.objects.filter(accesible=True, owner=user)
        # user = CustomUser.objects.all()
        
        context['directories'] = directories

        if request.method == 'POST' and 'file' in request.FILES:
            filename = request.FILES['file'].name
            owner_pk = request.POST.get('owner_pk')
            
            directory_pk = request.POST.get('parent_directory_pk')
            if directory_pk == "":
                directory_pk = None
                directory = None
            else:
                try:
                    directory = Directory.objects.get(pk=directory_pk)
                except Directory.DoesNotExist:
                    context['failure'] = 'Folder nie istnieje'
                    return render(request, 'compiler/index.html', context)
            
            if directory_pk != None and Directory.objects.get(pk=directory_pk).owner != user:
                context['failure'] = 'Folder nie należy do właściciela'
                return render(request, 'compiler/index.html', context)
            
            # check if file already exists in directory:
            if (File.objects.filter(directory=directory, name=filename, accesible=True, owner=user).exists()):
                context['failure'] = 'Plik o podanej nazwie już istnieje w tym folderze'
                return render(request, 'compiler/index.html', context)
            
            description = request.POST.get('file_description')
            if description == None:
                description = ""

            file = File(name=filename, owner=user, directory=directory, description=description)
            file.save()
            parse_file_to_sections(request.FILES['file'].read().decode('utf-8'), file)

    elif (mode == 'add_dir'):
        # get all directories:
        directories = Directory.objects.filter(accesible=True, owner=user)
        context['directories'] = directories

        if request.method == 'POST':
            directory_name = request.POST.get('directory_name')
            parent_directory_pk = request.POST.get('parent_directory_pk')
            if (parent_directory_pk == ""):
                parent_directory = None
            else:
                try:
                    parent_directory = Directory.objects.get(pk=parent_directory_pk, owner=user)
                except Directory.DoesNotExist:
                    context['failure'] = 'Lokalizacja nie istnieje lub ma innego właściciela'
                    return render(request, 'compiler/index.html', context)
            
            # check if directory already exists in parent:
            if (Directory.objects.filter(parent=parent_directory, name=directory_name, accesible=True).exists()):
                context['failure'] = 'Folder o podanej nazwie już istnieje w tym folderze'
                return render(request, 'compiler/index.html', context)
            
            # owner_pk = request.POST.get('owner_pk')
            # try:
            #     owner = User.objects.get(pk=owner_pk)
            # except User.DoesNotExist:
            #     context['failure'] = 'Właściciel nie istnieje'
            #     return render(request, 'compiler/index.html', context)
            
            description = request.POST.get('description')
            if description == None:
                description = ""
            
            # create directory:
            new_directory = Directory(name=directory_name, parent=parent_directory, owner=user, description=description)
            new_directory.save()
            context = get_file_layout(user)
            # get all directories:
            directories = Directory.objects.filter(accesible=True)
            context['directories'] = directories
            context['user'] = user
            context['success'] = 'Folder dodany'
        
    elif (mode == 'show_file' and file_pk != None):
        if (file_pk == None):
            return render(request, 'compiler/index.html', context)

        try:
            compile(context, request, file_pk)

        except File.DoesNotExist:
            return render(request, 'compiler/index.html', context)

        source_code = ""

        file_to_display = File.objects.get(pk=file_pk, owner=user)
        if (file_to_display):
            sections = Section.objects.filter(file=file_to_display).order_by('begin')
            for section in sections:
                source_code += get_text_from_section(section)

        context["source_code"] = source_code
        
    return render(request, 'compiler/index.html', context)

def show_file(request, file_pk):
    context = {}
    sections = []

    file_to_display = File.objects.get(pk=file_pk)
    if (file_to_display):
        sections = Section.objects.filter(file=file_to_display).order_by('begin')
    
    context['sections'] = sections
    return render(request, 'compiler/show_file.html', context)

def compile_file(request, file_pk):
    context = {}
    # get session variables and save them to context:
    try:
        context['STD'] = request.session['STD']
    except:
        pass
    try:
        context['OPT'] = request.session['OPT']
    except:
        pass
    try:
        context['PROC'] = request.session['PROC']
    except:
        pass
    try:
        context['DEP'] = request.session['DEP']
    except:
        pass

    compile(context, request, file_pk)
    return render(request, "compiler/show_asm.html", context)

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

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if username == "":
                form.add_error(None, 'This field is required')
                return render(request, 'compiler/login.html', {'form': form})
            if password == "":
                form.add_error(None, 'This field is required')
                return render(request, 'compiler/login.html', {'form': form})
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/compiler/editor/show_file')
            else:
                form.add_error(None, 'Invalid login credentials')
    else:
        form = LoginForm()

    return render(request, 'compiler/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('/compiler/login')

@login_required
def delete_file(request, file_pk):
    context = {'source_code': 'Usunięto plik'}
    user = request.user
    

    try:
        file_to_delete = File.objects.filter(pk = file_pk, accesible = True, owner=user)
    except File.DoesNotExist:
        context['failure'] = 'Wybrany plik nie istnieje lub został usunięty'
        return render(request, 'compiler/index.html', context)
    
    # check if file exists:
    if (file_to_delete):
        file_to_delete = file_to_delete[0]

    file_to_delete.accesible = False
    file_to_delete.deleted_date = datetime.now()
    if (file_to_delete):
        file_to_delete.save()
    context = get_file_layout(user)
    context['user'] = user


    return render(request, 'compiler/index.html', context)

@login_required
def delete_directory(request, dir_pk):
    context = {'source_code': 'Usunięto folder'}
    user = request.user
    

    dir_to_delete = Directory.objects.get(pk=dir_pk, owner=user)

    # Recursively set all subdirectories and files to inaccessible:
    clean(dir_to_delete)
    

    context = get_file_layout(user)
    context['user'] = user
    context['success']='Usunięto folder'


    return render(request, 'compiler/index.html', context)

def generate_file_tree_html(request):
    user = request.user
    context = get_file_layout(user)
    context['user'] = user
    return render(request, 'compiler/files_view.html', context)

def generate_file_form_html(request):
    context = {}
    user = request.user
    context['user'] = user
    directories = Directory.objects.filter(accesible=True, owner=user)
    context['directories'] = directories
    return render(request, 'compiler/add_file.html', context)

def generate_directory_form_html(request):
    context = {}
    user = request.user
    context['user'] = user
    directories = Directory.objects.filter(accesible=True, owner=user)
    context['directories'] = directories
    return render(request, 'compiler/add_directory.html', context)
