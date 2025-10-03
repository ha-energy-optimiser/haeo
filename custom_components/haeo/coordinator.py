"""Data update coordinator for the Home Assistant Energy Optimization integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_POWER,
    CONF_HORIZON_HOURS,
    CONF_PERIOD_MINUTES,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    OPTIMIZATION_STATUS_FAILED,
    OPTIMIZATION_STATUS_PENDING,
    OPTIMIZATION_STATUS_SUCCESS,
)
from .data_loader import DataLoader
from .model import Network

_LOGGER = logging.getLogger(__name__)


def _calculate_time_parameters(horizon_hours: int, period_minutes: int) -> tuple[int, int]:
    """Calculate period in seconds and number of periods from horizon and period configuration.

    Args:
        horizon_hours: Optimization horizon in hours
        period_minutes: Optimization period in minutes

    Returns:
        Tuple of (period_seconds, n_periods)

    """
    period_seconds = period_minutes * 60  # Convert minutes to seconds
    horizon_seconds = horizon_hours * 3600  # Convert hours to seconds
    n_periods = horizon_seconds // period_seconds
    return period_seconds, n_periods


class HaeoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data update coordinator for HAEO integration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.config = entry.data
        self.network: Network | None = None
        self.optimization_result: dict[str, Any] | None = None
        self.optimization_status = OPTIMIZATION_STATUS_PENDING
        self.data_loader = DataLoader(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )

    def get_future_timestamps(self) -> list[str]:
        """Get list of ISO timestamps for each optimization period."""
        if not self.optimization_result or not self.network:
            return []

        start_time = self.optimization_result["timestamp"]
        timestamps = []

        for i in range(self.network.n_periods):
            period_time = start_time + timedelta(seconds=self.network.period * i)
            timestamps.append(period_time.isoformat())

        return timestamps

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data from Home Assistant entities and run optimization."""
        try:
            # Calculate time parameters from configuration
            period_seconds, n_periods = _calculate_time_parameters(
                self.config[CONF_HORIZON_HOURS],
                self.config[CONF_PERIOD_MINUTES],
            )

            # Create new network with current sensor data (includes sensor availability check)
            self.network = await self.data_loader.load_network_data(self.entry, period_seconds, n_periods)

            # Check if sensor data is available
            if not getattr(self.network, "_sensor_data_available", True):
                self.optimization_status = OPTIMIZATION_STATUS_FAILED
                _LOGGER.warning("Required sensor data not available, skipping optimization")
                # Don't raise UpdateFailed here - let the sensors show as unavailable
                return None

            # Run optimization on the new network
            if not self.network:
                raise RuntimeError("Network not initialized")

            _LOGGER.debug("Running optimization for network with %d elements", len(self.network.elements))

            try:
                cost = self.network.optimize()
            except Exception as ex:
                _LOGGER.error("Optimization failed: %s", ex)
                raise

            self.optimization_result = {
                "cost": cost,
                "timestamp": dt_util.utcnow(),
            }
            self.optimization_status = OPTIMIZATION_STATUS_SUCCESS

            _LOGGER.debug("Optimization completed successfully with cost: %s", cost)

            return self.optimization_result

        except Exception as ex:
            self.optimization_status = OPTIMIZATION_STATUS_FAILED
            _LOGGER.error("Failed to update HAEO data: %s", ex)
            raise UpdateFailed(f"Error updating HAEO data: {ex}") from ex

    def get_element_data(self, element_name: str) -> dict[str, Any] | None:
        """Get data for a specific element directly from the network."""
        if not self.network or element_name not in self.network.elements:
            return None

        from pulp import value

        element = self.network.elements[element_name]
        element_data = {}

        # Helper to extract values safely
        def extract_values(variables):
            result = []
            for var in variables:
                val = value(var)
                result.append(float(val) if isinstance(val, (int, float)) else 0.0)
            return result

        # Get power values (net power, can be positive or negative)
        if hasattr(element, "power") and element.power is not None:
            # Connections have a single power attribute (net flow)
            element_data[ATTR_POWER] = extract_values(element.power)
        elif hasattr(element, "power_consumption") and element.power_consumption is not None:
            # Elements like batteries have separate consumption and production
            consumption = extract_values(element.power_consumption)
            production = (
                extract_values(element.power_production)
                if hasattr(element, "power_production") and element.power_production is not None
                else [0.0] * len(consumption)
            )
            # Net power = production - consumption (positive = net production, negative = net consumption)
            element_data[ATTR_POWER] = [p - c for p, c in zip(production, consumption, strict=False)]

        if hasattr(element, "energy") and element.energy is not None:
            element_data["energy"] = extract_values(element.energy)

        return element_data if element_data else None

    @property
    def last_optimization_cost(self) -> float | None:
        """Get the last optimization cost."""
        if self.optimization_result:
            return self.optimization_result["cost"]
        return None

    @property
    def last_optimization_time(self) -> Any | None:
        """Get the last optimization timestamp."""
        if self.optimization_result:
            return self.optimization_result["timestamp"]
        return None
