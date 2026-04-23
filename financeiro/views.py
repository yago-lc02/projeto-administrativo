from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Pessoa, Classificacao, MovimentoContas, ParcelaContas
from uuid import uuid4


class VerificarDadosNFView(APIView):
    def post(self, request):
        dados = request.data
        try:
            # Pegando os dados no formato do seu extrator (Etapa 1)
            cnpj_forn = dados['Fornecedor']['CNPJ']
            doc_fat = dados['Faturado']['CPF'] or dados['Faturado']['CNPJ']
            # Pega a primeira categoria da lista de despesas
            categoria_nome = dados['Classificação da DESPESA'][0]['categoria']

            fornecedor = Pessoa.objects.filter(cnpj_cpf=cnpj_forn).first()
            faturado = Pessoa.objects.filter(cnpj_cpf=doc_fat).first()
            despesa = Classificacao.objects.filter(descricao=categoria_nome).first()

            return Response({
                "fornecedor": {
                    "nome": dados['Fornecedor']['Razão Social'],
                    "status": f"EXISTE - ID: {fornecedor.id}" if fornecedor else "NÃO EXISTE"
                },
                "faturado": {
                    "nome": dados['Faturado']['Nome Completo'],
                    "status": f"EXISTE - ID: {faturado.id}" if faturado else "NÃO EXISTE"
                },
                "despesa": {
                    "descricao": categoria_nome,
                    "status": f"EXISTE - ID: {despesa.id}" if despesa else "NÃO EXISTE"
                }
            })
        except Exception as e:
            return Response({"error": f"Formato de JSON inválido: {str(e)}"}, status=400)


class SalvarDadosNFView(APIView):
    def post(self, request):
        dados = request.data
        try:
            # Extração dos dados no formato da Etapa 1
            cnpj_forn = dados['Fornecedor']['CNPJ']
            nome_forn = dados['Fornecedor']['Razão Social']

            doc_fat = dados['Faturado']['CPF'] or dados['Faturado']['CNPJ']
            nome_fat = dados['Faturado']['Nome Completo']

            categoria_nome = dados['Classificação da DESPESA'][0]['categoria']

            # Tratamento de valores: Transforma "3.254,07" em 3254.07 (float)
            valor_str = dados['ValorTotal'].replace('.', '').replace(',', '.')
            valor_final = float(valor_str)

            # Criando ou recuperando entidades
            fornecedor, _ = Pessoa.objects.get_or_create(
                cnpj_cpf=cnpj_forn,
                defaults={'nome_razao_social': nome_forn, 'tipo': 'FORNECEDOR'}
            )
            faturado, _ = Pessoa.objects.get_or_create(
                cnpj_cpf=doc_fat,
                defaults={'nome_razao_social': nome_fat, 'tipo': 'FATURADO'}
            )
            despesa, _ = Classificacao.objects.get_or_create(
                descricao=categoria_nome,
                defaults={'tipo': 'DESPESA'}
            )

            # Criando o Movimento
            movimento = MovimentoContas.objects.create(
                tipo='PAGAR',
                numero_nota=dados['Número da Nota Fiscal'],
                data_emissao=self.formatar_data(dados['Data de Emissão']),
                valor_total=valor_final,
                pessoa=fornecedor
            )
            movimento.classificacoes.add(despesa)

            # Criando a Parcela (usando o primeiro item da lista de parcelas)
            # Em vez de criar apenas a parcela [0], fazemos um loop:
            for parc in dados['Parcelas']:
                ParcelaContas.objects.create(
                    movimento=movimento,
                    identificacao_unica=str(uuid4()),
                    numero_parcela=int(parc['numero']),
                    valor_parcela=float(parc['valor'].replace('.', '').replace(',', '.')),
                    data_vencimento=self.formatar_data(parc['vencimento']),
                    situacao='PENDENTE'
                )

            return Response({"message": "Registro lançado com sucesso!"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"message": f"Erro ao processar: {str(e)}"}, status=400)

    def formatar_data(self, data_str):
        # Substitui hifens por barras para padronizar e depois quebra
        data_padronizada = data_str.replace('-', '/')
        dia, mes, ano = data_padronizada.split('/')
        return f"{ano}-{mes}-{dia}"