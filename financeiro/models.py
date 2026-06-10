from django.db import models


class Pessoa(models.Model):
    TIPO_CHOICES = [
        ('FORNECEDOR', 'Fornecedor'),
        ('FATURADO', 'Faturado'),
    ]

    nome_razao_social = models.CharField(max_length=255, verbose_name="Nome / Razão Social")
    fantasia = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Fantasia")
    cnpj_cpf = models.CharField(max_length=20, unique=True, verbose_name="CNPJ / CPF")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Pessoa")
    status_ativo = models.BooleanField(default=True, verbose_name="Status Ativo")

    class Meta:
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"

    def __str__(self):
        return f"{self.nome_razao_social} ({self.tipo})"


class Classificacao(models.Model):

    TIPOS_CLASSIFICACAO = [
        ('DESPESA', 'Despesa'),
        ('RECEITA', 'Receita'),
    ]

    class Meta:
        verbose_name = "Classificação"
        verbose_name_plural = "Classificações"

    descricao = models.CharField(max_length=255)
    categoria = models.CharField(max_length=100, blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPOS_CLASSIFICACAO)
    status_ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.descricao} - {self.tipo}"


class MovimentoContas(models.Model):
    TIPOS_MOVIMENTO = [
        ('A PAGAR', 'A pagar'),
        ('A RECEBER', 'A receber')
    ]

    class Meta:
        verbose_name = "Movimento de Conta"
        verbose_name_plural = "Movimentos de Contas"

    def __str__(self):
        return f"Nota {self.numero_nota} - {self.pessoa.nome_razao_social}"

    tipo = models.CharField(max_length=10, choices=TIPOS_MOVIMENTO)
    numero_nota = models.CharField(max_length=50)
    data_emissao = models.DateField()
    valor_total = models.DecimalField(max_digits=15, decimal_places=2)
    descricao_produtos = models.TextField(blank=True, null=True)
    status_ativo = models.BooleanField(default=True)

    # Chave Estrangeira para Pessoas
    pessoa = models.ForeignKey(Pessoa, on_delete=models.PROTECT, related_name='movimentos')

    # Relacionamento N:N com Classificação
    classificacoes = models.ManyToManyField(Classificacao, related_name='movimentos')


class ParcelaContas(models.Model):

    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"

    def __str__(self):
        return f"Parcela {self.numero_parcela} - R$ {self.valor_parcela}"

    movimento = models.ForeignKey(MovimentoContas, on_delete=models.CASCADE, related_name='parcelas')
    identificacao_unica = models.CharField(max_length=100, unique=True)
    numero_parcela = models.IntegerField()
    valor_parcela = models.DecimalField(max_digits=15, decimal_places=2)
    data_vencimento = models.DateField()
    situacao = models.CharField(max_length=50)