from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<str:key>/", views.cart_update, name="cart_update"),
    path("cart/remove/<str:key>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/<str:number>/success/", views.order_success, name="order_success"),
    path("track/", views.order_track, name="order_track"),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("my-orders/<str:number>/", views.my_order_detail, name="my_order_detail"),
]
