from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from app.config import get_settings


class SecretResolutionError(RuntimeError):
    pass


class SecretResolver:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: SecretClient | None = None

    def get_linkedin_credentials(self) -> tuple[str, str]:
        email = self._get_secret(
            inline_value=self.settings.linkedin_email,
            secret_name=self.settings.linkedin_email_secret_name,
            label="LinkedIn email",
        )
        password = self._get_secret(
            inline_value=self.settings.linkedin_password,
            secret_name=self.settings.linkedin_password_secret_name,
            label="LinkedIn password",
        )
        return email, password

    def _get_secret(self, *, inline_value: str, secret_name: str, label: str) -> str:
        if inline_value:
            return inline_value

        client = self._get_client()
        if client is None:
            raise SecretResolutionError(
                f"{label} is not configured. Set {secret_name} in Azure Key Vault or provide an env override."
            )

        secret = client.get_secret(secret_name)
        if not secret.value:
            raise SecretResolutionError(f"{label} secret '{secret_name}' is empty")
        return secret.value

    def _get_client(self) -> SecretClient | None:
        if not self.settings.key_vault_url:
            return None
        if self._client is None:
            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=self.settings.key_vault_url, credential=credential)
        return self._client