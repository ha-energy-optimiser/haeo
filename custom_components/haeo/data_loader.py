"""Sensor data loading system using Home Assistant's SensorDeviceClass and unit conversion."""

from __future__ import annotations

from dataclasses import fields
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor.const import DEVICE_CLASS_UNITS, UNIT_CONVERTERS, SensorDeviceClass
import numpy as np

from .const import CONF_ELEMENT_TYPE, FIELD_TYPE_CONSTANT, FIELD_TYPE_FORECAST, FIELD_TYPE_SENSOR
from .model import Network
from .types import ELEMENT_TYPES

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    # Union type for field values that can be either configuration objects or actual values
    FieldValue = (
        str  # sensor entity IDs
        | list[str]  # list of sensor entity IDs
        | float  # constant numeric values
        | list[float]  # list of constant numeric values
        | bool  # constant boolean values
        | list[bool]  # list of constant boolean values
        | None  # None values
    )

_LOGGER = logging.getLogger(__name__)


# Unit conversion functions
def convert_to_base_unit(value: float, from_unit: str | None, device_class: SensorDeviceClass) -> float:
    """Convert a value to base unit using Home Assistant converters."""
    if device_class in [SensorDeviceClass.MONETARY, SensorDeviceClass.BATTERY]:
        # MONETARY and BATTERY don't need unit conversion (already in correct units)
        return value
    if device_class in UNIT_CONVERTERS:
        converter = UNIT_CONVERTERS[device_class]
        # Get the appropriate base unit for this device class
        if device_class == SensorDeviceClass.POWER:
            return converter.convert(value, from_unit, "W")
        if device_class in [SensorDeviceClass.ENERGY, SensorDeviceClass.ENERGY_STORAGE]:
            return converter.convert(value, from_unit, "Wh")
        # Use the first valid unit as base
        valid_units = DEVICE_CLASS_UNITS.get(device_class, set())
        base_unit = next(iter(valid_units)) if valid_units else None
        if base_unit:
            return converter.convert(value, from_unit, base_unit)
    # For types without converters, return as-is
    return value


# Field type detection functions
def get_field_type(field_name: str, config_class: type) -> tuple[SensorDeviceClass | str, str]:
    """Get the field type from metadata.

    Args:
        field_name: Name of the field to get type for
        config_class: The configuration class containing the field

    Returns:
        Tuple of (device_class_or_type, property_type)

    Raises:
        ValueError: If field_type is not specified in metadata

    """
    for field_info in fields(config_class):
        if field_info.name == field_name:
            # field_type must be specified in metadata
            field_type = field_info.metadata.get("field_type")
            if field_type is None:
                msg = f"Field '{field_name}' in {config_class.__name__} must have 'field_type' specified in metadata"
                raise ValueError(
                    msg,
                )

            return field_type

    msg = f"Field '{field_name}' not found in {config_class.__name__}"
    raise ValueError(msg)


def get_field_device_class(field_name: str, config_class: type) -> SensorDeviceClass | str:
    """Get the device class from field type tuple."""
    field_type = get_field_type(field_name, config_class)
    return field_type[0]


def get_field_property_type(field_name: str, config_class: type) -> str:
    """Get the property type (constant, sensor, forecast) from field type tuple."""
    field_type = get_field_type(field_name, config_class)
    return field_type[1]


def is_sensor_field(field_name: str, config_class: type) -> bool:
    """Check if a field is sensor-based (not a constant)."""
    try:
        property_type = get_field_property_type(field_name, config_class)
        return property_type in [FIELD_TYPE_SENSOR, FIELD_TYPE_FORECAST]
    except ValueError:
        # If field_type is not properly defined, assume it's not a sensor field
        return False


def is_forecast_field(field_name: str, config_class: type | None = None) -> bool:
    """Check if a field represents forecast data."""
    if config_class:
        try:
            property_type = get_field_property_type(field_name, config_class)
            return property_type == FIELD_TYPE_FORECAST
        except ValueError:
            # If field_type is not properly defined, fall back to name-based detection
            return "forecast" in field_name.lower()

    # Fallback to name-based detection (for backward compatibility)
    return "forecast" in field_name.lower()


def is_constant_field(field_name: str, config_class: type) -> bool:
    """Check if a field is a constant value (not sensor-based)."""
    try:
        property_type = get_field_property_type(field_name, config_class)
        return property_type == FIELD_TYPE_CONSTANT
    except ValueError:
        # If field_type is not properly defined, assume it's not a constant field
        return False


class DataLoader:
    """Generic data loading system for HAEO that handles all schema types."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the data loader."""
        self.hass = hass

    async def load_network_data(self, config_entry: ConfigEntry, period_seconds: int, n_periods: int) -> Network:
        """Load complete network data from configuration entry.

        Args:
            config_entry: The configuration entry containing participants and settings
            period_seconds: Time period in seconds for optimization
            n_periods: Number of time periods for the optimization horizon

        Returns:
            A fully populated Network object with all elements and their data loaded

        """
        # Create network with configured horizon and period
        network = Network(
            name=f"haeo_network_{config_entry.entry_id}",
            period=period_seconds,
            n_periods=n_periods,
        )

        # Get participants from configuration
        participants = config_entry.data.get("participants", {})

        if not participants:
            _LOGGER.warning("No participants configured for hub")
            return network

        # Check sensor availability first
        sensor_data_available = self._check_sensor_data_availability(config_entry)

        # Load all elements from participants
        for element_name, element_config in participants.items():
            await self._load_element_data(network, element_name, element_config, n_periods)

        # Store sensor availability status in the network for the coordinator to use
        network.sensor_data_available = sensor_data_available

        return network

    def _check_sensor_data_availability(self, config_entry: ConfigEntry) -> bool:
        """Check if all required sensor data is available for optimization.

        Args:
            config_entry: The configuration entry containing participants and settings

        Returns:
            True if all required sensor data is available, False otherwise

        """
        config = config_entry.data
        participants = config.get("participants", {})

        for element_name, element_config in participants.items():
            element_type = element_config[CONF_ELEMENT_TYPE]
            config_class = ELEMENT_TYPES.get(element_type)

            if not config_class:
                continue

            # Check all sensor fields using the types system
            for field_info in fields(config_class):
                field_name = field_info.name

                # Skip element_type and constant fields
                if field_name == "element_type" or is_constant_field(field_name, config_class):
                    continue

                # Get field value from configuration
                field_value = element_config.get(field_name)

                # Check if this is a sensor field that needs data
                if is_sensor_field(field_name, config_class) and field_value:
                    if isinstance(field_value, str):
                        sensor_ids = [field_value]
                    elif isinstance(field_value, list) and field_value and isinstance(field_value[0], str):
                        sensor_ids = field_value
                    else:
                        # Skip non-string values (constants, etc.)
                        continue

                    # Check if all sensors are available
                    for sensor_id in sensor_ids:
                        if not self._is_sensor_available(sensor_id, f"{element_name} {field_name}"):
                            return False

        return True

    def _is_sensor_available(self, sensor_id: str, context: str) -> bool:
        """Check if a sensor is available and has valid state."""
        state = self.hass.states.get(sensor_id)
        if not state or state.state in ["unknown", "unavailable", "none"]:
            _LOGGER.warning(
                "%s sensor %s not available (state: %s)",
                context,
                sensor_id,
                state.state if state else "not found",
            )
            return False
        return True

    async def _load_element_data(
        self,
        network: Network,
        element_name: str,
        element_config: dict[str, Any],
        n_periods: int,
    ) -> None:
        """Load data for a single element and add it to the network.

        Args:
            network: The network to add the element to
            element_name: Name of the element
            element_config: Configuration for the element
            n_periods: Number of time periods for the optimization

        """
        element_type = element_config.get(CONF_ELEMENT_TYPE)
        config_class = ELEMENT_TYPES.get(element_type)

        if not config_class:
            _LOGGER.error("Unknown element type: %s", element_type)
            return

        element_params = {}

        # Process all fields from the configuration class
        for field_info in fields(config_class):
            field_name = field_info.name

            # Skip element_type field
            if field_name == "element_type":
                continue

            # Get field value from configuration
            field_value = element_config.get(field_name)

            # Load field value using the data loading system
            loaded_value = await self.load_field_data(field_name, field_value, config_class, n_periods)

            if loaded_value is not None:
                element_params[field_name] = loaded_value

        _LOGGER.debug(
            "Adding element: %s (%s) with params: %s",
            element_name,
            element_type,
            list(element_params.keys()),
        )

        try:
            network.add(element_type, element_name, **element_params)
        except Exception:
            _LOGGER.exception("Failed to add element %s", element_name)
            raise

    async def load_field_data(
        self,
        field_name: str,
        field_value: FieldValue,
        config_class: type,
        n_periods: int | None = None,
    ) -> FieldValue | None:
        """Load field data based on its type and return populated data.

        Args:
            field_name: Name of the field to load
            field_value: The field value from configuration (could be sensor ID(s), constant, etc.)
            config_class: The configuration class for the element type
            n_periods: Number of periods for forecast data (uses 1 for current values if None)

        Returns:
            The loaded field value (sensor data, forecast data, or constants as-is)

        """
        if n_periods is None:
            n_periods = 1

        # Get field type information
        try:
            field_type = get_field_type(field_name, config_class)
            device_class, property_type = field_type
        except ValueError:
            # If field_type is not properly defined, return as-is
            return field_value

        # Handle different field types
        if property_type == FIELD_TYPE_CONSTANT:
            return field_value

        if property_type in [FIELD_TYPE_SENSOR, FIELD_TYPE_FORECAST]:
            return await self._load_sensor_field_data(field_value, property_type, device_class, n_periods)

        return field_value

    async def _load_sensor_field_data(
        self,
        field_value: FieldValue,
        property_type: str,
        device_class: SensorDeviceClass | str,
        n_periods: int,
    ) -> FieldValue | None:
        """Load sensor or forecast field data."""
        sensor_ids = self._extract_sensor_ids(field_value)
        if not sensor_ids:
            return field_value

        if property_type == FIELD_TYPE_FORECAST:
            return await self.load_sensor_forecast(sensor_ids, n_periods)

        # For single-value sensor fields, sum all sensor values
        return await self._sum_sensor_values(sensor_ids, device_class)

    def _extract_sensor_ids(self, field_value: FieldValue) -> list[str] | None:
        """Extract sensor IDs from field value."""
        if isinstance(field_value, list):
            # Check if it's a list of sensor IDs (strings) or constant values (numbers)
            if field_value and isinstance(field_value[0], str):
                return field_value
            # It's a list of constant values, return None to indicate no sensors
            return None
        if isinstance(field_value, str):
            return [field_value]

        # Single constant value or other type
        return None

    async def _sum_sensor_values(self, sensor_ids: list[str], device_class: SensorDeviceClass | str) -> float | None:
        """Sum values from multiple sensors."""
        total_value = None
        for sensor_id in sensor_ids:
            sensor_value = await self.load_sensor_value(sensor_id)
            if sensor_value is not None:
                total_value = total_value + sensor_value if total_value is not None else sensor_value
        return total_value

    async def _load_current_sensor_values(
        self,
        sensor_ids: list[str],
        device_class: str | SensorDeviceClass,
        n_periods: int,
    ) -> list[float] | None:
        """Load current values from sensors and repeat for all periods."""
        total_value = None

        for sensor_id in sensor_ids:
            sensor_value = await self.load_sensor_value(sensor_id)
            if sensor_value is not None:
                total_value = total_value + sensor_value if total_value is not None else sensor_value

        # Return as list repeated for all periods, or single value if n_periods=1
        if total_value is not None:
            if n_periods == 1:
                return [total_value]  # Return as single-element list for consistency
            return [total_value] * n_periods
        return None

    async def load_sensor_value(
        self,
        sensor_id: str,
    ) -> float | None:
        """Load current value from a sensor and convert to base units."""
        state = self.hass.states.get(sensor_id)
        if not state or state.state in ["unknown", "unavailable", "none"]:
            _LOGGER.warning("Sensor %s not available (state: %s)", sensor_id, state.state if state else "not found")
            return None

        try:
            value = float(state.state)
            # Convert to base units if we know the device class from the sensor
            device_class = state.attributes.get("device_class")
            if device_class and device_class in [
                SensorDeviceClass.POWER,
                SensorDeviceClass.ENERGY,
                SensorDeviceClass.ENERGY_STORAGE,
                SensorDeviceClass.MONETARY,
                SensorDeviceClass.BATTERY,
            ]:
                unit = state.attributes.get("unit_of_measurement")
                value = convert_to_base_unit(value, unit, device_class)
            return value
        except (ValueError, TypeError):
            _LOGGER.exception("Invalid numeric value in sensor %s", sensor_id)
            return None

    async def load_sensor_forecast(
        self,
        sensor_ids: str | list[str],
        n_periods: int,
    ) -> list[float] | None:
        """Load forecast data from sensor(s) and combine them."""
        if isinstance(sensor_ids, str):
            sensor_ids = [sensor_ids]

        if not sensor_ids:
            return None

        combined_forecast = None

        for sensor_id in sensor_ids:
            state = self.hass.states.get(sensor_id)
            if not state:
                _LOGGER.warning("Forecast sensor %s not found", sensor_id)
                continue

            # Try to get forecast from attributes first
            forecast_attr = state.attributes.get("forecast")
            if forecast_attr and isinstance(forecast_attr, list):
                try:
                    raw_forecast = forecast_attr[:n_periods]
                    _LOGGER.debug("Raw forecast for %s: %d values", sensor_id, len(raw_forecast))
                    sensor_forecast = [float(x) for x in raw_forecast]
                    _LOGGER.debug("Converted forecast for %s: %d values", sensor_id, len(sensor_forecast))
                    # Convert to base units using sensor's device class if available
                    sensor_device_class = state.attributes.get("device_class")
                    if sensor_device_class and sensor_device_class in [
                        SensorDeviceClass.POWER,
                        SensorDeviceClass.ENERGY,
                        SensorDeviceClass.ENERGY_STORAGE,
                        SensorDeviceClass.MONETARY,
                        SensorDeviceClass.BATTERY,
                    ]:
                        unit = state.attributes.get("unit_of_measurement")
                        sensor_forecast = [convert_to_base_unit(x, unit, sensor_device_class) for x in sensor_forecast]
                    # Resample to desired number of periods if needed
                    _LOGGER.debug(
                        "Forecast data for %s: %d values, target: %d",
                        sensor_id,
                        len(sensor_forecast),
                        n_periods,
                    )
                    if len(sensor_forecast) != n_periods:
                        sensor_forecast = self._resample_forecast(sensor_forecast, n_periods)
                    _LOGGER.debug("Loaded forecast for %s: %d values", sensor_id, len(sensor_forecast))
                except (ValueError, TypeError):
                    _LOGGER.exception("Invalid forecast data in sensor %s", sensor_id)
                    # Fall back to current state value when forecast is invalid
                    sensor_forecast = self._get_repeated_value(state, sensor_id, n_periods)
            else:
                # Fallback: repeat current state value
                sensor_forecast = self._get_repeated_value(state, sensor_id, n_periods)

            if sensor_forecast:
                if combined_forecast is None:
                    combined_forecast = sensor_forecast
                else:
                    # Sum the forecasts element-wise
                    combined_forecast = [a + b for a, b in zip(combined_forecast, sensor_forecast, strict=False)]

        return combined_forecast

    def _resample_forecast(self, forecast: list[float], target_periods: int) -> list[float]:
        """Resample forecast to target number of periods using numpy interpolation."""
        if len(forecast) == target_periods:
            return forecast
        if len(forecast) == 0:
            return [0.0] * target_periods
        if len(forecast) == 1:
            # Single value, repeat for all periods
            return [forecast[0]] * target_periods

        # Use numpy interpolation for resampling
        source_indices = np.arange(len(forecast))
        target_indices = np.linspace(0, len(forecast) - 1, target_periods)

        resampled_values = np.interp(target_indices, source_indices, forecast)
        return resampled_values.tolist()

    def _get_repeated_value(self, state: Any, sensor_id: str, n_periods: int) -> list[float] | None:
        """Get repeated current state value for forecast periods."""
        try:
            current_value = float(state.state)
            # Convert to base units using sensor's device class
            device_class = state.attributes.get("device_class")
            if device_class and device_class in [
                SensorDeviceClass.POWER,
                SensorDeviceClass.ENERGY,
                SensorDeviceClass.ENERGY_STORAGE,
                SensorDeviceClass.MONETARY,
                SensorDeviceClass.BATTERY,
            ]:
                unit = state.attributes.get("unit_of_measurement")
                current_value = convert_to_base_unit(current_value, unit, device_class)
            return [current_value] * n_periods
        except (ValueError, TypeError):
            _LOGGER.exception("Invalid state value in sensor %s", sensor_id)
            return None
