# Generated by Django 5.0.6 on 2024-08-21 19:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0002_solicitud_cantidad_solicitud_identificador_and_more'),
        ('proveedores', '0009_remove_propuestas_sol_propuesta_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='propuestas_sol',
            name='usuario',
        ),
        migrations.AddField(
            model_name='propuestas_sol',
            name='id_solicitud',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='compras.solicitud'),
            preserve_default=False,
        ),
    ]
