"""Base classes and utilities for HAEO config flows."""

from __future__ import annotations

import logging

import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

# Optimized validators using voluptuous built-ins
validate_element_name = vol.All(str, vol.Strip, vol.Length(min=1, msg="Name cannot be empty"))
validate_positive_number = vol.All(
    vol.Coerce(float), vol.Range(min=0, min_included=False, msg="Value must be positive")
)
validate_percentage = vol.All(vol.Coerce(float), vol.Range(min=0, max=100, msg="Value must be between 0 and 100"))
validate_efficiency = vol.All(
    vol.Coerce(float), vol.Range(min=0, max=1, min_included=False, msg="Efficiency must be between 0 and 1")
)
validate_non_negative_number = vol.All(vol.Coerce(float), vol.Range(min=0, msg="Value must be non-negative"))
