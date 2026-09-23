import json
import logging
import re
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404
from .models import Carro, ImagemCarro, Marca, Modelo
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect


logger = logging.getLogger(__name__)

PHONE_RE = re.compile(r"^[0-9\s()+-]{7,20}$")

def home(request):
    carros = Carro.objects.filter(ativo=True)

    # --- filtros (IDs) ---
    marca_id = request.GET.get("marca", "").strip()
    modelo_id = request.GET.get("modelo", "").strip()
    combustivel = request.GET.get("combustivel", "").strip()
    ano_min = request.GET.get("ano_min", "").strip()
    ano_max = request.GET.get("ano_max", "").strip()
    transmissao = request.GET.get("transmissao")
    preco_min = request.GET.get("preco_min")
    preco_max = request.GET.get("preco_max")
    tipo = request.GET.get('tipo')
    

    if marca_id.isdigit():
        carros = carros.filter(marca_id=int(marca_id))

    if modelo_id.isdigit():
        carros = carros.filter(modelo_id=int(modelo_id))

    if combustivel:
        carros = carros.filter(combustivel=combustivel)

    if ano_min.isdigit():
        carros = carros.filter(ano__gte=int(ano_min))

    if ano_max.isdigit():
        carros = carros.filter(ano__lte=int(ano_max))

    if transmissao:
        carros = carros.filter(transmissao=transmissao)

    if preco_min:
        try:
            carros = carros.filter(preco__gte=float(preco_min))
        except ValueError:
            pass

    if preco_max:
        try:
            carros = carros.filter(preco__lte=float(preco_max))
        except ValueError:
            pass
    
    if tipo:
        carros = carros.filter(tipo_veiculo=tipo)

    # --- ordenação ---
    sort = request.GET.get("sort", "recentes")
    sort_map = {
        "recentes": "-criado_em",
        "preco_asc": "preco",
        "preco_desc": "-preco",
        "ano_desc": "-ano",
        "ano_asc": "ano",
        "km_asc": "quilometragem",
        "km_desc": "-quilometragem",
    }
    carros = carros.order_by(sort_map.get(sort, "-criado_em"))

    # --- capa primeiro ---
    imagens_qs = ImagemCarro.objects.order_by("-destaque", "id")
    carros = carros.prefetch_related(Prefetch("imagens", queryset=imagens_qs))

    # --- paginação ---
    paginator = Paginator(carros, 6)
    page_obj = paginator.get_page(request.GET.get("page"))

    filtros = {
        "marca": marca_id,
        "modelo": modelo_id,
        "combustivel": combustivel,
        "ano_min": ano_min,
        "ano_max": ano_max,
        "sort": sort,
        "transmissao": transmissao,
        "preco_min": preco_min,
        "preco_max": preco_max,
        "tipo": tipo
    }

    return render(request, "carros/home.html", {
        "carros": page_obj.object_list,
        "page_obj": page_obj,
        "filtros": filtros,
        "marcas": Marca.objects.all(),
        "modelos": Modelo.objects.select_related("marca").all(),
    })

def detalhe_carro(request, pk):
    carro = get_object_or_404(Carro, id=pk, ativo=True)
    imagens = carro.imagens.all().order_by('-destaque', 'id')
    imagem_capa = imagens.first()
    whatsapp_message = (
        f"Olá, tenho interesse no {carro.marca.nome} {carro.modelo.nome} "
        f"{carro.ano} anunciado no site Gatilhauto."
    )
    return render(request, "carros/detalhe_carro.html", {
        "carro": carro,
        "imagens": imagens,
        "imagem_capa": imagem_capa,
        "whatsapp_url": (
            f"https://wa.me/{settings.CONTACT_PHONE_E164}"
            f"?text={quote(whatsapp_message)}"
        ),
    })

def api_modelos_por_marca(request):
    marca_id = request.GET.get("marca_id")
    if not marca_id or not marca_id.isdigit():
        return JsonResponse([], safe=False)

    modelos = (
        Modelo.objects
        .filter(marca_id=int(marca_id))
        .order_by("nome")
        .values("id", "nome")
    )
    return JsonResponse(list(modelos), safe=False)

def sobre(request):
    return render(request, "carros/sobre.html")

def reclamacoes(request):
    return render(request, "carros/reclamacoes.html")

def politica_privacidade(request):
    return render(request, "carros/politica_privacidade.html")

def politica_cookies(request):
    return render(request, "carros/politica_cookies.html")

def termos_condicoes(request):
    return render(request, "carros/termos_condicoes.html")

def servicos(request):
    return render(request, "carros/servicos.html", {
        "AGENDAMENTO_URL": getattr(settings, "GA_AGENDAMENTO_URL", ""),
    })

@require_POST
@csrf_protect
def callme(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    nome = (data.get("nome") or "").strip()
    phone = (data.get("phone") or "").strip()
    page = (data.get("page") or "").strip()

    if not phone or not PHONE_RE.match(phone):
        return JsonResponse({"ok": False, "error": "Telefone inválido"}, status=400)

    subject = "Gatilhauto - Pedido de contacto (Ligue-me)"
    message = f"Novo pedido de contacto:\n\nNome: {nome or '-'}\nTelefone: {phone}\nPágina: {page or '-'}\n"
    to_email = settings.CALLME_TO_EMAIL

    if not settings.EMAIL_CONFIGURED:
        logger.error("Formulário Liga-me indisponível: configuração de email ausente.")
        return JsonResponse(
            {"ok": False, "error": "Serviço de email temporariamente indisponível"},
            status=503,
        )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Falha ao enviar pedido de contacto Liga-me.")
        return JsonResponse(
            {"ok": False, "error": "Não foi possível enviar o pedido"},
            status=503,
        )

    return JsonResponse({"ok": True})
