# Generated by Django 2.0.6 on 2018-07-12 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0011_auto_20180710_2124'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plant',
            name='common_name',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]
