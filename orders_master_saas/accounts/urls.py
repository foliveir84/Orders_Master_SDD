from django.urls import path

from accounts.views import OrdersLoginView

urlpatterns = [
    path("login/", OrdersLoginView.as_view(), name="login"),
]