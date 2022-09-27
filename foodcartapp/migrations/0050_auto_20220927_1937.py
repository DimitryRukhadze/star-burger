# Generated by Django 3.2.15 on 2022-09-27 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0049_alter_order_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='status',
        ),
        migrations.AddField(
            model_name='order',
            name='comments',
            field=models.TextField(blank=True, verbose_name='Комментарии к заказу'),
        ),
    ]
