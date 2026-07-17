class DataUnavailableError(Exception):
    """Raised when a data-layer call can't return usable data (bad symbol, provider
    outage, missing credential, etc). Pages catch this and render an inline message
    instead of crashing the callback."""
