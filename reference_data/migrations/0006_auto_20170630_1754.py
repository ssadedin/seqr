# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-30 17:54
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reference_data', '0005_auto_20170627_0318'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clinvar',
            old_name='genome_build_id',
            new_name='genome_version',
        ),
        migrations.RenameField(
            model_name='gencoderelease',
            old_name='genome_build_id',
            new_name='genome_version',
        ),
        migrations.AlterUniqueTogether(
            name='gencoderelease',
            unique_together=set([('release_number', 'release_date', 'genome_version')]),
        ),
    ]
