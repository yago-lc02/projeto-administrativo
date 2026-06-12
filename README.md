# CashFlow - Sistema de Gestão Financeira com IA Administrativa 🚀

Este projeto consiste em uma plataforma inteligente para controle de movimentações financeiras corporativas (A Pagar e A Receber), desenvolvido como parte dos requisitos práticos de Engenharia de Software.

O sistema conta com regras rígidas de consistência de parcelamentos, auditoria automatizada e um pipeline de **Inteligência Artificial Híbrida via RAG** (Retrieval-Augmented Generation) integrado à API do Google Gemini.

---

## 🛠️ Tecnologias Utilizadas

* **Back-end:** Django 5.0 + Django REST Framework (DRF)
* **Banco de Dados:** PostgreSQL (Ambiente Conteinerizado)
* **Arquitetura de Dados:** NumPy (Processamento e similaridade vetorial matemática)
* **Inteligência Artificial:** SDK Google GenAI (`gemini-2.5-flash` e `text-embedding-004`)
* **Front-end:** HTML5, CSS3, Bootstrap 5 e JavaScript Assíncrono (Fetch API)
* **Infraestrutura:** Docker e Docker Compose

---

## ⚙️ Funcionalidades Principais (Etapa 4 - Concluída)

1. **Painel de Lançamentos:** Listagem reativa com filtros dinâmicos e simultâneos por descrição, tipo e parceiro.
2. **CRUD Completo de Parceiros (Pessoas):** Interface gráfica dedicada para cadastrar, listar, editar e inativar Fornecedores, Clientes e Faturados.
3. **CRUD Completo de Categorias (Classificações):** Módulo dinâmico na interface para gerenciar classificações de Receitas e Despesas.
4. **Geração de Parcelas:** Algoritmo dinâmico que divide valores totais respeitando intervalos de 30 dias e garantindo a paridade da primeira parcela de consistência.
5. **Alteração Segura:** Edição completa de metadados com recálculo automático do cronograma financeiro associado.
6. **Exclusão Lógica Unificada:** Inativação de registros (`status_ativo=False`) em cascata, mantendo a integridade histórica dos dados no banco para fins de auditoria.
7. **Auditor Sênior (Chat RAG):** Chat alimentado por IA capaz de ler e interpretar o banco de dados dinamicamente usando buscas por metadados textuais ou proximidade semântica avançada por embeddings.

---

## 🐳 Como Rodar o Projeto Completamente

Certifique-se de ter o **Docker** e o **Docker Compose** instalados na sua máquina.

### 1. Clonar o Repositório
```bash
git clone [https://github.com/yago-lc02/projeto-administrativo.git](https://github.com/yago-lc02/projeto-administrativo.git)
cd projeto-administrativo
