import logging

from phonenumbers import is_valid_number
from phonenumbers.phonenumberutil import NumberParseException
from phonenumber_field.phonenumber import PhoneNumber

from django.http import JsonResponse
from django.templatetags.static import static
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import (
    ValidationError,
    ModelSerializer,
    ListField
)
from django.db import transaction
from django.conf import settings

from .models import Product, Order, OrderItem
from geodata.models import PlaceGeolocation
from geodata.views import fetch_coordinates


class OrderSerializer(ModelSerializer):
    products = ListField(allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'firstname',
            'lastname',
            'address',
            'products',
            'phonenumber'
        ]

    def validate_phonenumber(self, value):
        try:
            phone_num = PhoneNumber.from_string(value, region='RU')
            if not is_valid_number(phone_num):
                raise ValidationError(
                    {
                        'error': 'Phone number is invalid'
                     }
                )

        except NumberParseException:
            raise ValidationError(
                {
                    'error': 'Phone number is invalid'
                }
            )

        return phone_num

    def validate_products(self, value):
        for product in value:
            try:
                product['obj'] = Product.objects.get(id=product.get('product'))
            except ObjectDoesNotExist:
                raise ValidationError({
                    'error': f'No product with id {product.get("product")}'
                })
        return value

    def create(self, validated_data):
        new_order = Order(
            firstname=validated_data['firstname'],
            lastname=validated_data['lastname'],
            phonenumber=validated_data['phonenumber'],
            address=validated_data['address']
        )
        new_order.save()
        return new_order


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@transaction.non_atomic_requests
@api_view(['POST'])
def register_order(request):
    order = request.data
    serializer = OrderSerializer(data=order)
    serializer.is_valid(raise_exception=True)

    serialized_order = serializer.save()
    try:
        order_lon, order_lat = fetch_coordinates(
            settings.YA_API_KEY,
            serialized_order.address
        )
        PlaceGeolocation.objects.get_or_create(
            address=serialized_order.address,
            lon=order_lon,
            lat=order_lat
        )
    except TypeError:
        logging.warning("Order location not found")
    ordered_products = serializer.validated_data['products']

    order_items = [
        OrderItem(
            order=serialized_order,
            product=product['obj'],
            quantity=product['quantity'],
            price=product['obj'].price * int(product['quantity'])
        )
        for product in ordered_products
    ]

    OrderItem.objects.bulk_create(order_items)

    return Response(serializer.data)
