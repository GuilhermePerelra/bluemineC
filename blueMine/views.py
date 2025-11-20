
from django.shortcuts import render

from usuario.models import Usuario

def home(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        senha = request.POST.get('senha')

        try:
            usuario_obj = Usuario.objects.get(usuario=usuario, senha=senha)
            return render(request, 'privado/demandas.html', {'nome': usuario_obj.nome})
        except Usuario.DoesNotExist:
            return render(request, 'publico/index.html', {'erro': 'Usuário ou senha inválidos.'})
    return render(request, 'publico/index.html')

def cadastro(request, tipo):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        nomeUsuario = request.POST.get('nomeUsuario')
        senha = request.POST.get('senha')
        tipo =  tipo.lower()

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
        case 'colaborador':
            return render(request, 'publico/cadastro.html', {'tipo': 'Colaborador'})
        case 'responsavel':
            return render(request, 'publico/cadastro.html', {'tipo': 'Responsável'})
        case _:
            return render(request, 'index.html')


   