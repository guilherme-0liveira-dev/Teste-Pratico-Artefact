"""Pure deterministic business rule engine for Empório da Música.

All calculations here are mathematically exact using Decimal to prevent float rounding errors.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass
class InstallmentOption:
    installments: int
    monthly_amount: Decimal
    total_amount: Decimal
    is_allowed: bool
    explanation: str


@dataclass
class ReturnEligibilityResult:
    is_eligible: bool
    return_type: str
    deadline_days: int
    freight_covered_by: str
    explanation: str


@dataclass
class ShippingResult:
    city: str
    is_local: bool
    fee_brl: Decimal
    is_free_shipping: bool
    estimated_days: str
    delivery_method: str
    notes: str


def calculate_pix_discount(price: Decimal, is_promotional: bool = False) -> tuple[Decimal, Decimal]:
    """Calculate 5% PIX discount on regular catalog price.

    Returns:
        tuple[final_price, discount_amount]
    Rule:
        PIX discount is 5% on regular prices.
        PIX discount is NOT cumulative with promotional prices.
    """
    if is_promotional:
        return price.quantize(Decimal("0.01")), Decimal("0.00")

    discount = (price * Decimal("0.05")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    final_price = (price - discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return final_price, discount


def calculate_installments(price: Decimal) -> list[InstallmentOption]:
    """Calculate all 1 to 12 installment options according to store rules:

    - 1x to 3x: sem juros, sem valor mínimo de parcela (exceto abaixo de R$ 50,00 total).
    - 4x a 6x: sem juros, parcela mínima de R$ 80,00.
    - 7x a 12x: sem juros, parcela mínima de R$ 100,00.
    """
    options: list[InstallmentOption] = []
    price_dec = price.quantize(Decimal("0.01"))

    for n in range(1, 13):
        monthly = (price_dec / Decimal(n)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (monthly * Decimal(n)).quantize(Decimal("0.01"))

        if price_dec < Decimal("50.00") and n > 1:
            options.append(
                InstallmentOption(
                    installments=n,
                    monthly_amount=monthly,
                    total_amount=total,
                    is_allowed=False,
                    explanation="Compras abaixo de R$ 50,00 não são elegíveis a parcelamento.",
                )
            )
            continue

        if 1 <= n <= 3:
            options.append(
                InstallmentOption(
                    installments=n,
                    monthly_amount=monthly,
                    total_amount=total,
                    is_allowed=True,
                    explanation=f"{n}x de R$ {monthly:.2f} sem juros (sem parcela mínima).",
                )
            )
        elif 4 <= n <= 6:
            if monthly >= Decimal("80.00"):
                options.append(
                    InstallmentOption(
                        installments=n,
                        monthly_amount=monthly,
                        total_amount=total,
                        is_allowed=True,
                        explanation=f"{n}x de R$ {monthly:.2f} sem juros (atende mínimo de R$ 80,00).",
                    )
                )
            else:
                options.append(
                    InstallmentOption(
                        installments=n,
                        monthly_amount=monthly,
                        total_amount=total,
                        is_allowed=False,
                        explanation=f"Não permitido: parcela de R$ {monthly:.2f} é inferior ao mínimo de R$ 80,00 para 4x a 6x.",
                    )
                )
        elif 7 <= n <= 12:
            if monthly >= Decimal("100.00"):
                options.append(
                    InstallmentOption(
                        installments=n,
                        monthly_amount=monthly,
                        total_amount=total,
                        is_allowed=True,
                        explanation=f"{n}x de R$ {monthly:.2f} sem juros (atende mínimo de R$ 100,00).",
                    )
                )
            else:
                options.append(
                    InstallmentOption(
                        installments=n,
                        monthly_amount=monthly,
                        total_amount=total,
                        is_allowed=False,
                        explanation=f"Não permitido: parcela de R$ {monthly:.2f} é inferior ao mínimo de R$ 100,00 para 7x a 12x.",
                    )
                )

    return options


def get_max_allowed_installments(price: Decimal) -> InstallmentOption | None:
    """Return the highest allowed installment option for a given price."""
    allowed = [opt for opt in calculate_installments(price) if opt.is_allowed]
    return allowed[-1] if allowed else None


def evaluate_return_eligibility(
    days_since_delivery: int,
    is_online_purchase: bool = True,
    reason: str = "arrependimento",
) -> ReturnEligibilityResult:
    """Evaluate return or exchange eligibility according to store policy (Section 4):

    - Arrependimento (CDC Compras Online): 7 dias corridos após o recebimento. Frete pela loja.
    - Troca por defeito de fabricação: 30 dias corridos na loja. Após 30 dias, garantia com fabricante.
    - Troca por preferência (cor/modelo): 7 dias corridos, produto intacto em embalagem original.
    """
    reason_lower = reason.lower().strip()

    if "arrepend" in reason_lower:
        if not is_online_purchase:
            return ReturnEligibilityResult(
                is_eligible=False,
                return_type="Direito de Arrependimento",
                deadline_days=7,
                freight_covered_by="N/A",
                explanation="O direito de arrependimento de 7 dias é exclusivo para compras online/remotas (Art. 49 CDC). Para compras presenciais, consulte trocas por defeito ou preferência.",
            )
        if days_since_delivery <= 7:
            return ReturnEligibilityResult(
                is_eligible=True,
                return_type="Direito de Arrependimento (CDC)",
                deadline_days=7,
                freight_covered_by="Loja",
                explanation=f"Dentro do prazo legal de 7 dias corridos (solicitado no dia {days_since_delivery}). O frete de devolução é coberto pela Empório da Música e o reembolso será efetuado na mesma forma de pagamento em até 10 dias úteis.",
            )
        else:
            return ReturnEligibilityResult(
                is_eligible=False,
                return_type="Direito de Arrependimento (CDC)",
                deadline_days=7,
                freight_covered_by="N/A",
                explanation=f"Prazo expirado. A solicitação ocorreu após {days_since_delivery} dias corridos (o limite legal é de 7 dias corridos a partir do recebimento).",
            )

    if "defeito" in reason_lower:
        if days_since_delivery <= 30:
            return ReturnEligibilityResult(
                is_eligible=True,
                return_type="Troca por Defeito de Fabricação",
                deadline_days=30,
                freight_covered_by="Loja",
                explanation=f"Dentro do prazo de 30 dias corridos para troca direta com a loja por defeito de fabricação (dia {days_since_delivery}). A loja providenciará a substituição ou reparo.",
            )
        else:
            return ReturnEligibilityResult(
                is_eligible=False,
                return_type="Garantia do Fabricante / Legal",
                deadline_days=30,
                freight_covered_by="Conforme fabricante",
                explanation=f"O prazo para troca direta na loja (30 dias) expirou (dia {days_since_delivery}). No entanto, o instrumento conta com a garantia legal de 90 dias e garantia do fabricante (de 6 meses a 2 anos). A loja pode intermediar o acionamento da garantia.",
            )

    # Preferência / modelo / cor
    if days_since_delivery <= 7:
        return ReturnEligibilityResult(
            is_eligible=True,
            return_type="Troca por Preferência",
            deadline_days=7,
            freight_covered_by="Cliente / Loja conforme acordado",
            explanation="Dentro do prazo de 7 dias para troca por preferência (cor/modelo/tamanho). O produto deve estar em perfeito estado e na embalagem original, sujeito à disponibilidade em estoque.",
        )
    return ReturnEligibilityResult(
        is_eligible=False,
        return_type="Troca por Preferência",
        deadline_days=7,
        freight_covered_by="N/A",
        explanation=f"Prazo expirado para troca por preferência (limite de 7 dias, solicitação no dia {days_since_delivery}).",
    )


def calculate_shipping(
    order_total: Decimal, destination_city: str = "Campo Grande"
) -> ShippingResult:
    """Calculate shipping policy rules (Section 5):

    - Região Metropolitana de Campo Grande:
      - Acima de R$ 500,00: Frete Grátis
      - Abaixo de R$ 500,00: Taxa fixa de R$ 35,00
      - Prazo: 1 a 3 dias úteis por motoboy próprio
    - Outras cidades:
      - Correios (PAC / SEDEX) ou Jadlog
      - Valor depende do CEP e dimensões; cotação detalhada no checkout
    """
    city_clean = destination_city.strip().lower()
    is_local = "campo grande" in city_clean

    if is_local:
        if order_total >= Decimal("500.00"):
            return ShippingResult(
                city=destination_city,
                is_local=True,
                fee_brl=Decimal("0.00"),
                is_free_shipping=True,
                estimated_days="1 a 3 dias úteis",
                delivery_method="Motoboy próprio",
                notes="Frete Grátis aplicado (pedido igual ou superior a R$ 500,00 para Campo Grande/MS).",
            )
        else:
            return ShippingResult(
                city=destination_city,
                is_local=True,
                fee_brl=Decimal("35.00"),
                is_free_shipping=False,
                estimated_days="1 a 3 dias úteis",
                delivery_method="Motoboy próprio",
                notes="Taxa fixa de entrega local de R$ 35,00 (pedidos abaixo de R$ 500,00 na Grande Campo Grande).",
            )

    return ShippingResult(
        city=destination_city,
        is_local=False,
        fee_brl=Decimal("0.00"),
        is_free_shipping=False,
        estimated_days="PAC: 5-12 dias úteis | SEDEX: 2-5 dias úteis | Jadlog: 3-8 dias úteis",
        delivery_method="Correios (PAC/SEDEX) ou Jadlog com seguro incluso",
        notes="Para envios fora de Campo Grande, o frete é calculado no checkout pelo CEP, peso e dimensões do instrumento.",
    )
