# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-11-12 16:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seqr', '0014_userpolicy'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='workspace_name',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='workspace_namespace',
            field=models.TextField(blank=True, null=True),
        ),
    ]
