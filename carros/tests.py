import base64
import json
import tempfile

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .admin import CarroAdminForm
from .models import Carro, ImagemCarro, Marca, Modelo


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
        self.assertContains(response, "€ 19990")
        self.assertNotContains(response, "19990,00")
        self.assertNotContains(response, "19990.00")

    def test_preco_sem_decimais_na_listagem(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "€ 19990")
        self.assertNotContains(response, "19990,00")
        self.assertNotContains(response, "19990.00")

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
        self._media_dir = tempfile.TemporaryDirectory()
        self._media_override = override_settings(MEDIA_ROOT=self._media_dir.name)
        self._media_override.enable()
        self.addCleanup(self._media_override.disable)
        self.addCleanup(self._media_dir.cleanup)

    @staticmethod
    def imagem_teste(nome):
        conteudo = base64.b64decode(
            "R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
        )
        return SimpleUploadedFile(nome, conteudo, content_type="image/gif")

    def dados_carro(self, **alteracoes):
        dados = {
            "titulo": "Criada no Admin",
            "marca": str(self.marca.pk),
            "modelo": str(self.modelo.pk),
            "ano": "2024",
            "quilometragem": "100",
            "preco": "15000",
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
        dados.update(alteracoes)
        return dados

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
        form = self.dados_carro()
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

    def test_preco_e_quilometragem_sao_inteiros_no_admin(self):
        carro = Carro.objects.create(
            titulo="Sem decimais",
            marca=self.marca,
            modelo=self.modelo,
            ano=2024,
            quilometragem=1234,
            preco="15000.00",
        )
        form = CarroAdminForm(instance=carro)
        self.assertEqual(form["preco"].value(), 15000)
        self.assertEqual(form["quilometragem"].value(), 1234)

        form_decimal = CarroAdminForm(
            data=self.dados_carro(preco="15000.50"),
            instance=carro,
        )
        self.assertFalse(form_decimal.is_valid())
        self.assertIn("preco", form_decimal.errors)

        response = self.client.get(reverse("admin:carros_carro_changelist"))
        self.assertContains(response, ">15000<")
        self.assertNotContains(response, "15000,00")
        self.assertNotContains(response, "15000.00")

    def test_admin_aceita_varias_imagens_no_mesmo_cadastro(self):
        dados = self.dados_carro()
        dados["novas_imagens"] = [
            self.imagem_teste("frente.gif"),
            self.imagem_teste("traseira.gif"),
        ]
        response = self.client.post(reverse("admin:carros_carro_add"), dados)
        self.assertEqual(response.status_code, 302)
        carro = Carro.objects.get(titulo="Criada no Admin")
        self.assertEqual(carro.imagens.count(), 2)

    def test_upload_temporario_sobrevive_a_erro_do_formulario(self):
        upload_url = reverse("admin:carros_carro_upload_imagem_temporaria")
        upload_response = self.client.post(
            upload_url,
            {"imagem": self.imagem_teste("lateral.gif")},
        )
        self.assertEqual(upload_response.status_code, 200)
        item = upload_response.json()
        temporarias = json.dumps([item])

        add_url = reverse("admin:carros_carro_add")
        response = self.client.post(
            add_url,
            self.dados_carro(titulo="", imagens_temporarias=temporarias),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["adminform"].form["imagens_temporarias"].value(),
            temporarias,
        )

        response = self.client.post(
            add_url,
            self.dados_carro(imagens_temporarias=temporarias),
        )
        self.assertEqual(response.status_code, 302)
        carro = Carro.objects.get(titulo="Criada no Admin")
        self.assertEqual(carro.imagens.count(), 1)
        self.assertFalse(ImagemCarro.objects.filter(carro=carro, imagem="").exists())

    def test_edicao_mantem_modelo_da_marca_no_formulario(self):
        carro = Carro.objects.create(
            titulo="Editar modelo",
            marca=self.marca,
            modelo=self.modelo,
            ano=2024,
            quilometragem=100,
            preco="15000",
        )
        response = self.client.get(
            reverse("admin:carros_carro_change", args=[carro.pk])
        )
        self.assertEqual(response.status_code, 200)
        campo = response.context["adminform"].form["modelo"]
        self.assertEqual(campo.value(), self.modelo.pk)
        self.assertIn(self.modelo, campo.field.queryset)
        self.assertEqual(
            response.context["adminform"].form["modelo_atual"].value(),
            str(self.modelo.pk),
        )
        self.assertContains(
            response,
            f'name="modelo_atual" value="{self.modelo.pk}"',
        )

    def test_servicos_nao_mostra_botao_agendar(self):
        response = self.client.get(reverse("servicos"))
        self.assertNotContains(response, ">Agendar<")
