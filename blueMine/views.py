
from django.forms import model_to_dict
from django.shortcuts import render, redirect

from demanda.models import Demanda
from usuario.models import Tipo_Usuario, Usuario

def home(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        senha = request.POST.get('senha')

        try:
            usuario_obj = Usuario.objects.get(usuario=usuario, senha=senha)
            request.session['usuario_id'] = usuario_obj.id
            
            listaFuncionarios = Usuario.objects.filter(tipo = Tipo_Usuario.FUNC)
            listaFuncionarios = [model_to_dict(func, fields=['id', 'nome']) for func in listaFuncionarios]
            
            if (usuario_obj.tipo == Tipo_Usuario.LID):
                departamentos = usuario_obj.departamentos_liderados.all()
                demandas = Demanda.objects.filter(departamento__in=departamentos)
            elif (usuario_obj.tipo == Tipo_Usuario.FUNC):
                demandas = Demanda.objects.filter(funcionario = usuario_obj)
            else:
                demandas = Demanda.objects.all()
            
            return render(request, 'privado/demandas.html', 
                          {'usuario_obj': usuario_obj,
                           'funcionarios': listaFuncionarios
                           })
        except Usuario.DoesNotExist:
            return render(request, 'publico/index.html', {'erro': 'Usuário ou senha inválidos.'})
        
    return render(request, 'publico/index.html')

def logout(request):
    request.session.flush()
    return redirect('home')

def cadastro(request, tipo):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        nomeUsuario = request.POST.get('nomeUsuario')
        senha = request.POST.get('senha')
        tipo =  tipo.lower()
        
        if tipo == "colaborador":
            tipo = Tipo_Usuario.FUNC
        elif tipo == "lider":
            tipo = Tipo_Usuario.LID
        elif tipo == "adm":
            tipo = Tipo_Usuario.ADM
        else:
            tipo = Tipo_Usuario.FUNC

        usuarioNovo = Usuario(
            nome=nome,
            email=email,
            usuario=nomeUsuario,
            senha=senha,
            tipo=tipo
        )
        usuarioNovo.save()
        return render (request, 'publico/index.html', {'nome': nome})

    match(tipo):
        case 'lider':
            return render(request, 'publico/cadastro.html', {'tipo': 'lider'})
        case 'responsavel':
            return render(request, 'publico/cadastro.html', {'tipo': 'responsável'})
        case _:
            return render(request, 'index.html')


   