from django.db import models
from departamento.models import Departamento
from usuario.models import Usuario

class Tipo_Status(models.TextChoices):
    ABERTO = 'aberto', 'Aberto'
    EM_ANDAMENTO = 'em_andamento', 'Em Andamento'
    CONCLUIDO = 'concluido', 'Concluído'

class Tipo_Demanda(models.TextChoices):
    CORRECAO = 'correcao', 'Correção'
    MELHORIA = 'melhoria', 'Melhoria'
    IMPLEMENTACAO = 'implementacao', 'Implementação'

class Demanda(models.Model):
    funcionario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='demandas_funcionario')
    lider = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='demandas_lider')
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='demandas_departamento')
    titulo = models.CharField(max_length=30)
    descricao = models.TextField()
    tipo = models.CharField(max_length=20, choices=Tipo_Demanda.choices, default=Tipo_Demanda.CORRECAO)
    data_criacao = models.DateTimeField(auto_now_add=True)
    prazo = models.DateTimeField()
    anexo = models.FileField(upload_to='anexos/', null=True, blank=True)
    status = models.CharField(max_length=15, choices=Tipo_Status.choices, default=Tipo_Status.ABERTO)

    def __str__(self):
        return self.titulo
