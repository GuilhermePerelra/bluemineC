from django.shortcuts import render, redirect
from usuario.models import Usuario, Tipo_Usuario
from departamento.models import Departamento
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden

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
        # admins conseguem escolher lideres; se criador for líder (não admin), ele se torna líder por padrão
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
        #Pega lista de ids dos lideres na requisição
        lideres_ids = request.POST.getlist('lideres') if 'lideres' in request.POST else None

        departamento.nome = nome
        departamento.save()

        if lideres_ids is not None:
            # verifica se a lista ta vazia
            if len(lideres_ids) == 0:
                messages.error(request, 'O departamento precisa ter pelo menos um líder.')
            else:
                # Previne o lider logado de se remover, verificando se esta na lista de ids de lideres enviada
                if usuario_obj in departamento.lideres.all() and str(usuario_obj.id) not in lideres_ids:
                    messages.error(request, 'Você não pode remover a si mesmo via edição. Use o botão "Sair do departamento" para sair como líder.')
                else:
                    departamento.lideres.set(lideres_ids)

        #Pega lista de membros se estiver na requisição
        membros_ids = request.POST.getlist('membros') if 'membros' in request.POST else None
        if membros_ids is not None:
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
    usuario_obj = checkSession(request)
    if not usuario_obj:
        return redirect('home')

    try:
        departamento = Departamento.objects.get(id=id)
    except Departamento.DoesNotExist:
        messages.error(request, 'Departamento não encontrado.')
        return redirect('departamento')

    # verifica se o usuario é lider de algum departamento ou se é tipo admin
    if usuario_obj not in departamento.lideres.all() and usuario_obj.tipo != Tipo_Usuario.ADM:
        messages.error(request, 'Você não tem permissão para sair deste departamento.')
        return redirect('departamento')

    if request.method == 'POST':
        current_leaders = list(departamento.lideres.all())
        if usuario_obj in current_leaders:
        #Bloqueia de sair do departamento se não tiver algum lider substituto
            if len(current_leaders) <= 1:
                messages.error(request, 'Não é possível sair: este departamento ficaria sem líderes substitutos.')
                return redirect('departamento')

            departamento.lideres.remove(usuario_obj)
            messages.success(request, 'Você saiu do grupo de líderes deste departamento.')
            return redirect('departamento')

    return redirect('departamento')


def removerMembro(request, dep_id, usuario_id):
    """Remove a member from departamento.membros. Allowed for ADM or department leaders."""
    usuario_obj = checkSession(request)
    if not usuario_obj:
        return redirect('home')

    try:
        departamento = Departamento.objects.get(id=dep_id)
    except Departamento.DoesNotExist:
        messages.error(request, 'Departamento não encontrado.')
        return redirect('departamento')

    # Verifica se o usuario atual é um lider ou um admin
    if usuario_obj.tipo != Tipo_Usuario.ADM and usuario_obj not in departamento.lideres.all():
        return HttpResponseForbidden('Sem permissão')

    if request.method == 'POST':
        try:
            membro = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuário não encontrado.')
            return redirect('departamento')

        if membro in departamento.membros.all():
            departamento.membros.remove(membro)
            messages.success(request, f'Usuário {membro.nome} removido do departamento.')
        else:
            messages.info(request, 'Usuário não é membro deste departamento.')

    return redirect('departamento')
