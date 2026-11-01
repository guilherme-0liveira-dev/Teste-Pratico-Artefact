"""Unit tests for deterministic business rules (PIX, installments, returns, shipping)."""

from decimal import Decimal

from app.services.business_rules import (
    calculate_installments,
    calculate_pix_discount,
    calculate_shipping,
    evaluate_return_eligibility,
    get_max_allowed_installments,
)

# ============================================================================
# PIX Discount Tests
# ============================================================================


def test_pix_discount_regular_price():
    """PIX discount is 5% on regular catalog price."""
    price = Decimal("1000.00")
    final_price, discount = calculate_pix_discount(price, is_promotional=False)
    assert final_price == Decimal("950.00")
    assert discount == Decimal("50.00")


def test_pix_discount_cents_rounding():
    """PIX discount properly rounds half up to 2 decimal places."""
    price = Decimal("599.90")
    final_price, discount = calculate_pix_discount(price, is_promotional=False)
    # 599.90 * 0.05 = 29.995 -> 30.00
    assert discount == Decimal("30.00")
    assert final_price == Decimal("569.90")


def test_pix_discount_non_cumulative_with_promotions():
    """PIX discount is NOT cumulative with promotional pricing."""
    price = Decimal("800.00")
    final_price, discount = calculate_pix_discount(price, is_promotional=True)
    assert final_price == Decimal("800.00")
    assert discount == Decimal("0.00")


# ============================================================================
# Installment Tier Tests
# ============================================================================


def test_installments_under_50_reais():
    """Orders below R$ 50.00 cannot be split into multiple installments."""
    price = Decimal("45.00")
    options = calculate_installments(price)
    # 1x allowed, 2x+ disallowed
    assert options[0].is_allowed is True
    assert options[1].is_allowed is False


def test_installments_1_to_3_no_minimum():
    """Installments 1 to 3 have no minimum monthly value."""
    price = Decimal("60.00")
    options = calculate_installments(price)
    # 3x of R$ 20.00 is allowed because it is in the 1-3x tier
    opt_3x = next(o for o in options if o.installments == 3)
    assert opt_3x.is_allowed is True
    assert opt_3x.monthly_amount == Decimal("20.00")


def test_installments_4_to_6_min_80_reais():
    """Installments 4 to 6 require minimum installment of R$ 80.00."""
    price = Decimal("400.00")
    options = calculate_installments(price)

    # 400 / 4 = 100.00 >= 80.00 -> Allowed
    opt_4x = next(o for o in options if o.installments == 4)
    assert opt_4x.is_allowed is True

    # 400 / 5 = 80.00 >= 80.00 -> Allowed (exact boundary)
    opt_5x = next(o for o in options if o.installments == 5)
    assert opt_5x.is_allowed is True

    # 400 / 6 = 66.67 < 80.00 -> Disallowed
    opt_6x = next(o for o in options if o.installments == 6)
    assert opt_6x.is_allowed is False


def test_installments_7_to_12_min_100_reais():
    """Installments 7 to 12 require minimum installment of R$ 100.00."""
    price = Decimal("800.00")
    options = calculate_installments(price)

    # 800 / 8 = 100.00 >= 100.00 -> Allowed (exact boundary)
    opt_8x = next(o for o in options if o.installments == 8)
    assert opt_8x.is_allowed is True

    # 800 / 9 = 88.89 < 100.00 -> Disallowed
    opt_9x = next(o for o in options if o.installments == 9)
    assert opt_9x.is_allowed is False


def test_get_max_allowed_installments():
    """Returns the highest permitted installment tier for a product price."""
    price = Decimal("1299.00")
    # 1299 / 12 = 108.25 >= 100.00 -> Can go up to 12x
    best = get_max_allowed_installments(price)
    assert best is not None
    assert best.installments == 12
    assert best.is_allowed is True


# ============================================================================
# Return & Exchange Policy Tests
# ============================================================================


def test_return_withdrawal_online_within_7_days():
    """Online withdrawal within 7 days is fully eligible with store covering freight."""
    res = evaluate_return_eligibility(
        days_since_delivery=5, is_online_purchase=True, reason="arrependimento"
    )
    assert res.is_eligible is True
    assert res.freight_covered_by == "Loja"


def test_return_withdrawal_online_after_7_days():
    """Online withdrawal after 7 days is expired under CDC."""
    res = evaluate_return_eligibility(
        days_since_delivery=8, is_online_purchase=True, reason="arrependimento"
    )
    assert res.is_eligible is False


def test_return_withdrawal_in_person():
    """Withdrawal right under CDC Art. 49 only applies to remote purchases."""
    res = evaluate_return_eligibility(
        days_since_delivery=3, is_online_purchase=False, reason="arrependimento"
    )
    assert res.is_eligible is False


def test_return_defect_within_30_days():
    """Store exchanges products with manufacturing defects within 30 days."""
    res = evaluate_return_eligibility(days_since_delivery=20, reason="defeito")
    assert res.is_eligible is True
    assert res.deadline_days == 30


def test_return_defect_after_30_days_refers_to_manufacturer():
    """After 30 days, store refers client to manufacturer warranty."""
    res = evaluate_return_eligibility(days_since_delivery=45, reason="defeito")
    assert res.is_eligible is False
    assert "garantia do fabricante" in res.explanation.lower()


# ============================================================================
# Shipping Calculation Tests
# ============================================================================


def test_shipping_local_free_above_500():
    """Free shipping applies for orders >= R$ 500 in Campo Grande."""
    res = calculate_shipping(order_total=Decimal("599.90"), destination_city="Campo Grande")
    assert res.is_local is True
    assert res.is_free_shipping is True
    assert res.fee_brl == Decimal("0.00")
    assert "Motoboy" in res.delivery_method


def test_shipping_local_fixed_fee_under_500():
    """R$ 35 fixed fee applies for orders < R$ 500 in Campo Grande."""
    res = calculate_shipping(order_total=Decimal("429.90"), destination_city="Campo Grande")
    assert res.is_local is True
    assert res.is_free_shipping is False
    assert res.fee_brl == Decimal("35.00")


def test_shipping_other_cities():
    """Outside Campo Grande, external carriers (Correios / Jadlog) apply."""
    res = calculate_shipping(order_total=Decimal("1200.00"), destination_city="Dourados")
    assert res.is_local is False
    assert "Correios" in res.delivery_method
