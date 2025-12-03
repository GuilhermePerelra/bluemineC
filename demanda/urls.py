from django.urls import path
from demanda import views

urlpatterns = [
    path('demandas/', views.demandas, name='demandas'),
    path('minhas-demandas/', views.minhas_demandas, name='minhasDemandas'),
    path('criar-demanda/', views.criarDemanda, name='criarDemanda'),
    path('editar-demanda/<int:id>/', views.editarDemanda, name='editarDemanda'),
    path('reatribuir-demanda/<int:id>/', views.reatribuirDemanda, name='reatribuirDemanda'),
    path('excluir-demanda/<int:id>/', views.excluirDemanda, name='excluirDemanda'),
]
