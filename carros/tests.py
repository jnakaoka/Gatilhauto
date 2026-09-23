from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Carro, Marca, Modelo


class SiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.marca = Marca.objects.create(nome="Marca Teste")
        cls.modelo = Modelo.objects.create(marca=cls.marca, nome="Modelo Teste")
        cls.carro = Carro.objects.create(
            titulo="Viatura Teste",
            marca=cls.marca,
            modelo=cls.modelo,
            ano=2025,
            quilometragem=1000,
            preco="19990.00",
            combustivel="gasolina",
            transmissao="manual",
            tipo_veiculo="auto",
            ativo=True,
        )

    def test_paginas_publicas(self):
        for name in (
            "home",
            "sobre",
            "servicos",
            "politica_privacidade",
            "politica_cookies",
            "termos_condicoes",
            "reclamacoes",
        ):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_detalhe_tem_whatsapp_e_telefone_corretos(self):
        response = self.client.get(reverse("detalhe_carro", args=[self.carro.pk]))
        self.assertContains(response, "https://wa.me/351913378940")
        self.assertContains(response, "Marca%20Teste%20Modelo%20Teste%202025")
        self.assertContains(response, "tel:+351913378940")

    def test_carro_inativo_nao_e_publicado(self):
        self.carro.ativo = False
        self.carro.save(update_fields=["ativo"])
        response = self.client.get(reverse("detalhe_carro", args=[self.carro.pk]))
        self.assertEqual(response.status_code, 404)

    def test_modelo_deve_pertencer_a_marca(self):
        outra_marca = Marca.objects.create(nome="Outra Marca")
        carro = Carro(
            titulo="Inválido",
            marca=outra_marca,
            modelo=self.modelo,
            ano=2025,
            quilometragem=0,
            preco="1000.00",
            combustivel="gasolina",
            transmissao="manual",
        )
        with self.assertRaises(ValidationError):
            carro.full_clean()

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_CONFIGURED=True,
        DEFAULT_FROM_EMAIL="gatilhauto@gmail.com",
        CALLME_TO_EMAIL="gatilhauto@gmail.com",
    )
    def test_liga_me_envia_email(self):
        response = self.client.post(
            reverse("callme"),
            data='{"nome":"Cliente","phone":"+351 912 345 678","page":"/"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["gatilhauto@gmail.com"])

    @override_settings(EMAIL_CONFIGURED=False)
    def test_liga_me_nao_finge_sucesso_sem_email_configurado(self):
        response = self.client.post(
            reverse("callme"),
            data='{"nome":"Cliente","phone":"+351 912 345 678","page":"/"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["ok"])


class AdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="admin_teste",
            email="admin@example.invalid",
            password="senha-forte-de-teste",
        )
        cls.marca = Marca.objects.create(nome="Marca Admin")
        cls.modelo = Modelo.objects.create(marca=cls.marca, nome="Modelo Admin")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_admin_carrega_modelos_por_marca(self):
        response = self.client.get(
            reverse("admin:carros_carro_modelos_por_marca"),
            {"marca_id": self.marca.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [{"id": self.modelo.pk, "nome": self.modelo.nome}],
        )

    def test_admin_cria_edita_e_elimina_viatura(self):
        add_url = reverse("admin:carros_carro_add")
        form = {
            "titulo": "Criada no Admin",
            "marca": str(self.marca.pk),
            "modelo": str(self.modelo.pk),
            "ano": "2024",
            "quilometragem": "100",
            "preco": "15000.00",
            "combustivel": "gasolina",
            "transmissao": "manual",
            "tipo_veiculo": "auto",
            "descricao": "",
            "ativo": "on",
            "imagens-TOTAL_FORMS": "0",
            "imagens-INITIAL_FORMS": "0",
            "imagens-MIN_NUM_FORMS": "0",
            "imagens-MAX_NUM_FORMS": "1000",
            "_save": "Guardar",
        }
        response = self.client.post(add_url, form)
        self.assertEqual(response.status_code, 302)

        carro = Carro.objects.get(titulo="Criada no Admin")
        form.update({"titulo": "Editada no Admin", "ano": "2025"})
        response = self.client.post(
            reverse("admin:carros_carro_change", args=[carro.pk]),
            form,
        )
        self.assertEqual(response.status_code, 302)
        carro.refresh_from_db()
        self.assertEqual(carro.titulo, "Editada no Admin")
        self.assertEqual(carro.ano, 2025)

        response = self.client.post(
            reverse("admin:carros_carro_delete", args=[carro.pk]),
            {"post": "yes"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Carro.objects.filter(pk=carro.pk).exists())
