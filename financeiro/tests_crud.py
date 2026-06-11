from django.test import TestCase, Client
from django.urls import reverse
from .models import Pessoa, Classificacao


class PessoaCRUDTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.pessoa_ativa = Pessoa.objects.create(
            nome_razao_social="Fornecedor Teste S/A",
            fantasia="Fornecedor Teste",
            cnpj_cpf="12.345.678/0001-99",
            tipo="FORNECEDOR",
            status_ativo=True
        )
        self.pessoa_inativa = Pessoa.objects.create(
            nome_razao_social="Cliente Inativo LTDA",
            fantasia="Cliente Inativo",
            cnpj_cpf="98.765.432/0001-11",
            tipo="FATURADO",
            status_ativo=False
        )

    def test_listar_pessoas_vazio_por_padrao(self):
        """A listagem deve nascer vazia se nenhum filtro ou todos for passado"""
        response = self.client.get(reverse('listar_pessoas'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['pessoas'])

    def test_listar_pessoas_com_parametro_todos(self):
        """Deve listar todos os registros ativos ao passar todos=true"""
        response = self.client.get(reverse('listar_pessoas') + '?todos=true')
        self.assertEqual(response.status_code, 200)
        pessoas = response.context['pessoas']
        self.assertIn(self.pessoa_ativa, pessoas)
        self.assertNotIn(self.pessoa_inativa, pessoas)

    def test_incluir_pessoa_sucesso(self):
        """Deve incluir um novo parceiro com sucesso"""
        data = {
            'nome_razao_social': 'Novo Cliente Fantástico',
            'fantasia': 'Novo Cliente',
            'cnpj_cpf': '11.111.111/1111-11',
            'tipo': 'FATURADO'
        }
        response = self.client.post(reverse('incluir_pessoa'), data)
        self.assertEqual(response.status_code, 302)  # Redirecionamento
        # Verifica se foi persistido
        pessoa = Pessoa.objects.filter(cnpj_cpf='11.111.111/1111-11').first()
        self.assertIsNotNone(pessoa)
        self.assertTrue(pessoa.status_ativo)

    def test_incluir_pessoa_cnpj_duplicado_ativo(self):
        """Deve recusar a inclusão se o CNPJ/CPF já estiver cadastrado e ativo"""
        data = {
            'nome_razao_social': 'Outro Fornecedor',
            'cnpj_cpf': '12.345.678/0001-99',  # Mesmo CNPJ do fornecedor ativo
            'tipo': 'FORNECEDOR'
        }
        response = self.client.post(reverse('incluir_pessoa'), data)
        self.assertEqual(response.status_code, 200)  # Renderiza de novo com erro
        self.assertContains(response, 'Este CNPJ / CPF já está cadastrado no sistema.')

    def test_incluir_pessoa_cnpj_duplicado_inativo_reativacao(self):
        """Deve reativar e atualizar o parceiro se o CNPJ/CPF pertencer a um inativo"""
        data = {
            'nome_razao_social': 'Cliente Reativado com Novo Nome',
            'fantasia': 'Cliente Reativado',
            'cnpj_cpf': '98.765.432/0001-11',  # Mesmo CNPJ do inativo
            'tipo': 'FATURADO'
        }
        response = self.client.post(reverse('incluir_pessoa'), data)
        self.assertEqual(response.status_code, 302)
        
        self.pessoa_inativa.refresh_from_db()
        self.assertTrue(self.pessoa_inativa.status_ativo)
        self.assertEqual(self.pessoa_inativa.nome_razao_social, 'Cliente Reativado com Novo Nome')

    def test_alterar_pessoa_sucesso(self):
        """Deve alterar dados de um parceiro existente"""
        data = {
            'nome_razao_social': 'Fornecedor Teste Modificado',
            'fantasia': 'Fantasia Modificada',
            'cnpj_cpf': '12.345.678/0001-99',
            'tipo': 'FORNECEDOR'
        }
        response = self.client.post(reverse('alterar_pessoa', args=[self.pessoa_ativa.id]), data)
        self.assertEqual(response.status_code, 302)
        self.pessoa_ativa.refresh_from_db()
        self.assertEqual(self.pessoa_ativa.nome_razao_social, 'Fornecedor Teste Modificado')

    def test_excluir_pessoa_logico(self):
        """A exclusão deve ser lógica (inativação)"""
        response = self.client.post(reverse('excluir_pessoa', args=[self.pessoa_ativa.id]))
        self.assertEqual(response.status_code, 302)
        self.pessoa_ativa.refresh_from_db()
        self.assertFalse(self.pessoa_ativa.status_ativo)


class ClassificacaoCRUDTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.class_ativa = Classificacao.objects.create(
            descricao="Energia Elétrica",
            categoria="Custos Fixos",
            tipo="DESPESA",
            status_ativo=True
        )
        self.class_inativa = Classificacao.objects.create(
            descricao="Vendas de Soja Antigas",
            categoria="Receitas Operacionais",
            tipo="RECEITA",
            status_ativo=False
        )

    def test_listar_classificacoes_vazio_por_padrao(self):
        """A listagem de classificações deve nascer vazia"""
        response = self.client.get(reverse('listar_classificacoes'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['classificacoes'])

    def test_listar_classificacoes_com_parametro_todos(self):
        """Deve listar todas as classificações ativas com todos=true"""
        response = self.client.get(reverse('listar_classificacoes') + '?todos=true')
        self.assertEqual(response.status_code, 200)
        classificacoes = response.context['classificacoes']
        self.assertIn(self.class_ativa, classificacoes)
        self.assertNotIn(self.class_inativa, classificacoes)

    def test_incluir_classificacao_sucesso(self):
        """Deve cadastrar uma classificação com sucesso"""
        data = {
            'descricao': 'Fertilizantes NPK',
            'categoria': 'Produção Rural',
            'tipo': 'DESPESA'
        }
        response = self.client.post(reverse('incluir_classificacao'), data)
        self.assertEqual(response.status_code, 302)
        c = Classificacao.objects.filter(descricao='Fertilizantes NPK').first()
        self.assertIsNotNone(c)
        self.assertTrue(c.status_ativo)

    def test_alterar_classificacao_sucesso(self):
        """Deve alterar dados de uma classificação"""
        data = {
            'descricao': 'Energia Rural Elétrica',
            'categoria': 'Custos Operacionais',
            'tipo': 'DESPESA'
        }
        response = self.client.post(reverse('alterar_classificacao', args=[self.class_ativa.id]), data)
        self.assertEqual(response.status_code, 302)
        self.class_ativa.refresh_from_db()
        self.assertEqual(self.class_ativa.descricao, 'Energia Rural Elétrica')

    def test_excluir_classificacao_logico(self):
        """A exclusão de classificação deve ser lógica"""
        response = self.client.post(reverse('excluir_classificacao', args=[self.class_ativa.id]))
        self.assertEqual(response.status_code, 302)
        self.class_ativa.refresh_from_db()
        self.assertFalse(self.class_ativa.status_ativo)
