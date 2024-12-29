from omegaconf.errors import ConfigKeyError

class MissingDescriptionError(Exception):
    """Custom exception for repositories missing descriptions."""
    pass

class PromptTemplateNotFoundError(ConfigKeyError):
    """Custom exception for missing templates."""
    pass

class ChatTemplateNotFoundError(FileNotFoundError):
    """Custom exception for missing templates."""
    pass

class GitHubApiKeyNotFoundError(ValueError):
    pass