from django.db import models


class Pessoa(models.Model):
    TIPO_CHOICES = [
        ('FORNECEDOR', 'Fornecedor'),
        ('FATURADO', 'Faturado'),
    ]

    nome_razao_social = models.CharField(max_length=255, verbose_name="Nome / Razão Social")
    fantasia = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Fantasia")
    cnpj_cpf = models.CharField(max_length=20, unique=True, verbose_name="CNPJ / CPF") # Aqui o detalhe que você queria
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Pessoa")
    status_ativo = models.BooleanField(default=True, verbose_name="Status Ativo")

    class Meta:
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"

    def __str__(self):
        return f"{self.nome_razao_social} ({self.tipo})"


class Classificacao(models.Model):
    # Regra: Define se é DESPESA ou RECEITA [cite: 238, 393]
    TIPOS_CLASSIFICACAO = [
        ('DESPESA', 'Despesa'),
        ('RECEITA', 'Receita'),
    ]

    class Meta:
        verbose_name = "Classificação"
        verbose_name_plural = "Classificações"

    descricao = models.CharField(max_length=255)  # [cite: 381, 387]
    categoria = models.CharField(max_length=100, blank=True, null=True)  # [cite: 382, 390]
    tipo = models.CharField(max_length=20, choices=TIPOS_CLASSIFICACAO)  # [cite: 393-394]
    status_ativo = models.BooleanField(default=True)  # [cite: 397-398]

    def __str__(self):
        return f"{self.descricao} - {self.tipo}"


class MovimentoContas(models.Model):
    TIPOS_MOVIMENTO = [
        ('PAGAR', 'Pagar'),
        ('RECEBER', 'Receber')
    ]

    class Meta:
        verbose_name = "Movimento de Conta"
        verbose_name_plural = "Movimentos de Contas"

    def __str__(self):
        return f"Nota {self.numero_nota} - {self.pessoa.nome_razao_social}"

    tipo = models.CharField(max_length=10, choices=TIPOS_MOVIMENTO)  # [cite: 234]
    numero_nota = models.CharField(max_length=50)  # [cite: 352-353]
    data_emissao = models.DateField()  # [cite: 354-355]
    valor_total = models.DecimalField(max_digits=15, decimal_places=2)  # [cite: 356, 358]
    descricao_produtos = models.TextField(blank=True, null=True)  # [cite: 357, 359]

    # Chave Estrangeira para Pessoas [cite: 341, 360]
    pessoa = models.ForeignKey(Pessoa, on_delete=models.PROTECT, related_name='movimentos')

    # Relacionamento N:N com Classificação [cite: 344]
    classificacoes = models.ManyToManyField(Classificacao, related_name='movimentos')


class ParcelaContas(models.Model):

    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"

    def __str__(self):
        return f"Parcela {self.numero_parcela} - R$ {self.valor_parcela}"

    movimento = models.ForeignKey(MovimentoContas, on_delete=models.CASCADE, related_name='parcelas')
    identificacao_unica = models.CharField(max_length=100, unique=True)  # [cite: 236]
    numero_parcela = models.IntegerField()  # [cite: 388-389]
    valor_parcela = models.DecimalField(max_digits=15, decimal_places=2)  # [cite: 391-392]
    data_vencimento = models.DateField()  # [cite: 395-396]
    situacao = models.CharField(max_length=50)  # [cite: 399-400]