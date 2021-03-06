# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-06-05 19:59
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0003_auto_20170503_1809'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='plant',
            name='timetofirstharvest',
        ),
        migrations.AddField(
            model_name='plant',
            name='time_to_first_harvest',
            field=models.DecimalField(blank=True, db_column='time_to_first_harvest', decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='pH_max',
            field=models.DecimalField(blank=True, db_column='ph_max', decimal_places=2, max_digits=4, null=True, validators=[django.core.validators.MaxValueValidator(14, message='pH should be in range 0-14')]),
        ),
        migrations.AlterField(
            model_name='plant',
            name='pH_min',
            field=models.DecimalField(blank=True, db_column='ph_min', decimal_places=2, max_digits=4, null=True, validators=[django.core.validators.MaxValueValidator(14, message='pH should be in range 0-14')]),
        ),
    ]
