# Generated by Django 3.2.15 on 2022-10-10 22:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geodata', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='OrderGeo',
            new_name='PlaceGeo',
        ),
    ]
