# Reshat Payment System — Django + Stripe API

## Описание

Система позволяет просматривать каталог товаров, оплачивать покупку любого товара через Stripe Checkout (USD/EUR), а также собирать заказы с несколькими товарами, применять скидки и налоги, работать с мультивалютностью на backend и frontend.

- **Django backend** + Stripe API
- Оформление Bootstrap 5 (адаптивно)
- Поддержка Docker & env-переменных
- Дисконт/налоги у заказов, мультивалюта, выбор курса на сайте
- Stripe Checkout и Stripe PaymentIntent (демо)
- Доступ к админ-панели для тестирования

## Запуск (локально)

1. Клонируйте репозиторий:
   
    git clone https://github.com/regidf12/reshat_payment_system.git
    
    cd reshat_payment_system

2. Создайте virtualenv и установите зависимости:
   
    python -m venv venv

    source venv/bin/activate  # или .\venv\Scripts\activate на Windows

    pip install --upgrade pip

    pip install -r requirements.txt

3. Создайте файл `.env` в корне со следующим содержимым:

    ```
    STRIPE_SECRET_KEY=sk_test_********
    STRIPE_PUBLIC_KEY=pk_test_********
    DJANGO_SECRET_KEY= Все что угодно
    DEBUG=False
    ```

4. Примените миграции и создайте суперпользователя:

    python manage.py migrate

    python manage.py createsuperuser. 

5. Запустите сервер:

    python manage.py runserver

## Запуск с Docker

1. Отредактируйте `.env` как выше  
    
2. Запустите через Docker Compose:

    docker-compose up --build    

    Заходим на http://localhost:8000/

## Онлайн решение

1. http://5.129.247.4:8000/

## Админ-панель

В админке можно:
- Просматривать/править товары, заказы, скидки, налоги.
- Добавлять тестовые товары, создавать заказ вручную.

**Тестовый вход:**  
- **username**: `regidf`  
- **password**: `wz4xonbm`  
(Задайте реальные креды или создайте пользователя через createsuperuser)

## Тестовая карта Stripe

- Любая валидная дата, например: "12/34"
- Любой CVC (например: 111)
- Карта: 4242 4242 4242 4242

## Контакты

По всем вопросам — [telegram](https://t.me/flow_env) или issue на GitHub.
