from django.db import models

from departamento.models import Departamento

class Tipo_Usuario(models.TextChoices):
    ADM = 'adm', 'Administrador'
    FUNC = 'func', 'Funcionário'
    LID = 'lid', 'Líder'


class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    tipo = models.CharField(max_length=4, choices=Tipo_Usuario.choices)
    email = models.EmailField(unique=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome