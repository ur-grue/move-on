from __future__ import annotations

from moveon.dpa import get_dpa, get_dpa_for_provider, list_countries


class TestDpaDatabase:
    def test_all_eu_countries(self):
        eu_codes = {
            "AT",
            "BE",
            "BG",
            "HR",
            "CY",
            "CZ",
            "DK",
            "EE",
            "FI",
            "FR",
            "DE",
            "GR",
            "HU",
            "IE",
            "IT",
            "LV",
            "LT",
            "LU",
            "MT",
            "NL",
            "PL",
            "PT",
            "RO",
            "SK",
            "SI",
            "ES",
            "SE",
        }
        codes = set(list_countries())
        assert eu_codes.issubset(codes)

    def test_eea_countries(self):
        codes = set(list_countries())
        assert "IS" in codes
        assert "LI" in codes
        assert "NO" in codes

    def test_uk_included(self):
        assert "GB" in list_countries()

    def test_total_count(self):
        assert len(list_countries()) == 31

    def test_get_dpa_germany(self):
        dpa = get_dpa("DE")
        assert dpa is not None
        assert dpa["country"] == "Germany"
        assert "bfdi" in dpa["email"]
        assert dpa["website"].startswith("https://")

    def test_get_dpa_case_insensitive(self):
        assert get_dpa("de") is not None
        assert get_dpa("De") is not None

    def test_get_dpa_unknown(self):
        assert get_dpa("XX") is None

    def test_france_no_email(self):
        dpa = get_dpa("FR")
        assert dpa is not None
        assert dpa["email"] is None
        assert "complaint_url" in dpa

    def test_all_have_required_fields(self):
        for code in list_countries():
            dpa = get_dpa(code)
            assert dpa is not None
            assert dpa["country"]
            assert dpa["country_code"]
            assert dpa["authority_name"]
            assert dpa["authority_name_en"]
            assert dpa["website"]
            assert dpa["phone"]


class TestDpaProviderRouting:
    def test_openai_routes_to_ireland(self):
        dpa = get_dpa_for_provider("openai")
        assert dpa is not None
        assert dpa["country_code"] == "IE"

    def test_mistral_routes_to_france(self):
        dpa = get_dpa_for_provider("mistral")
        assert dpa is not None
        assert dpa["country_code"] == "FR"

    def test_country_override(self):
        dpa = get_dpa_for_provider("openai", country="DE")
        assert dpa is not None
        assert dpa["country_code"] == "DE"

    def test_unknown_provider_no_country(self):
        assert get_dpa_for_provider("unknown_provider") is None

    def test_all_providers_have_jurisdiction(self):
        from moveon.dpa import PROVIDER_JURISDICTIONS
        from moveon.parsers import REGISTRY

        for provider in REGISTRY:
            assert provider in PROVIDER_JURISDICTIONS, (
                f"{provider} missing from PROVIDER_JURISDICTIONS"
            )
