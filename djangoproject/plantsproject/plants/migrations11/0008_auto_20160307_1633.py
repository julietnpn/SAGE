# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-08 00:33
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0007_auto_20160307_1627'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='plantregion',
            unique_together=set([('plants', 'regions')]),
        ),
    ]
