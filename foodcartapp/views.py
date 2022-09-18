import json

from phonenumbers import is_valid_number
from phonenumbers.phonenumberutil import NumberParseException
from phonenumber_field.phonenumber import PhoneNumber

from django.http import JsonResponse
from django.templatetags.static import static
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Order, OrderItem


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

@api_view(['POST'])
def register_order(request):
    try:
        order = request.data
    except ValueError:
        return Response({
            'error': 'no valid json',
        })

    mandatory_fields = ['firstname', 'lastname', 'products', 'phonenumber', 'address']

    for field in mandatory_fields:
        try:
            order[field]
        except KeyError:
            return Response({
                'error': f'KeyError. Field {field} is empty',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    for field, field_value in order.items():
        if not field_value:
            return Response({
                'error': f'{field} value must not be empty',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    if not isinstance(order['firstname'], str):
        return Response({
            'error': f'firstname value must be str',
        },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    ordered_products = order['products']

    if not isinstance(ordered_products, list):
        return Response({
            'error': 'Products must be given as list of instances'
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    for product in ordered_products:
        try:
            Product.objects.get(id=product['product'])
        except ObjectDoesNotExist:
            return Response({
                'error': f'No product with id {product["product"]}'
            },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    try:
        phone_num = PhoneNumber.from_string(order['phonenumber'], region='RU')

        if not is_valid_number(phone_num):
            return Response({
            'error': 'Phone number is invalid'
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        new_order = Order.objects.create(
            customer_name=order['firstname'],
            customer_surname=order['lastname'],
            phonenumber=phone_num,
            address=order['address']
        )
    except NumberParseException:
        raise

    for product in ordered_products:
        ordered_food = Product.objects.get(id=product['product'])
        OrderItem.objects.create(
            order=new_order,
            product=ordered_food,
            quantity=product['quantity']
        )

    return Response(order)
