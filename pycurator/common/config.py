"""Access and loading of deployment-specific settings."""

from pathlib import Path

from pydantic import BaseSettings

from pycurator.common.paths import DOTENV_PATH


class Settings(BaseSettings):
    """Application settings with defaults.

    See https://saurabh-kumar.com/python-dotenv/#file-format for .env format documentation.

    Attributes:
        ef_dir: Directory containing entity-fishing.
        ef_server: Slurm node to run entity-finishing on.
        gpt2_server: Machine running the GPT-2 server.
    """

    ef_dir: Path = Path("/nas/gaia/lestat/users/mdehaven/software2/nerd")
    ef_server: str = "saga28"
    gpt2_server: str = "sagalg02"

    class Config:
        """Model configuration."""

        allow_mutation = False
        env_file = DOTENV_PATH


settings = Settings()
