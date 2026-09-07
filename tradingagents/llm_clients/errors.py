"""Errors whose output contracts must not be weakened by agent fallbacks."""


class RequiredStructuredOutputError(ValueError):
    """A provider exhausted validated JSON generation; free text is not safe."""
