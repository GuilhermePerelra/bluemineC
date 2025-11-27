from django.shortcuts import render, redirect
from django.db.models import Count
from demanda.models import Demanda
from departamento.models import Departamento
from usuario.models import Usuario, Tipo_Usuario


def index(request):
    # filtros
    dept_id = request.GET.get('dept')

    # totais simples
    total_demandas = Demanda.objects.count()
    total_concluidas = Demanda.objects.filter(status='concluido').count()

    # contagem por departamento
    departamentos = (
        Departamento.objects.annotate(qtd=Count('demandas_departamento')).order_by('nome')
    )

    # identificar usuário (padrão: None)
    usuario_obj = None
    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        try:
            usuario_obj = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            usuario_obj = None

    # últimas demandas (base)
    ult_qs = Demanda.objects.select_related('departamento', 'lider').order_by('-data_criacao')

    # aplicar filtro por departamento (query param) se fornecido
    if dept_id:
        try:
            ult_qs = ult_qs.filter(departamento_id=int(dept_id))
        except Exception:
            pass

    # aplicar restrição por perfil: usuários sem privilégio (func) veem apenas demandas do(s) seu(s) departamento(s)
    if usuario_obj and not usuario_obj.temPrivilegio():
        # inferir departamentos a partir das demandas do próprio usuário
        dept_ids = list(Demanda.objects.filter(funcionario=usuario_obj).values_list('departamento_id', flat=True).distinct())
        if dept_ids:
            ult_qs = ult_qs.filter(departamento_id__in=dept_ids)
        else:
            # fallback: mostrar apenas demandas em que é funcionário
            ult_qs = ult_qs.filter(funcionario=usuario_obj)

    ultimas = ult_qs[:8]

    context = {
        'total_demandas': total_demandas,
        'total_concluidas': total_concluidas,
        'departamentos': departamentos,
        'ultimas': ultimas,
        'selected_dept': int(dept_id) if dept_id and dept_id.isdigit() else None,
        'usuario_obj': usuario_obj,
    }
    return render(request, 'privado/dashboard.html', context)
