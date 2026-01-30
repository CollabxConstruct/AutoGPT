from backend.integrations.providers import ProviderName


class TestProviderName:
    def test_known_provider(self):
        assert ProviderName.GITHUB == "github"
        assert ProviderName.GITHUB.value == "github"

    def test_missing_provider_creates_pseudo_member(self):
        custom = ProviderName("custom_provider")
        assert custom.value == "custom_provider"
        assert custom.name == "CUSTOM_PROVIDER"
        assert isinstance(custom, ProviderName)

    def test_missing_provider_non_string(self):
        result = ProviderName._missing_(123)
        assert result is None
