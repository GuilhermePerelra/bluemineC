from django.shortcuts import render, redirect
from demanda.models import Demanda
from usuario.models import Tipo_Usuario, Usuario

def home(request):
    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        return redirect('demandas')

    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        senha = request.POST.get('senha')
        try:
            usuario_obj = Usuario.objects.get(usuario=usuario, senha=senha)
            request.session['usuario_id'] = usuario_obj.id
            return redirect("demandas")
        except Usuario.DoesNotExist:
            return render(request, 'publico/index.html', {'erro': 'Usuário ou senha inválidos.'})

    return render(request, 'publico/index.html')


def logout(request):
    if 'usuario_id' in request.session:
        del request.session['usuario_id']
    return redirect('home')

def cadastro(request, tipo):
    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        return redirect('demandas')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        nomeUsuario = request.POST.get('nomeUsuario')
        senha = request.POST.get('senha')

        tipo_lower = tipo.lower()
        if tipo_lower == "colaborador":
            tipo_usuario = Tipo_Usuario.FUNC
        elif tipo_lower == "lider":
            tipo_usuario = Tipo_Usuario.LID
        elif tipo_lower == "adm":
            tipo_usuario = Tipo_Usuario.ADM
        else:
            tipo_usuario = Tipo_Usuario.FUNC

        usuarioNovo = Usuario(
            nome=nome,
            email=email,
            usuario=nomeUsuario,
            senha=senha,
            tipo=tipo_usuario
        )
        usuarioNovo.save()
        request.session['usuario_id'] = usuarioNovo.id
        return redirect('demandas')

    match tipo:
        case 'lider':
            return render(request, 'publico/cadastro.html', {'tipo': 'lider'})
        case 'colaborador':
            return render(request, 'publico/cadastro.html', {'tipo': 'colaborador'})
        case _:
            return render(request, 'publico/index.html')
