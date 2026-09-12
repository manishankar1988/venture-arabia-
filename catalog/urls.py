from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("products/", views.product_list, name="product_list"),
    path("products/category/<slug:slug>/", views.category_detail, name="category"),
    path("products/<slug:slug>/", views.product_detail, name="product_detail"),
    path("services/", views.service_list, name="service_list"),
    path("services/request-quote/", views.quote_request, name="quote_request"),
    path("services/<slug:slug>/", views.service_detail, name="service_detail"),
]
