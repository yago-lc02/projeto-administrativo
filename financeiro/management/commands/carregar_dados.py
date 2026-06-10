import random
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from django.db import connection
from financeiro.models import Pessoa, Classificacao, MovimentoContas, ParcelaContas

class Command(BaseCommand):
    help = 'Injeta 200 registros realistas e altamente comutados entre Receitas e Despesas para o RAG, limpando a base antes.'

    def handle(self, *args, **options):
        # =========================================================================
        # PASSO 1: LIMPEZA AUTOMÁTICA DA BASE DE DADOS E RESET DE SEQUÊNCIAS
        # =========================================================================
        self.stdout.write(self.style.WARNING('Limpando registros antigos do banco de dados...'))
        ParcelaContas.objects.all().delete()
        MovimentoContas.objects.all().delete()
        Pessoa.objects.all().delete()

        # Executa SQL nativo para forçar o PostgreSQL a zerar os contadores de ID ⚙️
        with connection.cursor() as cursor:
            self.stdout.write(self.style.WARNING('Resetando contadores de ID (Sequences) para o padrão 1...'))
            cursor.execute("ALTER SEQUENCE financeiro_pessoa_id_seq RESTART WITH 1;")
            cursor.execute("ALTER SEQUENCE financeiro_movimentocontas_id_seq RESTART WITH 1;")
            cursor.execute("ALTER SEQUENCE financeiro_parcelacontas_id_seq RESTART WITH 1;")

        self.stdout.write(self.style.SUCCESS('Banco de dados e contadores resetados com sucesso!'))
        self.stdout.write(self.style.WARNING('Iniciando a geração de registros altamente comutados...'))

        # =========================================================================
        # PASSO 2: CONFIGURAÇÃO DE CATEGORIAS E PRODUTOS
        # =========================================================================
        categorias_projeto = [
            {"descricao": "INSUMOS AGRÍCOLAS", "produtos": "Sementes, Fertilizantes, Defensivos Agrícolas", "tipo": "DESPESA"},
            {"descricao": "MANUTENÇÃO E OPERAÇÃO", "produtos": "Combustíveis, Peças, Componentes Mecânicos, Pneus", "tipo": "DESPESA"},
            {"descricao": "SERVIÇOS OPERACIONAIS", "produtos": "Frete e Transporte, Colheita Terceirizada, Secagem", "tipo": "DESPESA"},
            {"descricao": "ADMINISTRATIVAS", "produtos": "Honorários Contábeis, Itens de consumo geral, Alimentos", "tipo": "DESPESA"},
            {"descricao": "VENDA DE PRODUÇÃO", "produtos": "Soja em Grão, Milho em Grão, Sacas de Café", "tipo": "RECEITA"},
            {"descricao": "SERVIÇOS PRESTADOS", "produtos": "Arrendamento de Maquinário, Consultoria Agronômica", "tipo": "RECEITA"}
        ]

        obj_classificacoes = []
        for cat in categorias_projeto:
            obj, _ = Classificacao.objects.get_or_create(
                descricao=cat["descricao"],
                defaults={"categoria": "PRODUÇÃO RURAL", "tipo": cat["tipo"], "status_ativo": True}
            )
            obj_classificacoes.append({"obj": obj, "produtos": cat["produtos"].split(", "), "tipo": cat["tipo"]})

        # =========================================================================
        # PASSO 3: CADASTRO DE PARCEIROS COMUTÁVEIS (Operam Receita e Despesa)
        # =========================================================================
        parceiros_misto = [
            {"nome": "COMIGO COOPERATIVA AGROINDUSTRIAL", "fantasia": "COMIGO", "cnpj": "11.111.111/0001-01"},
            {"nome": "CARGILL ALIMENTOS SA", "fantasia": "CARGILL", "cnpj": "11.111.111/0001-02"},
            {"nome": "LOUIS DREYFUS COMPANY BRASIL", "fantasia": "LDC", "cnpj": "11.111.111/0001-03"},
            {"nome": "RIVEMA MAQUINAS E EQUIPAMENTOS LTDA", "fantasia": "RIVEMA", "cnpj": "00.000.000/0001-01"},
            {"nome": "COMBUSTIVEIS RIO VERDE LTDA", "fantasia": "POSTO RIO VERDE", "cnpj": "00.000.000/0001-02"},
            {"nome": "DISTRIBUIDORA DE SEMENTES CERRADO LTDA", "fantasia": "SEMENTES CERRADO", "cnpj": "00.000.000/0001-03"}
        ]

        faturados_reais = [
            {"nome": "OLLYVER OTTOBONI", "cpf_cnpj": "001.234.567-89"},
            {"nome": "ANTONIO BORGES", "cpf_cnpj": "002.987.654-32"},
            {"nome": "YAGO LEMES MANAGEMENT", "cpf_cnpj": "45.123.896/0001-12"}
        ]

        obj_parceiros = []
        for p in parceiros_misto:
            obj, _ = Pessoa.objects.get_or_create(
                nome_razao_social=p["nome"],
                defaults={"fantasia": p["fantasia"], "cnpj_cpf": p["cnpj"], "tipo": "MISTO", "status_ativo": True}
            )
            obj_parceiros.append(obj)

        obj_faturados = []
        for fat in faturados_reais:
            obj, _ = Pessoa.objects.get_or_create(
                nome_razao_social=fat["nome"],
                defaults={"fantasia": fat["nome"].split()[0], "cnpj_cpf": fat["cpf_cnpj"], "tipo": "FATURADO", "status_ativo": True}
            )
            obj_faturados.append(obj)

        data_base = date(2026, 1, 1)
        
        # =========================================================================
        # PASSO 4: LAÇO DE GERAÇÃO DOS 200 REGISTROS BALANCEADOS
        # =========================================================================
        for idx in range(200):
            # 50% de chance para cada natureza de operação
            tipo_movimento = random.choice(["A PAGAR", "A RECEBER"])
            
            # Filtra a classificação condizente com a natureza
            tipo_filtro = "RECEITA" if tipo_movimento == "A RECEBER" else "DESPESA"
            classif_filtradas = [c for c in obj_classificacoes if c["tipo"] == tipo_filtro]
            classif_escolhida = random.choice(classif_filtradas)
            produto_sorteado = random.choice(classif_escolhida["produtos"])
            
            # Escolha aleatória de parceiros e faturados (Gerando a comutação total!)
            parceiro = random.choice(obj_parceiros)
            faturado = random.choice(obj_faturados)
            
            # Construção de descrições ricas contendo Tipo, Produto e Envolvidos para busca textual
            if tipo_movimento == "A PAGAR":
                texto_desc = f"Despesa operacional: Compra de {produto_sorteado} junto ao parceiro {parceiro.nome_razao_social}. Documento faturado para {faturado.nome_razao_social}."
            else:
                texto_desc = f"Receita de produção: Venda comercial de {produto_sorteado} entregue para {parceiro.nome_razao_social}. Liquidação faturada em favor de {faturado.nome_razao_social}."

            num_nota = f"000.{random.randint(100,999)}.{idx+1:03d}"
            dt_emissao = data_base + timedelta(days=random.randint(0, 150))
            val_total = round(random.uniform(1500.00, 145000.00), 2)

            # Persistência do Movimento com status_ativo=True (Regra da Etapa 4)
            movimento = MovimentoContas.objects.create(
                tipo=tipo_movimento,
                numero_nota=num_nota,
                data_emissao=dt_emissao,
                valor_total=Decimal(str(val_total)),
                descricao_produtos=texto_desc,
                pessoa=parceiro,
                status_ativo=True  # ◄ GARANTE A EXCLUSÃO LÓGICA ATIVA POR PADRÃO
            )
            movimento.classificacoes.add(classif_escolhida["obj"])

            # Geração da Parcela de Consistência P1 obrigatória
            identificador = f"ID-NF-{num_nota}-P1-{get_random_string(4).upper()}"
            ParcelaContas.objects.create(
                movimento=movimento,
                identificacao_unica=identificador,
                numero_parcela=1,
                valor_parcela=Decimal(str(val_total)),
                data_vencimento=dt_emissao + timedelta(days=30),
                situacao=random.choice(["ABERTO", "QUITADO"])
            )

        self.stdout.write(self.style.SUCCESS('200 registros gerados com sucesso!'))