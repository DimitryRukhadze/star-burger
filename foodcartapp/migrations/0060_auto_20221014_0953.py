# Generated by Django 3.2.15 on 2022-10-14 06:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0059_alter_orderitem_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='restaurants',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='foodcartapp.restaurant', verbose_name='Ресторан'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='item_price',
            field=models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Цена позиции'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='foodcartapp.order', verbose_name='Заказ'),
        ),
    ]
