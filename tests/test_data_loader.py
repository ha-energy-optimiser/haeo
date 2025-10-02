"""Test the HAEO sensor loader."""

import pytest
from unittest.mock import Mock
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor.const import SensorDeviceClass
from dataclasses import dataclass, field

from custom_components.haeo.data_loader import (
    DataLoader,
    get_field_type,
    get_field_device_class,
    get_field_property_type,
    is_sensor_field,
    is_forecast_field,
    is_constant_field,
    convert_to_base_unit,
)


# Mock configuration classes for testing field type detection
@dataclass
class MockConfigWithBatterySensor:
    """Mock config class with battery sensor field."""

    current_charge_sensor: str = field(metadata={"field_type": (SensorDeviceClass.BATTERY, "sensor")})


@dataclass
class MockConfigWithPriceSensor:
    """Mock config class with price sensor field."""

    price_import_sensor: str = field(metadata={"field_type": (SensorDeviceClass.MONETARY, "sensor")})


@dataclass
class MockConfigWithPowerSensor:
    """Mock config class with power sensor field."""

    forecast_sensors: str = field(metadata={"field_type": (SensorDeviceClass.POWER, "forecast")})


@dataclass
class MockConfigWithBatterySOC:
    """Mock config class with battery SOC field."""

    min_charge_percentage: float = field(metadata={"field_type": (SensorDeviceClass.BATTERY, "constant")})


@dataclass
class MockConfigWithEfficiency:
    """Mock config class with efficiency field."""

    efficiency: float = field(metadata={"field_type": ("%", "constant")})


@dataclass
class MockConfigWithCapacity:
    """Mock config class with capacity field."""

    capacity: float = field(metadata={"field_type": ("capacity", "constant")})


# Field type detection tests
async def test_get_field_type_battery_sensor(hass: HomeAssistant):
    """Test field type detection for battery sensor."""
    field_type = get_field_type("current_charge_sensor", MockConfigWithBatterySensor)
    assert field_type == (SensorDeviceClass.BATTERY, "sensor")


async def test_get_field_type_battery_soc_field(hass: HomeAssistant):
    """Test field type detection for battery SOC field."""
    field_type = get_field_type("min_charge_percentage", MockConfigWithBatterySOC)
    assert field_type == (SensorDeviceClass.BATTERY, "constant")


async def test_get_field_type_efficiency_field(hass: HomeAssistant):
    """Test field type detection for efficiency field."""
    field_type = get_field_type("efficiency", MockConfigWithEfficiency)
    assert field_type == ("%", "constant")


async def test_get_field_type_price_sensor(hass: HomeAssistant):
    """Test field type detection for price sensor."""
    field_type = get_field_type("price_import_sensor", MockConfigWithPriceSensor)
    assert field_type == (SensorDeviceClass.MONETARY, "sensor")


async def test_get_field_type_power_sensor(hass: HomeAssistant):
    """Test field type detection for power sensor."""
    field_type = get_field_type("forecast_sensors", MockConfigWithPowerSensor)
    assert field_type == (SensorDeviceClass.POWER, "forecast")


# New helper function tests
async def test_get_field_device_class(hass: HomeAssistant):
    """Test getting device class from field type."""
    device_class = get_field_device_class("current_charge_sensor", MockConfigWithBatterySensor)
    assert device_class == SensorDeviceClass.BATTERY

    device_class = get_field_device_class("efficiency", MockConfigWithEfficiency)
    assert device_class == "%"


async def test_get_field_property_type(hass: HomeAssistant):
    """Test getting property type from field type."""
    property_type = get_field_property_type("current_charge_sensor", MockConfigWithBatterySensor)
    assert property_type == "sensor"

    property_type = get_field_property_type("min_charge_percentage", MockConfigWithBatterySOC)
    assert property_type == "constant"


async def test_get_field_type_unknown_field(hass: HomeAssistant):
    """Test field type detection for unknown field."""
    with pytest.raises(ValueError, match="Field 'unknown_field' not found"):
        get_field_type("unknown_field", MockConfigWithBatterySensor)


# Field classification tests
async def test_is_sensor_field_true(hass: HomeAssistant):
    """Test sensor field detection for sensor fields."""
    assert is_sensor_field("current_charge_sensor", MockConfigWithBatterySensor) is True
    assert is_sensor_field("price_import_sensor", MockConfigWithPriceSensor) is True
    assert is_sensor_field("forecast_sensors", MockConfigWithPowerSensor) is True


async def test_is_sensor_field_false(hass: HomeAssistant):
    """Test sensor field detection for non-sensor fields."""
    assert is_sensor_field("capacity", MockConfigWithCapacity) is False
    assert is_sensor_field("min_charge_percentage", MockConfigWithBatterySOC) is False
    assert is_sensor_field("efficiency", MockConfigWithEfficiency) is False


async def test_is_forecast_field_true(hass: HomeAssistant):
    """Test forecast field detection for forecast fields."""
    assert is_forecast_field("forecast_sensors") is True
    assert is_forecast_field("price_import_forecast_sensor") is True


async def test_is_forecast_field_false(hass: HomeAssistant):
    """Test forecast field detection for non-forecast fields."""
    assert is_forecast_field("current_charge_sensor") is False
    assert is_forecast_field("capacity") is False


async def test_is_constant_field_true(hass: HomeAssistant):
    """Test constant field detection for constant fields."""
    assert is_constant_field("capacity", MockConfigWithCapacity) is True
    assert is_constant_field("min_charge_percentage", MockConfigWithBatterySOC) is True


async def test_is_constant_field_false(hass: HomeAssistant):
    """Test constant field detection for sensor fields."""
    assert is_constant_field("current_charge_sensor", MockConfigWithBatterySensor) is False


# Unit conversion tests
async def test_convert_battery_percentage(hass: HomeAssistant):
    """Test unit conversion for battery percentage (no conversion needed)."""
    result = convert_to_base_unit(75.5, "%", SensorDeviceClass.BATTERY)
    assert result == 75.5


async def test_convert_monetary_price(hass: HomeAssistant):
    """Test unit conversion for monetary price (no conversion needed)."""
    result = convert_to_base_unit(0.25, "$/kWh", SensorDeviceClass.MONETARY)
    assert result == 0.25


async def test_convert_power_kw_to_w(hass: HomeAssistant):
    """Test unit conversion for power from kW to W."""
    result = convert_to_base_unit(1000, "kW", SensorDeviceClass.POWER)
    assert result == 1000000.0


async def test_convert_power_w_to_w(hass: HomeAssistant):
    """Test unit conversion for power from W to W (no conversion needed)."""
    result = convert_to_base_unit(1000, "W", SensorDeviceClass.POWER)
    assert result == 1000.0


async def test_convert_energy_kwh_to_wh(hass: HomeAssistant):
    """Test unit conversion for energy from kWh to Wh."""
    result = convert_to_base_unit(5, "kWh", SensorDeviceClass.ENERGY)
    assert result == 5000.0


async def test_convert_energy_wh_to_wh(hass: HomeAssistant):
    """Test unit conversion for energy from Wh to Wh (no conversion needed)."""
    result = convert_to_base_unit(5000, "Wh", SensorDeviceClass.ENERGY)
    assert result == 5000.0


async def test_convert_unknown_device_class(hass: HomeAssistant):
    """Test unit conversion for unknown device class (returns as-is)."""
    result = convert_to_base_unit(42, "unknown", "unknown_device_class")
    assert result == 42


# SensorDataLoader tests
@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = Mock(spec=HomeAssistant)
    hass.states = Mock()
    return hass


@pytest.fixture
def sensor_loader(mock_hass):
    """Create a DataLoader instance."""
    return DataLoader(mock_hass)


async def test_load_sensor_value_available_power(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading available power sensor value."""
    # Mock sensor state
    mock_state = Mock()
    mock_state.state = "1000"
    mock_state.attributes = {"device_class": SensorDeviceClass.POWER, "unit_of_measurement": "W"}
    mock_hass.states.get.return_value = mock_state

    result = await sensor_loader.load_sensor_value("sensor.test_power", SensorDeviceClass.POWER)
    assert result == 1000.0


async def test_load_sensor_value_available_energy(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading available energy sensor value."""
    # Mock sensor state
    mock_state = Mock()
    mock_state.state = "5.5"
    mock_state.attributes = {"device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": "kWh"}
    mock_hass.states.get.return_value = mock_state

    result = await sensor_loader.load_sensor_value("sensor.test_energy", SensorDeviceClass.ENERGY)
    assert result == 5500.0  # 5.5 kWh = 5500 Wh


async def test_load_sensor_value_available_battery(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading available battery sensor value."""
    # Mock sensor state
    mock_state = Mock()
    mock_state.state = "75"
    mock_state.attributes = {"device_class": SensorDeviceClass.BATTERY, "unit_of_measurement": "%"}
    mock_hass.states.get.return_value = mock_state

    result = await sensor_loader.load_sensor_value("sensor.test_battery", SensorDeviceClass.BATTERY)
    assert result == 75.0


async def test_load_sensor_value_unavailable_sensor(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading value from unavailable sensor."""
    mock_hass.states.get.return_value = None

    result = await sensor_loader.load_sensor_value("sensor.unavailable", SensorDeviceClass.POWER)
    assert result is None


async def test_load_sensor_value_unknown_state(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading value from sensor with unknown state."""
    mock_state = Mock()
    mock_state.state = "unknown"
    mock_hass.states.get.return_value = mock_state

    result = await sensor_loader.load_sensor_value("sensor.unknown", SensorDeviceClass.POWER)
    assert result is None


async def test_load_sensor_value_invalid_number(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading value from sensor with invalid number."""
    mock_state = Mock()
    mock_state.state = "not_a_number"
    mock_hass.states.get.return_value = mock_state

    result = await sensor_loader.load_sensor_value("sensor.invalid", SensorDeviceClass.POWER)
    assert result is None


async def test_load_sensor_forecast_with_forecast_attribute(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading forecast data from sensor with forecast attribute."""
    # Mock sensor state with forecast
    mock_state = Mock()
    mock_state.state = "100"
    mock_state.attributes = {
        "device_class": SensorDeviceClass.POWER,
        "unit_of_measurement": "W",
        "forecast": [100, 200, 300, 400, 500],
    }
    mock_hass.states.get.return_value = mock_state

    result = await sensor_loader.load_sensor_forecast("sensor.test", "power", 3)
    assert result == [100, 200, 300]


async def test_load_sensor_forecast_without_forecast_attribute(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading forecast data from sensor without forecast attribute."""
    # Mock sensor state without forecast
    mock_state = Mock()
    mock_state.state = "150"
    mock_state.attributes = {"device_class": SensorDeviceClass.POWER, "unit_of_measurement": "W"}
    mock_hass.states.get.return_value = mock_state

    result = await sensor_loader.load_sensor_forecast("sensor.test", "power", 3)
    assert result == [150, 150, 150]  # Repeated current value


async def test_load_sensor_forecast_missing_sensor(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading forecast data from missing sensor."""
    mock_hass.states.get.return_value = None

    result = await sensor_loader.load_sensor_forecast("sensor.missing", "power", 3)
    assert result is None


async def test_load_sensor_forecast_invalid_forecast_data(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading forecast data with invalid forecast values."""
    # Mock sensor state with invalid forecast data
    mock_state = Mock()
    mock_state.state = "100"
    mock_state.attributes = {
        "device_class": SensorDeviceClass.POWER,
        "unit_of_measurement": "W",
        "forecast": ["invalid", "data", "here"],
    }
    mock_hass.states.get.return_value = mock_state

    result = await sensor_loader.load_sensor_forecast("sensor.test", "power", 3)
    assert result == [100, 100, 100]  # Falls back to repeated current value


async def test_load_sensor_forecast_multiple_sensors_sum(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading and summing forecast data from multiple sensors."""
    # Mock first sensor
    mock_state1 = Mock()
    mock_state1.state = "100"
    mock_state1.attributes = {
        "device_class": SensorDeviceClass.POWER,
        "unit_of_measurement": "W",
        "forecast": [100, 200, 300],
    }

    # Mock second sensor
    mock_state2 = Mock()
    mock_state2.state = "50"
    mock_state2.attributes = {
        "device_class": SensorDeviceClass.POWER,
        "unit_of_measurement": "W",
        "forecast": [50, 100, 150],
    }

    mock_hass.states.get.side_effect = [mock_state1, mock_state2]

    result = await sensor_loader.load_sensor_forecast(["sensor.test1", "sensor.test2"], "power", 3)
    assert result == [150, 300, 450]  # Sum of both sensors


async def test_resample_forecast_exact_length(hass: HomeAssistant, sensor_loader):
    """Test forecast resampling with exact target length."""
    forecast = [100, 200, 300, 400, 500]
    result = sensor_loader._resample_forecast(forecast, 5)
    assert result == [100, 200, 300, 400, 500]


async def test_resample_forecast_downsample(hass: HomeAssistant, sensor_loader):
    """Test forecast resampling with downsampling."""
    forecast = [100, 200, 300, 400, 500, 600]
    result = sensor_loader._resample_forecast(forecast, 3)
    assert result == [100.0, 350.0, 600.0]  # Numpy interpolated values


async def test_resample_forecast_upsample(hass: HomeAssistant, sensor_loader):
    """Test forecast resampling with upsampling."""
    forecast = [100, 200]
    result = sensor_loader._resample_forecast(forecast, 4)
    assert result == [100.0, 133.33333333333334, 166.66666666666666, 200.0]  # Numpy interpolated values


async def test_get_repeated_value_with_conversion(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test getting repeated value with unit conversion."""
    # Mock sensor state
    mock_state = Mock()
    mock_state.state = "5.5"
    mock_state.attributes = {"device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": "kWh"}
    mock_hass.states.get.return_value = mock_state

    result = sensor_loader._get_repeated_value(mock_state, "sensor.test", 3)
    assert result == [5500.0, 5500.0, 5500.0]  # 5.5 kWh = 5500 Wh


async def test_get_repeated_value_without_conversion(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test getting repeated value without unit conversion."""
    # Mock sensor state
    mock_state = Mock()
    mock_state.state = "75"
    mock_state.attributes = {"device_class": SensorDeviceClass.BATTERY, "unit_of_measurement": "%"}
    mock_hass.states.get.return_value = mock_state

    result = sensor_loader._get_repeated_value(mock_state, "sensor.test", 3)
    assert result == [75.0, 75.0, 75.0]  # No conversion needed for percentage


async def test_get_repeated_value_invalid_number(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test getting repeated value with invalid number."""
    # Mock sensor state
    mock_state = Mock()
    mock_state.state = "not_a_number"
    mock_hass.states.get.return_value = mock_state

    result = sensor_loader._get_repeated_value(mock_state, "sensor.test", 3)
    assert result is None


# New DataLoader tests
async def test_load_field_data_constant(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading constant field data."""
    result = await sensor_loader.load_field_data("capacity", 1000, MockConfigWithCapacity, 3)
    assert result == 1000


async def test_load_field_data_sensor(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading sensor field data."""
    # Mock sensor state
    mock_state = Mock()
    mock_state.state = "1000"
    mock_state.attributes = {"device_class": SensorDeviceClass.POWER, "unit_of_measurement": "W"}
    mock_hass.states.get.return_value = mock_state

    result = await sensor_loader.load_field_data("current_charge_sensor", "sensor.test", MockConfigWithBatterySensor, 3)
    assert result == [1000.0, 1000.0, 1000.0]


async def test_load_field_data_forecast(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading forecast field data."""
    # Mock sensor state with forecast
    mock_state = Mock()
    mock_state.state = "100"
    mock_state.attributes = {
        "device_class": SensorDeviceClass.POWER,
        "unit_of_measurement": "W",
        "forecast": [100, 200, 300, 400, 500],
    }
    mock_hass.states.get.return_value = mock_state

    result = await sensor_loader.load_field_data("forecast_sensors", "sensor.test", MockConfigWithPowerSensor, 3)
    assert result == [100, 200, 300]


async def test_load_field_data_multiple_sensors(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading data from multiple sensors."""
    # Mock first sensor
    mock_state1 = Mock()
    mock_state1.state = "100"
    mock_state1.attributes = {"device_class": SensorDeviceClass.POWER, "unit_of_measurement": "W"}

    # Mock second sensor
    mock_state2 = Mock()
    mock_state2.state = "200"
    mock_state2.attributes = {"device_class": SensorDeviceClass.POWER, "unit_of_measurement": "W"}

    mock_hass.states.get.side_effect = [mock_state1, mock_state2]

    result = await sensor_loader.load_field_data(
        "current_charge_sensor", ["sensor.test1", "sensor.test2"], MockConfigWithBatterySensor, 3
    )
    assert result == [300.0, 300.0, 300.0]  # Sum of both sensors repeated for 3 periods


async def test_load_field_data_unavailable_sensor(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading data from unavailable sensor."""
    mock_hass.states.get.return_value = None

    result = await sensor_loader.load_field_data(
        "current_charge_sensor", "sensor.unavailable", MockConfigWithBatterySensor, 3
    )
    assert result is None


async def test_load_field_data_unknown_field_type(hass: HomeAssistant, sensor_loader, mock_hass):
    """Test loading data for field with unknown type."""
    # This would use a field that doesn't have field_type metadata
    result = await sensor_loader.load_field_data("unknown_field", "test_value", MockConfigWithBatterySensor, 3)
    assert result == "test_value"  # Should return as-is
