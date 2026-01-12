from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404
from .models import Carro, ImagemCarro, Marca, Modelo
from django.http import JsonResponse
from .models import Modelo

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
    return render(request, "carros/detalhe_carro.html", {
        "carro": carro,
        "imagens": imagens,
        "imagem_capa": imagem_capa,
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