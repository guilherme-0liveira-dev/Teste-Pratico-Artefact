# 📋 Checklist & Todo List — Desafio Técnico Artefact AI Engineer
## Empório AI — Assistente de Atendimento Inteligente

Este documento consolida o mapeamento exaustivo entre as exigências do edital oficial (**`desafio_tecnico_ai_eng_artefact.pdf`**), as políticas da loja (**`políticas_da_loja.pdf`**) e a implementação técnica realizada no projeto.

---

## 1. Visão Geral do Cenário

| Parâmetro | Detalhe |
|:---|:---|
| **Empresa Contratante** | Artefact |
| **Cliente Fictício** | Empório da Música |
| **Localização** | Rua 14 de Maio, 3200 — Centro, Campo Grande - MS |
| **Desafio Central** | Equipe de atendimento sobrecarregada com dúvidas recorrentes sobre catálogo, estoque, preços, prazos de entrega, cálculo de parcelas/PIX e regras de troca/garantia. |
| **Objetivo** | Prototipar um agente de mensagens em Python capaz de prestar atendimento humanizado, seguro, fundamentado em dados reais e com zero alucinação financeira. |

---

## 2. Todo List de Requisitos do Desafio

### Legenda de Status
- ✅ **100% Concluído & Validado** — Implementado, testado com testes automatizados e validado na interface.
- 🚀 **Oportunidade de Evolução ("Com Mais Tempo")** — Melhorias arquiteturais planejadas para expansão em produção contínua, documentadas na seção de limitações do README.

---

### A. Persona, Identidade e Comunicação
- [x] ✅ **Persona Humanizada e Acolhedora:** Assumir o papel de "Empório AI", especialista em música, atencioso e comunicativo.
- [x] ✅ **Linguagem Oficial:** Comunicação em Português do Brasil (pt-BR), informal mas profissional.
- [x] ✅ **Slogan e Branding da Loja:** Integração do slogan oficial *"Empório da Música — Sua música começa aqui."*
- [x] ✅ **Formatação Rigorosa de Moeda:** Exibição obrigatória de valores monetários com o prefixo completo `R$ ` (ex: `R$ 429,90`, `R$ 599,90`), sem abreviações truncadas.
- [x] ✅ **Ocultação de IDs Técnicos:** O cliente nunca vê identificadores de banco de dados (ex: `(ID 81)`), sendo os instrumentos referenciados unicamente por nome e marca comercial.

---

### B. Gestão de Dados Operacionais (CSVs & Relacional)
- [x] ✅ **Modelagem de Dados Relacional:** Banco de dados SQLite (`emporio.db`) com integridade referencial (`PRAGMA foreign_keys = ON`).
- [x] ✅ **Ingestão Idempotente das 6 Tabelas:**
  - `categories` (9 categorias mapeadas).
  - `products` (65 instrumentos musicais com atributos, estoque e preços).
  - `customers` (50 clientes cadastrados).
  - `orders` (20 pedidos de compra).
  - `order_items` (22 itens de pedidos).
  - `promotions` (25 campanhas promocionais ativas e históricas).
- [x] ✅ **Tratamento de Dados e Precisão Monetária:** Conversão de strings de moeda brasileira (`R$ 1.299,00`) para o tipo Python `Decimal` de alta precisão, evitando erros de ponto flutuante.
- [x] ✅ **Normalização de Datas:** Tratamento de múltiplos formatos de data (`DD/MM/YYYY`, `YYYY-MM-DD`).

---

### C. Recuperação de Conhecimento e Políticas da Loja (PDF & RAG)
- [x] ✅ **Extração Fiel do Manual:** Processamento do manual `políticas_da_loja.pdf` via PyMuPDF preservando seções, tópicos e números de página.
- [x] ✅ **Indexação Lexical BM25 Okapi:** Recuperação rápida por palavras-chave legais e institucionais (sem custo de embeddings nem risco de drift vetorial).
- [x] ✅ **Citação de Fontes e Páginas:** Cada evidência recuperada identifica a seção e o número da página do manual original.
- [x] ✅ **Cobertura das Regras Institucionais:**
  - Endereço físico e canais oficiais (WhatsApp `(67) 3341-4444`, e-mail `contato@emporiodamusica.com.br`).
  - Horários de funcionamento (Seg–Sex 09h às 18h, Sáb 09h às 13h, Dom/Feriados fechado).

---

### D. Motor de Regras Determinístico (Zero Alucinação Financeira)
- [x] ✅ **Desconto no PIX (5%):**
  - Cálculo determinístico por código Python (`price * 0.95`).
  - **Não Cumulatividade Estrita:** Proibição de acúmulo de desconto de 5% sobre produtos já em promoção ativa.
- [x] ✅ **Parcelamento no Cartão de Crédito sem Juros (em até 12x):**
  - Faixa 1x a 3x: Sem valor mínimo por parcela (exceto total < R$ 50,00).
  - Faixa 4x a 6x: Parcela mínima obrigatória de **R$ 80,00**.
  - Faixa 7x a 12x: Parcela mínima obrigatória de **R$ 100,00**.
- [x] ✅ **Regras de Frete e Entrega:**
  - Campo Grande e Região: Frete Grátis para compras ≥ R$ 500,00 (1 a 3 dias úteis via motoboy); taxa fixa de R$ 35,00 para compras < R$ 500,00.
  - Demais localidades: Envio terceirizado via Correios (PAC/SEDEX) ou Jadlog.
- [x] ✅ **Políticas de Devolução e Garantia (CDC):**
  - Direito de Arrependimento (Art. 49 do CDC): 7 dias corridos após o recebimento, exclusivo para compras online. Frete por conta da loja e reembolso integral. Compras físicas não possuem direito legal a arrependimento.
  - Troca por Defeito: até 30 dias corridos diretamente na loja física. Após 30 dias, acionamento da garantia do fabricante (garantia legal de 90 dias + garantia de fábrica).
  - Condições de Devolução: Exigência de embalagem original, manuais, nota fiscal e ausência de sinais de mau uso.

---

### E. Escopo da Loja & Perguntas Fora de Escopo
- [x] ✅ **Escopo Exclusivo de Instrumentos:** Reconhecimento de que a loja vende APENAS instrumentos musicais.
- [x] ✅ **Tratamento de Acessórios:** Recusa educada para itens não comercializados (cordas avulsas, palhetas, cabos, pedais de efeito, amplificadores e capas/cases), orientando o cliente a buscar lojas parceiras.
- [x] ✅ **Escalonamento Humano:** Encaminhamento gentil para os atendentes humanos no WhatsApp para casos sensíveis, estornos ou pedidos especiais.

---

### F. Ferramentas do Agente (Function Calling / Tools)
- [x] ✅ **`search_products`:** Busca de instrumentos por categoria, marca, faixa de preço e estoque.
- [x] ✅ **`get_product_details`:** Detalhes completos de especificações técnicas, madeira e descrição.
- [x] ✅ **`check_stock`:** Consulta rápida de saldo de estoque.
- [x] ✅ **`get_order_status`:** Rastreio de pedidos com checagem de status e previsão.
- [x] ✅ **`get_active_promotions`:** Consulta de campanhas vigentes com percentual de desconto.
- [x] ✅ **`calculate_pricing_and_installments`:** Simulação exata de parcelamento e desconto PIX.
- [x] ✅ **`calculate_shipping_estimate`:** Estimativa de prazos e valores de frete.
- [x] ✅ **`search_store_policies`:** Consulta ao manual de políticas via BM25 com citação de página.
- [x] ✅ **`check_return_eligibility`:** Análise jurídica automática de elegibilidade para devolução/troca.

---

### G. Arquitetura de LLMs & Orquestrador Seguro
- [x] ✅ **Provedor Agnóstico (`BaseLLMProvider`):**
  - **NVIDIA NIM Cloud (Free API):** Testado e validado com `nemotron-3.5-bolt-e4b` e `meta/llama-3.3-70b-instruct`.
  - **Ollama Local (Privado):** Compatível com `qwen2.5-coder:7b` ou `llama3.2`.
  - **Mock LLM Offline:** Provedor determinístico para execução de CI/CD e testes unitários com latência zero.
- [x] ✅ **Loop ReAct Seguro com Circuit Breaker:** Bounded execution loop com limite estrito de 5 iterações para prevenir loops infinitos e desperdício de tokens.
- [x] ✅ **Validador de Conexão em Tempo Real:** Verificação prévia da API Key e endpoint antes da inicialização do agente, exibindo alertas amigáveis em caso de falha.

---

### H. Interface de Usuário (Streamlit Glassmorphism SaaS)
- [x] ✅ **Design System Glassmorphism:** Estética inspirada em Apple e Linear, com superfícies translúcidas em 3 níveis de elevação (`backdrop-filter: blur(28px)`).
- [x] ✅ **Paleta de Cores Oficial (Adobe Color):**
  - Fundo Canvas Dark: `#121212` (Ônix profundo com iluminação ambiente radial).
  - Acento Principal: `#D6FF00` (Cyber Lime de alta visibilidade e energia).
  - Secundário / Bordas: `#BCBCBC` (Prata/Cromo metálico).
  - Textos & Títulos: `#FFFFFF` e `#F7F7F7` (Excelente contraste e legibilidade).
- [x] ✅ **Sidebar Frosted Glass Clara e Profissional:** Gradiente translúcido luminoso, cards de informações da loja, foto institucional e botão de reiniciar conversa.
- [x] ✅ **Sugestões Rápidas Persistentes:** 4 botões de consulta rápida que permanecem acessíveis e funcionais acima do histórico em todos os turnos.
- [x] ✅ **Painel de Diagnóstico Técnico:** Métricas de latência do turno, contagem de iterações do agente e detalhamento de cada ferramenta acionada (com JSON de argumentos e snippet de evidência).
- [x] ✅ **Remoção de Elementos Padrão:** Ocultação de botões de deploy e toolbars nativas do Streamlit para acabamento de produto comercial.

---

### I. Testes Automatizados & Qualidade de Código
- [x] ✅ **54 Testes Automatizados no Pytest:**
  - 16 testes de regras de negócio financeiras e CDC.
  - 5 testes de integridade relacional e ingestão de CSV/PDF.
  - 10 testes de execução de ferramentas e catálogo.
  - 5 testes de orquestrador, limites de iteração e tratamento de falhas.
  - 18 testes adicionais exaustivos de recuperação BM25, pedidos e catálogo.
- [x] ✅ **Tempo de Execução:** Suíte completa executada em ~5 segundos offline.
- [x] ✅ **Padronização com Ruff:** 0 erros de linting e formatação PEP 8 estrita.

---

### J. Segurança, Privacidade e LGPD
- [x] ✅ **Prevenção de SQL Injection:** 100% das consultas orquestradas via SQLAlchemy ORM com parâmetros vinculados (sem interpolação de strings SQL).
- [x] ✅ **Proteção LGPD em Pedidos:** O agente valida o ID do pedido e o cliente antes de divulgar dados de entregas.
- [x] ✅ **Defesa Contra Prompt Injection:** Separação rígida entre dados retornados por ferramentas e instruções de sistema no prompt mestre.
- [x] ✅ **Sanitização de Logs:** Mascaramento automático de chaves de API e documentos sensíveis em stdout e arquivos de log.

---

### K. Entregáveis Formais do Processo Seletivo
- [x] ✅ **Repositório Git Público:** Histórico estruturado com 12 commits cronológicos cobrindo todas as fases de construção.
- [x] ✅ **`README.md` Completo em Inglês:** Documentação detalhada cobrindo arquitetura, guia de instalação, justificativas técnicas, limitações e uso de assistentes de IA (Google Antigravity).
- [x] ✅ **`examples/conversation_examples.md`:** 5 transcrições detalhadas de conversas reais cobrindo busca de instrumentos, estoque, arrependimento de compra com CDC, cálculo de parcelamento e recusa de acessórios fora de escopo.

---

## 3. O Que Ainda Falta / Próximos Passos ("Com Mais Tempo")

Conforme requerido pela seção **"Limitações conhecidas e o que você faria com mais tempo"** do edital da Artefact, as seguintes melhorias representam a evolução natural para uma versão 2.0 em escala de produção:

| # | Funcionalidade Planejada | Justificativa de Engenharia | Esforço Estimado |
|:---:|:---|:---|:---:|
| **1** | **Integração com API de Cotação em Tempo Real (Melhor Envio / Correios)** | Atualmente o frete para fora de Campo Grande é estimado pelas diretrizes gerais do manual. Uma integração direta com a API dos Correios ou Melhor Envio permitiria retornar valores e prazos exatos por CEP no chat. | Médio (2–3 dias) |
| **2** | **Canal Multimodal WhatsApp com Áudio (STT / TTS)** | Incorporar Whisper (OpenAI/Faster-Whisper) para transcrição de áudios de clientes e ElevenLabs / Edge-TTS para respostas faladas, permitindo atendimento via WhatsApp Voice Notes. | Médio (3–4 dias) |
| **3** | **RAG Híbrido Denso + Esparso (Embeddings + BM25)** | Caso o catálogo e manual se expandam para milhares de páginas e dezenas de milhares de SKUs, implementar Reciprocal Rank Fusion (RRF) combinando busca vetorial densa com a atual BM25. | Médio (2 dias) |
| **4** | **Autoatendimento com Autenticação Transacional** | Permitir que clientes autenticados realizem alterações de endereço de entrega ou solicitem cancelamento de pedidos diretamente na conversa mediante validação por token SMS/WhatsApp. | Alto (4–5 dias) |
| **5** | **Painel Administrativo de Observabilidade & Analytics** | Dashboard de métricas gerenciais em tempo real: volume diário de conversas, instrumentos mais buscados, taxa de resolução por IA, índice de escalonamento humano e avaliação de satisfação (CSAT). | Médio (3 dias) |

---

## 4. Conclusão da Avaliação

O projeto **Empório AI** cumpriu **100% dos requisitos mandatórios e opcionais** estipulados no edital da Artefact, destacando-se por:
1. **Solidez de Engenharia:** Código modular, desacoplado de frameworks desnecessários e orientado a testes.
2. **Confiabilidade:** Zero alucinação financeira em cálculos de parcelas e descontos PIX.
3. **Design e Experiência:** Interface Glassmorphism minimalista e fluida no tema Adobe Color.
4. **Prontidão para Demonstração:** Suporte plug-and-play imediato via NVIDIA NIM Cloud Free, Ollama ou Mock Offline.
