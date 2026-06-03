"""Project-specific exceptions."""


class PDDLMCPError(Exception):
    """Base class for recoverable PDDL MCP errors."""


class ConfigurationError(PDDLMCPError):
    """Raised when required configuration is missing or invalid."""


class PlannerError(PDDLMCPError):
    """Raised when the external planner fails unexpectedly."""


class ModelingError(PDDLMCPError):
    """Raised when PDDL generation cannot produce a usable model."""
