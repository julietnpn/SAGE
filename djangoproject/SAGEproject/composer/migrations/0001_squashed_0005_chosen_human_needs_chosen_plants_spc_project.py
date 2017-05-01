# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-10-05 20:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    #replaces = [(b'composer', '0001_initial'), (b'composer', '0002_auto_20160707_1217'), (b'composer', '0003_auto_20160707_1242'), (b'composer', '0004_auto_20160707_1245'), (b'composer', '0005_chosen_human_needs_chosen_plants_spc_project')]

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Human_Needs_Library',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('need', models.TextField()),
                ('type', models.IntegerField()),
            ],
            options={
                'db_table': 'Human_Needs_Library',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Chosen_Human_Needs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_id', models.IntegerField()),
                ('human_need_lib_id', models.IntegerField()),
            ],
            options={
                'db_table': 'Chosen_Human_Needs',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Chosen_Plants',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_id', models.IntegerField()),
                ('plant_id', models.IntegerField()),
                ('key_species', models.BooleanField()),
            ],
            options={
                'db_table': 'Chosen_Plants',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='SPC_Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField()),
                ('address', models.TextField()),
            ],
            options={
                'db_table': 'SPC_Project',
                'managed': True,
            },
        ),
    ]