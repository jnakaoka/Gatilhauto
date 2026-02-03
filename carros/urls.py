from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    # path("viaturas/<int:carro_id>/", views.detalhe_carro, name="detalhe_carro"),
    path("sobre/", views.sobre, name="sobre"),
    path("livro-de-reclamacoes/", views.reclamacoes, name="reclamacoes"),
    path("api/modelos-por-marca/", views.api_modelos_por_marca, name="api_modelos_por_marca"),
    path("viaturas/<int:pk>/", views.detalhe_carro, name="detalhe_carro"),
    path("privacidade/", views.politica_privacidade, name="politica_privacidade"),
    path("cookies/", views.politica_cookies, name="politica_cookies"),
    path("termos/", views.termos_condicoes, name="termos_condicoes"),
    path("servicos/", views.servicos, name="servicos"),
    path("api/callme/", views.callme, name="callme"),
    # path("admin/modelos-por-marca/", views.modelos_por_marca, name="modelos_por_marca"),
    # path("viaturas/<int:pk>/", views.detalhe_carro, name="detalhe_carro"),
]
