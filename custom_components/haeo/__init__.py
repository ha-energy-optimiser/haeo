"""The Home Assistant Energy Optimization integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryNotReady

from .coordinator import HaeoDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

type HaeoConfigEntry = ConfigEntry[HaeoDataUpdateCoordinator | None]


async def async_setup_entry(hass: HomeAssistant, entry: HaeoConfigEntry) -> bool:
    """Set up Home Assistant Energy Optimization from a config entry."""
    _LOGGER.info("Setting up HAEO integration")

    # Store coordinator in runtime data first (required for platform setup)
    coordinator = HaeoDataUpdateCoordinator(hass, entry)
    entry.runtime_data = coordinator

    # Set up config entry update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    try:
        # Fetch initial data
        await coordinator.async_refresh()
    except Exception as ex:
        _LOGGER.exception("Failed to initialize HAEO integration")
        raise ConfigEntryNotReady from ex

    _LOGGER.info("HAEO integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HaeoConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading HAEO integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up coordinator
        entry.runtime_data = None

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: HaeoConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
