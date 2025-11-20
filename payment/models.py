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
        verbose_name = 'Товары'
        verbose_name_plural = 'Товары'
        ordering = ['name']

    def __str__(self):
        return self.name

class Discount(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name='Наименование скидки'
    )
    stripe_coupon_id = models.CharField(
        max_length=100, 
        help_text="ID купона в Stripe"
    )

    class Meta:
        verbose_name = 'Скидки'
        verbose_name_plural = 'Скидки'
        ordering = ['name']

    def __str__(self):
        return self.name

class Tax(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name='Наименование налога'
    )
    stripe_tax_rate_id = models.CharField(max_length=100, help_text="ID налоговой ставки в Stripe")

    class Meta:
        verbose_name = 'Налоги'
        verbose_name_plural = 'Налоги'
        ordering = ['name']

    def __str__(self):
        return self.name

class Order(models.Model):
    items = models.ManyToManyField(Item)
    discount = models.ForeignKey(
        'Discount',
        null=True,
        blank=True, 
        on_delete=models.SET_NULL
    )
    tax = models.ForeignKey('Tax', null=True, blank=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Заказы'
        verbose_name_plural = 'Заказы'
        ordering = ['-created']

    def total(self):
        return sum(item.price for item in self.items.all())
