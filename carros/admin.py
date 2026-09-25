import json
import time
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django import forms
from django.contrib import admin
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.urls import path

from .models import Carro, ImagemCarro, Marca, Modelo


# --- Inline para criar Modelos dentro da Marca ---
class ModeloInline(admin.TabularInline):
    model = Modelo
    extra = 1


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    inlines = [ModeloInline]


@admin.register(Modelo)
class ModeloAdmin(admin.ModelAdmin):
    list_display = ("nome", "marca")
    list_filter = ("marca",)
    search_fields = ("nome", "marca__nome")

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        marca_id = request.GET.get("marca_id")
        if marca_id and marca_id.isdigit():
            queryset = queryset.filter(marca_id=int(marca_id))
        return queryset, use_distinct

# --- Inline para imagens do carro ---
class ImagemCarroInline(admin.TabularInline):
    model = ImagemCarro
    extra = 1


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        clean_one = super().clean
        if isinstance(data, (list, tuple)):
            return [clean_one(item, initial) for item in data]
        return [clean_one(data, initial)]


class WholeNumberField(forms.IntegerField):
    """Campo inteiro que também remove o .00 dos valores antigos no formulário."""

    def prepare_value(self, value):
        if value in (None, ""):
            return value
        try:
            numero = Decimal(str(value))
            if numero == numero.to_integral_value():
                return int(numero)
        except (InvalidOperation, TypeError, ValueError):
            return super().prepare_value(value)
        return super().prepare_value(value)


class CarroAdminForm(forms.ModelForm):
    preco = WholeNumberField(
        label="Preço",
        min_value=0,
        widget=forms.NumberInput(attrs={"step": "1", "inputmode": "numeric"}),
    )
    quilometragem = WholeNumberField(
        label="Quilometragem",
        min_value=0,
        help_text="Em km",
        widget=forms.NumberInput(attrs={"step": "1", "inputmode": "numeric"}),
    )
    novas_imagens = MultipleImageField(
        label="Adicionar imagens",
        required=False,
        help_text="Pode selecionar várias imagens de uma só vez.",
    )
    imagens_temporarias = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Carro
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1) Por padrão, não mostra nada até escolher Marca
        self.fields["modelo"].queryset = Modelo.objects.none()

        # 2) O POST tem prioridade, inclusive ao voltar com erros de validação.
        marca_id = self.data.get("marca") if self.is_bound else None

        # 3) Ao editar, usa a marca da instância apenas se não veio um POST.
        if not marca_id and self.instance and self.instance.pk and self.instance.marca_id:
            self.fields["modelo"].queryset = (
                Modelo.objects.filter(marca_id=self.instance.marca_id).order_by("nome")
            )
            return

        # 4) Fallback para valores iniciais.
        if not marca_id:
            marca_id = self.initial.get("marca")

        if marca_id and str(marca_id).isdigit():
            self.fields["modelo"].queryset = (
                Modelo.objects.filter(marca_id=int(marca_id)).order_by("nome")
            )


@admin.register(Carro)
class CarroAdmin(admin.ModelAdmin):
    form = CarroAdminForm

    list_display = ("titulo", "marca", "modelo", "ano", "preco", "ativo", "tipo_veiculo", "transmissao", "combustivel")
    list_filter = ("marca", "ano", "combustivel", "transmissao", "ativo", "tipo_veiculo", "modelo")
    search_fields = ("titulo", "marca__nome", "modelo__nome")
    inlines = [ImagemCarroInline]

    # ❌ Importante: remove autocomplete do modelo (vamos controlar via endpoint)
    # autocomplete_fields = ("marca", "modelo")

    class Media:
        js = (
            "carros/admin/carro_modelos_por_marca.js",
            "carros/admin/carro_upload_imagens.js",
        )

        # adiciona também um css qualquer inexistente só pra ver 404 no network
        #css = {"all": ("carros/admin/teste.css",)}

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "modelos-por-marca/",
                self.admin_site.admin_view(self.modelos_por_marca),
                name="carros_carro_modelos_por_marca",
            ),
            path(
                "upload-imagem-temporaria/",
                self.admin_site.admin_view(self.upload_imagem_temporaria),
                name="carros_carro_upload_imagem_temporaria",
            ),
        ]
        return custom + urls

    def modelos_por_marca(self, request):
        marca_id = request.GET.get("marca_id")
        if not marca_id or not marca_id.isdigit():
            return JsonResponse([], safe=False)

        modelos = (
            Modelo.objects.filter(marca_id=int(marca_id))
            .order_by("nome")
            .values("id", "nome")
        )
        return JsonResponse(list(modelos), safe=False)

    def upload_imagem_temporaria(self, request):
        if request.method != "POST":
            return JsonResponse({"erro": "Método não permitido."}, status=405)

        upload = request.FILES.get("imagem")
        if not upload:
            return JsonResponse({"erro": "Nenhuma imagem recebida."}, status=400)
        if upload.size > 20 * 1024 * 1024:
            return JsonResponse({"erro": "A imagem excede o limite de 20 MB."}, status=400)

        try:
            forms.ImageField().clean(upload)
            upload.seek(0)
        except ValidationError:
            return JsonResponse({"erro": "O arquivo enviado não é uma imagem válida."}, status=400)

        if not request.session.session_key:
            request.session.create()

        self._limpar_uploads_expirados(request.session.session_key)
        extensao = Path(upload.name).suffix.lower()[:10]
        nome_storage = default_storage.save(
            f"tmp/admin_uploads/{request.session.session_key}/{uuid.uuid4().hex}{extensao}",
            upload,
        )
        token = signing.dumps(
            {
                "storage_name": nome_storage,
                "session_key": request.session.session_key,
                "nome_original": Path(upload.name).name,
            },
            salt="carros.admin.upload",
            compress=True,
        )
        return JsonResponse({"token": token, "nome": Path(upload.name).name})

    @staticmethod
    def _limpar_uploads_expirados(session_key):
        pasta = Path(default_storage.path(f"tmp/admin_uploads/{session_key}"))
        if not pasta.exists():
            return
        limite = time.time() - (24 * 60 * 60)
        for arquivo in pasta.iterdir():
            if arquivo.is_file() and arquivo.stat().st_mtime < limite:
                arquivo.unlink(missing_ok=True)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        for upload in form.cleaned_data.get("novas_imagens", []):
            ImagemCarro.objects.create(carro=form.instance, imagem=upload)

        try:
            temporarias = json.loads(form.cleaned_data.get("imagens_temporarias") or "[]")
        except (TypeError, json.JSONDecodeError):
            temporarias = []

        for item in temporarias:
            token = item.get("token") if isinstance(item, dict) else None
            if not token:
                continue
            try:
                dados = signing.loads(
                    token,
                    salt="carros.admin.upload",
                    max_age=24 * 60 * 60,
                )
            except signing.BadSignature:
                continue
            if dados.get("session_key") != request.session.session_key:
                continue

            nome_storage = dados.get("storage_name")
            if not nome_storage or not default_storage.exists(nome_storage):
                continue
            with default_storage.open(nome_storage, "rb") as arquivo:
                imagem = ImagemCarro(carro=form.instance)
                imagem.imagem.save(
                    dados.get("nome_original") or Path(nome_storage).name,
                    File(arquivo),
                    save=True,
                )
            default_storage.delete(nome_storage)

    def save_model(self, request, obj, form, change):
        if obj.marca_id and obj.modelo_id and obj.modelo.marca_id != obj.marca_id:
            from django.core.exceptions import ValidationError
            raise ValidationError("O modelo selecionado não pertence à marca escolhida.")
        super().save_model(request, obj, form, change)


@admin.register(ImagemCarro)
class ImagemCarroAdmin(admin.ModelAdmin):
    list_display = ('carro', 'destaque', 'criado_em')
