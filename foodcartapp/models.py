from django.db import models
from django.db.models import F
from django.core.validators import MinValueValidator
from django.utils import timezone

from phonenumber_field.modelfields import PhoneNumberField


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class OrderItemQuerySet(models.QuerySet):
    def get_item_price(self):
        return self.annotate(total_price=F('item_price') * F('quantity'))


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name



class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):

    NOT_PROCESSED = 'NP'
    PROCESSED = 'PR'
    FINISHED = 'FN'

    ELECTRON = 'El'
    CASHE = 'Ca'

    ord_stats = [
        (NOT_PROCESSED, 'Необработанный'),
        (PROCESSED, 'Обработанный'),
        (FINISHED, 'Завершенный')
    ]

    payments = [
        (ELECTRON, 'Банковской картой'),
        (CASHE, 'Наличными')
    ]

    firstname = models.CharField(
        max_length=200,
        verbose_name='Имя'
    )
    lastname = models.CharField(
        max_length=200,
        verbose_name='Фамилия'
    )
    phonenumber = PhoneNumberField(
        region='RU',
        verbose_name='Телефон'
    )
    address=models.CharField(
        max_length=200,
        verbose_name='Адрес'
    )
    status = models.CharField(
        max_length=20,
        verbose_name='Статус заказа',
        choices=ord_stats,
        default=NOT_PROCESSED,
        db_index=True,
    )
    comments = models.TextField(
        blank=True,
        verbose_name='Комментарии к заказу'
    )
    registered_at = models.DateTimeField(
        verbose_name='Зарегистрирован',
        default=timezone.now,
        db_index=True
    )
    processed_at = models.DateTimeField(
        verbose_name='Обработан',
        blank=True,
        null=True
    )
    delivered_at = models.DateTimeField(
        verbose_name='Доставлен',
        blank=True,
        null=True
    )
    payment_type = models.CharField(
        max_length=20,
        verbose_name='Способ оплаты',
        choices=payments,
        default=CASHE
    )

    restaurants = models.ForeignKey(
        Restaurant,
        verbose_name='Ресторан',
        on_delete=models.CASCADE,
        related_name='orders',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Заказ',
        verbose_name_plural = 'Заказы'
        ordering = ['status', 'registered_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    objects = OrderItemQuerySet.as_manager()
    item_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Цена позиции')
