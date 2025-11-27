from django.shortcuts import render, redirect
from usuario.models import Usuario, Tipo_Usuario
from demanda.models import Departamento

def checkSession(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return None
    try:
        return Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        request.session.flush()
        return None


def departamento(request):
    usuario_obj = checkSession(request)
    if not usuario_obj:
        return redirect('home')

    lideres = Usuario.objects.filter(tipo=Tipo_Usuario.LID)
    departamentos = Departamento.objects.all()

    return render(request, "privado/departamento.html", {
        'usuario_obj': usuario_obj,
        'lideres': lideres,
        'departamentos': departamentos,
    })


def criarDepartamento(request):
    usuario_obj = checkSession(request)
    if not usuario_obj:
        return redirect('home')

    if usuario_obj.tipo not in [Tipo_Usuario.LID, Tipo_Usuario.ADM]:
        return redirect('departamento')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        lideres_ids = request.POST.getlist('lideres')

        departamento = Departamento.objects.create(nome=nome)
        departamento.lideres.set(lideres_ids)

        return redirect('departamento')

    return redirect('departamento')


def editarDepartamento(request, id):
    usuario_obj = checkSession(request)
    if not usuario_obj:
        return redirect('home')

    if usuario_obj.tipo not in [Tipo_Usuario.LID, Tipo_Usuario.ADM]:
        return redirect('departamento')

    try:
        departamento = Departamento.objects.get(id=id)
    except Departamento.DoesNotExist:
        return redirect('departamento')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        lideres_ids = request.POST.getlist('lideres')

        departamento.nome = nome
        departamento.save()
        departamento.lideres.set(lideres_ids)

        return redirect('departamento')

    return redirect('departamento')


def excluirDepartamento(request, id):
    usuario_obj = checkSession(request)
    if not usuario_obj:
        return redirect('home')

    if usuario_obj.tipo not in [Tipo_Usuario.LID, Tipo_Usuario.ADM]:
        return redirect('departamento')

    try:
        departamento = Departamento.objects.get(id=id)
        departamento.delete()
    except Departamento.DoesNotExist:
        pass

    return redirect('departamento')
