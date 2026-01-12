# carros/admin.py
from django import forms
from django.contrib import admin
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


class CarroAdminForm(forms.ModelForm):
    class Meta:
        model = Carro
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1) Por padrão, não mostra nada até escolher Marca
        self.fields["modelo"].queryset = Modelo.objects.none()

        # 2) Se estiver editando e já tiver marca, filtra modelos daquela marca
        if self.instance and self.instance.pk and self.instance.marca_id:
            self.fields["modelo"].queryset = (
                Modelo.objects.filter(marca_id=self.instance.marca_id).order_by("nome")
            )
            return

        # 3) ✅ Se estiver criando (ADD) e a marca veio no POST/GET, filtra também
        marca_id = None

        # Se veio via POST (clicou em salvar)
        if hasattr(self, "data"):
            marca_id = self.data.get("marca")

        # fallback: se veio via GET (menos comum no admin)
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
        js = ("carros/admin/carro_modelos_por_marca.js",)

        # adiciona também um css qualquer inexistente só pra ver 404 no network
        #css = {"all": ("carros/admin/teste.css",)}

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "modelos-por-marca/",
                self.admin_site.admin_view(self.modelos_por_marca),
                name="carros_carro_modelos_por_marca",
            )
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
    def save_model(self, request, obj, form, change):
        if obj.marca_id and obj.modelo_id and obj.modelo.marca_id != obj.marca_id:
            from django.core.exceptions import ValidationError
            raise ValidationError("O modelo selecionado não pertence à marca escolhida.")
        super().save_model(request, obj, form, change)


@admin.register(ImagemCarro)
class ImagemCarroAdmin(admin.ModelAdmin):
    list_display = ('carro', 'destaque', 'criado_em')


