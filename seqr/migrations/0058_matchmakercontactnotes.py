# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-25 15:55
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('seqr', '0057_merge_20190513_2009'),
    ]

    operations = [
        migrations.CreateModel(
            name='MatchmakerContactNotes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('guid', models.CharField(db_index=True, max_length=30, unique=True)),
                ('created_date', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('last_modified_date', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('institution', models.CharField(db_index=True, max_length=200, unique=True)),
                ('comments', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]