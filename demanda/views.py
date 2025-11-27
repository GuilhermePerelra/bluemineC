from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from demanda.models import Demanda, Tipo_Status
from usuario.models import Usuario, Tipo_Usuario
from departamento.models import Departamento


def demandas(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('home')

    usuario_obj = Usuario.objects.get(id=usuario_id)
    funcionarios = Usuario.objects.filter(tipo=Tipo_Usuario.FUNC)
    departamentos = Departamento.objects.all()

    if usuario_obj.tipo == Tipo_Usuario.LID:
        deps_lider = usuario_obj.departamentos_liderados.all()
        demandas = Demanda.objects.filter(lider=usuario_obj)
    elif usuario_obj.tipo == Tipo_Usuario.FUNC:
        demandas = Demanda.objects.filter(funcionario=usuario_obj)
    else:
        demandas = Demanda.objects.all()

    # provide status choices for templates (avoid _meta access in templates)
    try:
        status_choices = Demanda._meta.get_field('status').choices
    except Exception:
        status_choices = Tipo_Status.choices

    return render(request, "privado/demandas.html", {
        'usuario_obj': usuario_obj,
        'funcionarios': funcionarios,
        'departamentos': departamentos,
        'demandas': demandas,
        'status_choices': status_choices,
    })


def criarDemanda(request):
    if request.method == "POST":
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return redirect('home')

        usuario_obj = Usuario.objects.get(id=usuario_id)
        # permitir criação apenas para usuários com privilégio (LID/ADM)
        if not usuario_obj.temPrivilegio():
            return redirect('demandas')

        lider = usuario_obj

        funcionario = Usuario.objects.get(id=request.POST.get('funcionario'))
        departamento = Departamento.objects.get(id=request.POST.get('departamento'))

        prazo_str = request.POST.get('prazo')  # ex: '2025-11-27T05:00'
        demanda = Demanda(
            titulo=request.POST.get('titulo'),
            descricao=request.POST.get('descricao'),
            funcionario=funcionario,
            lider=lider,
            departamento=departamento,
            tipo=request.POST.get('tipo'),
            prazo = datetime.strptime(prazo_str, '%Y-%m-%dT%H:%M')
        )

        anexo = request.FILES.get('anexo')
        if anexo:
            demanda.anexo = anexo

        demanda.save()
        return redirect("demandas")

    return redirect("demandas")


def editarDemanda(request, id):
    demanda = get_object_or_404(Demanda, id=id)
    if request.method == "POST":
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return redirect('home')
        usuario_obj = Usuario.objects.get(id=usuario_id)

        # usuários privilegiados (LID/ADM) podem editar todos os campos
        if usuario_obj.temPrivilegio():
            demanda.titulo = request.POST.get('titulo')
            demanda.descricao = request.POST.get('descricao')
            demanda.funcionario = Usuario.objects.get(id=request.POST.get('funcionario'))
            demanda.departamento = Departamento.objects.get(id=request.POST.get('departamento'))
            demanda.tipo = request.POST.get('tipo')
            demanda.prazo = request.POST.get('prazo')

            anexo = request.FILES.get('anexo')
            if anexo:
                demanda.anexo = anexo

            demanda.save()
            return redirect("demandas")

        # funcionário pode alterar somente descricao e status de sua própria demanda
        if demanda.funcionario_id == usuario_obj.id:
            demanda.descricao = request.POST.get('descricao', demanda.descricao)
            new_status = request.POST.get('status')
            # validar status
            try:
                allowed = [c[0] for c in Demanda._meta.get_field('status').choices]
            except Exception:
                allowed = []
            if new_status and new_status in allowed:
                demanda.status = new_status
            demanda.save()
            return redirect("demandas")

        # caso não tenha permissão
        return redirect("demandas")

    return redirect("demandas")


def excluirDemanda(request, id):
    demanda = get_object_or_404(Demanda, id=id)
    if request.method == "POST":
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return redirect('home')
        usuario_obj = Usuario.objects.get(id=usuario_id)

        # permitir exclusão apenas para ADM ou líder da demanda
        if usuario_obj.tipo == Tipo_Usuario.ADM or demanda.lider_id == usuario_obj.id:
            demanda.delete()
        return redirect("demandas")

    return redirect("demandas")


def minhas_demandas(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('home')

    usuario_obj = Usuario.objects.get(id=usuario_id)
    demandas = Demanda.objects.filter(funcionario=usuario_obj)

    try:
        status_choices = Demanda._meta.get_field('status').choices
    except Exception:
        status_choices = Tipo_Status.choices

    return render(request, "privado/minhasDemandas.html", {
        'usuario_obj': usuario_obj,
        'demandas': demandas,
        'status_choices': status_choices,
    })


def reatribuirDemanda(request, id):
    # permite que liders e o funcionario atual reatribua a outro funcionario do mesmo departamento
    if request.method != 'POST':
        return redirect('demandas')

    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('home')
    usuario_obj = Usuario.objects.get(id=usuario_id)

    demanda = get_object_or_404(Demanda, id=id)

    # permitir se for lider/adm ou o funcionario atual
    if not (usuario_obj.temPrivilegio() or demanda.funcionario_id == usuario_obj.id):
        return redirect('demandas')

    novo_id = request.POST.get('novo_funcionario')
    try:
        novo = Usuario.objects.get(id=int(novo_id))
    except Exception:
        return redirect('demandas')

    # somente para funcionários
    if novo.tipo != Tipo_Usuario.FUNC:
        return redirect('demandas')

    # se usuário atual é privilegiado (LID/ADM) permite reatribuir para qualquer FUNC
    if usuario_obj.temPrivilegio():
        demanda.funcionario = novo
        demanda.save()
        return redirect('demandas')

    # se usuário atual é FUNC, só permite reatribuir para FUNC que já tenham demanda no mesmo departamento
    has_worked = Demanda.objects.filter(funcionario=novo, departamento=demanda.departamento).exists()
    if has_worked:
        demanda.funcionario = novo
        demanda.save()

    return redirect('demandas')
