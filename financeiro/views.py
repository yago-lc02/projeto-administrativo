import os
import json
import numpy as np
from decimal import Decimal
from datetime import timedelta

from google import genai
from google.genai import types

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Pessoa, Classificacao, MovimentoContas, ParcelaContas
from uuid import uuid4
from django.shortcuts import render, redirect
from datetime import timedelta
from django.utils.crypto import get_random_string
from django.contrib import messages


# =========================================================================
# CLASSE DE INTELIGÊNCIA ARTIFICIAL (RAG) - CONSERVADA E INTOCADA 🚀
# =========================================================================
class ConsultaRAGView(APIView):
    def post(self, request):
        pergunta = request.data.get('pergunta', '')
        metodo = request.data.get('metodo', 'simples')  # 'simples' ou 'embeddings'

        if not pergunta:
            return Response({"error": "A pergunta não pode estar vazia."}, status=status.HTTP_400_BAD_REQUEST)

        # Inicialização do Gemini
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            client = genai.Client(api_key=api_key)
        except Exception as e:
            return Response({"error": f"Falha ao inicializar o cliente Gemini: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Buscamos os dados do banco filtrando por registros ativos para a IA não auditar lixo inativo
        try:
            movimentos = list(MovimentoContas.objects.filter(status_ativo=True).select_related('pessoa').order_by('-id')[:20])
        except Exception as e:
            return Response({
                "error": f"Erro ao consultar a tabela MovimentoContas. Verifique se as colunas existem. Detalhe: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not movimentos:
            return Response(
                {"resposta": "Nenhum registro de movimentação financeira foi localizado no banco de dados atualmente."},
                status=status.HTTP_200_OK)

        contexto_banco = ""

        # =========================================================================
        # ABORDAGEM 1: RAG SIMPLES (Busca de Metadados Textuais via SQL)
        # =========================================================================
        if metodo == 'simples':
            contexto_banco = "DADOS ATUAIS COMPLETOS DO SISTEMA FINANCEIRO E CADASTROS:\n"
            for mov in movimentos[:10]:
                p = mov.pessoa
                nome_fornecedor = getattr(p, 'nome_razao_social', 'Não Identificado')
                fantasia_fornecedor = getattr(p, 'fantasia', 'Não informado')
                cnpj_cpf = getattr(p, 'cnpj_cpf', 'Não informado')
                tipo_pessoa = getattr(p, 'tipo', 'Não informado')

                classificacoes_lista = []
                for c in mov.classificacoes.all():
                    desc = getattr(c, 'descricao', '')
                    cat = getattr(c, 'categoria', '')
                    tipo_c = getattr(c, 'tipo', '')
                    classificacoes_lista.append(f"[{desc} ({cat}) - {tipo_c}]")
                texto_classificacoes = " , ".join(
                    classificacoes_lista) if classificacoes_lista else "Sem classificação registrada"

                num_nota = getattr(mov, 'numero_nota', 'S/N')
                val_total = getattr(mov, 'valor_total', '0.00')
                tipo_mov = getattr(mov, 'tipo', 'A PAGAR')
                dt_emissao = getattr(mov, 'data_emissao', 'Não informada')

                parcelas_info = []
                parcelas = ParcelaContas.objects.filter(movimento=mov)
                for p_obj in parcelas:
                    p_num = getattr(p_obj, 'numero_parcela', '1')
                    p_val = getattr(p_obj, 'valor_parcela', '0.00')
                    p_venc = getattr(p_obj, 'data_vencimento', 'Não informada')
                    parcelas_info.append(f"[Parc {p_num}: R$ {p_val} Venc: {p_venc}]")
                texto_parcelas = " | ".join(parcelas_info) if parcelas_info else "Nenhuma parcela registrada"

                contexto_banco += (
                    f"- Nota: {num_nota} | Fornecedor: {nome_fornecedor} (Fantasia: {fantasia_fornecedor}) | "
                    f"CNPJ/CPF: {cnpj_cpf} | Tipo Pessoa: {tipo_pessoa} | "
                    f"Classificações: {texto_classificacoes} | Valor Total: R$ {val_total} | "
                    f"Tipo Movimento: {tipo_mov} | Data Emissão: {dt_emissao} | Parcelas: {texto_parcelas}\n"
                )

        # =========================================================================
        # ABORDAGEM 2: RAG EMBEDDINGS (Busca Semântica Avançada) 🚀
        # =========================================================================
        elif metodo == 'embeddings':
            try:
                query_embedding_response = client.models.embed_content(
                    model='gemini-embedding-001',
                    contents=pergunta
                )
                vector_pergunta = np.array(query_embedding_response.embeddings[0].values)

                trechos_e_scores = []

                for mov in movimentos:
                    p = mov.pessoa
                    nome_fornecedor = getattr(p, 'nome_razao_social', 'Não Identificado')
                    fantasia_fornecedor = getattr(p, 'fantasia', 'Não informado')
                    cnpj_cpf = getattr(p, 'cnpj_cpf', 'Não informado')
                    tipo_pessoa = getattr(p, 'tipo', 'Não informado')

                    classificacoes_lista = []
                    for c in mov.classificacoes.all():
                        classificacoes_lista.append(
                            f"categoria {getattr(c, 'categoria', '')} descrita como {getattr(c, 'descricao', '')} classificada tipo {getattr(c, 'tipo', '')}")
                    texto_classificacoes = " e ".join(
                        classificacoes_lista) if classificacoes_lista else "sem classificações de categorias"

                    num_nota = getattr(mov, 'numero_nota', 'S/N')
                    val_total = getattr(mov, 'valor_total', '0.00')
                    tipo_mov = getattr(mov, 'tipo', 'A PAGAR')
                    dt_emissao = getattr(mov, 'data_emissao', 'Não informada')

                    parcelas_info = []
                    parcelas = ParcelaContas.objects.filter(movimento=mov)
                    for p_obj in parcelas:
                        parcelas_info.append(
                            f"parcela número {getattr(p_obj, 'numero_parcela', '1')} com valor de R$ {getattr(p_obj, 'valor_parcela', '0.00')} vencendo em {getattr(p_obj, 'data_vencimento', 'Não informada')}")
                    texto_parcelas = ", ".join(parcelas_info) if parcelas_info else "sem parcelas detalhadas"

                    texto_nota = (
                        f"Nota Fiscal Número: {num_nota}. Fornecedor Emitente: {nome_fornecedor}, também conhecido pelo nome fantasia {fantasia_fornecedor}, "
                        f"inscrito no documento fiscal CNPJ ou CPF número {cnpj_cpf}, enquadrado como tipo de pessoa {tipo_pessoa}. "
                        f"Valor Total do movimento: R$ {val_total}. Classificações financeiras atreladas: {texto_classificacoes}. "
                        f"Natureza da operation: {tipo_mov}. Emitido na data de: {dt_emissao}. "
                        f"Cronograma de parcelamento registrado: {texto_parcelas}."
                    )

                    nota_embedding_response = client.models.embed_content(
                        model='gemini-embedding-001',
                        contents=texto_nota
                    )
                    vector_nota = np.array(nota_embedding_response.embeddings[0].values)

                    dot_product = np.dot(vector_pergunta, vector_nota)
                    norm_pergunta = np.linalg.norm(vector_pergunta)
                    norm_nota = np.linalg.norm(vector_nota)

                    similarity = dot_product / (norm_pergunta * norm_nota) if (norm_pergunta * norm_nota) > 0 else 0

                    trechos_e_scores.append((similarity, texto_nota))

                trechos_e_scores.sort(key=lambda x: x[0], reverse=True)
                melhores_contextos = [trecho for score, trecho in trechos_e_scores[:3]]

                contexto_banco = "CONTEXTO SEMÂNTICO SELECIONADO POR PROXIMIDADE VETORIAL:\n" + "\n".join(
                    melhores_contextos)

            except Exception as e:
                return Response({"error": f"Erro no pipeline de Embeddings: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({"error": "Método de consulta inválido."}, status=status.HTTP_400_BAD_REQUEST)

        # =========================================================================
        # PROMPT DE GERAÇÃO FINAL (Processa a resposta para AMBOS os métodos)
        # =========================================================================
        prompt_sistema = (
            "Você é um analista financeiro sênior e auditor de contas corporativas. "
            "Baseando-se estritamente no contexto dos dados reais do banco fornecidos abaixo (que abrangem notas, dados cadastrais de pessoas, CNPJ/CPF, classificações e parcelas), "
            "responda à pergunta do usuário de forma altamente profissional, encorpada e formal. "
            "Formate valores em Reais (R$) e datas adequadamente. Se os dados fornecidos não contiverem "
            "a resposta para a pergunta, informe formalmente que o registro específico não foi localizado na base atual.\n\n"
            f"CONTEXTO DOS DADOS DO BANCO:\n{contexto_banco}\n\n"
            f"PERGUNTA DO USUÁRIO: {pergunta}"
        )

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt_sistema,
            )
            return Response({"resposta": response.text}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Erro na API do Gemini durante a generation: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================================================================
# INTERFACE GRÁFICA (TELA DE LANÇAMENTOS) - REGRAS DA ETAPA 4 🎨
# =========================================================================
def listar_lancamentos(request, *args, **kwargs):
    """
    Controlador responsável por renderizar a tela do primeiro protótipo (CASHFLOW).
    Aplica rigorosamente as regras do PDF do professor.
    """
    # Sempre carregamos os parceiros ATIVOS para popular o filtro Select
    pessoas = Pessoa.objects.filter(status_ativo=True).order_by('nome_razao_social')

    # Captura os parâmetros de busca do formulário
    descricao = request.GET.get('descricao', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    pessoa_id = request.GET.get('pessoa', '').strip()
    todos = request.GET.get('todos', '').strip()

    # REGRA DO PROFESSOR: A tabela nasce estritamente vazia
    movimentos = None

    # Se o usuário acionou o botão "TODOS" ou clicou em "Consultar" com algum filtro preenchido
    if todos == 'true' or descricao or tipo or pessoa_id:
        # 🔒 CORREÇÃO DA ETAPA 4: Filtra os movimentos onde status_ativo=True e a pessoa está ativa!
        movimentos = MovimentoContas.objects.filter(status_ativo=True, pessoa__status_ativo=True).select_related('pessoa').order_by('-data_emissao')

        # Filtros combinados multi-elemento cumulativos
        if descricao:
            movimentos = movimentos.filter(descricao_produtos__icontains=descricao)
        if tipo:
            movimentos = movimentos.filter(tipo=tipo)
        if pessoa_id:
            movimentos = movimentos.filter(pessoa_id=pessoa_id)

    context = {
        'movimentos': movimentos,
        'pessoas': list(pessoas),
    }

    return render(request, 'financeiro/lancamentos.html', context)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse  # ◄ CORREÇÃO: Importa a ferramenta de rotas dinâmicas
from .models import MovimentoContas

# =========================================================================
# GERAÇÃO DE PARCELAS DINÂMICAS ⚙️
# =========================================================================
from django.db import transaction

@csrf_exempt
def gerar_parcelas_api(request):
    """
    Recebe um POST via fetch() contendo o ID do movimento e a lista de parcelas geradas/editadas.
    Salva as parcelas sequenciais no banco.
    """
    if request.method == 'POST':
        try:
            # 1. Captura e converte os dados que vieram do JavaScript
            dados = json.loads(request.body)
            movimento_id = dados.get('movimento_id')
            parcelas_dados = dados.get('parcelas', [])

            if not movimento_id or not parcelas_dados:
                return JsonResponse({'sucesso': False, 'mensagem': 'Dados inválidos para parcelamento.'}, status=400)

            # 2. Busca o lançamento original no banco de dados
            movimento = get_object_or_404(MovimentoContas, id=movimento_id)

            # 3. Criação das parcelas dentro de uma transação atômica
            with transaction.atomic():
                # Exclui parcelas antigas vinculadas a este movimento (permite regerar)
                ParcelaContas.objects.filter(movimento=movimento).delete()

                for p_dado in parcelas_dados:
                    n_parcela = int(p_dado.get('numero_parcela'))
                    valor_p = Decimal(str(p_dado.get('valor_parcela')))
                    venc_p = p_dado.get('data_vencimento')
                    status_p = p_dado.get('situacao', 'PENDENTE')

                    # Mapeia PENDENTE -> ABERTO para compatibilidade com o banco de dados
                    situacao_db = 'ABERTO' if status_p == 'PENDENTE' else 'PAGO'
                    hash_identificador = f"ID-NF-{movimento.id}-P{n_parcela}"

                    # Cria o objeto no banco de dados
                    ParcelaContas.objects.create(
                        movimento=movimento,
                        numero_parcela=n_parcela,
                        valor_parcela=valor_p,
                        data_vencimento=venc_p,
                        situacao=situacao_db,
                        identificacao_unica=hash_identificador
                    )

            return JsonResponse({
                'sucesso': True, 
                'mensagem': f'{len(parcelas_dados)} parcelas salvas com sucesso!'
            })

        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': str(e)}, status=500)

    return JsonResponse({'sucesso': False, 'mensagem': 'Método não permitido.'}, status=405)


def obter_parcelas_api(request, movimento_id):
    """
    Retorna as parcelas existentes vinculadas a um movimento_id como JSON.
    """
    if request.method == 'GET':
        try:
            movimento = get_object_or_404(MovimentoContas, id=movimento_id)
            parcelas = ParcelaContas.objects.filter(movimento=movimento).order_by('numero_parcela')
            
            lista_parcelas = []
            for p in parcelas:
                # Mapeia ABERTO -> PENDENTE e PAGO -> PAGO para o frontend
                situacao_fe = 'PENDENTE' if p.situacao == 'ABERTO' else 'PAGO'
                lista_parcelas.append({
                    'numero_parcela': p.numero_parcela,
                    'valor_parcela': float(p.valor_parcela),
                    'data_vencimento': p.data_vencimento.strftime('%Y-%m-%d'),
                    'situacao': situacao_fe
                })
            
            return JsonResponse({
                'sucesso': True,
                'parcelas': lista_parcelas
            })
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': str(e)}, status=500)
            
    return JsonResponse({'sucesso': False, 'mensagem': 'Método não permitido.'}, status=405)


def incluir_lancamento(request):
    if request.method == 'POST':
        # 1. Coleta os dados vindos do formulário HTML
        descricao = request.POST.get('descricao_produtos')
        tipo = request.POST.get('tipo')
        pessoa_id = request.POST.get('pessoa')
        classificacao_id = request.POST.get('classificacao')
        numero_nota = request.POST.get('numero_nota')
        data_emissao = request.POST.get('data_emissao')
        valor_total = request.POST.get('valor_total')

        try:
            # Converte a string da data do HTML para um objeto date do Python
            from datetime import datetime
            data_emissao_obj = datetime.strptime(data_emissao, '%Y-%m-%d').date()

            # 2. Cria o registro principal do Movimento
            movimento = MovimentoContas.objects.create(
                tipo=tipo,
                numero_nota=numero_nota,
                data_emissao=data_emissao_obj,
                valor_total=valor_total,
                descricao_produtos=descricao,
                pessoa_id=pessoa_id
            )
            
            # 3. Vincula a classificação (Relacionamento ManyToMany)
            if classificacao_id:
                movimento.classificacoes.add(classificacao_id)

            # 4. Cria a primeira parcela padrão vinculada (Regra de consistência)
            identificador = f"ID-NF-{numero_nota}-P1-{get_random_string(4).upper()}"
            ParcelaContas.objects.create(
                movimento=movimento,
                identificacao_unica=identificador,
                numero_parcela=1,
                valor_parcela=valor_total,
                data_vencimento=timedelta(days=30) + data_emissao_obj, # Vence em 30 dias
                situacao='ABERTO'
            )

            messages.success(request, 'Lançamento incluído com sucesso!')
            return redirect('listar_lancamentos') # Redireciona de volta para a tabela

        except Exception as e:
            messages.error(request, f'Erro ao salvar o lançamento: {e}')
    
    # Se for GET (carregando a página pela primeira vez):
    # Puxa apenas quem está ativo no sistema para listar nos selects da tela
    parceiros = Pessoa.objects.filter(status_ativo=True).order_by('nome_razao_social')
    classificacoes = Classificacao.objects.filter(status_ativo=True).order_by('descricao')
    
    context = {
        'parceiros': parceiros,
        'classificacoes': classificacoes
    }
    return render(request, 'financeiro/incluir_lancamento.html', context)


def excluir_lancamento(request):
    if request.method == 'POST':
        movimento_id = request.POST.get('movimento_id')
        try:
            movimento = MovimentoContas.objects.get(id=movimento_id)
            
            # 🔒 EXCLUSÃO LÓGICA: Inativa o registro
            movimento.status_ativo = False
            movimento.save()

            messages.success(request, 'Lançamento inativado com sucesso!')
        except MovimentoContas.DoesNotExist:
            messages.error(request, 'Lançamento não encontrado.')
        except Exception as e:
            messages.error(request, f'Erro ao inativar: {e}')
            
    # 🔄 CORREÇÃO DEFECITIVA: Usa o reverse para descobrir a URL correta do seu sistema
    # e injeta o '?todos=true' no final dela de forma dinâmica!
    url_destino = f"{reverse('listar_lancamentos')}?todos=true"
    return redirect(url_destino)
