from django.db import models

class Item(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название',
        help_text='Наименование товара: "Картина"'
    )
    description = models.CharField(
        max_length=200,
        verbose_name='Описание',
        help_text='Описание товара: "Новый"'
    )
    price = models.DecimalField(
       max_digits=10,
       decimal_places=2,
       verbose_name='Цена',
       help_text='Цена товара: "0.00"'
    )
    currency = models.CharField(
        max_length=3, 
        default='usd', choices=[('usd', 'USD'), ('eur', 'EUR')]
    )

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товар'
        ordering = ['name']

    def __str__(self):
        return self.name

class Order(models.Model):
    items = models.ManyToManyField(Item)
    created = models.DateTimeField(auto_now_add=True)

    def total(self):
        return sum(item.price for item in self.items.all())

class Discount(models.Model):
    name = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=10, decimal_places=2) # фикс сумма, %) — на доработку

    def __str__(self):
        return self.name

class Tax(models.Model):
    name = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name