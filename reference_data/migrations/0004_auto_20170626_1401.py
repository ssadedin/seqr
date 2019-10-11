# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-26 14:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reference_data', '0003_clinvar'),
    ]

    operations = [
#         migrations.AlterField(
#             model_name='clinvar',
#             name='genome_build_id',
#             field=models.CharField(choices=[(b'37', b'GRCh37'), (b'38', b'GRCh38')], max_length=3),
#         ),
        migrations.AlterField(
            model_name='gencoderelease',
            name='genome_build_id',
            field=models.CharField(choices=[(b'37', b'GRCh37'), (b'38', b'GRCh38')], max_length=3),
        ),
    ]
