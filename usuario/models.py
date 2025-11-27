import random
import string
from django.db import models

from departamento.models import Departamento

class Tipo_Usuario(models.TextChoices):
    ADM = 'adm', 'Administrador'
    FUNC = 'func', 'Funcionário'
    LID = 'lid', 'Líder'

class Status(models.TextChoices):
    ATIVO = 'atv', 'Ativo'
    INATIVO = 'inat', 'Inativo'

class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    usuario = models.CharField(max_length=100)
    senha = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    tipo = models.CharField(max_length=4, choices=Tipo_Usuario.choices)
    email = models.EmailField(unique=True)
    status = models.CharField(max_length=4, choices=Status.choices, default=Status.ATIVO)


    def temPrivilegio(self):
        return self.tipo == Tipo_Usuario.ADM or self.tipo == Tipo_Usuario.LID
    

    def __str__(self):
        return self.nome
    
    def Usuario(departamento, nome, usuario, matricula, tipo, email):
        usuario = Usuario()
        usuario.departamento = departamento
        usuario.nome = nome
        usuario.usuario = usuario
        usuario.matricula = matricula
        usuario.tipo = tipo
        usuario.email = email
        return usuario
    
    def save(self, *args, **kwargs):
        if not self.matricula:
            self.matricula = self.gerar_matricula()
        super().save(*args, **kwargs)

    @staticmethod
    def gerar_matricula():
        # Gera matrícula aleatória de 8 caracteres alfanuméricos
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))