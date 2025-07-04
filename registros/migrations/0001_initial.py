# Generated by Django 5.2 on 2025-04-14 20:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Docente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='RegistroUsoLaboratorio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('grupo', models.CharField(max_length=20)),
                ('materia', models.CharField(max_length=100)),
                ('carrera', models.CharField(max_length=100)),
                ('unidad', models.CharField(max_length=50)),
                ('tema', models.CharField(max_length=200)),
                ('horas_programadas', models.DecimalField(decimal_places=2, max_digits=4)),
                ('horas_cumplidas', models.DecimalField(decimal_places=2, max_digits=4)),
                ('docente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registros.docente')),
            ],
        ),
    ]
