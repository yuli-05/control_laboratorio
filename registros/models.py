from django.db import models

class Docente(models.Model):
    nombre = models.CharField(max_length=100)
    cedula = models.CharField(max_length=10)
    carrera = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class RegistroUsoLaboratorio(models.Model):
    LABORATORIOS = [
        ('G1', 'Laboratorio G1'),
        ('G2', 'Laboratorio G2'),
        ('G3', 'Laboratorio G3'),
        ('G4', 'Laboratorio G4'),
        ('G5', 'Laboratorio G5'),
        ('G6', 'Laboratorio G6'),
        ('K1', 'Laboratorio K1'),
        ('K2', 'Laboratorio K2'),
        ('H1', 'Laboratorio H1'),
    ]

    fecha = models.DateField()
    laboratorio = models.CharField(max_length=50, choices=LABORATORIOS)
    grupo = models.CharField(max_length=20)
    numero_estudiantes = models.PositiveIntegerField("Número de estudiantes", default=0)
    docente = models.ForeignKey('Docente', on_delete=models.CASCADE)
    materia = models.CharField(max_length=100)
    carrera = models.CharField(max_length=100)
    unidad = models.CharField(max_length=50)
    tema = models.CharField(max_length=200)
    horas_programadas = models.DecimalField(max_digits=4, decimal_places=2)
    horas_cumplidas = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return f"{self.docente} - {self.fecha} - {self.grupo}"


class Laboratorio(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
