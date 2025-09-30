"""Config flow for Home Assistant Energy Optimization integration."""

from __future__ import annotations

from .flows.hub import HubConfigFlow

# Main config flow class for the integration
HaeoConfigFlow = HubConfigFlow
