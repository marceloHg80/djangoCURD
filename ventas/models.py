from django.db import models

# Create your models here.
from django.db import models

class Venta(models.Model):
    producto = models.CharField(max_length=100)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateField()
    cliente = models.CharField(max_length=100, blank=True)

    def total(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.producto} - {self.fecha_venta}"