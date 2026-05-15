from django.contrib.auth.views import LoginView


class OrdersLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True