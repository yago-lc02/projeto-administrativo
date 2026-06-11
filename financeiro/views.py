import os
import json
import numpy as np
from decimal import Decimal
from datetime import timedelta

from google import genai
from google.genai import types

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse  
from django.contrib import messages
from django.db import transaction
from django.utils.crypto import get_random_string

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Pessoa, Classificacao, MovimentoContas, ParcelaContas
from uuid import uuid4

def limpar_valor_monetario(valor_str):
    if not valor_str:
        return Decimal('0.00')
    valor_limpo = valor_str.replace('.', '').replace(',', '.')
    return Decimal(valor_limpo)

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
# INTERFACE GRÁFICA (TELA DE LANÇAMENTOS) - REGRAS DA ETAPA 4
# =========================================================================
def listar_lancamentos(request, *args, **kwargs):
    """
    Controlador responsável por renderizar a tela do primeiro protótipo (CASHFLOW).
    """
    pessoas = Pessoa.objects.filter(status_ativo=True).order_by('nome_razao_social')

    descricao = request.GET.get('descricao', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    person_id = request.GET.get('pessoa', '').strip()
    todos = request.GET.get('todos', '').strip()

    # REGRA DO PROFESSOR (Item 3.a): A tabela nasce vazia por padrão
    movimentos = None

    # Item 3.b: Carrega dados através da Busca ou botão TODOS
    if todos == 'true' or descricao or tipo or person_id:
        # Item 3.c: Filtra apenas movimentos ativos e de parceiros ativos (Exclusão lógica)
        movimentos = MovimentoContas.objects.filter(status_ativo=True, pessoa__status_ativo=True).select_related('pessoa').prefetch_related('classificacoes').order_by('-data_emissao')

        # Item 3.e: Filtros multi-elemento cumulativos
        if descricao:
            movimentos = movimentos.filter(descricao_produtos__icontains=descricao)
        if tipo:
            movimentos = movimentos.filter(tipo=tipo)
        if person_id:
            movimentos = movimentos.filter(pessoa_id=person_id)

    context = {
        'movimentos': movimentos,
        'pessoas': list(pessoas),
    }
    return render(request, 'financeiro/lancamentos.html', context)


# =========================================================================
# FLUXO DE INCLUSÃO DE LANÇAMENTOS - ETAPA 3
# =========================================================================
def incluir_lancamento(request):
    """
    Controlador responsável por processar o formulário de cadastro de uma nova Nota.
    """
    if request.method == 'POST':
        try:
            pessoa_id = request.POST.get('pessoa')
            classificacao_id = request.POST.get('classificacao')
            
            pessoa = get_object_or_404(Pessoa, id=pessoa_id)
            classificacao = get_object_or_404(Classificacao, id=classificacao_id)
            
            # Item 3.g: No CREATE o campo status nasce oculto como ATIVO 
            movimento = MovimentoContas.objects.create(
                tipo=request.POST.get('tipo'),
                numero_nota=request.POST.get('numero_nota'),
                data_emissao=request.POST.get('data_emissao'),
                valor_total=limpar_valor_monetario(request.POST.get('valor_total')),
                descricao_produtos=request.POST.get('descricao_produtos'),
                pessoa=pessoa,
                status_ativo=True
            )
            movimento.classificacoes.add(classificacao)
            
            # Gera automaticamente a 1ª parcela de consistência exigida pelo caso de uso
            hash_identificador = f"ID-NF-{movimento.id}-P1"
            ParcelaContas.objects.create(
                movimento=movimento,
                numero_parcela=1,
                valor_parcela=movimento.valor_total,
                data_vencimento=movimento.data_emissao,
                situacao='ABERTO',
                identificacao_unica=hash_identificador
            )
            
            messages.success(request, 'Lançamento e parcela de consistência gravados com sucesso!')
            return redirect(f"{reverse('listar_lancamentos')}?todos=true")
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar lançamento: {e}')
            
    # Carrega selects da tela de inclusão
    parceiros = Pessoa.objects.filter(status_ativo=True).order_by('nome_razao_social')
    classificacoes = Classificacao.objects.all().order_by('descricao')
    
    return render(request, 'financeiro/incluir_lancamento.html', {
        'parceiros': parceiros,
        'classificacoes': classificacoes
    })


# =========================================================================
# INTERFACES DE API PARA GERENCIAMENTO DE PARCELAS DINÂMICAS
# =========================================================================
@csrf_exempt
def gerar_parcelas_api(request):
    """
    Recebe um POST via fetch() contendo o ID do movimento e a lista de parcelas geradas/editadas.
    Salva as parcelas sequenciais no banco.
    """
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            movimento_id = dados.get('movimento_id')
            parcelas_dados = dados.get('parcelas', [])

            if not movimento_id or not parcelas_dados:
                return JsonResponse({'sucesso': False, 'mensagem': 'Dados inválidos para parcelamento.'}, status=400)

            movimento = get_object_or_404(MovimentoContas, id=movimento_id)

            with transaction.atomic():
                # Exclui parcelas antigas vinculadas a este movimento para permitir regerar a grade
                ParcelaContas.objects.filter(movimento=movimento).delete()

                for p_dado in parcelas_dados:
                    n_parcela = int(p_dado.get('numero_parcela'))
                    valor_p = Decimal(str(p_dado.get('valor_parcela')))
                    venc_p = p_dado.get('data_vencimento')
                    status_p = p_dado.get('situacao', 'PENDENTE')

                    # Mapeia para compatibilidade estrutural com o BD Legado
                    situacao_db = 'ABERTO' if status_p == 'PENDENTE' else 'PAGO'
                    hash_identificador = f"ID-NF-{movimento.id}-P{n_parcela}"

                    # Regra de negócio: Vencimento da parcela não pode ser anterior à data de emissão do lançamento
                    from datetime import date, datetime
                    
                    if isinstance(venc_p, str):
                        if '-' in venc_p:
                            venc_date = datetime.strptime(venc_p.split()[0], '%Y-%m-%d').date()
                        elif '/' in venc_p:
                            venc_date = datetime.strptime(venc_p.split()[0], '%d/%m/%Y').date()
                        else:
                            raise ValueError(f"Formato de data inválido para a parcela {n_parcela}: {venc_p}")
                    elif isinstance(venc_p, datetime):
                        venc_date = venc_p.date()
                    else:
                        venc_date = venc_p
                        
                    emissao_date = movimento.data_emissao
                    if isinstance(emissao_date, str):
                        if '-' in emissao_date:
                            emissao_date = datetime.strptime(emissao_date.split()[0], '%Y-%m-%d').date()
                        elif '/' in emissao_date:
                            emissao_date = datetime.strptime(emissao_date.split()[0], '%d/%m/%Y').date()
                    elif isinstance(emissao_date, datetime):
                        emissao_date = emissao_date.date()
                        
                    if venc_date < emissao_date:
                        raise ValueError(f"A data de vencimento da parcela {n_parcela} ({venc_date.strftime('%d/%m/%Y')}) não pode ser menor que a data de emissão do lançamento ({emissao_date.strftime('%d/%m/%Y')}).")

                    ParcelaContas.objects.create(
                        movimento=movimento,
                        numero_parcela=n_parcela,
                        valor_parcela=valor_p,
                        data_vencimento=venc_p,
                        situacao=situacao_db,
                        identificacao_unica=hash_identificador
                    )

            messages.success(request, f'{len(parcelas_dados)} parcelas salvas com sucesso!')
            return JsonResponse({
                'sucesso': True, 
                'mensagem': f'{len(parcelas_dados)} parcelas salvas com sucesso!'
            })

        except Exception as e:
            messages.error(request, f'Erro ao salvar parcelas: {str(e)}')
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
                situacao_fe = 'PENDENTE' if p.situacao == 'ABERTO' else 'PAGO'
                lista_parcelas.append({
                    'numero_parcela': p.numero_parcela,
                    'valor_parcela': float(p.valor_parcela),
                    'data_vencimento': p.data_vencimento.strftime('%Y-%m-%d'),
                    'situacao': situacao_fe  # ◄ CORREÇÃO: Deixe apenas a variável limpa aqui!
                })
            
            return JsonResponse({
                'sucesso': True,
                'parcelas': lista_parcelas
            })
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': str(e)}, status=500)
            
    return JsonResponse({'sucesso': False, 'mensagem': 'Método não permitido.'}, status=405)


# =========================================================================
# FLUXO DE ALTERAÇÃO DE LANÇAMENTOS - ETAPA 4
# =========================================================================
def alterar_lancamento(request, movimento_id):
    """
    Controlador responsável por carregar os dados de um lançamento existente
    e salvar as modificações feitas pelo usuário.
    """
    # Busca o movimento pelo ID que veio da URL
    movimento = get_object_or_404(MovimentoContas, id=movimento_id)

    if request.method == 'POST':
        try:
            pessoa_id = request.POST.get('pessoa')
            classificacao_id = request.POST.get('classificacao')
            
            pessoa = get_object_or_404(Pessoa, id=pessoa_id)
            classificacao = get_object_or_404(Classificacao, id=classificacao_id)
            
            # Atualiza os campos do registro existente
            movimento.tipo = request.POST.get('tipo')
            movimento.numero_nota = request.POST.get('numero_nota')
            movimento.data_emissao = request.POST.get('data_emissao')
            movimento.valor_total = limpar_valor_monetario(request.POST.get('valor_total'))
            movimento.descricao_produtos = request.POST.get('descricao_produtos')
            movimento.pessoa = p = pessoa
            movimento.save()
            
            # Atualiza a classificação (limpa as antigas e poe a nova)
            movimento.classificacoes.clear()
            movimento.classificacoes.add(classificacao)
            
            # Regra de consistência: Atualiza também a primeira parcela vinculada para manter o valor igual
            parcela_p1 = ParcelaContas.objects.filter(movimento=movimento, numero_parcela=1).first()
            if parcela_p1:
                parcela_p1.valor_parcela = movimento.valor_total
                parcela_p1.data_vencimento = movimento.data_emissao
                parcela_p1.save()

            messages.success(request, 'Lançamento financeiro atualizado com sucesso!')
            return redirect(f"{reverse('listar_lancamentos')}?todos=true")
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar lançamento: {e}')

    # Se for GET, carrega a tela com os dados atuais do registro preenchidos
    parceiros = Pessoa.objects.filter(status_ativo=True).order_by('nome_razao_social')
    classificacoes = Classificacao.objects.all().order_by('descricao')
    
    # Puxa a classificação atual dele para marcar o 'selected' no HTML
    classificacao_atual = movimento.classificacoes.first()

    return render(request, 'financeiro/alterar_lancamento.html', {
        'movimento': movimento,
        'parceiros': parceiros,
        'peers_lista': parceiros,
        'classificacoes': classificacoes,
        'classificacao_atual': classificacao_atual
    })


# =========================================================================
# LÓGICA DE EXCLUSÃO LÓGICA (INATIVAÇÃO) - ETAPA 4
# =========================================================================
def excluir_lancamento(request, movimento_id):
    movimento = get_object_or_404(MovimentoContas, id=movimento_id)
    
    if request.method == 'POST':
        try:
            # Item 3.i: Altera o campo STATUS para INATIVO
            movimento.status_ativo = False
            movimento.save()

            messages.success(request, 'Lançamento inativado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao inativar: {e}')
            
        url_destino = f"{reverse('listar_lancamentos')}?todos=true"
        return redirect(url_destino)
        
    return render(request, 'financeiro/excluir_lancamento.html', {'movimento': movimento})


# =========================================================================
# INTEGRAÇÃO DO ANALISADOR DE JSON (ETAPA 2)
# =========================================================================
class VerificarDadosNFView(APIView):
    def post(self, request):
        dados = request.data
        try:
            cnpj_forn = dados['Fornecedor']['CNPJ']
            doc_fat = dados['Faturado'].get('CPF') or dados['Faturado'].get('CNPJ')
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
            cnpj_forn = dados['Fornecedor']['CNPJ']
            nome_forn = dados['Fornecedor']['Razão Social']

            doc_fat = dados['Faturado'].get('CPF') or dados['Faturado'].get('CNPJ')
            nome_fat = dados['Faturado']['Nome Completo']

            categoria_nome = dados['Classificação da DESPESA'][0]['categoria']

            valor_final = float(dados['ValorTotal'].replace('.', '').replace(',', '.'))

            fornecedor, _ = Pessoa.objects.get_or_create(
                cnpj_cpf=cnpj_forn,
                defaults={'nome_razao_social': nome_forn, 'tipo': 'FORNECEDOR', 'status_ativo': True}
            )
            faturado, _ = Pessoa.objects.get_or_create(
                cnpj_cpf=doc_fat,
                defaults={'nome_razao_social': nome_fat, 'tipo': 'FATURADO', 'status_ativo': True}
            )
            despesa, _ = Classificacao.objects.get_or_create(
                descricao=categoria_nome,
                defaults={'tipo': 'DESPESA', 'categoria': 'PRODUÇÃO RURAL', 'status_ativo': True}
            )

            nota_numero = dados['Número da Nota Fiscal']
            ja_existe = MovimentoContas.objects.filter(
                pessoa=fornecedor,
                numero_nota=nota_numero,
                status_ativo=True
            ).exists()

            if ja_existe:
                return Response(
                    {"message": "Dados já cadastrados: Esta nota fiscal já foi lançada para este fornecedor."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            movimento = MovimentoContas.objects.create(
                tipo='A PAGAR',
                numero_nota=dados['Número da Nota Fiscal'],
                data_emissao=self.formatar_data(dados['Data de Emissão']),
                valor_total=valor_final,
                pessoa=fornecedor,
                status_ativo=True
            )
            movimento.classificacoes.add(despesa)

            for parc in dados['Parcelas']:
                ParcelaContas.objects.create(
                    movimento=movimento,
                    identificacao_unica=str(uuid4()),
                    numero_parcela=int(parc['numero']),
                    valor_parcela=float(parc['valor'].replace('.', '').replace(',', '.')),
                    data_vencimento=self.formatar_data(parc['vencimento']),
                    situacao='ABERTO'
                )

            return Response({"message": "Registro lançado com sucesso!"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"message": f"Erro ao processar: {str(e)}"}, status=400)

    def formatar_data(self, data_str):
        data_padronizada = data_str.replace('-', '/')
        partes = data_padronizada.split('/')
        return f"{partes[2]}-{partes[1]}-{partes[0]}"


def analisador_json_tela(request):
    return render(request, 'financeiro/analisar_json.html')


# =========================================================================
# INTEGRAÇÃO DA TELA DE CHAT RAG (ETAPA 3)
# =========================================================================
def chat_rag_tela(request):
    return render(request, 'financeiro/chat.html')


# =========================================================================
# CRUD DE PESSOAS (PARCEIROS COMERCIAIS)
# =========================================================================
def listar_pessoas(request):
    """
    Controlador responsável por listar e filtrar os parceiros (Pessoas).
    A tabela nasce vazia por padrão, carregando dados se pesquisado ou pelo botão "Todos".
    """
    nome_razao = request.GET.get('nome_razao_social', '').strip()
    cnpj_cpf = request.GET.get('cnpj_cpf', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    todos = request.GET.get('todos', '').strip()

    pessoas = None

    if todos == 'true' or nome_razao or cnpj_cpf or tipo:
        pessoas = Pessoa.objects.filter(status_ativo=True).order_by('nome_razao_social')

        if nome_razao:
            pessoas = pessoas.filter(nome_razao_social__icontains=nome_razao)
        if cnpj_cpf:
            pessoas = pessoas.filter(cnpj_cpf__icontains=cnpj_cpf)
        if tipo:
            pessoas = pessoas.filter(tipo=tipo)

    context = {
        'pessoas': pessoas,
    }
    return render(request, 'financeiro/pessoas.html', context)


def incluir_pessoa(request):
    """
    Controlador responsável por incluir um novo parceiro.
    Garante a unicidade do CNPJ/CPF e trata reativação lógica caso o registro anterior estivesse inativo.
    """
    if request.method == 'POST':
        nome_razao_social = request.POST.get('nome_razao_social', '').strip()
        fantasia = request.POST.get('fantasia', '').strip() or None
        cnpj_cpf = request.POST.get('cnpj_cpf', '').strip()
        tipo = request.POST.get('tipo')

        if not nome_razao_social or not cnpj_cpf or not tipo:
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
        else:
            existente = Pessoa.objects.filter(cnpj_cpf=cnpj_cpf).first()
            if existente:
                if existente.status_ativo:
                    messages.error(request, 'Este CNPJ / CPF já está cadastrado no sistema.')
                    return render(request, 'financeiro/incluir_pessoa.html', {
                        'nome_razao_social': nome_razao_social,
                        'fantasia': fantasia,
                        'cnpj_cpf': cnpj_cpf,
                        'tipo': tipo,
                    })
                else:
                    # Se existia inativo, reativa e atualiza
                    existente.nome_razao_social = nome_razao_social
                    existente.fantasia = fantasia
                    existente.tipo = tipo
                    existente.status_ativo = True
                    existente.save()
                    messages.success(request, 'Parceiro reativado e atualizado com sucesso!')
                    return redirect(f"{reverse('listar_pessoas')}?todos=true")
            else:
                try:
                    Pessoa.objects.create(
                        nome_razao_social=nome_razao_social,
                        fantasia=fantasia,
                        cnpj_cpf=cnpj_cpf,
                        tipo=tipo,
                        status_ativo=True
                    )
                    messages.success(request, 'Parceiro cadastrado com sucesso!')
                    return redirect(f"{reverse('listar_pessoas')}?todos=true")
                except Exception as e:
                    messages.error(request, f'Erro ao cadastrar parceiro: {str(e)}')

    return render(request, 'financeiro/incluir_pessoa.html')


def alterar_pessoa(request, pessoa_id):
    """
    Controlador responsável por alterar os dados de um parceiro existente.
    """
    pessoa = get_object_or_404(Pessoa, id=pessoa_id)

    if request.method == 'POST':
        nome_razao_social = request.POST.get('nome_razao_social', '').strip()
        fantasia = request.POST.get('fantasia', '').strip() or None
        cnpj_cpf = request.POST.get('cnpj_cpf', '').strip()
        tipo = request.POST.get('tipo')

        if not nome_razao_social or not cnpj_cpf or not tipo:
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
        else:
            existente = Pessoa.objects.filter(cnpj_cpf=cnpj_cpf).exclude(id=pessoa.id).first()
            if existente:
                messages.error(request, 'Este CNPJ / CPF já está cadastrado para outro parceiro.')
            else:
                try:
                    pessoa.nome_razao_social = nome_razao_social
                    pessoa.fantasia = fantasia
                    pessoa.cnpj_cpf = cnpj_cpf
                    pessoa.tipo = tipo
                    pessoa.save()
                    messages.success(request, 'Parceiro atualizado com sucesso!')
                    return redirect(f"{reverse('listar_pessoas')}?todos=true")
                except Exception as e:
                    messages.error(request, f'Erro ao atualizar parceiro: {str(e)}')

    return render(request, 'financeiro/alterar_pessoa.html', {'pessoa': pessoa})


def excluir_pessoa(request, pessoa_id):
    """
    Controlador responsável por realizar a inativação lógica do parceiro (exclusão lógica).
    """
    pessoa = get_object_or_404(Pessoa, id=pessoa_id)

    if request.method == 'POST':
        try:
            pessoa.status_ativo = False
            pessoa.save()
            messages.success(request, 'Parceiro inativado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao inativar parceiro: {str(e)}')

        return redirect(f"{reverse('listar_pessoas')}?todos=true")

    return render(request, 'financeiro/excluir_pessoa.html', {'pessoa': pessoa})


# =========================================================================
# CRUD DE CLASSIFICAÇÕES (CATEGORIAS)
# =========================================================================
def listar_classificacoes(request):
    """
    Controlador responsável por listar e filtrar as classificações.
    A tabela nasce vazia por padrão, carregando dados se pesquisado ou pelo botão "Todos".
    """
    descricao = request.GET.get('descricao', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    todos = request.GET.get('todos', '').strip()

    classificacoes = None

    if todos == 'true' or descricao or categoria or tipo:
        classificacoes = Classificacao.objects.filter(status_ativo=True).order_by('descricao')

        if descricao:
            classificacoes = classificacoes.filter(descricao__icontains=descricao)
        if categoria:
            classificacoes = classificacoes.filter(categoria__icontains=categoria)
        if tipo:
            classificacoes = classificacoes.filter(tipo=tipo)

    context = {
        'classificacoes': classificacoes,
    }
    return render(request, 'financeiro/classificacoes.html', context)


def incluir_classificacao(request):
    """
    Controlador responsável por incluir uma nova classificação.
    """
    if request.method == 'POST':
        descricao = request.POST.get('descricao', '').strip()
        categoria = request.POST.get('categoria', '').strip() or None
        tipo = request.POST.get('tipo')

        if not descricao or not tipo:
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
        else:
            try:
                Classificacao.objects.create(
                    descricao=descricao,
                    categoria=categoria,
                    tipo=tipo,
                    status_ativo=True
                )
                messages.success(request, 'Classificação cadastrada com sucesso!')
                return redirect(f"{reverse('listar_classificacoes')}?todos=true")
            except Exception as e:
                messages.error(request, f'Erro ao cadastrar classificação: {str(e)}')

    return render(request, 'financeiro/incluir_classificacao.html')


def alterar_classificacao(request, classificacao_id):
    """
    Controlador responsável por alterar os dados de uma classificação existente.
    """
    classificacao = get_object_or_404(Classificacao, id=classificacao_id)

    if request.method == 'POST':
        descricao = request.POST.get('descricao', '').strip()
        categoria = request.POST.get('categoria', '').strip() or None
        tipo = request.POST.get('tipo')

        if not descricao or not tipo:
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
        else:
            try:
                classificacao.descricao = descricao
                classificacao.categoria = categoria
                classificacao.tipo = tipo
                classificacao.save()
                messages.success(request, 'Classificação atualizada com sucesso!')
                return redirect(f"{reverse('listar_classificacoes')}?todos=true")
            except Exception as e:
                messages.error(request, f'Erro ao atualizar classificação: {str(e)}')

    return render(request, 'financeiro/alterar_classificacao.html', {'classificacao': classificacao})


def excluir_classificacao(request, classificacao_id):
    """
    Controlador responsável por inativar logicamente uma classificação (exclusão lógica).
    """
    classificacao = get_object_or_404(Classificacao, id=classificacao_id)

    if request.method == 'POST':
        try:
            classificacao.status_ativo = False
            classificacao.save()
            messages.success(request, 'Classificação inativada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao inativar classificação: {str(e)}')

        return redirect(f"{reverse('listar_classificacoes')}?todos=true")

    return render(request, 'financeiro/excluir_classificacao.html', {'classificacao': classificacao})