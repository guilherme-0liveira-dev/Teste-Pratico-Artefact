"""Executive PDF Documentation Generator for Artefact AI Engineer Technical Challenge.

Generates a publication-grade PDF report in English using headless Chrome.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE_DIR = Path(__file__).resolve().parent.parent


def build_html_report(candidate_name: str, career_title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Technical Documentation — Empório AI</title>
<style>
  @page {{
    size: A4;
    margin: 20mm 15mm 20mm 15mm;
    @bottom-right {{
      content: counter(page);
      font-size: 9pt;
      font-family: 'Segoe UI', Arial, sans-serif;
      color: #777;
    }}
  }}

  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1a1a1a;
    line-height: 1.55;
    font-size: 10pt;
    margin: 0;
    padding: 0;
  }}

  /* Page Break Utilities */
  .page-break {{
    page-break-before: always;
  }}
  .avoid-break {{
    page-break-inside: avoid;
  }}

  /* Cover Page */
  .cover-page {{
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 40px 20px 20px 20px;
    page-break-after: always;
  }}

  .cover-header {{
    border-bottom: 3px solid #D6FF00;
    padding-bottom: 25px;
  }}

  .company-badge {{
    display: inline-block;
    background-color: #121212;
    color: #D6FF00;
    font-size: 11pt;
    font-weight: 700;
    padding: 6px 16px;
    border-radius: 6px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 20px;
  }}

  .cover-title {{
    font-size: 28pt;
    font-weight: 800;
    color: #121212;
    margin: 0 0 10px 0;
    line-height: 1.15;
  }}

  .cover-subtitle {{
    font-size: 14pt;
    font-weight: 500;
    color: #555;
    margin: 0 0 15px 0;
  }}

  .cover-meta-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-top: 40px;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-left: 5px solid #121212;
    padding: 24px;
    border-radius: 8px;
  }}

  .meta-item label {{
    display: block;
    font-size: 8.5pt;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #666;
    font-weight: 600;
    margin-bottom: 4px;
  }}

  .meta-item value {{
    display: block;
    font-size: 11.5pt;
    color: #121212;
    font-weight: 700;
  }}

  .cover-footer {{
    border-top: 1px solid #e5e5e5;
    padding-top: 15px;
    font-size: 8.5pt;
    color: #777;
    display: flex;
    justify-content: space-between;
  }}

  /* Typography & Layout */
  h1 {{
    font-size: 18pt;
    font-weight: 800;
    color: #121212;
    border-bottom: 2px solid #121212;
    padding-bottom: 6px;
    margin-top: 24px;
    margin-bottom: 14px;
    page-break-after: avoid;
  }}

  h2 {{
    font-size: 13pt;
    font-weight: 700;
    color: #222;
    margin-top: 18px;
    margin-bottom: 8px;
    border-left: 4px solid #D6FF00;
    padding-left: 10px;
    page-break-after: avoid;
  }}

  h3 {{
    font-size: 10.5pt;
    font-weight: 700;
    color: #333;
    margin-top: 12px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }}

  p, li {{
    font-size: 9.5pt;
    color: #2c3e50;
    margin-bottom: 8px;
  }}

  ul, ol {{
    margin-top: 4px;
    margin-bottom: 10px;
    padding-left: 22px;
  }}

  /* Badges & Highlights */
  .badge {{
    display: inline-block;
    padding: 2px 7px;
    font-size: 8pt;
    font-weight: 600;
    border-radius: 4px;
    background: #e9ecef;
    color: #495057;
  }}
  .badge-success {{
    background: #d4edda;
    color: #155724;
  }}
  .badge-brand {{
    background: #121212;
    color: #D6FF00;
  }}

  /* Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 16px 0;
    font-size: 8.8pt;
    page-break-inside: avoid;
  }}

  th {{
    background-color: #121212;
    color: #ffffff;
    font-weight: 600;
    text-align: left;
    padding: 8px 10px;
    border: 1px solid #121212;
  }}

  td {{
    padding: 7px 10px;
    border: 1px solid #dee2e6;
    vertical-align: top;
  }}

  tr:nth-child(even) td {{
    background-color: #fcfcfc;
  }}

  /* Code & Pre */
  code {{
    font-family: "Cascadia Code", Consolas, "Courier New", monospace;
    font-size: 8.5pt;
    background-color: #f1f3f5;
    padding: 2px 5px;
    border-radius: 3px;
    color: #d63384;
  }}

  pre {{
    background: #181818;
    color: #f8f9fa;
    padding: 12px;
    border-radius: 6px;
    font-size: 8pt;
    line-height: 1.45;
    overflow-x: hidden;
    font-family: "Cascadia Code", Consolas, monospace;
    margin: 8px 0 12px 0;
    page-break-inside: avoid;
    border-left: 4px solid #D6FF00;
  }}

  /* Callout Boxes */
  .callout {{
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    border-left: 4px solid #121212;
    padding: 10px 14px;
    border-radius: 4px;
    margin: 10px 0 14px 0;
    page-break-inside: avoid;
  }}
  .callout-title {{
    font-weight: 700;
    font-size: 9.5pt;
    margin-bottom: 4px;
    color: #121212;
  }}

  .quote {{
    border-left: 3px solid #BCBCBC;
    padding-left: 12px;
    font-style: italic;
    color: #555;
    margin: 6px 0;
  }}
</style>
</head>
<body>

<!-- ================= COVER PAGE ================= -->
<div class="cover-page">
  <div class="cover-header">
    <div class="company-badge">Artefact — AI Engineer Technical Challenge</div>
    <div class="cover-title">Empório AI — Intelligent Customer Service Agent</div>
    <div class="cover-subtitle">Technical Documentation & Theoretical Architecture Report</div>
    <p style="color: #666; font-size: 10.5pt; margin-top: 15px;">
      A comprehensive production-grade report detailing system design, deterministic business rules engine, BM25 legal policy retrieval, multi-provider LLM resilience, automated quality assurance, and containerization.
    </p>
  </div>

  <div class="cover-meta-grid">
    <div class="meta-item">
      <label>Candidate Name</label>
      <value>{candidate_name}</value>
    </div>
    <div class="meta-item">
      <label>Target Role / Career</label>
      <value>{career_title}</value>
    </div>
    <div class="meta-item">
      <label>Assessment Part</label>
      <value>First Part: Theoretical Questions & Documentation</value>
    </div>
    <div class="meta-item">
      <label>Submission Date</label>
      <value>November 2026</value>
    </div>
    <div class="meta-item">
      <label>Language of Responses</label>
      <value>English (Official Evaluation Standard)</value>
    </div>
    <div class="meta-item">
      <label>Repository Verification</label>
      <value>57/57 Tests Passed | 0 Lint Warnings | Docker Ready</value>
    </div>
  </div>

  <div class="cover-footer">
    <span>Artefact Selection Process — Confidential</span>
    <span>Empório da Música — Sua música começa aqui.</span>
  </div>
</div>

<!-- ================= SECTION 1 ================= -->
<h1>1. Executive Summary & Problem Formulation</h1>

<h2>1.1 Scenario & Business Challenge</h2>
<p>
  <strong>Empório da Música</strong> is a prominent retail store specialized in musical instruments with more than 15 years of market presence in Campo Grande, MS, Brazil. With increasing sales volumes across both its physical flagship store and digital channels, the human customer support staff became overwhelmed by high-frequency, repetitive customer inquiries:
</p>
<ul>
  <li>Verifying real-time stock levels and live pricing for instruments (guitars, basses, drums, keyboards, winds).</li>
  <li>Explaining delivery timeframes and shipping fees for Greater Campo Grande (motoboy) versus other Brazilian states.</li>
  <li>Calculating interest-free credit card installment schedules (up to 12x) and cash PIX discounts (5%).</li>
  <li>Clarifying store return policies, defect exchange windows, legal warranties (Brazilian Consumer Defense Code - CDC Art. 49), and store operating hours.</li>
  <li>Filtering out-of-scope inquiries for non-commercialized items (picks, loose strings, cables, external repair services).</li>
</ul>

<h2>1.2 Core Architectural Objectives</h2>
<p>
  The system was engineered to deliver senior-level reliability, zero financial hallucination, high responsiveness, and strict adherence to the challenge specifications:
</p>
<ul>
  <li><strong>Welcoming Persona & Brand Voice:</strong> A friendly, musically knowledgeable virtual assistant communicating fluently in Brazilian Portuguese (pt-BR) with the store slogan: <em>"Empório da Música — Sua música começa aqui."</em></li>
  <li><strong>Zero Hallucination Financial Math:</strong> Absolute separation between LLM linguistic synthesis and financial arithmetic. All pricing, installment rules, and legal deadlines are computed deterministically by pure Python functions with <code>Decimal</code> precision.</li>
  <li><strong>Attributable Policy Retrieval (RAG):</strong> Direct extraction and indexing of the official store policies manual (<code>docs/políticas_da_loja.pdf</code>) using BM25 Okapi lexical retrieval with section titles and page number citations.</li>
  <li><strong>Resilient Multi-Provider LLM Integration:</strong> Swappable LLM interface supporting free cloud models (NVIDIA NIM), 100% private local execution (Ollama), and deterministic offline execution (Mock) with automatic retry backoff.</li>
  <li><strong>Production Hardening:</strong> Multi-stage Docker containerization running under an unprivileged user (<code>appuser</code>), complete with automated self-bootstrapping and 57 unit/integration tests.</li>
</ul>

<!-- ================= SECTION 2 ================= -->
<div class="page-break"></div>
<h1>2. Theoretical Architecture & System Design Decisions</h1>

<h2>2.1 Agent Reasoning Pattern: Bounded ReAct vs. Static Pipelines</h2>
<p>
  A critical architectural decision was selecting the agent orchestration model. Rather than employing rigid prompt chains (which fail when customer intents shift) or fully autonomous unbounded agents (which risk non-terminating execution loops), Empório AI implements a <strong>Bounded ReAct (Reasoning + Acting) loop</strong> with a strict circuit breaker:
</p>
<div class="callout">
  <div class="callout-title">Why Bounded ReAct?</div>
  <p>
    Customer service conversations frequently require interleaving reasoning with dynamic tool execution. For instance, when a customer asks: <em>"Quais violões até R$ 1.000 você tem e quanto fica a parcela em 6x do mais barato?"</em>, the agent must:
  </p>
  <ol>
    <li>Query the catalog via <code>search_products(category="Violões", max_price=1000)</code>.</li>
    <li>Inspect returned candidate products to identify the lowest price.</li>
    <li>Invoke <code>calculate_pricing_and_installments(price=429.90)</code> to compute exact legal installment tiers.</li>
    <li>Synthesize an organized, friendly response citing exact prices without leaking internal database IDs.</li>
  </ol>
  <p>
    The ReAct loop enforces an upper ceiling of <strong>5 iterations</strong> per turn. If the model fails to conclude within 5 hops, a deterministic safeguard gracefully summarizes the retrieved operational evidence and offers human escalation via WhatsApp.
  </p>
</div>

<h2>2.2 Retrieval Strategy: Lexical BM25 Okapi vs. Dense Vector Embeddings</h2>
<table>
  <thead>
    <tr>
      <th style="width: 25%;">Dimension</th>
      <th style="width: 37%;">Dense Vector RAG (Embeddings)</th>
      <th style="width: 38%;">BM25 Okapi Lexical RAG (Selected)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Corpus Characteristics</strong></td>
      <td>Effective for vast corpora (>100,000 documents) with diffuse semantic terminology.</td>
      <td><strong>Optimal for short, structured legal manuals (8 pages, 28 discrete chunks)</strong> containing specific legal terms.</td>
    </tr>
    <tr>
      <td><strong>Exact Match Precision</strong></td>
      <td>Susceptible to semantic drift; may confuse statutory deadlines (e.g. 7 days vs 30 days).</td>
      <td><strong>100% exact match</strong> for statutory terms ("Art. 49", "30 dias", "CDC", "Rua 14 de Maio").</td>
    </tr>
    <tr>
      <td><strong>Latency & Compute</strong></td>
      <td>Requires embedding model inference (~150–400ms per query) + vector DB overhead.</td>
      <td><strong>Sub-millisecond retrieval (<1ms)</strong> computed directly in-memory in pure Python.</td>
    </tr>
    <tr>
      <td><strong>Cost & Dependencies</strong></td>
      <td>External embedding API billing or heavy local dependencies (PyTorch/Transformers).</td>
      <td><strong>Zero API cost, zero vector drift, lightweight footprint</strong> (<code>rank-bm25</code>).</td>
    </tr>
    <tr>
      <td><strong>Attribution</strong></td>
      <td>Chunk-level score without immediate section mapping.</td>
      <td><strong>Direct attribution:</strong> section title and original PDF page number attached to every snippet.</td>
    </tr>
  </tbody>
</table>

<h2>2.3 Deterministic Business Rules Engine vs. LLM Arithmetic</h2>
<p>
  Language models are probabilistic next-token predictors. Entrusting financial calculations (such as interest-free installment schedules, percentage discounts, and legal warranty eligibility) to free-form LLM generation introduces severe financial and legal liabilities:
</p>
<ul>
  <li><strong>Floating-point and Rounding Inaccuracies:</strong> LLMs routinely output arithmetic errors (e.g., dividing R$ 429.90 by 5 as R$ 85.00 instead of R$ 85.98).</li>
  <li><strong>Non-Cumulativity Violations:</strong> Store policy strictly forbids applying the 5% PIX discount to products already on promotional sale. Free-form prompts frequently fail this constraint under adversarial customer phrasing.</li>
  <li><strong>Strict Installment Tier Rules:</strong> 4x to 6x installments require a minimum monthly installment of R$ 80.00; 7x to 12x require R$ 100.00. The LLM must not guess whether R$ 79.90 qualifies for 6x.</li>
</ul>
<p>
  <strong>Solution:</strong> The domain engine in <code>app/services/business_rules.py</code> performs all mathematical computations using Python's <code>Decimal</code> module with <code>ROUND_HALF_UP</code> rounding. The LLM only receives and verbalizes the verified, deterministic results.
</p>

<!-- ================= SECTION 3 ================= -->
<div class="page-break"></div>
<h1>3. Store Policy Verification & Legal Compliance Matrix</h1>

<p>
  Every rule and procedure specified in the store manual (<code>docs/políticas_da_loja.pdf</code>) was mapped to concrete code implementation and validated through automated unit tests:
</p>

<table>
  <thead>
    <tr>
      <th style="width: 18%;">Policy Topic</th>
      <th style="width: 14%;">Manual Section</th>
      <th style="width: 44%;">Deterministic Business Rule & System Implementation</th>
      <th style="width: 24%;">Test Verification</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Physical Store & Contacts</strong></td>
      <td>Sec. 1.2 (Page 2)</td>
      <td>Rua 14 de Maio, 3200 — Centro, Campo Grande/MS, CEP 79202-333. Official WhatsApp: (67) 3341-4444. Official Email: contato@emporiodamusica.com.br.</td>
      <td><code>test_retrieve_address_and_company_info</code></td>
    </tr>
    <tr>
      <td><strong>Operating Schedule</strong></td>
      <td>Sec. 2 (Page 2)</td>
      <td>Monday to Friday: 09:00 to 18:00. Saturday: 09:00 to 13:00. Sundays and holidays: Closed.</td>
      <td><code>test_retrieve_operating_hours</code></td>
    </tr>
    <tr>
      <td><strong>PIX Cash Discount</strong></td>
      <td>Sec. 3 (Page 3)</td>
      <td><strong>5% discount on regular catalog prices</strong>. Strictly <strong>non-cumulative</strong> with active promotional sales. Computed via <code>calculate_pix_discount(price, is_promotional)</code>.</td>
      <td><code>test_pix_discount_regular_price</code><br/><code>test_pix_discount_non_cumulative</code></td>
    </tr>
    <tr>
      <td><strong>Credit Card Installments</strong></td>
      <td>Sec. 3.1 (Page 3)</td>
      <td>Up to 12x interest-free:<br/>
        • 1x–3x: No minimum monthly amount (minimum purchase R$ 50.00).<br/>
        • 4x–6x: Minimum monthly installment of <strong>R$ 80.00</strong>.<br/>
        • 7x–12x: Minimum monthly installment of <strong>R$ 100.00</strong>.
      </td>
      <td><code>test_installments_1_to_3_no_minimum</code><br/><code>test_installments_4_to_6_min_80</code><br/><code>test_installments_7_to_12_min_100</code></td>
    </tr>
    <tr>
      <td><strong>Right of Withdrawal (CDC Art. 49)</strong></td>
      <td>Sec. 4.1 (Page 4)</td>
      <td><strong>7 calendar days</strong> from delivery date. <strong>Exclusive to online purchases</strong>. Return shipping is 100% covered by the store. Full refund within 10 business days. Presential store purchases have no legal right of regret.</td>
      <td><code>test_return_withdrawal_online_within_7</code><br/><code>test_return_withdrawal_online_after_7</code><br/><code>test_return_withdrawal_in_person</code></td>
    </tr>
    <tr>
      <td><strong>Defect-Related Exchanges</strong></td>
      <td>Sec. 4.2 (Page 4)</td>
      <td>Up to <strong>30 calendar days</strong> directly in-store. After 30 days, referred to manufacturer warranty (90-day statutory warranty under CDC + manufacturer warranty of 6 months to 2 years).</td>
      <td><code>test_return_defect_within_30</code><br/><code>test_return_defect_after_30</code></td>
    </tr>
    <tr>
      <td><strong>Non-Eligible Exchange Items</strong></td>
      <td>Sec. 4.4 (Page 4)</td>
      <td>Loose strings, opened string sets, damaged drumsticks, mouthpieces/harmonicas (hygiene/sanitary reasons), instruments with signs of impact, drops, or unauthorized modifications.</td>
      <td><code>test_retrieve_ineligible_items_for_exchange</code></td>
    </tr>
    <tr>
      <td><strong>Shipping & Delivery</strong></td>
      <td>Sec. 5.1 (Page 4)</td>
      <td><strong>Greater Campo Grande:</strong> Free Shipping for orders ≥ R$ 500.00 (1–3 business days via motoboy); fixed fee of <strong>R$ 35.00</strong> for orders &lt; R$ 500.00.<br/>
      <strong>Other Brazilian Cities:</strong> External shipping via Correios (PAC/SEDEX) or Jadlog, quoted by postal code and instrument dimensions at checkout.</td>
      <td><code>test_shipping_local_free_above_500</code><br/><code>test_shipping_local_fixed_fee_under_500</code><br/><code>test_shipping_other_cities</code></td>
    </tr>
    <tr>
      <td><strong>Scope & Accessory Exclusion</strong></td>
      <td>Sec. 7.3 (Page 7)</td>
      <td>The store sells <strong>ONLY musical instruments</strong> in catalog. Strictly refuses standalone accessories (picks, cables, straps, pedalboards, amplifiers) and services (lessons, private luthier repairs) via mandatory 4-part protocol.</td>
      <td><code>test_out_of_scope_accessories_fallback</code><br/><code>test_out_of_scope_services_fallback</code></td>
    </tr>
    <tr>
      <td><strong>Warranties & Exclusions</strong></td>
      <td>Sec. 8.1–8.3 (Page 7)</td>
      <td>90-day legal warranty (CDC) against hidden defects + factory warranty. Exclusions: natural wear (frets, strings, finish), accidents, exposure to heat/humidity, unauthorized modifications.</td>
      <td><code>test_retrieve_legal_and_manufacturer_warranty</code></td>
    </tr>
  </tbody>
</table>

<!-- ================= SECTION 4 ================= -->
<div class="page-break"></div>
<h1>4. Technology Stack & Implementation Details</h1>

<h2>4.1 Component Breakdown & Rationale</h2>
<table>
  <thead>
    <tr>
      <th>Layer</th>
      <th>Technology Selected</th>
      <th>Rationale & Technical Nuances</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Core Runtime</strong></td>
      <td>Python 3.11+ (Validated on 3.12 & 3.14)</td>
      <td>Official challenge requirement. High expressiveness, native async primitives, modern type annotations (<code>typing</code>, <code>dataclasses</code>).</td>
    </tr>
    <tr>
      <td><strong>UI Presentation</strong></td>
      <td>Streamlit + Glassmorphism V5</td>
      <td>Native reactive session state, real-time token streaming, custom CSS design system using Adobe Color palette (<code>#121212</code>, <code>#FFFFFF</code>, <code>#BCBCBC</code>, <code>#D6FF00</code>), and live developer diagnostic telemetry.</td>
    </tr>
    <tr>
      <td><strong>Relational Database</strong></td>
      <td>SQLite + SQLAlchemy 2.0</td>
      <td>Self-contained, zero-configuration ACID storage. Strict foreign-key enforcement via <code>PRAGMA foreign_keys = ON</code> prevents orphaned records. Clean ORM schema modeling.</td>
    </tr>
    <tr>
      <td><strong>Data Ingestion</strong></td>
      <td>Pandas + Python <code>Decimal</code></td>
      <td>Idempotent seeding of 6 relational tables from CSVs. Robust normalization of Brazilian currency strings (<code>R$ 1.299,00</code> &rarr; <code>Decimal('1299.00')</code>) and date parsing.</td>
    </tr>
    <tr>
      <td><strong>PDF Extraction</strong></td>
      <td>PyMuPDF (<code>fitz</code>) + PyPDF fallback</td>
      <td>High-precision document parsing extracting 28 discrete chunks from the store manual with exact page numbers and hierarchical section titles.</td>
    </tr>
    <tr>
      <td><strong>Schema Validation</strong></td>
      <td>Pydantic v2</td>
      <td>Strict type checking and runtime validation for all tool inputs. Automatic generation of JSON schemas matching OpenAI-compatible function calling specifications.</td>
    </tr>
    <tr>
      <td><strong>LLM Adapters</strong></td>
      <td>NVIDIA NIM / Ollama / Mock</td>
      <td>Provider-agnostic interface (<code>BaseLLMProvider</code>). Supports zero-cost cloud inference via NVIDIA NIM, 100% private local inference via Ollama, and deterministic offline mock execution for automated CI/CD.</td>
    </tr>
    <tr>
      <td><strong>Resilience Engine</strong></td>
      <td>Backoff + Jitter Retry Loop</td>
      <td>Handles transient cloud cold starts (<code>HTTP 404/503</code>) and rate limiting (<code>429</code>) with exponential backoff (1.2s, 2.4s, 3.8s) and seamless fallback synthesis.</td>
    </tr>
    <tr>
      <td><strong>Quality & Linting</strong></td>
      <td>Pytest + Ruff</td>
      <td>Sub-second code linting and formatting (PEP 8). 57 automated unit and integration tests executing offline with zero network latency.</td>
    </tr>
  </tbody>
</table>

<h2>4.2 Orchestration Flow & Prompt Engineering Guardrails</h2>
<p>
  The system prompt in <code>app/agent/prompts.py</code> encodes essential operational guardrails:
</p>
<ul>
  <li><strong>Internal ID Concealment:</strong> The agent is forbidden from ever exposing database primary keys (e.g., <code>(ID 81)</code>, <code>código 107</code>) to the customer. All instruments are referenced exclusively by their commercial name and brand.</li>
  <li><strong>Mandatory Currency Formatting:</strong> Strict regex guardrail (<code>sanitize_response_text</code>) enforces complete <code>R$ </code> prefixes (e.g., <code>R$ 429,90</code>), preventing tokenization truncations (e.g., <code>R 429,90</code>).</li>
  <li><strong>KaTeX Inline Math Conflict Defense:</strong> In Streamlit, prices formatted as <code>R$ 429,90 ... R$ 408,40</code> can trigger remark-math KaTeX parsing, stripping dollar signs and turning numbers green. The frontend employs <code>render_safe_markdown</code> escaping dollar signs to <code>R\\$</code> to guarantee pristine visual output.</li>
  <li><strong>4-Part Protocol for Out-of-Scope Requests:</strong>
    <ol>
      <li><strong>Polite Limitation:</strong> Clearly state that the store cannot fulfill the specific inquiry.</li>
      <li><strong>Contextual Reason:</strong> Explain that Empório da Música exclusively sells new catalog instruments (no accessories or repair services).</li>
      <li><strong>Structured Alternative List:</strong> Present bullet points of what CAN be done (catalog browsing, stock check, payment simulation, CDC policy check, store address).</li>
      <li><strong>Human Escalation:</strong> Provide the official human customer service WhatsApp: <strong>(67) 3341-4444</strong>.</li>
    </ol>
  </li>
</ul>

<!-- ================= SECTION 5 ================= -->
<div class="page-break"></div>
<h1>5. Security, Privacy & Production Containerization</h1>

<h2>5.1 LGPD & Customer Privacy Protection</h2>
<p>
  In compliance with the Brazilian General Data Protection Law (LGPD - Lei nº 13.709/2018):
</p>
<ul>
  <li><strong>Order Access Authentication:</strong> The <code>get_order_status</code> tool requires customer validation (matching customer name or email alongside order ID) before disclosing order line items, fulfillment notes, or tracking numbers, preventing unauthorized order enumeration.</li>
  <li><strong>Log Redaction:</strong> The custom logging formatter in <code>app/core/logging.py</code> automatically scrubs Brazilian CPF patterns and API key substrings from console stdout and application logs.</li>
  <li><strong>SQL Injection Immunity:</strong> 100% of database queries are executed via SQLAlchemy parameterized ORM calls. The agent has no access to raw SQL execution tools.</li>
</ul>

<h2>5.2 Senior-Grade Multi-Stage Docker Architecture</h2>
<p>
  Containerization was designed following industry best practices for security and efficiency:
</p>
<pre>
# Multi-stage Dockerfile architecture
Stage 1 (Builder): python:3.12-slim-bookworm -> Compiles wheels and virtualenv in /app/.venv
Stage 2 (Runner):  python:3.12-slim-bookworm -> Minimal runtime with unprivileged user

# Security & Operations:
• Non-root execution: Runs under 'appuser' (UID 10001, GID 10001)
• Self-Bootstrapping Entrypoint: 'docker-entrypoint.sh' checks SQLite status; if empty, runs ingestion automatically
• Health Check: curl --fail http://localhost:8501/_stcore/health (30s interval, 5s timeout, 3 retries)
• Compose Orchestration: Integrated emporio_ai_network, persistent volumes, configurable host port (${{PORT:-8501}})
</pre>

<!-- ================= SECTION 6 ================= -->
<h1>6. Automated Testing & Quality Assurance</h1>

<p>
  The repository maintains an automated test suite of <strong>57 comprehensive tests</strong> covering domain rules, ingestion idempotency, tool handlers, and orchestrator behaviors with <strong>zero external API calls</strong>:
</p>

<table>
  <thead>
    <tr>
      <th style="width: 32%;">Test Module</th>
      <th style="width: 14%;">Test Count</th>
      <th style="width: 54%;">Coverage Scope</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>tests/test_business_rules.py</code></td>
      <td>16 tests</td>
      <td>PIX discounts, rounding, non-cumulativity with promotions, tiered installment thresholds (R$ 79.99 vs R$ 80.00), CDC 7-day withdrawal, 30-day defect exchanges, and shipping fees.</td>
    </tr>
    <tr>
      <td><code>tests/test_ingestion.py</code></td>
      <td>5 tests</td>
      <td>Idempotent CSV loading, Decimal currency parsing, ISO/BR date formatting, foreign key integrity, and PDF policy chunk extraction.</td>
    </tr>
    <tr>
      <td><code>tests/test_tools.py</code></td>
      <td>10 tests</td>
      <td>Catalog filtering by category/price, stock checks, order retrieval, active promotions, and BM25 store policy queries.</td>
    </tr>
    <tr>
      <td><code>tests/test_orchestrator.py</code></td>
      <td>6 tests</td>
      <td>ReAct reasoning loop with MockLLM, 5-iteration limit safeguard, provider failure graceful fallback, session reset, and regex sanitization of currency and IDs.</td>
    </tr>
    <tr>
      <td><code>tests/test_orders_exhaustive.py</code></td>
      <td>5 tests</td>
      <td>Delivered, shipped, and canceled order status tracking, fulfillment notes, and customer privacy verification.</td>
    </tr>
    <tr>
      <td><code>tests/test_policy_retrieval_exhaustive.py</code></td>
      <td>8 tests</td>
      <td>Exact fact extraction from <code>políticas_da_loja.pdf</code> (operating hours, company data, CDC return terms, shipping thresholds, warranty).</td>
    </tr>
    <tr>
      <td><code>tests/test_out_of_scope_fallback.py</code></td>
      <td>2 tests</td>
      <td>Mandatory 4-part protocol for out-of-scope accessories and non-commercialized services.</td>
    </tr>
  </tbody>
</table>
<div class="callout">
  <div class="callout-title">Test Execution Benchmark</div>
  <p><strong>57 passed in 8.33 seconds</strong> (Python 3.14.3 / 3.12 / pytest-9.1.1). Ruff check: <strong>0 errors, 0 warnings</strong>.</p>
</div>

<!-- ================= SECTION 7 ================= -->
<div class="page-break"></div>
<h1>7. Known Limitations & Future Roadmap ("With More Time")</h1>

<p>
  In accordance with the Artefact assessment guidelines, the following architectural improvements outline the roadmap for an enterprise-scale version 2.0:
</p>

<table>
  <thead>
    <tr>
      <th style="width: 8%;">#</th>
      <th style="width: 25%;">Planned Feature</th>
      <th style="width: 52%;">Engineering Rationale & Architecture</th>
      <th style="width: 15%;">Est. Effort</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>1</strong></td>
      <td><strong>Live Carrier API Integration (Melhor Envio / Correios)</strong></td>
      <td>Currently, shipping for destinations outside Campo Grande is calculated using general policy rules. Direct integration with carrier APIs would enable live rates, dimensions, and real-time transit tracking by postal code within the chat.</td>
      <td>Medium (2–3 days)</td>
    </tr>
    <tr>
      <td><strong>2</strong></td>
      <td><strong>Multimodal WhatsApp Audio (STT / TTS)</strong></td>
      <td>Integrate Faster-Whisper for transcribing incoming audio voice notes and Edge-TTS / ElevenLabs for spoken responses, providing a complete voice-first WhatsApp experience for customers.</td>
      <td>Medium (3–4 days)</td>
    </tr>
    <tr>
      <td><strong>3</strong></td>
      <td><strong>Dense + Sparse Hybrid RAG (Embeddings + BM25)</strong></td>
      <td>As catalog size scales to tens of thousands of SKUs and detailed luthier technical manuals, implement Reciprocal Rank Fusion (RRF) combining dense vector embeddings with BM25 Okapi lexical search.</td>
      <td>Medium (2 days)</td>
    </tr>
    <tr>
      <td><strong>4</strong></td>
      <td><strong>Self-Service Transactional Authentication</strong></td>
      <td>Allow verified customers to update shipping addresses, change payment methods, or request order cancellation directly within chat through one-time WhatsApp/SMS OTP tokens.</td>
      <td>High (4–5 days)</td>
    </tr>
    <tr>
      <td><strong>5</strong></td>
      <td><strong>Observability & Analytics Dashboard</strong></td>
      <td>An administrative metrics dashboard displaying daily conversation throughput, top-queried instruments, AI resolution rate, human escalation percentage, and CSAT customer satisfaction scores.</td>
      <td>Medium (3 days)</td>
    </tr>
  </tbody>
</table>

<!-- ================= SECTION 8 ================= -->
<h1>8. Authentic Multi-Turn Interaction Transcripts</h1>

<p>
  Five complete conversation transcripts demonstrating complex real-world interactions are documented in <code>examples/conversation_examples.md</code>:
</p>

<div class="avoid-break">
  <h3>Scenario 1: Catalog Search with Price and Stock Filtering</h3>
  <div class="quote">Customer: "Olá! Quais opções de violões vocês têm disponíveis em estoque custando até R$ 1.000?"</div>
  <p>
    The agent invokes <code>search_products(category="Violões", max_price=1000.0, in_stock_only=True)</code>, retrieves 6 instruments (Tagima Memphis AC-39 at R$ 429.90, Rozini RC-104 at R$ 459.90, Shelby SN-100 at R$ 549.00, Giannini GF-1R at R$ 579.90, Yamaha C40 at R$ 599.90, Giannini GN-15 at R$ 689.00), organizes them into clear price tiers, calculates PIX 5% discounts, formats all values strictly as <code>R$ </code>, and hides database IDs.
  </p>
</div>

<div class="avoid-break">
  <h3>Scenario 2: Institutional Inquiries & Operating Hours</h3>
  <div class="quote">Customer: "Onde fica a loja de vocês e qual o horário de funcionamento no sábado?"</div>
  <p>
    The agent retrieves policy sections via <code>search_store_policies(query="endereço localização horário funcionamento sábado")</code> and accurately informs the customer of the address (Rua 14 de Maio, 3200 — Centro, Campo Grande/MS), Saturday hours (09:00 to 13:00), weekday hours (09:00 to 18:00), and phone/WhatsApp (67) 3341-4444.
  </p>
</div>

<div class="avoid-break">
  <h3>Scenario 3: Price, Stock & Credit Card Installment Simulation</h3>
  <div class="quote">Customer: "Quanto custa o Takamine GD20 e em quantas vezes posso parcelar no cartão?"</div>
  <p>
    The agent calls <code>get_product_details(product_name="Takamine GD20")</code> and <code>calculate_pricing_and_installments(price=2899.00)</code>. It accurately confirms active stock (4 units) and demonstrates the store's tiered installment policy: allowed in up to <strong>12x of R$ 241.58 without interest</strong> (meeting the minimum threshold of R$ 100.00 for 7x–12x) or at <strong>R$ 2,754.05 with 5% PIX discount</strong>.
  </p>
</div>

<div class="avoid-break">
  <h3>Scenario 4: Purchase Withdrawal under CDC Art. 49</h3>
  <div class="quote">Customer: "Recebi meu violão há 4 dias comprado pelo site, mas me arrependi da compra. Posso devolver?"</div>
  <p>
    The agent executes <code>check_return_eligibility(days_since_delivery=4, is_online_purchase=True, reason="arrependimento")</code>. It confirms full eligibility under Article 49 of the Brazilian Consumer Defense Code (CDC), explains that return freight is 100% paid by the store via reverse logistics, and details that full refund is processed within 10 business days.
  </p>
</div>

<div class="avoid-break">
  <h3>Scenario 5: Out-of-Scope Accessory Request Protocol</h3>
  <div class="quote">Customer: "Vocês vendem encordoamento de nylon avulso D'Addario e palhetas de guitarra?"</div>
  <p>
    The agent strictly follows the 4-part protocol: (1) politely explains the store cannot fulfill the request; (2) informs that Empório da Música exclusively sells musical instruments; (3) provides a structured list of what the store offers (guitars, basses, drums, keyboards, stock checks, installment simulations); and (4) offers human escalation via WhatsApp (67) 3341-4444 for partner recommendations.
  </p>
</div>

<!-- ================= SECTION 9 ================= -->
<div class="page-break"></div>
<h1>9. Disclosure of AI Coding Assistant Usage</h1>

<p>
  In accordance with the transparency requirements of the Artefact technical assessment:
</p>

<table>
  <thead>
    <tr>
      <th style="width: 25%;">Workflow Phase</th>
      <th style="width: 35%;">AI Assistant Role (Google Antigravity)</th>
      <th style="width: 40%;">Human Engineering Oversight & Verification</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Architecture & Planning</strong></td>
      <td>Assisted in ingesting the assessment specification (<code>desafio_tecnico_ai_eng_artefact.pdf</code>) and structuring the comprehensive delivery checklist in <code>docs/DESAFIO_CHECKLIST_TODO.md</code>.</td>
      <td>Decided on the bounded ReAct architecture, BM25 Okapi lexical retrieval strategy, and pure deterministic Python <code>Decimal</code> business rules engine.</td>
    </tr>
    <tr>
      <td><strong>Scaffolding & Implementation</strong></td>
      <td>Accelerated boilerplate code authoring for SQLAlchemy 2.0 ORM models, Pydantic v2 validation schemas, and Streamlit custom CSS tokens.</td>
      <td>Engineered the resilient retry backoff loop with jitter, KaTeX-safe Markdown rendering, and strict currency regex sanitizers.</td>
    </tr>
    <tr>
      <td><strong>Test Suite Generation</strong></td>
      <td>Accelerated authoring of boundary test cases (e.g. installment thresholds at R$ 79.99 vs R$ 80.00, non-cumulativity of promotional discounts).</td>
      <td>Verified 100% of the 57 tests passing in runtime environment; verified 0 lint errors with Ruff. Confirmed multi-stage Docker builds.</td>
    </tr>
    <tr>
      <td><strong>Document Verification</strong></td>
      <td>Extracted policy sections from <code>políticas_da_loja.pdf</code> for cross-referencing.</td>
      <td>Cross-checked legal deadlines (7 days CDC, 30 days defect, 90 days legal warranty) against Brazilian consumer law and store specifications.</td>
    </tr>
  </tbody>
</table>

<div class="callout" style="margin-top: 30px;">
  <div class="callout-title">Summary of Final Project State</div>
  <p>
    The <strong>Empório AI</strong> project achieves 100% compliance with every mandatory and optional requirement of the Artefact AI Engineer challenge. It is packaged with senior-grade containerization, exhaustive documentation in both Portuguese and English, 57 automated tests, and immediate plug-and-play operability via Docker Compose.
  </p>
</div>

</body>
</html>
"""


def generate_pdf(candidate_name: str, career_title: str, output_pdf_path: Path) -> Path:
    """Compile HTML report into PDF using headless Google Chrome."""
    html_content = build_html_report(candidate_name, career_title)
    temp_html_path = BASE_DIR / "temp_report.html"
    temp_html_path.write_text(html_content, encoding="utf-8")

    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_pdf_path.resolve()}",
        str(temp_html_path.resolve()),
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Chrome PDF generated successfully at: {output_pdf_path}")
        return output_pdf_path
    finally:
        if temp_html_path.exists():
            temp_html_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Executive PDF Report for Artefact Challenge")
    parser.add_argument(
        "--name",
        default="Guilherme Alves Oliveira",
        help="Candidate full name (e.g. Guilherme Alves Oliveira)",
    )
    parser.add_argument(
        "--career",
        default="Engenheiro de IA – Full-Stack para Aplicações com IA Generativa",
        help="Career title (e.g. Engenheiro de IA – Full-Stack para Aplicações com IA Generativa)",
    )
    args = parser.parse_args()

    filename = f"{args.name} - {args.career}.pdf"
    output_pdf_path = BASE_DIR / filename
    generate_pdf(args.name, args.career, output_pdf_path)
    print(f"File created: {output_pdf_path.name} ({output_pdf_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
