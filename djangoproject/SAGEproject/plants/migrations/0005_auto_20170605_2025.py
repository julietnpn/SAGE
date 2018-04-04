# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-06-05 20:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0004_auto_20170605_1959'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='plant',
            name='lifespan',
        ),
        migrations.AddField(
            model_name='plant',
            name='life_span',
            field=models.DecimalField(blank=True, db_column='life_span', decimal_places=2, max_digits=6, null=True),
        ),
    ]