from functools import reduce

from django.db import models
from django.db.models import F, Sum, Subquery
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
        return self.annotate(total_price=F('price') * F('quantity'))


class OrderQuerySet(models.QuerySet):
    def get_order_price(self):
        return self.annotate(total_price=Sum('items__price'))

    def get_available_restaurants(self):
        for order in self:
            order_products = [
                item.product
                for item in order.items.all()
            ]
            menu_items = [
                product.menu_items.all()
                for product in order_products
            ]

            if not menu_items:
                order.available_restaurants = []
            else:
                available_restaurants = []
                for menu_item in menu_items:
                    restaurants = [
                        item.restaurant
                        for item in menu_item
                    ]
                    available_restaurants.append(restaurants)

                order.available_restaurants = list(
                    reduce(
                        set.intersection,
                        [set(rest) for rest in available_restaurants]
                    )
                )


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
    CASH = 'Ca'

    ORDER_STATUSES = [
        (NOT_PROCESSED, 'Необработанный'),
        (PROCESSED, 'Обработанный'),
        (FINISHED, 'Завершенный')
    ]

    PAYMENT_TYPES = [
        (ELECTRON, 'Банковской картой'),
        (CASH, 'Наличными')
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
    address = models.CharField(
        max_length=200,
        verbose_name='Адрес'
    )
    status = models.CharField(
        max_length=20,
        verbose_name='Статус заказа',
        choices=ORDER_STATUSES,
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
        choices=PAYMENT_TYPES,
        blank=True
    )

    chosen_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Ресторан, взявший заказ',
        on_delete=models.CASCADE,
        related_name='orders',
        blank=True,
        null=True
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ',
        verbose_name_plural = 'Заказы'
        ordering = ['status', 'registered_at']


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )
    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        on_delete=models.CASCADE,
        related_name='items'
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Цена позиции',
        validators=[MinValueValidator(0)]
    )
    objects = OrderItemQuerySet.as_manager()
