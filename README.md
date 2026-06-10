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

## ⚙️ Funcionalidades Principais (Etapa 4)

1. **Painel de Lançamentos:** Listagem reativa com filtros dinâmicos por Tipo de Movimentação.
2. **Geração de Parcelas:** Algoritmo dinâmico que divide valores totais respeitando intervalos de 30 dias e garantindo a paridade da primeira parcela de consistência.
3. **Alteração Segura:** Edição completa de metadados com recálculo automático do cronograma financeiro associado.
4. **Exclusão Lógica:** Inativação de registros (`status_ativo=False`) mantendo a integridade histórica dos dados no banco, conforme requisitos de auditoria.
5. **Auditor Sênior (Chat RAG):** Chat alimentado por IA capaz de ler e interpretar o banco de dados dinamicamente usando buscas por metadados textuais ou proximidade semântica por embeddings.

---

## 🐳 Como Rodar o Projeto Completamente

Certifique-se de ter o **Docker** e o **Docker Compose** instalados na sua máquina.

### 1. Clonar o Repositório
```bash
git clone [https://github.com/yago-lc02/projeto-administrativo.git](https://github.com/yago-lc02/projeto-administrativo.git)
cd projeto-administrativo