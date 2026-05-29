from django.urls import path
from extractor import views

urlpatterns = [
    path("health/", views.health),
    # Anti-patron: agrega los crudos en el request (linea base de latencia).
    path("reporte-oncall/", views.reporte_oncall),
    # Dispara el precalculo de un consolidado y lo escribe en Mongo.
    path("consolidar/", views.trigger_consolidacion),
]
