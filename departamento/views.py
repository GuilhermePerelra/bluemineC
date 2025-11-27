from django.shortcuts import render, redirect
from usuario.models import Usuario, Tipo_Usuario
from demanda.models import Departamento
from django.contrib import messages
from django.shortcuts import get_object_or_404

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
    funcionarios = Usuario.objects.filter(tipo=Tipo_Usuario.FUNC)
    # funcionários sem departamento (não presentes em qualquer departamento.membros)
    funcionarios_sem_departamento = [u for u in funcionarios if not u.departamentos.exists()]
    if usuario_obj.tipo == Tipo_Usuario.FUNC:
        departamentos = Departamento.objects.filter(membros=usuario_obj)
    else:
        departamentos = Departamento.objects.all()

    return render(request, "privado/departamento.html", {
        'usuario_obj': usuario_obj,
        'lideres': lideres,
        'funcionarios': funcionarios,
        'funcionarios_sem_departamento': funcionarios_sem_departamento,
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
        # admins can choose líderes; se criador for líder (não admin), ele se torna líder por padrão
        if usuario_obj.tipo == Tipo_Usuario.ADM:
            lideres_ids = request.POST.getlist('lideres')
        else:
            lideres_ids = [str(usuario_obj.id)]

        departamento = Departamento.objects.create(nome=nome)
        departamento.lideres.set(lideres_ids)
        membros_ids = request.POST.getlist('membros')
        if membros_ids:
            departamento.membros.set(membros_ids)

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

        membros_ids = request.POST.getlist('membros')
        if membros_ids:
            departamento.membros.set(membros_ids)

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


def sairDepartamento(request, id):
    """Remove the current user from departamento.lideres.
    Block the operation if it would leave the department without any leader.
    """
    usuario_obj = checkSession(request)
    if not usuario_obj:
        return redirect('home')

    try:
        departamento = Departamento.objects.get(id=id)
    except Departamento.DoesNotExist:
        messages.error(request, 'Departamento não encontrado.')
        return redirect('departamento')

    # Only current leaders or admins may perform leave
    if usuario_obj not in departamento.lideres.all() and usuario_obj.tipo != Tipo_Usuario.ADM:
        messages.error(request, 'Você não tem permissão para sair deste departamento.')
        return redirect('departamento')

    if request.method == 'POST':
        # If removing this leader would leave zero leaders, block
        current_leaders = list(departamento.lideres.all())
        if usuario_obj in current_leaders:
            if len(current_leaders) <= 1:
                messages.error(request, 'Não é possível sair: este departamento ficaria sem líderes substitutos.')
                return redirect('departamento')

            departamento.lideres.remove(usuario_obj)
            messages.success(request, 'Você saiu do grupo de líderes deste departamento.')
            return redirect('departamento')

    return redirect('departamento')
