# Generated by Django 3.2.15 on 2022-10-14 17:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0062_rename_item_price_orderitem_price'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='restaurants',
            new_name='chosen_restaurant',
        ),
    ]
