import json

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .consolidation import calcular_consolidado, consolidar_a_mongo


def health(request):
    return HttpResponse("OK", status=200)


def reporte_oncall(request):
    """ANTI-PATRON (linea base de latencia).

    Agrega los datos crudos de PostgreSQL en tiempo de request, como ocurria en
    Sprint 3. Sirve para comparar contra la lectura precalculada de Mongo del
    ms-reportes y evidenciar el retardo que genera la consulta de los datos.
    """
    empresa = request.GET.get("empresa", "")
    periodo = request.GET.get("periodo", "")
    doc = calcular_consolidado(empresa, periodo)
    return JsonResponse(doc)


@csrf_exempt
def trigger_consolidacion(request):
    """Precalcula el consolidado de (empresa, periodo) y lo escribe en Mongo."""
    if request.method == "POST":
        payload = json.loads(request.body or "{}")
        empresa = payload.get("empresa")
        periodo = payload.get("periodo")
    else:
        empresa = request.GET.get("empresa")
        periodo = request.GET.get("periodo")
    if not empresa or not periodo:
        return JsonResponse({"error": "empresa y periodo son obligatorios"}, status=400)
    doc = consolidar_a_mongo(empresa, periodo)
    return JsonResponse({"status": "ok", "reporte": doc})
