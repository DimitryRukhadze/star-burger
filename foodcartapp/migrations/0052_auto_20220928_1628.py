# Generated by Django 3.2.15 on 2022-09-28 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0051_remove_order_comments'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='comments',
            field=models.TextField(blank=True, verbose_name='Комментарии к заказу'),
        ),
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('NP', 'Необработанный'), ('PR', 'Обработанный'), ('FN', 'Завершенный')], db_index=True, default='NP', max_length=20, verbose_name='Статус заказа'),
        ),
    ]
