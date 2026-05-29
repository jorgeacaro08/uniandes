from django.urls import path
from empresas import views

urlpatterns = [
    path("health/", views.health),
    path("empresas/", views.lista_empresas),
    path("empresas/<str:nit>/", views.detalle_empresa),
]
