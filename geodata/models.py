from django.db import models


class PlaceGeo(models.Model):
    address = models.CharField(
        'Адрес',
        max_length=200,
        unique=True
    )
    lon = models.DecimalField(max_digits=16, decimal_places=14)
    lat = models.DecimalField(max_digits=16, decimal_places=14)
    last_update = models.DateTimeField(auto_now=True)
