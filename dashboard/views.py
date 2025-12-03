from django.shortcuts import render, redirect
from django.db.models import Count, Subquery, OuterRef, IntegerField, Value, Q
from django.db.models.functions import Coalesce
from demanda.models import Demanda
from departamento.models import Departamento
from usuario.models import Usuario, Tipo_Usuario


def index(request):
    # filtros
    dept_id = request.GET.get('dept')

    # identificar usuário (padrão: None)
    usuario_obj = None
    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        try:
            usuario_obj = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            usuario_obj = None

    # base_qs: for non-privileged users (FUNC) restrict to their departments; otherwise global
    if usuario_obj and not usuario_obj.temPrivilegio():
        # departments the user belongs to (via ManyToMany "membros")
        user_depts = usuario_obj.departamentos.all()
        base_qs = Demanda.objects.filter(departamento__in=user_depts)
    else:
        user_depts = Departamento.objects.all()
        base_qs = Demanda.objects.all()

    # totais usando base_qs (scoped for FUNC)
    total_demandas = base_qs.count()
    total_concluidas = base_qs.filter(status='concluido').count()

    # contagem por departamento (counts computed from base_qs)
    departamentos = (
        Departamento.objects.filter(id__in=user_depts.values_list('id', flat=True))
        .annotate(qtd=Count('demandas_departamento', filter=Q(demandas_departamento__in=base_qs)))
        .order_by('nome')
    )

    # últimas demandas (base) - include funcionario for display
    ultimas_demandas = base_qs.select_related('departamento', 'lider', 'funcionario').order_by('-data_criacao')

    # ordenação (query param)
    order = request.GET.get('order')

    # aplicar filtro por departamento (query param) se fornecido
    if dept_id:
        try:
            ultimas_demandas = ultimas_demandas.filter(departamento_id=int(dept_id))
        except Exception:
            pass

    # Se usuário privilegiado solicitou ordenação por volume de demandas por funcionário,
    # ordenamos as demandas por uma classificação do funcionário (mais demandas primeiro).
    if usuario_obj and usuario_obj.temPrivilegio() and order == 'func_count':
        try:
            # annotate each demanda with the number of concluded demandas for its funcionario
            concluidas_qs = Demanda.objects.filter(
                funcionario=OuterRef('funcionario'),
                status='concluido',
            )
            if dept_id and dept_id.isdigit():
                concluidas_qs = concluidas_qs.filter(departamento_id=int(dept_id))

            concluidas_count = Subquery(
                concluidas_qs.order_by().values('funcionario').annotate(c=Count('id')).values('c')[:1],
                output_field=IntegerField(),
            )

            ultimas_demandas = ultimas_demandas.annotate(
                concluidas_by_func=Coalesce(concluidas_count, Value(0))
            ).order_by('-concluidas_by_func', '-data_criacao')
        except Exception:
            pass

    # nota: ultimas_demandas já foi baseada em base_qs which is scoped for FUNC above

    ultimas = ultimas_demandas[:8]

    context = {
        'total_demandas': total_demandas,
        'total_concluidas': total_concluidas,
        'departamentos': departamentos,
        'ultimas': ultimas,
        'selected_dept': int(dept_id) if dept_id and dept_id.isdigit() else None,
    'order': order,
        'usuario_obj': usuario_obj,
    }
    return render(request, 'privado/dashboard.html', context)
