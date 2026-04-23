from django.contrib import admin
from .models import Pessoa, Classificacao, MovimentoContas, ParcelaContas


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    # Exibe os dados principais e o status para a regra de Inativação
    list_display = ('nome_razao_social', 'cnpj_cpf', 'tipo', 'status_ativo')
    list_filter = ('tipo', 'status_ativo')
    search_fields = ('nome_razao_social', 'cnpj_cpf')

    # Atende a regra: "Cadastros não podem ser excluídos"
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Classificacao)
class ClassificacaoAdmin(admin.ModelAdmin):
    # Padroniza a exibição da categoria de despesa
    list_display = ('descricao', 'tipo', 'status_ativo')
    list_filter = ('tipo', 'status_ativo')
    search_fields = ('descricao',)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MovimentoContas)
class MovimentoAdmin(admin.ModelAdmin):
    # Formata o valor da nota na listagem principal
    list_display = ('numero_nota', 'pessoa', 'get_valor_total_formatado', 'data_emissao', 'tipo')

    @admin.display(description='Valor Total')
    def get_valor_total_formatado(self, obj):
        if obj.valor_total:
            return f"R$ {obj.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return "R$ 0,00"


@admin.register(ParcelaContas)
class ParcelaAdmin(admin.ModelAdmin):
    # Exibe a Identificação UNICA e valor formatado conforme o PDF
    list_display = ('identificacao_unica', 'get_valor_formatado', 'data_vencimento', 'situacao')

    @admin.display(description='Valor da Parcela')
    def get_valor_formatado(self, obj):
        if obj.valor_parcela:
            return f"R$ {obj.valor_parcela:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return "R$ 0,00"