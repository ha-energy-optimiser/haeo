"""Test the HAEO sensor loader."""

from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
import pytest

from custom_components.haeo.const import (
    ATTR_FORECAST,
    CONF_CAPACITY,
    CONF_EFFICIENCY,
    CONF_FORECAST,
    CONF_IMPORT_PRICE,
    CONF_INITIAL_CHARGE_PERCENTAGE,
    CONF_MIN_CHARGE_PERCENTAGE,
    FIELD_TYPE_CONSTANT,
    FIELD_TYPE_FORECAST,
    FIELD_TYPE_SENSOR,
)
from custom_components.haeo.data_loader import (
    DataLoader,
    convert_to_base_unit,
    get_field_device_class,
    get_field_property_type,
    get_field_type,
)


# Mock configuration classes for testing field type detection
@dataclass
class MockConfigWithBatterySensor:
    """Mock config class with battery sensor field."""

    initial_charge_percentage: str = field(metadata={"field_type": (SensorDeviceClass.BATTERY, FIELD_TYPE_SENSOR)})


@dataclass
class MockConfigWithLiveForecastPrice:
    """Mock config class with live_forecast price field."""

    import_price: dict[str, Any] = field(metadata={"field_type": (SensorDeviceClass.MONETARY, "live_forecast")})


@dataclass
class MockConfigWithPriceSensor:
    """Mock config class with price sensor field."""

    import_price: str = field(metadata={"field_type": (SensorDeviceClass.MONETARY, FIELD_TYPE_SENSOR)})


@dataclass
class MockConfigWithPowerSensor:
    """Mock config class with power sensor field."""

    forecast: str = field(metadata={"field_type": (SensorDeviceClass.POWER, CONF_FORECAST)})


@dataclass
class MockConfigWithBatterySOC:
    """Mock config class with battery SOC field."""

    min_charge_percentage: float = field(metadata={"field_type": (SensorDeviceClass.BATTERY, FIELD_TYPE_CONSTANT)})


@dataclass
class MockConfigWithEfficiency:
    """Mock config class with efficiency field."""

    efficiency: float = field(metadata={"field_type": ("%", FIELD_TYPE_CONSTANT)})


@dataclass
class MockConfigWithCapacity:
    """Mock config class with capacity field."""

    capacity: float = field(metadata={"field_type": (CONF_CAPACITY, FIELD_TYPE_CONSTANT)})


# Field type detection tests
async def test_get_field_type_battery_sensor() -> None:
    """Test field type detection for battery sensor."""
    field_type = get_field_type(CONF_INITIAL_CHARGE_PERCENTAGE, MockConfigWithBatterySensor)
    assert field_type == (SensorDeviceClass.BATTERY, FIELD_TYPE_SENSOR)


async def test_get_field_type_battery_soc_field() -> None:
    """Test field type detection for battery SOC field."""
    field_type = get_field_type(CONF_MIN_CHARGE_PERCENTAGE, MockConfigWithBatterySOC)
    assert field_type == (SensorDeviceClass.BATTERY, FIELD_TYPE_CONSTANT)


async def test_get_field_type_efficiency_field() -> None:
    """Test field type detection for efficiency field."""
    field_type = get_field_type(CONF_EFFICIENCY, MockConfigWithEfficiency)
    assert field_type == ("%", FIELD_TYPE_CONSTANT)


async def test_get_field_type_import_price_sensor() -> None:
    """Test field type detection for price sensor."""
    field_type = get_field_type(CONF_IMPORT_PRICE, MockConfigWithPriceSensor)
    assert field_type == (SensorDeviceClass.MONETARY, FIELD_TYPE_SENSOR)


async def test_get_field_type_power_sensor() -> None:
    """Test field type detection for power sensor."""
    field_type = get_field_type(CONF_FORECAST, MockConfigWithPowerSensor)
    assert field_type == (SensorDeviceClass.POWER, CONF_FORECAST)


# New helper function tests
async def test_get_field_device_class() -> None:
    """Test getting device class from field type."""
    device_class = get_field_device_class(CONF_INITIAL_CHARGE_PERCENTAGE, MockConfigWithBatterySensor)
    assert device_class == SensorDeviceClass.BATTERY

    device_class = get_field_device_class(CONF_EFFICIENCY, MockConfigWithEfficiency)
    assert device_class == "%"


async def test_get_field_property_type() -> None:
    """Test getting property type from field type."""
    property_type = get_field_property_type(CONF_INITIAL_CHARGE_PERCENTAGE, MockConfigWithBatterySensor)
    assert property_type == FIELD_TYPE_SENSOR

    property_type = get_field_property_type(CONF_MIN_CHARGE_PERCENTAGE, MockConfigWithBatterySOC)
    assert property_type == FIELD_TYPE_CONSTANT


async def test_get_field_type_unknown_field() -> None:
    """Test field type detection for unknown field."""
    with pytest.raises(ValueError, match="Field 'unknown_field' not found"):
        get_field_type("unknown_field", MockConfigWithBatterySensor)


# Field classification tests
async def test_get_field_property_type_sensor() -> None:
    """Test field property type detection for sensor fields."""
    # Test sensor field detection
    prop_type = get_field_property_type(CONF_INITIAL_CHARGE_PERCENTAGE, MockConfigWithBatterySensor)
    assert prop_type in [FIELD_TYPE_SENSOR, FIELD_TYPE_FORECAST]

    prop_type = get_field_property_type(CONF_IMPORT_PRICE, MockConfigWithPriceSensor)
    assert prop_type in [FIELD_TYPE_SENSOR, FIELD_TYPE_FORECAST]

    prop_type = get_field_property_type(CONF_FORECAST, MockConfigWithPowerSensor)
    assert prop_type in [FIELD_TYPE_SENSOR, FIELD_TYPE_FORECAST]


async def test_get_field_property_type_constant() -> None:
    """Test field property type detection for constant fields."""
    # Test constant field detection
    prop_type = get_field_property_type(CONF_CAPACITY, MockConfigWithCapacity)
    assert prop_type == FIELD_TYPE_CONSTANT

    prop_type = get_field_property_type(CONF_MIN_CHARGE_PERCENTAGE, MockConfigWithBatterySOC)
    assert prop_type == FIELD_TYPE_CONSTANT


async def test_get_field_property_type_forecast() -> None:
    """Test field property type detection for forecast fields."""
    # Test forecast field detection
    prop_type = get_field_property_type(CONF_FORECAST, MockConfigWithPowerSensor)
    assert prop_type == FIELD_TYPE_FORECAST


async def test_get_field_property_type_undefined() -> None:
    """Test field property type detection for undefined fields."""
    # Test undefined field detection (returns None)
    prop_type = get_field_property_type("nonexistent_field", MockConfigWithBatterySensor)
    assert prop_type is None


# Unit conversion tests
async def test_convert_battery_percentage() -> None:
    """Test unit conversion for battery percentage (no conversion needed)."""
    result = convert_to_base_unit(75.5, "%", SensorDeviceClass.BATTERY)
    assert result == 75.5


async def test_convert_monetary_price() -> None:
    """Test unit conversion for monetary price (no conversion needed)."""
    result = convert_to_base_unit(0.25, "$/kWh", SensorDeviceClass.MONETARY)
    assert result == 0.25


async def test_convert_power_kw_to_w() -> None:
    """Test unit conversion for power from kW to W."""
    result = convert_to_base_unit(1000, UnitOfPower.KILO_WATT, SensorDeviceClass.POWER)
    assert result == 1000000.0


async def test_convert_power_w_to_w() -> None:
    """Test unit conversion for power from W to W (no conversion needed)."""
    result = convert_to_base_unit(1000, UnitOfPower.WATT, SensorDeviceClass.POWER)
    assert result == 1000.0


async def test_convert_energy_kwh_to_wh() -> None:
    """Test unit conversion for energy from kWh to Wh."""
    result = convert_to_base_unit(5, "kWh", SensorDeviceClass.ENERGY)
    assert result == 5000.0


async def test_convert_energy_wh_to_wh() -> None:
    """Test unit conversion for energy from Wh to Wh (no conversion needed)."""
    result = convert_to_base_unit(5000, "Wh", SensorDeviceClass.ENERGY)
    assert result == 5000.0


async def test_convert_unknown_device_class() -> None:
    """Test unit conversion for unknown device class (returns as-is)."""
    result = convert_to_base_unit(42, "unknown", "unknown_device_class")
    assert result == 42


# SensorDataLoader tests
@pytest.fixture
def sensor_loader(hass: HomeAssistant):
    """Create a DataLoader instance."""
    return DataLoader(hass)


async def test_load_sensor_value_available_power(hass: HomeAssistant, sensor_loader) -> None:
    """Test loading available power sensor value."""
    # Set up sensor state
    hass.states.async_set(
        "sensor.test_power",
        "1000",
        attributes={"device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT},
    )

    result = await sensor_loader.load_sensor_value("sensor.test_power")
    assert result == 1000.0


async def test_load_sensor_value_available_energy(hass: HomeAssistant, sensor_loader) -> None:
    """Test loading available energy sensor value."""
    # Set up sensor state
    hass.states.async_set(
        "sensor.test_energy", "5.5", attributes={"device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": "kWh"}
    )

    result = await sensor_loader.load_sensor_value("sensor.test_energy")
    assert result == 5500.0  # 5.5 kWh = 5500 Wh


async def test_load_sensor_value_available_battery(hass: HomeAssistant, sensor_loader) -> None:
    """Test loading available battery sensor value."""
    # Set up sensor state
    hass.states.async_set(
        "sensor.test_battery", "75", attributes={"device_class": SensorDeviceClass.BATTERY, "unit_of_measurement": "%"}
    )

    result = await sensor_loader.load_sensor_value("sensor.test_battery")
    assert result == 75.0


async def test_load_sensor_value_unavailable_sensor(hass: HomeAssistant, sensor_loader) -> None:
    """Test loading value from unavailable sensor."""
    # Don't set any state for the sensor - it should be unavailable

    result = await sensor_loader.load_sensor_value("sensor.unavailable")
    assert result is None


async def test_load_sensor_value_unknown_state(hass: HomeAssistant, sensor_loader) -> None:
    """Test loading value from sensor with unknown state."""
    # Set up sensor state with unknown value
    hass.states.async_set("sensor.unknown", "unknown")

    result = await sensor_loader.load_sensor_value("sensor.unknown")
    assert result is None


async def test_load_sensor_value_invalid_number(hass: HomeAssistant, sensor_loader) -> None:
    """Test loading value from sensor with invalid number."""
    # Set up sensor state with invalid number
    hass.states.async_set("sensor.invalid", "not_a_number")

    result = await sensor_loader.load_sensor_value("sensor.invalid")
    assert result is None


async def test_load_sensor_forecast_with_forecast_attribute(hass: HomeAssistant, sensor_loader) -> None:
    """Test loading forecast data from sensor with forecast attribute."""
    # Set up sensor state with forecast
    hass.states.async_set(
        "sensor.test",
        "100",
        attributes={
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
            ATTR_FORECAST: [100, 200, 300, 400, 500],
        },
    )

    result = await sensor_loader.load_sensor_forecast("sensor.test", 3)
    assert result == [100, 200, 300]


async def test_load_sensor_forecast_without_forecast_attribute(hass: HomeAssistant, sensor_loader) -> None:
    """Test loading forecast data from sensor without forecast attribute."""
    # Set up sensor state without forecast
    hass.states.async_set(
        "sensor.test",
        "150",
        attributes={"device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT},
    )

    result = await sensor_loader.load_sensor_forecast("sensor.test", 3)
    assert result == [150, 150, 150]  # Repeated current value


async def test_load_sensor_forecast_missing_sensor(hass: HomeAssistant, sensor_loader) -> None:
    """Test loading forecast data from missing sensor."""
    # Don't set any state for the sensor - it should be missing

    result = await sensor_loader.load_sensor_forecast("sensor.missing", 3)
    assert result is None


async def test_load_sensor_forecast_invalid_forecast_data(hass: HomeAssistant, sensor_loader) -> None:
    """Test loading forecast data with invalid forecast values."""
    # Set up sensor state with invalid forecast data
    hass.states.async_set(
        "sensor.test",
        "100",
        attributes={
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
            ATTR_FORECAST: ["invalid", "data", "here"],
        },
    )

    result = await sensor_loader.load_sensor_forecast("sensor.test", 3)
    assert result == [100, 100, 100]  # Falls back to repeated current value


async def test_load_sensor_forecast_multiple_sensors_sum(hass: HomeAssistant, sensor_loader) -> None:
    """Test loading and summing forecast data from multiple sensors."""
    # Set up first sensor
    hass.states.async_set(
        "sensor.test1",
        "100",
        attributes={
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
            ATTR_FORECAST: [100, 200, 300],
        },
    )

    # Set up second sensor
    hass.states.async_set(
        "sensor.test2",
        "50",
        attributes={
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
            ATTR_FORECAST: [50, 100, 150],
        },
    )

    result = await sensor_loader.load_sensor_forecast(["sensor.test1", "sensor.test2"], 3)
    assert result == [150, 300, 450]  # Sum of both sensors


async def test_resample_forecast_exact_length(hass: HomeAssistant, sensor_loader) -> None:
    """Test forecast resampling with exact target length."""
    forecast = [100, 200, 300, 400, 500]
    result = sensor_loader._resample_forecast(forecast, 5)
    assert result == [100, 200, 300, 400, 500]


async def test_resample_forecast_downsample(hass: HomeAssistant, sensor_loader) -> None:
    """Test forecast resampling with downsampling."""
    forecast = [100, 200, 300, 400, 500, 600]
    result = sensor_loader._resample_forecast(forecast, 3)
    assert result == [100.0, 350.0, 600.0]  # Numpy interpolated values


async def test_resample_forecast_upsample(hass: HomeAssistant, sensor_loader) -> None:
    """Test forecast resampling with upsampling."""
    forecast = [100, 200]
    result = sensor_loader._resample_forecast(forecast, 4)
    assert result == [100.0, 133.33333333333334, 166.66666666666666, 200.0]  # Numpy interpolated values


async def test_get_repeated_value_with_conversion(hass: HomeAssistant, sensor_loader) -> None:
    """Test getting repeated value with unit conversion."""
    # Set up sensor state
    hass.states.async_set(
        "sensor.test", "5.5", attributes={"device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": "kWh"}
    )

    # Get the actual state object from hass.states
    state = hass.states.get("sensor.test")
    result = sensor_loader._get_repeated_value(state, "sensor.test", 3)
    assert result == [5500.0, 5500.0, 5500.0]  # 5.5 kWh = 5500 Wh


async def test_get_repeated_value_without_conversion(hass: HomeAssistant, sensor_loader) -> None:
    """Test getting repeated value without unit conversion."""
    # Set up sensor state
    hass.states.async_set(
        "sensor.test", "75", attributes={"device_class": SensorDeviceClass.BATTERY, "unit_of_measurement": "%"}
    )

    # Get the actual state object from hass.states
    state = hass.states.get("sensor.test")
    result = sensor_loader._get_repeated_value(state, "sensor.test", 3)
    assert result == [75.0, 75.0, 75.0]  # No conversion needed for percentage


async def test_get_repeated_value_invalid_number(hass: HomeAssistant, sensor_loader) -> None:
    """Test getting repeated value with invalid number."""
    # Set up sensor state with invalid number
    hass.states.async_set("sensor.test", "not_a_number")

    # Get the actual state object from hass.states
    state = hass.states.get("sensor.test")
    result = sensor_loader._get_repeated_value(state, "sensor.test", 3)
    assert result is None


# New DataLoader tests
async def test_load_field_data_constant(hass: HomeAssistant, sensor_loader: DataLoader) -> None:
    """Test loading constant field data."""
    result = await sensor_loader.load_field_data(CONF_CAPACITY, 1000, MockConfigWithCapacity, 3)
    assert result == 1000


async def test_load_field_data_sensor(hass: HomeAssistant, sensor_loader: DataLoader) -> None:
    """Test loading sensor field data."""
    # Set up sensor state
    hass.states.async_set(
        "sensor.test",
        "1000",
        attributes={"device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT},
    )

    result = await sensor_loader.load_field_data(
        CONF_INITIAL_CHARGE_PERCENTAGE,
        "sensor.test",
        MockConfigWithBatterySensor,
        3,
    )
    assert result == 1000.0


async def test_load_field_data_forecast(hass: HomeAssistant, sensor_loader: DataLoader) -> None:
    """Test loading forecast field data."""
    # Set up sensor state with forecast
    hass.states.async_set(
        "sensor.test",
        "100",
        attributes={
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
            ATTR_FORECAST: [100, 200, 300, 400, 500],
        },
    )

    result = await sensor_loader.load_field_data(CONF_FORECAST, "sensor.test", MockConfigWithPowerSensor, 3)
    assert result == [100, 200, 300]


async def test_load_field_data_multiple_sensors(hass: HomeAssistant, sensor_loader: DataLoader) -> None:
    """Test loading data from multiple sensors."""
    # Set up first sensor
    hass.states.async_set(
        "sensor.test1",
        "100",
        attributes={"device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT},
    )

    # Set up second sensor
    hass.states.async_set(
        "sensor.test2",
        "200",
        attributes={"device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT},
    )

    result = await sensor_loader.load_field_data(
        CONF_INITIAL_CHARGE_PERCENTAGE,
        ["sensor.test1", "sensor.test2"],
        MockConfigWithBatterySensor,
        3,
    )
    assert result == 300.0  # Sum of both sensors


async def test_load_field_data_unavailable_sensor(hass: HomeAssistant, sensor_loader: DataLoader) -> None:
    """Test loading data from unavailable sensor."""
    # Don't set any state for the sensor - it should be unavailable

    result = await sensor_loader.load_field_data(
        CONF_INITIAL_CHARGE_PERCENTAGE,
        "sensor.unavailable",
        MockConfigWithBatterySensor,
        3,
    )
    assert result is None


async def test_load_field_data_unknown_field_type(hass: HomeAssistant, sensor_loader: DataLoader) -> None:
    """Test loading data for field with unknown type."""
    # This would use a field that doesn't have field_type metadata
    result = await sensor_loader.load_field_data("unknown_field", "test_value", MockConfigWithBatterySensor, 3)
    assert result == "test_value"  # Should return as-is


async def test_load_field_data_live_forecast_both_sensors(hass: HomeAssistant, sensor_loader: DataLoader) -> None:
    """Test loading live_forecast field data with both live and forecast sensors."""
    # Set up mock sensor states
    hass.states.async_set("sensor.live_price", "0.15", {"device_class": "monetary"})
    hass.states.async_set("sensor.forecast_1", "0.16", {"device_class": "monetary", "forecast": [0.16, 0.17, 0.18]})
    hass.states.async_set("sensor.forecast_2", "0.14", {"device_class": "monetary", "forecast": [0.14, 0.15, 0.16]})

    # Test with both live and forecast sensors
    field_value = {"live": "sensor.live_price", "forecast": ["sensor.forecast_1", "sensor.forecast_2"]}

    result = await sensor_loader.load_field_data("import_price", field_value, MockConfigWithLiveForecastPrice, 3)

    # Should return forecast data with first element replaced by live value
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0] == 0.15  # Live value
    assert result[1] == pytest.approx(0.32)  # Sum of forecast sensors for period 1 (0.17 + 0.15)
    assert result[2] == pytest.approx(0.34)  # Sum of forecast sensors for period 2 (0.18 + 0.16)


async def test_load_field_data_live_forecast_only_live(hass: HomeAssistant, sensor_loader: DataLoader) -> None:
    """Test loading live_forecast field data with only live sensor."""
    # Set up mock sensor state
    hass.states.async_set("sensor.live_price", "0.20", {"device_class": "monetary"})

    # Test with only live sensor
    field_value = {"live": "sensor.live_price"}

    result = await sensor_loader.load_field_data("import_price", field_value, MockConfigWithLiveForecastPrice, 3)

    # Should return live value repeated for all periods
    assert isinstance(result, list)
    assert len(result) == 3
    assert result == [0.20, 0.20, 0.20]


async def test_load_field_data_live_forecast_only_forecast(hass: HomeAssistant, sensor_loader: DataLoader) -> None:
    """Test loading live_forecast field data with only forecast sensors."""
    # Set up mock sensor states
    hass.states.async_set("sensor.forecast_1", "0.16", {"device_class": "monetary", "forecast": [0.16, 0.17, 0.18]})
    hass.states.async_set("sensor.forecast_2", "0.14", {"device_class": "monetary", "forecast": [0.14, 0.15, 0.16]})

    # Test with only forecast sensors
    field_value = {"forecast": ["sensor.forecast_1", "sensor.forecast_2"]}

    result = await sensor_loader.load_field_data("import_price", field_value, MockConfigWithLiveForecastPrice, 3)

    # Should return forecast data (sum of sensors)
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0] == pytest.approx(0.30)  # Sum of forecast sensors for period 0 (0.16 + 0.14)
    assert result[1] == pytest.approx(0.32)  # Sum of forecast sensors for period 1 (0.17 + 0.15)
    assert result[2] == pytest.approx(0.34)  # Sum of forecast sensors for period 2 (0.18 + 0.16)


async def test_load_field_data_live_forecast_no_sensors(hass: HomeAssistant, sensor_loader: DataLoader) -> None:
    """Test loading live_forecast field data with no sensors."""
    # Test with empty dict
    field_value = {}

    result = await sensor_loader.load_field_data("import_price", field_value, MockConfigWithLiveForecastPrice, 3)

    # Should return the field value as-is
    assert result == {}


async def test_load_field_data_live_forecast_invalid_field_value(
    hass: HomeAssistant, sensor_loader: DataLoader
) -> None:
    """Test loading live_forecast field data with invalid field value."""
    # Test with string instead of dict
    field_value = "invalid_string"

    result = await sensor_loader.load_field_data("import_price", field_value, MockConfigWithLiveForecastPrice, 3)

    # Should return the field value as-is
    assert result == "invalid_string"


# Nested parameter reconstruction tests
def test_reconstruct_nested_params_basic() -> None:
    """Test basic reconstruction of nested parameters."""
    # Test with flattened price fields
    element_params = {
        "name": "Test Grid",
        "import_price_live": "sensor.price_import",
        "import_price_forecast": ["sensor.price_forecast_1", "sensor.price_forecast_2"],
        "export_price_live": "sensor.price_export",
        "export_price_forecast": ["sensor.price_forecast_export_1"],
        "import_limit": 1000,
        "export_limit": 800,
    }

    # Import the method directly for testing
    from custom_components.haeo.data_loader import DataLoader

    # Create a mock hass for the DataLoader
    class MockHass:
        pass

    loader = DataLoader(MockHass())

    reconstructed = loader._reconstruct_nested_params(element_params)

    expected = {
        "name": "Test Grid",
        "import_limit": 1000,
        "export_limit": 800,
        "import_price": {
            "live": "sensor.price_import",
            "forecast": ["sensor.price_forecast_1", "sensor.price_forecast_2"],
        },
        "export_price": {"live": "sensor.price_export", "forecast": ["sensor.price_forecast_export_1"]},
    }

    assert reconstructed == expected


def test_reconstruct_nested_params_no_flattened() -> None:
    """Test reconstruction when no flattened fields are present."""
    element_params = {"name": "Test Battery", "capacity": 10000, "efficiency": 0.95}

    from custom_components.haeo.data_loader import DataLoader

    class MockHass:
        pass

    loader = DataLoader(MockHass())

    reconstructed = loader._reconstruct_nested_params(element_params)

    # Should return unchanged since no flattened fields
    assert reconstructed == element_params


def test_reconstruct_nested_params_mixed_fields() -> None:
    """Test reconstruction with mix of flattened and regular fields."""
    element_params = {
        "name": "Test Grid",
        "import_price_live": "sensor.price_import",
        "capacity": 5000,  # Regular field
        "import_price_forecast": ["sensor.price_forecast_1"],
        "efficiency": 0.9,  # Regular field
    }

    from custom_components.haeo.data_loader import DataLoader

    class MockHass:
        pass

    loader = DataLoader(MockHass())

    reconstructed = loader._reconstruct_nested_params(element_params)

    expected = {
        "name": "Test Grid",
        "capacity": 5000,
        "efficiency": 0.9,
        "import_price": {"live": "sensor.price_import", "forecast": ["sensor.price_forecast_1"]},
    }

    assert reconstructed == expected


def test_reconstruct_nested_params_invalid_format() -> None:
    """Test reconstruction with invalid flattened field format."""
    element_params = {
        "name": "Test Grid",
        "import_price_invalid": "sensor.price",  # Invalid suffix
        "export_price_also_invalid": ["sensor.price"],  # Invalid suffix
        "regular_field": 1000,
    }

    from custom_components.haeo.data_loader import DataLoader

    class MockHass:
        pass

    loader = DataLoader(MockHass())

    reconstructed = loader._reconstruct_nested_params(element_params)

    # Should return unchanged since fields don't match expected pattern
    assert reconstructed == element_params
