import json

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Empresa


def health(request):
    return HttpResponse("OK", status=200)


@csrf_exempt
def lista_empresas(request):
    if request.method == "GET":
        qs = Empresa.objects.all()
        activa = request.GET.get("activa")
        if activa is not None:
            qs = qs.filter(activa=(activa.lower() == "true"))
        data = [e.to_dict() for e in qs[:5000]]
        return JsonResponse({"empresas": data, "count": len(data)})

    if request.method == "POST":
        payload = json.loads(request.body or "{}")
        empresa, _ = Empresa.objects.update_or_create(
            nit=payload["nit"],
            defaults={
                "nombre": payload.get("nombre", ""),
                "sector": payload.get("sector", ""),
                "activa": payload.get("activa", True),
            },
        )
        return JsonResponse(empresa.to_dict(), status=201)

    return JsonResponse({"error": "metodo no permitido"}, status=405)


def detalle_empresa(request, nit):
    """Validacion puntual usada por el extractor (interaccion servicio-a-servicio)."""
    try:
        empresa = Empresa.objects.get(nit=nit)
    except Empresa.DoesNotExist:
        return JsonResponse({"error": "empresa no encontrada"}, status=404)
    return JsonResponse(empresa.to_dict())
