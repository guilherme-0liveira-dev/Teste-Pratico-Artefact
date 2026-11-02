# Empório AI — Assistente de Atendimento Inteligente & Customer Service Agent

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](docs/DOCKER_GUIDE.md)
[![Framework](https://img.shields.io/badge/Streamlit-1.66.1-red.svg)](https://streamlit.io/)
[![ORM](https://img.shields.io/badge/SQLAlchemy-2.0-orange.svg)](https://www.sqlalchemy.org/)
[![Validation](https://img.shields.io/badge/Pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![Linting](https://img.shields.io/badge/Ruff-Passed-brightgreen.svg)](https://astral.sh/ruff)
[![Tests](https://img.shields.io/badge/Tests-57%20Passed-success.svg)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

> **Idiomas / Languages:**  
> 🇧🇷 **[Versão em Português (pt-BR)](#-versão-em-português-pt-br)** | 🇬🇧 **[English Version (EN)](#-english-version-en)**

---

# 🇧🇷 Versão em Português (pt-BR)

Agente de atendimento conversacional com inteligência artificial, nível sênior, reprodutível e conteinerizado, desenvolvido para a **Empório da Música**, tradicional loja varejista de instrumentos musicais situada em Campo Grande / MS.

Desenvolvido para o **Desafio Técnico de AI Engineer da Artefact**, o sistema implementa uma arquitetura em camadas combinando motor de regras de negócio determinístico (zero alucinação financeira), recuperação lexical de políticas via BM25 com citação de páginas, execução estruturada de ferramentas com Pydantic v2 e suporte resiliente a múltiplos provedores de LLM (NVIDIA NIM Cloud gratuito, Ollama 100% privado local ou Mock determinístico offline).

---

## 1. Visão Geral do Cenário & Objetivos do Desafio

### Cenário
A Empório da Música atua no mercado de instrumentos há mais de 15 anos. Sua equipe de atendimento estava sobrecarregada com dúvidas repetitivas sobre horários de funcionamento, estoque de violões e instrumentos, preços em tempo real, prazos de entrega em Campo Grande e no Brasil, cálculo de parcelas/desconto PIX e regras de troca/garantia.

### Missão & Entregáveis Principais
- **Persona Humanizada & Alinhada à Marca:** Comunicação natural em Português do Brasil (pt-BR), tom acolhedor, conhecedor de música e respeitoso (*"Empório da Música — Sua música começa aqui."*).
- **Dados Operacionais Confiáveis:** Consulta direta a tabelas relacionais SQLite (produtos, estoque, pedidos, promoções ativas), sem invenção de produtos.
- **Recuperação Fiel de Políticas (RAG BM25):** Extração e citação de fatos do manual oficial da loja (`docs/políticas_da_loja.pdf`) com identificação da seção e número da página.
- **Cálculos Financeiros Determinísticos:** Cálculos de desconto PIX (5%), faixas de parcelamento sem juros em até 12x, regras de frete e prazos do CDC realizados puramente em Python com `Decimal`, prevenindo erros de arredondamento e alucinações matemáticas da LLM.
- **Tratamento de Perguntas Fora de Escopo:** Recusa polida para acessórios avulsos (cordas, palhetas, cabos, amplificadores) ou serviços externos (aulas, reformas de luthieria), fornecendo lista estruturada do que PODE ser feito na loja e contato humano no WhatsApp.
- **Resiliência e Tolerância a Falhas:** Loop de retentativas com backoff exponencial e jitter para contornar instabilidades transitórias de cold start em nuvem (`HTTP 404/503`) e sintetizador de fallback automático.

---

## 2. Arquitetura do Sistema & Fluxo de Dados

```mermaid
graph TD
    User([Cliente / Usuário]) <--> Streamlit[Camada de Apresentação: Streamlit UI Glassy V5]
    
    subgraph ApplicationLayer ["Camada de Aplicação"]
        Streamlit <--> Orchestrator[Orquestrador do Agente (ReAct Loop)]
        Orchestrator <--> Prompts[System Prompt & Diretrizes da Marca]
        Orchestrator <--> LLM[Interface BaseLLMProvider]
        Orchestrator <--> ToolDispatcher[Registro de Ferramentas & Schemas Pydantic v2]
    end

    subgraph LLMProviders ["Provedores de LLM Resilientes"]
        LLM -.-> Nvidia[NVIDIA NIM Cloud Free<br/>nvidia/nemotron-3.5-bolt-e4b (Oficial)<br/>Fallback: llama-3.1-nemotron-70b]
        LLM -.-> Ollama[Ollama Local Privado<br/>qwen2.5-coder:7b / llama3.2]
        LLM -.-> Mock[MockLLMProvider<br/>Fallback Determinístico Offline]
    end

    subgraph DomainLayer ["Camada de Domínio (Python Puro Determinístico)"]
        ToolDispatcher --> CatalogService[Serviço de Catálogo]
        ToolDispatcher --> OrderService[Serviço de Rastreio de Pedidos]
        ToolDispatcher --> RulesEngine[Motor de Regras de Negócio<br/>PIX 5% | Parcelamento 12x | Trocas CDC | Frete]
        ToolDispatcher --> PolicySearch[Serviço de Busca de Políticas<br/>BM25 Okapi]
    end

    subgraph InfrastructureLayer ["Camada de Infraestrutura & Armazenamento"]
        CatalogService --> SQLite[(SQLite: emporio.db)]
        OrderService --> SQLite
        RulesEngine -.-> SQLite
        PolicySearch --> PolicyChunks[(Chunks Indexados do PDF de Políticas)]
        
        CSVLoader[Pipeline de Ingestão de CSVs<br/>Pandas + Parser Decimal] --> SQLite
        PDFLoader[Extrator do Manual em PDF<br/>PyMuPDF + Chunking Semântico] --> SQLite
        PDFLoader --> PolicyChunks
    end
```

### Divisão em Camadas
1. **Camada de Apresentação (`app/main.py`):** Interface Streamlit com **Sidebar Glassy V5** (vidro líquido translúcido com iluminação ambiente), chips de sugestão rápida persistentes, histórico de mensagens, botões de recolher/expandir estilizados, **Painel de Diagnóstico Técnico** em tempo real e botão de **Limpar Cache**.
2. **Camada de Aplicação (`app/agent/`):** Orquestra o raciocínio multi-turnos, circuit breaker com limite estrito de 5 iterações (prevenção de loop infinito), validação rigorosa de ferramentas via Pydantic v2 e sanitização pós-processamento de moeda (`R$ `) e IDs de banco.
3. **Camada de Domínio (`app/services/`):** Lógica pura de negócio em Python sem dependências externas de rede ou LLM.
4. **Camada de Infraestrutura (`app/db/`, `app/ingestion/`, `app/retrieval/`, `app/llm/`):** Persistência relacional SQLite com integridade referencial ativa (`PRAGMA foreign_keys = ON`), extração PyMuPDF, indexação lexical Rank-BM25 e adaptadores de LLM intercambiáveis.

---

## 3. Decisões Técnicas & Justificativas de Engenharia

| Tecnologia | Escolha | Justificativa de Engenharia |
|:---|:---|:---|
| **Linguagem** | Python 3.11+ (Validado em 3.12 e 3.14) | Exigência do edital. Alta legibilidade, ecossistema maduro para IA generativa e tipagem estática moderna. |
| **Interface** | Streamlit + Design Glassmorphism V5 | Prototipação ágil de chat com session state nativo, tokens CSS da paleta Adobe (`#121212`, `#FFFFFF`, `#BCBCBC`, `#D6FF00`) e métricas de latência. |
| **Banco de Dados** | SQLite + SQLAlchemy 2.0 | Zero dependência de servidores externos pesados, conformidade ACID embutida, integridade referencial ativa e mapeamento ORM seguro. |
| **Validação de Schemas** | Pydantic v2 | Validação de alta performance dos argumentos das ferramentas do agente e geração automática de JSON schema para function calling. |
| **Ingestão de Dados** | Pandas + `Decimal` nativo | Normalização de moedas em formato brasileiro (`R$ 1.299,00` → `Decimal('1299.00')`) e tratamento idempotente de datas ISO/BR. |
| **Extração de PDF** | PyMuPDF (`pymupdf`) | Extração estruturada de alta fidelidade do manual oficial, preservando títulos, seções e números de página. |
| **Busca de Políticas** | Rank-BM25 (`rank-bm25`) | Recuperação lexical ultrarrápida. Como o manual é curto (8 páginas) e envolve termos jurídicos precisos, o BM25 elimina custo de embeddings e drift vetorial. |
| **Provedores de LLM** | NVIDIA NIM / Ollama / Mock | Abstração agnóstica (`BaseLLMProvider`). **Modelo Oficial:** `nvidia/nemotron-3.5-bolt-e4b` (alta precisão e raciocínio para function calling). Suporta fallback resiliente automático para `nvidia/llama-3.1-nemotron-70b-instruct` / `meta/llama-3.3-70b-instruct`, execução local via Ollama (`qwen2.5-coder:7b`) e Mock offline para CI/CD. |
| **Tolerância a Falhas** | Backoff Exponencial + Jitter | Absorve automaticamente instabilidades de cold start (`HTTP 404/503`) de modelos em nuvem sem interromper a conversa do usuário. |
| **Qualidade de Código** | Ruff + Pytest | Linting ultrarrápido (sub-segundo) e 57 testes automatizados cobrindo 100% das regras críticas de negócio sem chamadas de rede. |

---

## 4. Motor de Regras de Negócio Determinístico

A regra número um da arquitetura do Empório AI é: **a LLM nunca calcula valores monetários, parcelas ou regras legais de cabeça**. Todo cálculo é realizado por funções puras em [`app/services/business_rules.py`](app/services/business_rules.py):

1. **Desconto no PIX (5%):**
   - Aplica 5% de desconto à vista sobre o preço de tabela regular (`preço * 0,95`).
   - **Não Cumulatividade Estrita:** Proibição de acúmulo de desconto de 5% sobre instrumentos que já estejam em promoção ativa.
2. **Parcelamento sem Juros no Cartão de Crédito (até 12x):**
   - **1x a 3x:** Sem valor mínimo de parcela (exceto total da compra inferior a R$ 50,00).
   - **4x a 6x:** Parcela mínima obrigatória de **R$ 80,00**.
   - **7x a 12x:** Parcela mínima obrigatória de **R$ 100,00**.
3. **Direito de Arrependimento (CDC Art. 49):**
   - Limite estrito de **7 dias corridos** após o recebimento, exclusivo para **compras online**. Frete coberto pela loja e reembolso 100% integral.
   - Compras em loja física **não possuem direito legal a arrependimento**.
4. **Troca por Defeito:**
   - Até **30 dias corridos** diretamente no balcão da loja física. Após 30 dias, direciona para a garantia do fabricante (garantia legal de 90 dias + garantia contratual de fábrica).
5. **Frete e Prazos de Entrega:**
   - **Grande Campo Grande:** Frete Grátis para compras ≥ R$ 500,00 (1 a 3 dias úteis por motoboy próprio); taxa fixa de **R$ 35,00** para pedidos < R$ 500,00.
   - **Demais Cidades:** Envio via Correios (PAC/SEDEX) ou Jadlog cotado por CEP e peso no checkout.

---

## 5. Matriz de Verificação das Políticas da Loja

Todas as regras do manual oficial [`docs/políticas_da_loja.pdf`](docs/políticas_da_loja.pdf) foram mapeadas, implementadas e testadas:

| Área da Política | Fonte no Manual | Implementação no Sistema | Testes Automatizados |
|:---|:---|:---|:---|
| **Endereço e Contatos** | Seção 1.2 (Página 2) | Loja física: Rua 14 de Maio, 3200 — Campo Grande/MS. WhatsApp: (67) 3341-4444. | `test_retrieve_address_and_company_info` |
| **Horário de Atendimento** | Seção 2 (Página 2) | Seg–Sex: 09h às 18h; Sáb: 09h às 13h; Dom/Feriados: Fechado. | `test_retrieve_operating_hours` |
| **Pagamentos & PIX** | Seções 3 e 3.1 (Pág. 3) | 5% off à vista regular; regras de parcela mínima por faixa. | `test_pix_discount_*`, `test_installments_*` |
| **Arrependimento (CDC)** | Seção 4.1 (Página 4) | 7 dias corridos para compras online. Reembolso total e frete da loja. | `test_return_withdrawal_*` |
| **Troca por Defeito** | Seção 4.2 (Página 4) | Até 30 dias na loja; acima de 30 dias aciona garantia do fabricante. | `test_return_defect_*` |
| **Itens Não Elegíveis** | Seção 4.4 (Página 4) | Itens com mau uso, embalagem violada, gaitas/sopros (higiene pessoal). | `test_retrieve_ineligible_items_*` |
| **Regras de Frete** | Seção 5.1 (Página 4) | Frete grátis ≥ R$ 500 em Campo Grande; taxa fixa de R$ 35 abaixo de R$ 500. | `test_shipping_local_*` |
| **Escopo e Exclusões** | Seção 7.3 (Página 7) | Vende APENAS instrumentos. Recusa amigável de acessórios e serviços. | `test_out_of_scope_*` |
| **Garantia Legal e Fábrica**| Seções 8.1–8.3 (Pág. 7)| 90 dias legais pelo CDC + garantia contratual de fábrica. | `test_retrieve_legal_and_manufacturer_*`|

---

## 6. Instalação e Execução

### Opção 1: 🐳 Via Docker (Recomendada — Zero Configuração)

A aplicação completa com banco de dados SQLite e inicialização automática roda em um único comando:

```bash
# 1. Clonar o repositório
git clone https://github.com/guilherme-0liveira-dev/Teste-Pratico-Artefact.git
cd Teste-Pratico-Artefact

# 2. Configurar variáveis no .env (ou usar o modo mock offline padrão)
cp .env.example .env

# 3. Construir e subir o container
docker compose up --build
```

Acesse **`http://localhost:8501`** no seu navegador. O container detecta a ausência do banco e executa a ingestão automaticamente!

*Para instruções detalhadas de Docker e perfil Ollama local, consulte [`docs/DOCKER_GUIDE.md`](docs/DOCKER_GUIDE.md).*

---

### Opção 2: 🐍 Ambiente Virtual Python Local

#### Pré-requisitos
- Python 3.11, 3.12 ou superior
- Git

```powershell
# 1. Clonar o repositório
git clone https://github.com/guilherme-0liveira-dev/Teste-Pratico-Artefact.git
cd Teste-Pratico-Artefact

# 2. Criar e ativar o ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate    # Linux / macOS

# 3. Atualizar o pip e instalar dependências
python -m pip install --upgrade pip
pip install -e .
pip install -e .[dev]

# 4. Executar a ingestão inicial do banco de dados
python scripts/ingest.py

# 5. Iniciar a interface Streamlit
streamlit run app/main.py
```

---

### Opção 3: ⚡ Via UV (Gerenciador Ultrarrápido)

```bash
uv venv
source .venv/bin/activate  # ou .\.venv\Scripts\Activate.ps1 no Windows
uv pip install -e .[dev]

uv run python scripts/ingest.py
uv run streamlit run app/main.py
```

---

## 7. Configuração de Variáveis de Ambiente (`.env`)

Crie seu arquivo `.env` a partir do modelo fornecido:
```bash
cp .env.example .env
```

| Variável | Valor Padrão | Descrição |
|:---|:---|:---|
| `LLM_PROVIDER` | `nvidia` | Provedor ativo (`nvidia`, `ollama` ou `mock`). |
| `LLM_API_KEY` | `""` | Chave de API da NVIDIA NIM (gratuita em [build.nvidia.com](https://build.nvidia.com)). |
| `LLM_BASE_URL` | `https://integrate.api.nvidia.com/v1` | Endpoint compatível com a API da OpenAI. |
| `LLM_MODEL` | `nvidia/nemotron-3.5-bolt-e4b` | Modelo oficial utilizado (otimizado para function calling com fallback resiliente para `llama-3.1-nemotron-70b`). |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434/v1` | Endpoint do Ollama local. |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Modelo local para execução via Ollama. |
| `DATABASE_URL` | `sqlite:///data/emporio.db` | URI de conexão do banco de dados SQLite. |
| `LOG_LEVEL` | `INFO` | Nível de detalhamento dos logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `AGENT_MAX_ITERATIONS`| `5` | Limite de iterações do ReAct loop por mensagem. |

---

## 8. Testes Automatizados & Qualidade de Código

A suíte de testes cobre regras de negócio, integridade relacional, ferramentas e orquestrador com **zero chamadas externas de rede**:

```powershell
# Executar a suíte completa de 57 testes
python -m pytest tests/ -v

# Executar testes com relatório de cobertura de código
python -m pytest tests/ --cov=app --cov-report=term-missing

# Verificação de estilo e linting com Ruff
python -m ruff check .
python -m ruff format --check .
```

### Distribuição dos 57 Testes Automatizados:
- `tests/test_business_rules.py` (16 testes): Desconto PIX, regras de parcelamento de fronteira (R$ 79,99 vs R$ 80,00), devoluções CDC e frete.
- `tests/test_ingestion.py` (5 testes): Ingestão idempotente de CSVs, parser de moeda `Decimal`, datas ISO/BR e integridade referencial.
- `tests/test_tools.py` (10 testes): Filtros de catálogo, busca de estoque, rastreio de pedidos, promoções e busca BM25.
- `tests/test_orchestrator.py` (6 testes): Loop ReAct com MockLLM, circuit breaker de 5 iterações, guardrails regex de moeda (`R$ `) e tolerância a erros.
- `tests/test_orders_exhaustive.py` (5 testes): Status de entrega, notas de cancelamento e validação de privacidade do cliente.
- `tests/test_policy_retrieval_exhaustive.py` (8 testes): Recuperação de fatos institucionais do manual oficial via BM25.
- `tests/test_out_of_scope_fallback.py` (2 testes): Protocolo de 4 partes para recusa de acessórios e serviços fora de escopo.
- **Resultado:** **57 testes aprovados com 100% de sucesso** em ~6 segundos.

---

## 9. Segurança, Privacidade & LGPD

- **Privacidade LGPD:** A ferramenta `get_order_status` valida a identidade do cliente antes de divulgar dados sensíveis de pedidos e endereços.
- **Prevenção de SQL Injection:** 100% das consultas ao banco utilizam o ORM SQLAlchemy com parâmetros vinculados (sem interpolação de strings SQL).
- **Defesa Contra Prompt Injection:** O texto das políticas recuperadas e os dados do banco são tratados estritamente como payloads de dados passivos nas ferramentas.
- **Sanitização de Logs:** Mascaramento automático de dados de CPF e tokens de API em stdout e arquivos de log.
- **Hardening do Container:** Execução como usuário não-root (`appuser:appgroup` UID 10001), healthcheck integrado e limites de memória/CPU.

---

## 10. Exemplos de Interação com o Agente

Documentação detalhada com **5 transcrições completas de conversas reais** está disponível em [`examples/conversation_examples.md`](examples/conversation_examples.md):
1. **Cenário 1:** Consulta ao catálogo de violões até R$ 1.000 com estoque ativo e cálculo de parcelamento.
2. **Cenário 2:** Informações institucionais, endereço físico e horários de atendimento da loja.
3. **Cenário 3:** Consulta de preço e disponibilidade de modelo específico (Takamine GD20).
4. **Cenário 4:** Solicitação de devolução por arrependimento com aplicação do Art. 49 do CDC para compra online.
5. **Cenário 5:** Pergunta fora de escopo (venda de palhetas e cordas avulsas) acionando o protocolo obrigatório de recusa educada e encaminhamento ao WhatsApp humano.

---

## 11. Estrutura de Arquivos do Repositório

```text
emporio-ai/
├── app/
│   ├── agent/                 # Orquestração do agente, prompts e ferramentas
│   │   ├── orchestrator.py    # Loop ReAct de raciocínio, tolerância a falhas e guardrails
│   │   ├── prompts.py         # Persona, restrições de escopo e diretrizes de formatação
│   │   └── tools.py           # Schemas Pydantic v2 e executores de ferramentas
│   ├── core/                  # Configurações globais e logger sanitizado
│   │   ├── config.py
│   │   └── logging.py
│   ├── db/                    # Modelos ORM SQLAlchemy e conexão com SQLite
│   │   ├── connection.py
│   │   └── models.py
│   ├── ingestion/             # Ingestores de dados relacionais e do PDF de políticas
│   │   ├── csv_loader.py
│   │   └── pdf_loader.py
│   ├── llm/                   # Adaptadores de LLM (NVIDIA NIM / Ollama / Mock)
│   │   └── provider.py
│   ├── retrieval/             # Recuperação lexical BM25 das políticas da loja
│   │   └── policy_search.py
│   ├── services/              # Lógica de negócio em Python puro (Regras, Catálogo, Pedidos)
│   │   ├── business_rules.py  # Cálculos determinísticos de PIX, parcelas, devoluções e frete
│   │   ├── catalog.py         # Consultas de catálogo, estoque e campanhas promocionais
│   │   └── orders.py          # Rastreamento de pedidos e validação de privacidade
│   └── main.py                # Interface Streamlit Glassmorphism V5 com sidebar translúcida
├── data/                      # Armazenamento do banco de dados SQLite persistente
├── docs/                      # Documentação técnica e arquivos do edital
│   ├── AdobeColor-Meu tema de cores.jpeg # Paleta de cores oficial do projeto
│   ├── DESAFIO_CHECKLIST_TODO.md         # Mapeamento exaustivo de requisitos
│   ├── DOCKER_GUIDE.md                   # Guia avançado de conteinerização
│   ├── desafio_tecnico_ai_eng_artefact.pdf # Edital oficial do desafio
│   └── políticas_da_loja.pdf             # Manual interno da loja
├── examples/
│   └── conversation_examples.md          # 5 transcrições de conversas autênticas
├── scripts/
│   └── ingest.py              # Script CLI de ingestão e inicialização do banco
├── tests/                     # 57 testes automatizados unitários e de integração
├── .env.example               # Modelo de variáveis de ambiente
├── docker-compose.yml         # Especificação de orquestração Docker Compose
├── Dockerfile                 # Imagem multi-stage de produção
├── pyproject.toml             # Manifesto de dependências e empacotamento
└── README.md                  # Documentação principal bilíngue
```

---

## 12. Limitações Conhecidas e O Que Faria com Mais Tempo

Conforme solicitado no edital da Artefact, as seguintes melhorias representam o roadmap planejado para uma versão 2.0 em escala de produção contínua:

1. **Integração com APIs de Frete em Tempo Real (Melhor Envio / Correios):** Atualmente o frete para fora de Campo Grande é estimado pelas diretrizes gerais do manual. Uma integração direta com a API dos Correios ou Melhor Envio permitiria retornar valores e prazos exatos por CEP no próprio chat.
2. **Canal Multimodal de Áudio no WhatsApp (STT / TTS):** Incorporar modelos Whisper (Faster-Whisper) para transcrição de áudios de clientes e ElevenLabs / Edge-TTS para respostas em voz, permitindo atendimento via áudios no WhatsApp.
3. **RAG Híbrido Denso + Esparso (Embeddings + BM25):** Para expansão do catálogo a dezenas de milhares de itens e manuais técnicos complexos de luthieria, implementar Reciprocal Rank Fusion (RRF) combinando busca vetorial com BM25.
4. **Autoatendimento com Autenticação Transacional:** Permitir que clientes autenticados realizem alterações de endereço de entrega ou solicitem cancelamento de pedidos diretamente na conversa mediante validação por token SMS/WhatsApp.
5. **Painel Administrativo de Observabilidade & Analytics:** Dashboard com volume diário de conversas, instrumentos mais buscados, taxa de resolução por IA, índice de escalonamento humano e avaliação de satisfação (CSAT).

---

## 13. Declaração de Uso de Assistente de IA

Em total conformidade com as diretrizes do edital da Artefact:

- **Assistente Utilizado:** **Google Antigravity** (baseado em modelos DeepMind Gemini).
- **Fluxo de Trabalho e Papéis:**
  - **Planejamento e Arquitetura:** Mapeamento minucioso dos requisitos do edital (`desafio_tecnico_ai_eng_artefact.pdf`), estruturação da arquitetura modular e elaboração do checklist de entrega em `docs/DESAFIO_CHECKLIST_TODO.md`.
  - **Scaffolding e Implementação:** Aceleração na criação de modelos SQLAlchemy, schemas Pydantic v2 e estilização Glassmorphism V5 no Streamlit.
  - **Elaboração da Suíte de Testes:** Formulação de testes de casos de fronteira (ex.: parcelas em R$ 79,99 vs R$ 80,00, não-cumulatividade do PIX com promoções).
- **Revisão Humana e Verificação:**
  - Todas as regras e fórmulas foram conferidas manualmente linha por linha contra `políticas_da_loja.pdf`.
  - 100% dos 57 testes automatizados, checagens do Ruff e compilação do container Docker foram validados no ambiente de execução real.

---
---

# 🇬🇧 English Version (EN)

A production-grade, reproducible, containerized conversational AI customer service assistant engineered for **Empório da Música**, a retail musical instrument store located in Campo Grande / MS, Brazil.

Developed for the **Artefact AI Engineer Technical Challenge**, this system implements a clean, layered architecture combining a deterministic financial rules engine (zero financial hallucination), BM25 lexical policy retrieval with page-level citations, structured tool execution with Pydantic v2 schemas, and resilient multi-LLM support (cloud-free **NVIDIA NIM**, 100% private **Ollama**, or deterministic offline **Mock**).

---

## 1. Project Overview & Assessment Objectives

### Scenario
Empório da Música is a regional retail store with over 15 years in the market, operating in Campo Grande/MS. The customer service team was overburdened with repetitive inquiries regarding store opening hours, catalog availability, live pricing, delivery timelines, payment installment calculations, and return policies.

### Mission & Core Deliverables
- **Welcoming Persona & Brand Identity:** Communicates in natural Brazilian Portuguese (pt-BR) with a knowledgeable, friendly, and respectful tone (*"Empório da Música — Sua música começa aqui."*).
- **Verified Relational Data:** Retrieves operational data directly from structured relational storage (products, stock levels, orders, active promotions) with zero fabricated items.
- **Strict Policy Retrieval (RAG):** Extracts and cites facts from the official store policy manual (`docs/políticas_da_loja.pdf`) using page-level and section-level citations.
- **Deterministic Financial Calculations:** Employs pure, deterministic Python `Decimal` arithmetic for financial operations (5% PIX discount, tiered credit card installments, shipping thresholds, CDC return eligibility) rather than relying on hallucination-prone free-form LLM math.
- **Out-of-Scope Handling:** Gracefully explains that the store exclusively sells musical instruments, declining inquiries about accessories (cables, picks, strings, amps) or external services (classes, repairs) while providing actionable store suggestions and human escalation.
- **Fault-Tolerant Resilience:** Multi-attempt retry loop with exponential backoff and jitter to handle transient cloud cold starts (`HTTP 404/503`) and an automatic fallback synthesizer.

---

## 2. Architecture & Data Flow

```mermaid
graph TD
    User([Customer / User]) <--> Streamlit[Presentation Layer: Streamlit Glassy V5 UI]
    
    subgraph ApplicationLayer ["Application Layer"]
        Streamlit <--> Orchestrator[Agent Orchestrator (ReAct Loop)]
        Orchestrator <--> Prompts[System Prompt & Strict Brand Guardrails]
        Orchestrator <--> LLM[BaseLLMProvider Interface]
        Orchestrator <--> ToolDispatcher[Tool Registry & Pydantic v2 Schemas]
    end

    subgraph LLMProviders ["Resilient LLM Providers"]
        LLM -.-> Nvidia[NVIDIA NIM Cloud Free<br/>nvidia/nemotron-3.5-bolt-e4b (Official)<br/>Fallback: llama-3.1-nemotron-70b]
        LLM -.-> Ollama[Ollama Local Private<br/>qwen2.5-coder:7b / llama3.2]
        LLM -.-> Mock[MockLLMProvider<br/>Deterministic Offline Fallback]
    end

    subgraph DomainLayer ["Domain Layer (Pure Deterministic Python)"]
        ToolDispatcher --> CatalogService[Catalog Service]
        ToolDispatcher --> OrderService[Order Tracking Service]
        ToolDispatcher --> RulesEngine[Business Rules Engine<br/>PIX 5% | Installment Tiers | CDC Returns | Shipping]
        ToolDispatcher --> PolicySearch[Policy Search Service<br/>BM25 Okapi Retrieval]
    end

    subgraph InfrastructureLayer ["Infrastructure & Storage Layer"]
        CatalogService --> SQLite[(SQLite: emporio.db)]
        OrderService --> SQLite
        RulesEngine -.-> SQLite
        PolicySearch --> PolicyChunks[(Indexed PDF Policy Sections)]
        
        CSVLoader[CSV Ingestion Pipeline<br/>Pandas + Decimal Parsing] --> SQLite
        PDFLoader[PDF Text Extractor<br/>PyMuPDF + Structure Chunking] --> SQLite
        PDFLoader --> PolicyChunks
    end
```

### Architectural Layering
1. **Presentation Layer (`app/main.py`):** Interactive Streamlit interface featuring **Sidebar Glassy V5** (transparent liquid glass with ambient gradient lighting), quick suggestion chips, message history, collapse/expand toggle controls, a live **Developer Diagnostics Panel**, and a 1-click **Cache Cleaner**.
2. **Application Layer (`app/agent/`):** Orchestrates multi-turn conversation flow, enforces an anti-infinite-loop bounded tool execution limit (capped at 5 hops), validates tool inputs with Pydantic v2 schemas, sanitizes responses via post-processing regex guardrails, and renders KaTeX-safe Markdown.
3. **Domain Layer (`app/services/`):** Independent, pure Python business rules engine containing zero I/O or LLM dependencies. Computes exact Decimal prices, discount non-cumulativity, installment schedules, and return eligibility.
4. **Infrastructure Layer (`app/db/`, `app/ingestion/`, `app/retrieval/`, `app/llm/`):** SQLite relational persistence with foreign keys (`PRAGMA foreign_keys = ON`), PyMuPDF extraction, Rank-BM25 indexing, and swappable LLM adapters with backoff retries.

---

## 3. Technology Choices & Engineering Rationale

| Technology | Selection | Engineering Rationale |
|:---|:---|:---|
| **Language** | Python 3.11+ (Tested on 3.12 & 3.14) | Assessment requirement. High expressiveness, native async, and rich ecosystem for LLMs and data engineering. |
| **User Interface** | Streamlit + Custom Glassmorphism V5 | Rapid conversational UI with session state, custom CSS tokens (Adobe Palette: `#121212`, `#FFFFFF`, `#BCBCBC`, `#D6FF00`), and real-time latency diagnostics. |
| **Relational Storage** | SQLite + SQLAlchemy 2.0 | Zero external server dependency, embedded ACID compliance, strict foreign key enforcement (`PRAGMA foreign_keys=ON`), and type-safe ORM models. |
| **Schema Validation** | Pydantic v2 | High-performance argument validation for all agent tools; automatic generation of JSON schemas for LLM function calling. |
| **Data Ingestion** | Pandas + Python `Decimal` | Clean handling of tabular datasets, normalization of Brazilian currency strings (`R$ 1.299,00` → `Decimal('1299.00')`), and ISO datetime conversion. |
| **PDF Extraction** | PyMuPDF (`pymupdf`) | High-fidelity PDF parsing preserving layout hierarchy, titles, subsections, and exact page numbers. |
| **Policy Retrieval** | Rank-BM25 (`rank-bm25`) | Lightweight lexical retrieval. Store policies are concise (8 pages) and legal terms require exact keyword matching. Avoids vector database complexity, external embeddings cost, and vector drift. |
| **LLM Provider** | NVIDIA NIM / Ollama / Mock | Provider-agnostic abstraction (`BaseLLMProvider`). **Official Model:** `nvidia/nemotron-3.5-bolt-e4b` (optimized for high-precision reasoning and function calling). Includes resilient automatic fallback to `nvidia/llama-3.1-nemotron-70b-instruct` / `meta/llama-3.3-70b-instruct`, local Ollama execution (`qwen2.5-coder:7b`), and deterministic offline Mock. |
| **Resilience & Fault Tolerance** | Exponential Backoff + Jitter | Automatically handles transient cloud cold starts (`HTTP 404/503`) and API rate limits (`429`) with automatic fallback synthesis. |
| **Code Quality** | Ruff + Pytest | Sub-second linting, PEP 8 formatting, and 57 deterministic automated unit/integration tests with zero external API calls. |

---

## 4. Deterministic Business Rules Engine

A fundamental architectural principle of Empório AI is that **the LLM is never allowed to perform financial or policy arithmetic directly through free-form reasoning**. Instead, calculations are executed by deterministic Python functions in [`app/services/business_rules.py`](app/services/business_rules.py):

1. **PIX Discount (5%):**
   - Applies a 5% cash discount on regular catalog prices (`price * 0.95`).
   - **Strict Non-Cumulativity:** If a product is already subject to an active promotional campaign, the PIX discount is strictly disallowed or calculated solely from base price (preventing stacked discounts).
2. **Tiered Credit Card Installments (Sem Juros):**
   - **1x to 3x:** Interest-free, no minimum installment amount (except order total < R$ 50.00).
   - **4x to 6x:** Interest-free, strictly requires a minimum monthly installment of **R$ 80.00**.
   - **7x to 12x:** Interest-free, strictly requires a minimum monthly installment of **R$ 100.00**.
3. **Right of Withdrawal (CDC Art. 49):**
   - Strictly enforces **7 calendar days** after delivery for **online purchases**. The store pays return freight and provides a 100% full refund.
   - Presential physical store purchases have **no legal right to withdrawal by regret**.
4. **Defect-Related Exchanges:**
   - Up to **30 calendar days** directly with the physical store. Thereafter, refers customer to manufacturer warranty (90 days legal + factory warranty).
5. **Shipping & Freight (Campo Grande & Brazil):**
   - **Grande Campo Grande:** Free shipping for orders ≥ R$ 500.00 (1–3 business days via motoboy); fixed fee of **R$ 35.00** for orders < R$ 500.00.
   - **Other cities:** External shipping via Correios (PAC/SEDEX) or Jadlog, calculated by postal code at checkout.

---

## 5. Store Policy Verification Matrix

All policies extracted from [`docs/políticas_da_loja.pdf`](docs/políticas_da_loja.pdf) are mapped, indexed, and verified:

| Policy Area | Document Source | System Enforcement | Test Coverage |
|:---|:---|:---|:---|
| **Address & Contacts** | Sec. 1.2 (Page 2) | Physical store: Rua 14 de Maio, 3200 — Campo Grande/MS. WhatsApp: (67) 3341-4444. | `test_retrieve_address_and_company_info` |
| **Operating Hours** | Sec. 2 (Page 2) | Mon–Fri: 09:00–18:00; Sat: 09:00–13:00; Sun/Holidays: Closed. | `test_retrieve_operating_hours` |
| **Payment & PIX** | Sec. 3 & 3.1 (Page 3) | 5% off on regular prices; 1x–12x installment tier constraints. | `test_pix_discount_*`, `test_installments_*` |
| **CDC Withdrawal** | Sec. 4.1 (Page 4) | 7 calendar days for online purchases (CDC Art. 49). Full refund + store freight. | `test_return_withdrawal_*` |
| **Defect Exchange** | Sec. 4.2 (Page 4) | Up to 30 days in-store; >30 days referred to manufacturer warranty. | `test_return_defect_*` |
| **Ineligible Items** | Sec. 4.4 (Page 4) | Items with signs of misuse, missing packaging/invoice, or custom setups. | `test_retrieve_ineligible_items_*` |
| **Shipping Rules** | Sec. 5.1 (Page 4) | Free above R$ 500 in Campo Grande (1–3 days); R$ 35 fee below R$ 500. | `test_shipping_local_*` |
| **Scope & Exclusions** | Sec. 7.3 (Page 7) | Sells ONLY instruments. No accessories (strings, picks, cables) or services. | `test_out_of_scope_*` |
| **Warranty Terms** | Sec. 8.1–8.3 (Page 7) | 90-day legal warranty (CDC) + manufacturer contractual warranty. | `test_retrieve_legal_and_manufacturer_*` |

---

## 6. Setup & Installation

### Option 1: 🐳 Fast Track via Docker (Recommended — Zero Config)

The entire application, database, and optional local LLM are containerized using a multi-stage Docker architecture:

```bash
# 1. Clone the repository
git clone https://github.com/guilherme-0liveira-dev/Teste-Pratico-Artefact.git
cd Teste-Pratico-Artefact

# 2. (Optional) Configure NVIDIA NIM or Ollama in .env (or run offline demonstration mode)
cp .env.example .env

# 3. Build and launch with a single command
docker compose up --build
```

Open **`http://localhost:8501`** in your browser. The container automatically seeds the database on startup if it's not present!

*For advanced Docker operations (Ollama local container, health checks, persistent volumes), see [`docs/DOCKER_GUIDE.md`](docs/DOCKER_GUIDE.md).*

---

### Option 2: 🐍 Local Python Virtual Environment

#### Prerequisites
- Python 3.11, 3.12, or higher
- Git

```powershell
# 1. Clone the repository
git clone https://github.com/guilherme-0liveira-dev/Teste-Pratico-Artefact.git
cd Teste-Pratico-Artefact

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Windows
# source .venv/bin/activate    # On Linux/macOS

# 3. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -e .
pip install -e .[dev]

# 4. Ingest data and policies into SQLite
python scripts/ingest.py

# 5. Launch the Streamlit application
streamlit run app/main.py
```

---

### Option 3: ⚡ UV (Ultra-Fast Package Manager)

```bash
# Install with uv
uv venv
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows
uv pip install -e .[dev]

# Run ingestion and app
uv run python scripts/ingest.py
uv run streamlit run app/main.py
```

---

## 7. Environment Configuration (`.env`)

Copy the example environment template:
```bash
cp .env.example .env
```

| Variable | Default Value | Description |
|:---|:---|:---|
| `LLM_PROVIDER` | `nvidia` | Active LLM backend (`nvidia`, `ollama`, or `mock`). |
| `LLM_API_KEY` | `""` | API Key for NVIDIA NIM (from [build.nvidia.com](https://build.nvidia.com)). |
| `LLM_BASE_URL` | `https://integrate.api.nvidia.com/v1` | OpenAI-compatible endpoint URL. |
| `LLM_MODEL` | `nvidia/nemotron-3.5-bolt-e4b` | Official primary model identifier for cloud inference (with automatic fallback support). |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434/v1` | Local Ollama endpoint. |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Model identifier for local inference. |
| `DATABASE_URL` | `sqlite:///data/emporio.db` | SQLAlchemy database connection URI. |
| `LOG_LEVEL` | `INFO` | Application logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `AGENT_MAX_ITERATIONS` | `5` | Anti-infinite-loop tool execution limit. |

---

## 8. Automated Testing & Code Quality

The project features a comprehensive test suite covering business rules, ingestion idempotency, tool handlers, and agent orchestrator loops with **zero external API calls**:

```powershell
# Run the complete test suite (57 tests)
python -m pytest tests/ -v

# Run tests with test coverage reporting
python -m pytest tests/ --cov=app --cov-report=term-missing

# Run code style and linting checks with Ruff
python -m ruff check .
python -m ruff format --check .
```

### Test Suite Distribution (57 Tests Passing):
- `tests/test_business_rules.py`: 16 unit tests for PIX discounts, boundary installment rules (R$ 79.99 vs R$ 80.00), CDC returns, and freight thresholds.
- `tests/test_ingestion.py`: 5 tests validating Decimal currency strings, ISO/Brazilian date parsing, relational foreign-key integrity, and ingestion idempotency.
- `tests/test_tools.py`: 10 integration tests validating catalog filtering, stock checks, order lookup, promotion listing, and BM25 policy retrieval.
- `tests/test_orchestrator.py`: 6 integration tests using `MockLLMProvider` validating multi-step tool loops, anti-infinite-loop safeguards (capped at 5 turns), sanitize regex guardrails, and provider error handling.
- `tests/test_orders_exhaustive.py`: 5 tests validating order status tracking, fulfillment notes, and customer verification.
- `tests/test_policy_retrieval_exhaustive.py`: 8 tests validating exact legal and operational policy fact retrieval from `políticas_da_loja.pdf`.
- `tests/test_out_of_scope_fallback.py`: 2 tests ensuring graceful handling of excluded accessories and external services.
- **Result:** **57 passed tests** in under 6 seconds.

---

## 9. Security, Privacy & Guardrails

- **LGPD & Customer Privacy:** The `get_order_status` tool includes customer verification safeguards (`order_id` + `email` or `name`) before exposing order line items or shipping details, preventing unauthenticated order scraping.
- **SQL Injection Prevention:** 100% of database interactions utilize SQLAlchemy parameterized ORM queries. The agent has no access to execute arbitrary SQL strings.
- **Prompt Injection Defense:** Retrieved policy manual text and database evidence are treated as passive data payloads in tool responses, segregated from system-level instructions.
- **Sensitive Data Redaction in Logs:** `app/core/logging.py` includes a custom redacting log formatter that scrubs Brazilian CPFs and API key patterns from stdout and log files.
- **Docker Hardening:** Non-root execution (`appuser:appgroup` UID 10001), read-only root security principles, health check probes, and JSON-file log rotation.

---

## 10. Authentic Interaction Transcripts

Five comprehensive multi-turn transcripts are documented in [`examples/conversation_examples.md`](examples/conversation_examples.md):
1. **Scenario 1:** Catalog search for guitars under R$ 1,000 with in-stock filtering and installment computation.
2. **Scenario 2:** General store inquiries (physical address, contact numbers, and operating schedule).
3. **Scenario 3:** Price and live stock check for a specific model (Takamine GD20).
4. **Scenario 4:** Purchase withdrawal request under CDC Art. 49 for an online order, detailing return freight and refund terms.
5. **Scenario 5:** Out-of-scope query handling (accessories/guitar strings request) with mandatory polite refusal, store alternatives, and human WhatsApp escalation.

---

## 11. Repository File Structure

```text
emporio-ai/
├── app/
│   ├── agent/                 # Agent orchestration, system prompts, tool schemas
│   │   ├── orchestrator.py    # Multi-turn conversation reasoning loop & guardrails
│   │   ├── prompts.py         # Persona, scope enforcement & formatting directives
│   │   └── tools.py           # Pydantic v2 schemas & execution handlers
│   ├── core/                  # Global application configuration & redacting logger
│   │   ├── config.py
│   │   └── logging.py
│   ├── db/                    # SQLAlchemy ORM models & database session setup
│   │   ├── connection.py
│   │   └── models.py
│   ├── ingestion/             # Relational CSV and PDF ingestion services
│   │   ├── csv_loader.py
│   │   └── pdf_loader.py
│   ├── llm/                   # Multi-provider LLM interface (NVIDIA NIM / Ollama / Mock)
│   │   └── provider.py
│   ├── retrieval/             # BM25 lexical policy retrieval
│   │   └── policy_search.py
│   ├── services/              # Pure Python domain logic (Rules, Catalog, Orders)
│   │   ├── business_rules.py  # Deterministic pricing, installments, CDC returns & shipping
│   │   ├── catalog.py         # Product, stock, and promotion queries
│   │   └── orders.py          # Order status tracking & customer validation
│   └── main.py                # Streamlit UI with Sidebar Glassy V5 & ambient styling
├── data/                      # Persistent SQLite database storage
├── docs/                      # Assessment documentation & detailed guides
│   ├── AdobeColor-Meu tema de cores.jpeg # Official project color palette
│   ├── DESAFIO_CHECKLIST_TODO.md         # Exhaustive requirement checklist
│   ├── DOCKER_GUIDE.md                   # Containerization and orchestration guide
│   ├── desafio_tecnico_ai_eng_artefact.pdf # Official challenge specification
│   └── políticas_da_loja.pdf             # Internal store policies manual
├── examples/
│   └── conversation_examples.md          # 5 authentic interaction transcripts
├── scripts/
│   └── ingest.py              # CLI ingestion and database bootstrapper
├── tests/                     # 57 automated unit and integration tests
├── .env.example               # Environment variables template
├── docker-compose.yml         # Container orchestration specification
├── Dockerfile                 # Multi-stage production container image
├── pyproject.toml             # Project build configuration & dependency manifest
└── README.md                  # Comprehensive bilingual project documentation
```

---

## 12. Known Limitations & What to Do with More Time

As outlined in the Artefact assessment specifications, the following roadmap highlights natural architectural evolutions for a production 2.0 release:

1. **Live Carrier API Integration (Melhor Envio / Correios):** Currently, freight outside of Campo Grande is estimated using policy manual rules. Direct integration with carrier APIs would allow live, exact quotes and real-time transit tracking by postal code within the chat.
2. **Multimodal WhatsApp Voice Messaging (STT / TTS):** Incorporate Whisper (Faster-Whisper) for transcribing inbound customer voice notes and ElevenLabs / Edge-TTS for audio playback, enabling natural voice-note customer support.
3. **Dense + Sparse Hybrid RAG (Embeddings + BM25):** For scaling to tens of thousands of SKUs and deep technical luthier manuals, implement Reciprocal Rank Fusion (RRF) combining dense vector embeddings with BM25.
4. **Self-Service Customer Transactional Authentication:** Enable authenticated customers to update shipping addresses or initiate order cancellations directly within the chat via SMS/WhatsApp OTP token verification.
5. **Observability & Analytics Management Dashboard:** An executive dashboard displaying daily conversation volumes, top-queried instruments, AI resolution rates, human escalation ratios, and CSAT customer satisfaction scores.

---

## 13. Disclosure of AI Coding Assistant Usage

In full alignment with the Artefact assessment guidelines:

- **AI Assistant Used:** **Google Antigravity** (powered by DeepMind Gemini models).
- **Workflow & Roles:**
  - **Planning & Architecture:** Assisted in mapping requirements from `desafio_tecnico_ai_eng_artefact.pdf` and drafting the checklist in `docs/DESAFIO_CHECKLIST_TODO.md`.
  - **Implementation & Scaffolding:** Accelerated boilerplate authoring for SQLAlchemy models, Pydantic schemas, and Streamlit components.
  - **Test Suite Authoring:** Formulated edge-case test cases (e.g., boundary installment thresholds at R$ 79.99 vs R$ 80.00, non-cumulativity of promotional discounts).
- **Human Review & Verification:**
  - Every calculation, discount formula, and CDC legal rule was manually cross-checked against `políticas_da_loja.pdf`.
  - 100% of the 57 tests, lint checks, and container builds were executed and verified in the live runtime.
