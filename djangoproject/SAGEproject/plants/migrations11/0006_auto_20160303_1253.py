# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-03 20:53
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0005_auto_20160303_1245'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='plantdimensionsbyregion',
            name='plants',
        ),
        migrations.RemoveField(
            model_name='plantdimensionsbyregion',
            name='regions',
        ),
        migrations.RemoveField(
            model_name='plant',
            name='dimensions',
        ),
        migrations.DeleteModel(
            name='PlantDimensionsByRegion',
        ),
    ]