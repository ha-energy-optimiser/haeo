"""Test the HAEO sensor loader."""

from dataclasses import dataclass, field

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
    FIELD_TYPE_SENSOR,
)
from custom_components.haeo.data_loader import (
    DataLoader,
    convert_to_base_unit,
    get_field_device_class,
    get_field_property_type,
    get_field_type,
    is_constant_field,
    is_forecast_field,
    is_sensor_field,
)


# Mock configuration classes for testing field type detection
@dataclass
class MockConfigWithBatterySensor:
    """Mock config class with battery sensor field."""

    initial_charge_percentage: str = field(metadata={"field_type": (SensorDeviceClass.BATTERY, FIELD_TYPE_SENSOR)})


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
async def test_is_sensor_field_true() -> None:
    """Test sensor field detection for sensor fields."""
    assert is_sensor_field(CONF_INITIAL_CHARGE_PERCENTAGE, MockConfigWithBatterySensor) is True
    assert is_sensor_field(CONF_IMPORT_PRICE, MockConfigWithPriceSensor) is True
    assert is_sensor_field(CONF_FORECAST, MockConfigWithPowerSensor) is True


async def test_is_sensor_field_false() -> None:
    """Test sensor field detection for non-sensor fields."""
    assert is_sensor_field(CONF_CAPACITY, MockConfigWithCapacity) is False
    assert is_sensor_field(CONF_MIN_CHARGE_PERCENTAGE, MockConfigWithBatterySOC) is False
    assert is_sensor_field(CONF_EFFICIENCY, MockConfigWithEfficiency) is False


async def test_is_forecast_field_true() -> None:
    """Test forecast field detection for forecast fields."""
    assert is_forecast_field(CONF_FORECAST) is True
    assert is_forecast_field("import_price_forecast") is True


async def test_is_forecast_field_false() -> None:
    """Test forecast field detection for non-forecast fields."""
    assert is_forecast_field(CONF_INITIAL_CHARGE_PERCENTAGE) is False
    assert is_forecast_field(CONF_CAPACITY) is False


async def test_is_constant_field_true() -> None:
    """Test constant field detection for constant fields."""
    assert is_constant_field(CONF_CAPACITY, MockConfigWithCapacity) is True
    assert is_constant_field(CONF_MIN_CHARGE_PERCENTAGE, MockConfigWithBatterySOC) is True


async def test_is_constant_field_false() -> None:
    """Test constant field detection for sensor fields."""
    assert is_constant_field(CONF_INITIAL_CHARGE_PERCENTAGE, MockConfigWithBatterySensor) is False


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
