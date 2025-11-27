from django.urls import path
from departamento import views

urlpatterns = [
    path('', views.departamento, name='departamento'),
    path('criar/', views.criarDepartamento, name='criar_departamento'),
    path('editar/<int:id>/', views.editarDepartamento, name='editar_departamento'),
    path('excluir/<int:id>/', views.excluirDepartamento, name='excluir_departamento'),
    path('sair/<int:id>/', views.sairDepartamento, name='sair_departamento'),
]
