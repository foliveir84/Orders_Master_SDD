from django.urls import path

from orders import views

app_name = "orders"

urlpatterns = [
    path("", views.upload_view, name="upload"),
    path("results/", views.results_view, name="results"),
    path("recalc/", views.recalc_view, name="recalc"),
    path("download/", views.download_excel_view, name="download"),
]