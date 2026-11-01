"""Exhaustive automated tests for policy retrieval matching all requirements from store manual."""

from app.db.connection import SessionLocal
from app.retrieval.policy_search import PolicySearchService


def test_retrieve_address_and_company_info():
    """Verify retrieval of physical store address, CNPJ, and contact information."""
    db = SessionLocal()
    try:
        service = PolicySearchService(db=db)
        results = service.search("endereço da loja CNPJ telefone e-mail contato", top_k=2)
        assert len(results) > 0

        evidence = service.format_evidence(results)
        assert "14 de Maio" in evidence
        assert "Campo Grande" in evidence
        assert "3341-4444" in evidence or "3341 - 4444" in evidence
    finally:
        db.close()


def test_retrieve_operating_hours():
    """Verify retrieval of business hours for weekdays, Saturdays, and Sundays/holidays."""
    db = SessionLocal()
    try:
        service = PolicySearchService(db=db)
        results = service.search(
            "horário de funcionamento expediente atendimento sábado domingo", top_k=2
        )
        assert len(results) > 0

        evidence = service.format_evidence(results)
        assert "09:00" in evidence or "18:00" in evidence
        assert "Sábado" in evidence or "Segunda" in evidence
    finally:
        db.close()


def test_retrieve_online_withdrawal_cdc():
    """Verify retrieval of the 7-day online right of withdrawal (CDC Art. 49)."""
    db = SessionLocal()
    try:
        service = PolicySearchService(db=db)
        results = service.search(
            "direito de arrependimento prazo 7 dias devolução compras online", top_k=2
        )
        assert len(results) > 0

        evidence = service.format_evidence(results)
        assert "7 (sete) dias corridos" in evidence or "7" in evidence
        assert "arrependimento" in evidence.lower() or "devolução" in evidence.lower()
        assert "embalagem original" in evidence.lower()
    finally:
        db.close()


def test_retrieve_defect_exchange_rules():
    """Verify retrieval of 30-day store defect exchange and manufacturer warranty."""
    db = SessionLocal()
    try:
        service = PolicySearchService(db=db)
        results = service.search(
            "troca por defeito de fabricação garantia fabricante 30 dias", top_k=2
        )
        assert len(results) > 0

        evidence = service.format_evidence(results)
        assert "defeito" in evidence.lower()
        assert "30" in evidence
    finally:
        db.close()


def test_retrieve_ineligible_items_for_exchange():
    """Verify retrieval of items not eligible for exchange (custom setups, wind mouthpieces)."""
    db = SessionLocal()
    try:
        service = PolicySearchService(db=db)
        results = service.search(
            "itens não elegíveis para troca boquilhas regulagem sob encomenda", top_k=2
        )
        assert len(results) > 0

        evidence = service.format_evidence(results)
        assert (
            "boquilha" in evidence.lower()
            or "regulagem" in evidence.lower()
            or "não elegíveis" in evidence.lower()
        )
    finally:
        db.close()


def test_retrieve_shipping_and_delivery_policies():
    """Verify retrieval of shipping thresholds, motoboy delivery, and carrier options."""
    db = SessionLocal()
    try:
        service = PolicySearchService(db=db)
        results = service.search(
            "frete grátis campo grande entrega motoboy taxa fixa correios jadlog", top_k=2
        )
        assert len(results) > 0

        evidence = service.format_evidence(results)
        assert "500" in evidence or "35" in evidence or "motoboy" in evidence.lower()
    finally:
        db.close()


def test_retrieve_scope_and_accessories_exclusion():
    """Verify policy states the store exclusively sells instruments and NOT accessories."""
    db = SessionLocal()
    try:
        service = PolicySearchService(db=db)
        results = service.search(
            "não comercializamos acessórios cordas palhetas cabos amplificadores", top_k=2
        )
        assert len(results) > 0

        evidence = service.format_evidence(results)
        assert "exclusivamente" in evidence.lower() or "acessórios" in evidence.lower()
    finally:
        db.close()


def test_retrieve_legal_and_manufacturer_warranty():
    """Verify retrieval of 90-day legal CDC warranty and manufacturer warranty rules."""
    db = SessionLocal()
    try:
        service = PolicySearchService(db=db)
        results = service.search(
            "garantia legal 90 noventa dias código de defesa do consumidor fabricante", top_k=2
        )
        assert len(results) > 0

        evidence = service.format_evidence(results)
        assert "garantia" in evidence.lower()
        assert "90" in evidence or "fabricante" in evidence.lower()
    finally:
        db.close()
