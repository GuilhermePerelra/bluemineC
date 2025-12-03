from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from demanda.models import Demanda, Tipo_Status
from usuario.models import Usuario, Tipo_Usuario
from departamento.models import Departamento
from django.contrib import messages
from django.http import JsonResponse


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

    
    try:
        demandas = demandas.select_related('funcionario', 'departamento', 'lider')
    except Exception:
        pass

    
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
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('home')
    usuario_obj = Usuario.objects.get(id=usuario_id)

    
    if request.method != 'POST':
        return redirect('demandas')
    
    original_funcionario_id = demanda.funcionario_id

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
    if original_funcionario_id == usuario_obj.id:
        original_descr = demanda.descricao
        original_status = demanda.status

        novo_id = request.POST.get('novo_funcionario')
        new_status = request.POST.get('status')

       
        if novo_id:
            try:
                novo = Usuario.objects.get(id=int(novo_id))
            except Exception:
                novo = None

            if not novo:
                messages.error(request, 'Funcionário selecionado inválido.')
            elif novo.id == usuario_obj.id:
                messages.error(request, 'Não é possível reatribuir para si mesmo.')
            else:
                if novo.tipo == Tipo_Usuario.FUNC:
                    allowed = False
                    worked = False
                    try:
                        if novo.departamentos.filter(id=demanda.departamento_id).exists():
                            allowed = True
                        else:
                            worked = Demanda.objects.filter(funcionario=novo, departamento=demanda.departamento).exists()
                            if worked:
                                allowed = True
                    except Exception:
                        allowed = False

                    try:
                        members_count = demanda.departamento.membros.count()
                    except Exception:
                        members_count = 0

                    if not allowed and members_count == 0:
                        allowed = True

                    if allowed:
                        demanda.funcionario = novo
                        messages.success(request, f'Demanda reatribuída para {novo.nome}.')
                    else:
                        messages.error(request, 'Reatribuição negada: o funcionário não é membro do departamento e não possui histórico nesta unidade.')
                else:
                    messages.error(request, 'Apenas funcionários podem ser alvos de reatribuição.')
        if original_status == 'concluido':
            descricao_attempt = request.POST.get('descricao')
            status_attempt = new_status
            changed_descr = descricao_attempt is not None and descricao_attempt != original_descr
            changed_status = status_attempt is not None and status_attempt != original_status
            if changed_descr or changed_status:
                messages.error(request, 'Demanda concluída: descrição/status não podem ser alterados.')
        else:
            demanda.descricao = request.POST.get('descricao', demanda.descricao)
            try:
                allowed = [c[0] for c in Demanda._meta.get_field('status').choices]
            except Exception:
                allowed = []
            if new_status and new_status in allowed:
                demanda.status = new_status

        demanda.save()
        try:
            demanda.refresh_from_db()
        except Exception:
            messages.info(request, 'Deu ruim ao atualizar os dados da demanda.')
        return redirect("minhasDemandas")

    # caso não tenha permissão
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
    demandas = Demanda.objects.filter(funcionario=usuario_obj).select_related('funcionario', 'departamento', 'lider')

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
    if not novo_id:
        messages.error(request, 'Nenhum funcionário selecionado para reatribuição.')
        return redirect('minhasDemandas' if not usuario_obj.temPrivilegio() else 'demandas')

    try:
        novo = Usuario.objects.get(id=int(novo_id))
    except Exception:
        messages.error(request, 'Funcionário inválido.')
        return redirect('minhasDemandas' if not usuario_obj.temPrivilegio() else 'demandas')

    # somente para funcionários
    if novo.tipo != Tipo_Usuario.FUNC:
        messages.error(request, 'Apenas funcionários podem ser alvos de reatribuição.')
        return redirect('minhasDemandas' if not usuario_obj.temPrivilegio() else 'demandas')

    # se usuário atual é privilegiado (LID/ADM) permite reatribuir para qualquer FUNC
    if usuario_obj.temPrivilegio():
        demanda.funcionario = novo
        demanda.save()
        messages.success(request, f'Demanda reatribuída para {novo.nome}.')
        return redirect('demandas')

    # se usuário atual é FUNC, só permite reatribuir para FUNC que sejam membros do mesmo departamento
    allowed = False
    try:
        if novo.departamentos.filter(id=demanda.departamento_id).exists():
            allowed = True
        else:
            worked = Demanda.objects.filter(funcionario=novo, departamento=demanda.departamento).exists()
            if worked:
                allowed = True
    except Exception:
        allowed = False

    if allowed:
        demanda.funcionario = novo
        demanda.save()
        messages.success(request, f'Demanda reatribuída para {novo.nome}.')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'msg': f'Demanda reatribuída para {novo.nome}.'})
    else:
        try:
            members_count = demanda.departamento.membros.count()
        except Exception:
            members_count = 0

        if members_count == 0:
            demanda.funcionario = novo
            demanda.save()
            messages.success(request, f'Demanda reatribuída para {novo.nome} (fallback: departamento sem membros configurados).')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': True, 'msg': f'Demanda reatribuída para {novo.nome} (fallback).'})
        else:
            try:
                member_ids = list(demanda.departamento.membros.values_list('id', flat=True))
            except Exception:
                member_ids = []
            messages.error(request, f'Só é possível reatribuir para funcionários do mesmo departamento. Membros atuais: {member_ids}')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'msg': 'Só é possível reatribuir para funcionários do mesmo departamento.'})
    return redirect('minhasDemandas')
