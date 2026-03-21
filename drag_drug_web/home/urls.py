from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('process_drug_image/', views.process_drug_image, name='process_drug_image'),
]