from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from demanda.models import Demanda
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

    return render(request, "privado/demandas.html", {
        'usuario_obj': usuario_obj,
        'funcionarios': funcionarios,
        'departamentos': departamentos,
        'demandas': demandas,
    })


def criarDemanda(request):
    if request.method == "POST":
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return redirect('home')

        lider = Usuario.objects.get(id=usuario_id)

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

    return redirect("demandas")


def excluirDemanda(request, id):
    demanda = get_object_or_404(Demanda, id=id)

    if request.method == "POST":
        demanda.delete()
        return redirect("demandas")

    return redirect("demandas")


def minhas_demandas(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('home')

    usuario_obj = Usuario.objects.get(id=usuario_id)
    demandas = Demanda.objects.filter(funcionario=usuario_obj)

    return render(request, "privado/minhasDemandas.html", {
        'usuario_obj': usuario_obj,
        'demandas': demandas,
    })
