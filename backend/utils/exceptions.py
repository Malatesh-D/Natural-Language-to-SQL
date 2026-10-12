class QueryPilotError(Exception):
    """An expected, safe-to-display application error."""

class SQLValidationError(QueryPilotError):
    pass

class LLMConfigurationError(QueryPilotError):
    pass
