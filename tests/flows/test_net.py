"""Test data and validation for net flow configuration."""

# Test data for net flow
VALID_DATA = [
    {
        "description": "Basic net configuration",
        "config": {},
    },
]

INVALID_DATA = [
    {
        "description": "Empty config should fail validation",
        "config": {},
        "error": "cannot be empty",
    },
]
