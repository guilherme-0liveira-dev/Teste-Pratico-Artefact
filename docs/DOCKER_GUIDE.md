# 🐳 Guia de Containerização Docker — Empório AI

Este guia documenta a arquitetura de conteinerização do **Empório AI**, modelada seguindo as melhores práticas de **Engenharia de Software e Arquitetura de Plataforma (Nível Sênior)**.

---

## 🏗️ 1. Arquitetura do Container

A conteinerização foi projetada com base em três pilares fundamentais: **Segurança**, **Performance de Inicialização** e **Zero-Configuration Onboarding**.

```
+-------------------------------------------------------------------------+
|                        Docker Compose Environment                       |
|                                                                         |
|  +---------------------------+             +-------------------------+  |
|  |   Service: emporio-ai     |             |     Service: ollama     |  |
|  |  (Streamlit + Agent Core) |             |  (Profile: local-llm)   |  |
|  |                           |             |                         |  |
|  |   Port: 8501:8501         |             |   Port: 11434:11434     |  |
|  |   User: appuser (non-root)|             |   Ollama Inference API  |  |
|  |   Healthcheck: Active     |             +------------+------------+  |
|  +-------------+-------------+                          |               |
|                |                                        |               |
|                +-------------------+--------------------+               |
|                                    |                                    |
|                     Network: emporio_ai_network                         |
|                                                                         |
|  Volumes:                                                               |
|  - emporio_ai_sqlite_data  --> Persistência do Banco SQLite / Catálogo  |
|  - emporio_ai_ollama_models --> Armazenamento dos Modelos GGUF Locais   |
+-------------------------------------------------------------------------+
```

### Destaques Técnicos Sênior:
- **Multi-Stage Build (`Dockerfile`):**
  - **Stage 1 (`builder`):** Instala compiladores C e dependências nativas em um virtualenv isolado (`/opt/venv`).
  - **Stage 2 (`runner`):** Utiliza imagem minimalista `python:3.12-slim-bookworm` contendo apenas os binários finais compilados, reduzindo o tamanho da imagem e a superfície de ataque.
- **Segurança (Least Privilege):** A aplicação roda sob o usuário não-root `appuser` (UID 10001, GID 10001), prevenindo qualquer risco de escalonamento de privilégios no host.
- **Auto-Bootstrapping (`docker-entrypoint.sh`):** Em uma máquina virgem, o entrypoint detecta a ausência do banco SQLite e executa automaticamente a pipeline de ingestão (`scripts/ingest.py`) antes de iniciar o Streamlit.
- **Healthcheck Nativo:** Monitoramento contínuo via endpoint oficial `http://localhost:8501/_stcore/health`.
- **Limites de Recursos:** Políticas de contenção de CPU (`2.0 CPUs`) e Memória (`2GB`) no `docker-compose.yml`, além de rotação de logs para proteger o disco.

---

## 🚀 2. Como Executar

### Opção A: Execução Padrão (NVIDIA NIM ou Modo Demonstração)

1. **Configurar Credenciais (Opcional, mas recomendado):**
   Crie ou edite o arquivo `.env` na raiz do projeto:
   ```bash
   LLM_PROVIDER=nvidia
   LLM_API_KEY=nvapi-sua-chave-aqui
   LLM_MODEL=meta/llama-3.3-70b-instruct
   ```
   *(Caso não informe nenhuma chave, o sistema iniciará perfeitamente no Modo Demonstração Offline determinístico).*

2. **Subir os containers:**
   ```bash
   docker compose up --build
   ```

3. **Acessar a Aplicação:**
   Abra no seu navegador: **`http://localhost:8501`**

---

### Opção B: Execução com LLM Local Integrado (Ollama via Docker)

Se desejar rodar todo o ecossistema localmente sem sair do Docker:

1. **Subir aplicação + container do Ollama:**
   ```bash
   docker compose --profile local-llm up --build -d
   ```

2. **Baixar o modelo no container do Ollama:**
   ```bash
   docker compose exec ollama ollama run qwen2.5-coder:7b
   ```

3. **Conectar na interface do Streamlit:**
   - Na aba **⚙️ Configurar Conexão do Modelo**, selecione **Ollama Local**.
   - URL: `http://ollama:11434/v1` *(o container se comunica diretamente pela rede interna)*.

---

## 🛠️ 3. Comandos Úteis para o Dia a Dia

| Objetivo | Comando |
| :--- | :--- |
| **Subir em background (detached)** | `docker compose up -d` |
| **Visualizar logs em tempo real** | `docker compose logs -f emporio-ai` |
| **Verificar status de saúde do container** | `docker compose ps` |
| **Reexecutar ingestão manual no container** | `docker compose exec emporio-ai python scripts/ingest.py` |
| **Executar suite de testes dentro do container** | `docker compose run --rm emporio-ai pytest tests/` |
| **Derrubar containers mantendo dados salvos** | `docker compose down` |
| **Derrubar limpando volumes e banco de dados** | `docker compose down -v` |

---

## 🔒 4. Salvaguardas e Resiliência
- **Zero Vazamento de Segredos:** Arquivos `.env` e chaves locais são estritamente excluídos via `.dockerignore`.
- **Persistência Confiável:** Mesmo ao recriar a imagem com novas alterações de código, o volume nomeado `emporio_ai_sqlite_data` preserva o catálogo e o status dos pedidos.
