from django.db import models
from django.core.exceptions import ValidationError

class Carro(models.Model):
    COMBUSTIVEL_CHOICES = [
        ('gasolina', 'Gasolina'),
        ('diesel', 'Diesel'),
        ('hibrido', 'Híbrido'),
        ('eletrico', 'Elétrico'),
        ('gpl', 'GPL'),
        ('outro', 'Outro'),
    ]

    TRANSMISSAO_CHOICES = [
        ('manual', 'Manual'),
        ('automatica', 'Automática'),
    ]

    transmissao = models.CharField(
        max_length=20,
        choices=TRANSMISSAO_CHOICES
    )

    TIPO_VEICULO_CHOICES = [
        ('auto', 'Automóveis'),
        ('comercial', 'Comerciais'),
        ('classico', 'Clássicos'),
    ]

    tipo_veiculo = models.CharField(
        max_length=20,
        choices=TIPO_VEICULO_CHOICES,
        default='auto'
    )

    titulo = models.CharField(max_length=200)
    # marca = models.CharField(max_length=100)
    # modelo = models.CharField(max_length=100)
    marca = models.ForeignKey("Marca", on_delete=models.PROTECT, related_name="carros")
    modelo = models.ForeignKey("Modelo", on_delete=models.PROTECT, related_name="carros")
    ano = models.PositiveIntegerField()
    quilometragem = models.PositiveIntegerField(help_text="Em km")
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    combustivel = models.CharField(max_length=20, choices=COMBUSTIVEL_CHOICES, default='gasolina')
    transmissao = models.CharField(max_length=20, choices=TRANSMISSAO_CHOICES, default='manual')
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.ano})"


class ImagemCarro(models.Model):
    carro = models.ForeignKey(Carro, related_name='imagens', on_delete=models.CASCADE)
    imagem = models.ImageField(upload_to='carros/')
    destaque = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagem de {self.carro}"

class Marca(models.Model):
    nome = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Modelo(models.Model):
    marca = models.ForeignKey(Marca, related_name="modelos", on_delete=models.CASCADE)
    nome = models.CharField(max_length=80)

    class Meta:
        unique_together = ("marca", "nome")
        ordering = ["nome"]

    def __str__(self):
        return f"{self.marca.nome} {self.nome}"

def clean(self):
    if self.marca_id and self.modelo_id and self.modelo.marca_id != self.marca_id:
        raise ValidationError({"modelo": "O modelo selecionado não pertence à marca escolhida."})