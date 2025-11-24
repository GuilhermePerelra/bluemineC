from django.db import models

class Departamento(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100, unique=True)
    lideres = models.ManyToManyField(
        'Usuario',
        blank=True,
        related_name='departamentos')

    def __str__(self):
        return self.nome
