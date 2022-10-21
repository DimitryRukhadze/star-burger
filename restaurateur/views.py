from geopy import distance

from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Prefetch
from django.conf import settings

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import (
    Product,
    Restaurant,
    Order,
    OrderItem,
    RestaurantMenuItem
)
from geodata.models import PlaceGeolocation
from geodata.views import fetch_coordinates


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_availability = []
    for product in products:
        availability = {
            item.restaurant_id: item.availability
            for item in product.menu_items.all()
        }
        ordered_availability = [
            availability.get(restaurant.id, False)
            for restaurant in restaurants
        ]

        products_with_availability.append(
            (product, ordered_availability)
        )

    return render(
        request,
        template_name="products_list.html",
        context={
            'products_with_availability': products_with_availability,
            'restaurants': restaurants
        }
    )


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    order_details = Order.objects.prefetch_related(
            'items'
    ).prefetch_related(
        'chosen_restaurant'
    ).all().get_order_price()

    order_items = OrderItem.objects.select_related(
        'order'
    ).select_related(
        'product'
    ).filter(order__in=order_details)

    order_addresses = [
        order.address
        for order in order_details
    ]

    restaurants = Restaurant.objects.prefetch_related(
        Prefetch(
            'menu_items',
            queryset=RestaurantMenuItem.objects.prefetch_related(
                'product'
            ).filter(availability=True)
        )
    ).all()
    restaurants_addresses = [
        restaurant.address
        for restaurant in restaurants
    ]

    order_places = PlaceGeolocation.objects.filter(address__in=order_addresses)
    restaurant_places = PlaceGeolocation.objects.filter(address__in=restaurants_addresses)
    order_places_full = [place for place in order_places]
    order_places_addresses = order_places.values_list('address', flat=True)
    restaurant_places_addresses = restaurant_places.values_list('address', flat=True)

    for restaurant in restaurants:
        if restaurant.address not in restaurant_places_addresses:
            try:
                restaurant_lon, restaurant_lat = fetch_coordinates(
                    settings.YA_API_KEY,
                    restaurant.address
                )
                PlaceGeolocation.objects.create(
                    address=restaurant.address,
                    lon=restaurant_lon,
                    lat=restaurant_lat
                )
                restaurant.geo_pos = (restaurant_lon, restaurant_lat)
            except TypeError:
                print("Restaurant location not found")
        else:
            restaurant_place_geo = ''
            for place in restaurant_places:
                if place.address == restaurant.address:
                    restaurant_place_geo = (place.lon, place.lat)
            restaurant.geo_pos = restaurant_place_geo

    for order in order_details:
        order_items_products = [
            item.product
            for item in order_items
            if item.order == order
        ]

        if order.address not in order_places_addresses:
            try:
                order_lon, order_lat = fetch_coordinates(
                    settings.YA_API_KEY,
                    order.address
                )
                PlaceGeolocation.objects.update_or_create(
                    address=order.address,
                    lon=order_lon,
                    lat=order_lat
                )
                order_geo_pos = (order_lon, order_lat)
            except TypeError:
                print("Order location not found")
        else:
            order_geo_pos = ''
            for place in order_places_full:
                if place.address == order.address:
                    order_geo_pos = (place.lon, place.lat)

        if not order.chosen_restaurant:
            avail_restaurants = {}
            for restaurant in restaurants:
                for menu_item in restaurant.menu_items.all():
                    if restaurant.geo_pos:
                        dist_to_restaurant = distance.distance(
                            restaurant.geo_pos,
                            order_geo_pos
                        )
                        if menu_item.product in order_items_products\
                                and restaurant.name\
                                not in avail_restaurants.keys():
                            avail_restaurants[
                                restaurant.name
                            ] = dist_to_restaurant
            if not avail_restaurants:
                order.avail_restaurants = 'Ошибка определения координат'
            else:
                order.avail_restaurants = dict(
                    sorted(
                        avail_restaurants.items(), key=lambda x: x[1]
                    )
                )
        order.order_url = reverse(
            'admin:foodcartapp_order_change',
            args=(order.id,)
        )

    return render(request, template_name='order_items.html', context={
        'order_items': order_details
    })
