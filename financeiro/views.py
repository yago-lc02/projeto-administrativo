from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Pessoa, Classificacao, MovimentoContas, ParcelaContas
from uuid import uuid4


class VerificarDadosNFView(APIView):
    def post(self, request):
        dados = request.data
        try:
            # Pegando os dados no formato do extrator (Etapa 1)
            cnpj_forn = dados['Fornecedor']['CNPJ']

            # Ajuste dinâmico para CPF ou CNPJ do faturado
            doc_fat = dados['Faturado'].get('CPF') or dados['Faturado'].get('CNPJ')

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
            # 1. Extração dos dados
            cnpj_forn = dados['Fornecedor']['CNPJ']
            nome_forn = dados['Fornecedor']['Razão Social']

            doc_fat = dados['Faturado'].get('CPF') or dados['Faturado'].get('CNPJ')
            nome_fat = dados['Faturado']['Nome Completo']

            categoria_nome = dados['Classificação da DESPESA'][0]['categoria']

            # Tratamento de valor total
            valor_final = float(dados['ValorTotal'].replace('.', '').replace(',', '.'))

            # 2. Criando ou recuperando entidades (Regras 1, 2 e 3 do PDF)
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

            # 1. Verifique se a nota já existe antes de criar qualquer coisa
            nota_numero = dados['Número da Nota Fiscal']
            ja_existe = MovimentoContas.objects.filter(
                pessoa=fornecedor,
                numero_nota=nota_numero
            ).exists()

            if ja_existe:
                return Response(
                    {"message": "Dados já cadastrados: Esta nota fiscal já foi lançada para este fornecedor."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 3. Criando o Movimento (Regra 4 do PDF)
            movimento = MovimentoContas.objects.create(
                tipo='A PAGAR',
                numero_nota=dados['Número da Nota Fiscal'],
                data_emissao=self.formatar_data(dados['Data de Emissão']),
                valor_total=valor_final,
                pessoa=fornecedor
            )
            movimento.classificacoes.add(despesa)

            # 4. Criando TODAS as Parcelas (Regra: Uma ou mais parcelas)
            for parc in dados['Parcelas']:
                ParcelaContas.objects.create(
                    movimento=movimento,
                    identificacao_unica=str(uuid4()),  # Requisito: Identificacao (UNICA)
                    numero_parcela=int(parc['numero']),
                    valor_parcela=float(parc['valor'].replace('.', '').replace(',', '.')),
                    data_vencimento=self.formatar_data(parc['vencimento']),
                    situacao='PENDENTE'
                )

            # 5. Informar ao usuário (Regra 5 do PDF)
            return Response({"message": "Registro lançado com sucesso!"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"message": f"Erro ao processar: {str(e)}"}, status=400)

    def formatar_data(self, data_str):
        # Padroniza hifens para barras e inverte para o padrão do banco (YYYY-MM-DD)
        data_padronizada = data_str.replace('-', '/')
        partes = data_padronizada.split('/')
        return f"{partes[2]}-{partes[1]}-{partes[0]}"