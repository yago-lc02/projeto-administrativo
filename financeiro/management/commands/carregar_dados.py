import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from financeiro.models import Pessoa, Classificacao, MovimentoContas, ParcelaContas

class Command(BaseCommand):
    help = 'Injeta 200 registros realistas divididos entre Receitas e Despesas para o RAG, limpando a base antes.'

    def handle(self, *args, **options):
        # =========================================================================
        # PASSO 1: LIMPEZA AUTOMÁTICA DA BASE DE DADOS E RESET DE SEQUÊNCIAS
        # =========================================================================
        self.stdout.write(self.style.WARNING('Limpando registros antigos do banco de dados...'))
        ParcelaContas.objects.all().delete()
        MovimentoContas.objects.all().delete()
        Pessoa.objects.all().delete()

        # Executa SQL nativo para forçar o PostgreSQL a zerar os contadores de ID ⚙️
        from django.db import connection
        with connection.cursor() as cursor:
            self.stdout.write(self.style.WARNING('Resetando contadores de ID (Sequences) para o padrão 1...'))
            cursor.execute("ALTER SEQUENCE financeiro_pessoa_id_seq RESTART WITH 1;")
            cursor.execute("ALTER SEQUENCE financeiro_movimentocontas_id_seq RESTART WITH 1;")
            cursor.execute("ALTER SEQUENCE financeiro_parcelacontas_id_seq RESTART WITH 1;")

        self.stdout.write(self.style.SUCCESS('Banco de dados e contadores resetados com sucesso!'))
        self.stdout.write(self.style.WARNING('Iniciando a geração de registros balanceados (Receitas e Despesas)...'))

        # 1. Categorias do Prompt do seu Agente 1
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

        # Entities Reais
        fornecedores_reais = [
            {"nome": "RIVEMA MAQUINAS E EQUIPAMENTOS LTDA", "fantasia": "RIVEMA"},
            {"nome": "COMBUSTIVEIS RIO VERDE LTDA", "fantasia": "POSTO RIO VERDE"},
            {"nome": "DISTRIBUIDORA DE SEMENTES CERRADO LTDA", "fantasia": "SEMENTES CERRADO"}
        ]

        clientes_reais = [
            {"nome": "COMIGO COOPERATIVA AGROINDUSTRIAL", "fantasia": "COMIGO"},
            {"nome": "CARGILL ALIMENTOS SA", "fantasia": "CARGILL"},
            {"nome": "LOUIS DREYFUS COMPANY BRASIL", "fantasia": "LDC"}
        ]

        faturados_reais = [
            {"nome": "OLLYVER OTTOBONI", "cpf_cnpj": "001.234.567-89"},
            {"nome": "ANTONIO BORGES", "cpf_cnpj": "002.987.654-32"},
            {"nome": "YAGO LEMES MANAGEMENT", "cpf_cnpj": "45.123.896/0001-12"}
        ]

        # Cadastrar Fornecedores gerando CNPJ exclusivo incremental para evitar travas unique
        obj_fornecedores = []
        for idx_f, f in enumerate(fornecedores_reais):
            cnpj_forn = f"00.000.000/0001-{idx_f:02d}"
            obj, _ = Pessoa.objects.get_or_create(
                nome_razao_social=f["nome"],
                defaults={"fantasia": f["fantasia"], "cnpj_cpf": cnpj_forn, "tipo": "FORNECEDOR", "status_ativo": True}
            )
            obj_fornecedores.append(obj)

        # Cadastrar Clientes gerando CNPJ exclusivo incremental
        obj_clientes = []
        for idx_c, c in enumerate(clientes_reais):
            cnpj_clie = f"11.111.111/0001-{idx_c:02d}"
            obj, _ = Pessoa.objects.get_or_create(
                nome_razao_social=c["nome"],
                defaults={"fantasia": c["fantasia"], "cnpj_cpf": cnpj_clie, "tipo": "CLIENTE", "status_ativo": True}
            )
            obj_clientes.append(obj)

        # Cadastrar Faturados
        obj_faturados = []
        for fat in faturados_reais:
            obj, _ = Pessoa.objects.get_or_create(
                nome_razao_social=fat["nome"],
                defaults={"fantasia": fat["nome"].split()[0], "cnpj_cpf": fat["cpf_cnpj"], "tipo": "FATURADO", "status_ativo": True}
            )
            obj_faturados.append(obj)

        data_base = date(2026, 1, 1)
        
        # 3. Gerar os 200 registros de forma balanceada
        for idx in range(200):
            # Sorteia se este registro será Receita ou Despesa (50% de chance para cada)
            tipo_movimento = random.choice(["A PAGAR", "A RECEBER"])
            
            # Filtra as classificações condizentes com o tipo sorteado
            classif_filtradas = [c for c in obj_classificacoes if c["tipo"] == ("RECEITA" if tipo_movimento == "A RECEBER" else "DESPESA")]
            classif_escolhida = random.choice(classif_filtradas)
            produto_sorteado = random.choice(classif_escolhida["produtos"])
            
            faturado = random.choice(obj_faturados)
            
            if tipo_movimento == "A PAGAR":
                parceiro = random.choice(obj_fornecedores)
                texto_desc = f"Compra de {produto_sorteado} para uso na unidade produtora. Faturado para {faturado.nome_razao_social}."
            else:
                parceiro = random.choice(obj_clientes)
                texto_desc = f"Venda de {produto_sorteado} produzido na fazenda. Recebido de {parceiro.nome_razao_social} faturado em {faturado.nome_razao_social}."

            num_nota = f"000.{random.randint(100,999)}.{idx+1:03d}"
            dt_emissao = data_base + timedelta(days=random.randint(0, 120))
            val_total = round(random.uniform(3500.00, 120000.00), 2)

            movimento = MovimentoContas.objects.create(
                tipo=tipo_movimento,
                numero_nota=num_nota,
                data_emissao=dt_emissao,
                valor_total=val_total,
                descricao_produtos=texto_desc,
                pessoa=parceiro
            )
            movimento.classificacoes.add(classif_escolhida["obj"])

            # Parcela
            identificador = f"ID-NF-{num_nota}-P1-{get_random_string(4).upper()}"
            ParcelaContas.objects.create(
                movimento=movimento,
                identificacao_unica=identificador,
                numero_parcela=1,
                valor_parcela=val_total,
                data_vencimento=dt_emissao + timedelta(days=30),
                situacao=random.choice(["ABERTO", "QUITADO"])
            )

        self.stdout.write(self.style.SUCCESS('Sucesso! 200 movimentos (Receitas e Despesas) gerados com perfeito equilíbrio para o RAG.'))