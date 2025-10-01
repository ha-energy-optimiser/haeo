"""Test the model components."""

import pytest
from custom_components.haeo.const import (
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_CONNECTION,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_LOAD_FORECAST,
    ELEMENT_TYPE_NET,
)
from custom_components.haeo.model import Network
from custom_components.haeo.model.battery import Battery
from custom_components.haeo.model.connection import Connection
from custom_components.haeo.model.grid import Grid
from custom_components.haeo.model.load_constant import LoadConstant
from custom_components.haeo.model.load_forecast import LoadForecast
from custom_components.haeo.model.generator import Generator
from custom_components.haeo.model.net import Net


class TestBattery:
    """Test the Battery class."""

    def test_battery_initialization(self):
        """Test battery initialization."""
        battery = Battery(
            name="test_battery",
            period=3600,
            n_periods=24,
            capacity=10000,
            initial_charge_percentage=50,
            min_charge_percentage=10,
            max_charge_percentage=90,
            max_charge_power=5000,
            max_discharge_power=5000,
            efficiency=0.95,
        )

        assert battery.name == "test_battery"
        assert battery.period == 3600
        assert battery.n_periods == 24
        assert battery.capacity == 10000
        assert battery.efficiency == 0.95
        assert len(battery.power_consumption) == 24
        assert len(battery.power_production) == 24
        assert len(battery.energy) == 24

    def test_battery_constraints(self):
        """Test battery constraints generation."""
        battery = Battery(
            name="test_battery",
            period=3600,
            n_periods=3,
            capacity=10000,
            initial_charge_percentage=50,
        )

        constraints = battery.constraints()
        # Should have energy balance constraints for each time step after the first
        assert len(constraints) >= 2  # n_periods - 1


class TestGrid:
    """Test the Grid class."""

    def test_grid_initialization(self):
        """Test grid initialization."""
        price_import = [0.1, 0.2, 0.15]
        price_export = [0.05, 0.08, 0.06]

        grid = Grid(
            name="test_grid",
            period=3600,
            n_periods=3,
            import_limit=10000,
            export_limit=5000,
            price_import=price_import,
            price_export=price_export,
        )

        assert grid.name == "test_grid"
        assert grid.period == 3600
        assert grid.n_periods == 3
        assert len(grid.power_consumption) == 3
        assert len(grid.power_production) == 3
        assert grid.price_consumption == price_export
        assert grid.price_production == price_import

    def test_grid_invalid_forecast_length(self):
        """Test grid with invalid forecast length."""
        with pytest.raises(ValueError, match="price_import length"):
            Grid(
                name="test_grid",
                period=3600,
                n_periods=3,
                import_limit=10000,
                export_limit=5000,
                price_import=[0.1, 0.2],  # Wrong length
                price_export=[0.05, 0.08, 0.06],
            )

    def test_grid_invalid_export_forecast_length(self):
        """Test grid with invalid export forecast length."""
        with pytest.raises(ValueError, match="price_export length"):
            Grid(
                name="test_grid",
                period=3600,
                n_periods=3,
                import_limit=10000,
                export_limit=5000,
                price_import=[0.1, 0.2, 0.15],
                price_export=[0.05, 0.08],  # Wrong length
            )


class TestLoad:
    """Test the Load class."""

    def test_load_forecast_initialization(self):
        """Test forecast load initialization."""
        forecast = [1000, 1500, 2000]

        load = LoadForecast(
            name="test_load",
            period=3600,
            n_periods=3,
            forecast=forecast,
        )

        assert load.name == "test_load"
        assert load.period == 3600
        assert load.n_periods == 3
        assert load.power_consumption == forecast
        assert load.power_production is None

    def test_load_forecast_invalid_forecast_length(self):
        """Test forecast load with invalid forecast length."""
        with pytest.raises(ValueError, match="forecast length"):
            LoadForecast(
                name="test_load",
                period=3600,
                n_periods=3,
                forecast=[1000, 1500],  # Wrong length
            )

    def test_load_constant_initialization(self):
        """Test constant load initialization."""
        load = LoadConstant(
            name="test_load",
            period=3600,
            n_periods=3,
            power=1500,
        )

        assert load.name == "test_load"
        assert load.period == 3600
        assert load.n_periods == 3
        assert load.power_consumption == [1500, 1500, 1500]  # Constant power for all periods
        assert load.power_production is None


class TestGenerator:
    """Test the Generator class."""

    def test_generator_initialization_with_curtailment(self):
        """Test generator initialization with curtailment."""
        forecast = [1000, 1500, 2000]

        generator = Generator(
            name="test_generator",
            period=3600,
            n_periods=3,
            forecast=forecast,
            curtailment=True,
        )

        assert generator.name == "test_generator"
        assert generator.period == 3600
        assert generator.n_periods == 3
        assert len(generator.power_production) == 3
        assert generator.power_consumption is None

    def test_generator_initialization_without_curtailment(self):
        """Test generator initialization without curtailment."""
        forecast = [1000, 1500, 2000]

        generator = Generator(
            name="test_generator",
            period=3600,
            n_periods=3,
            forecast=forecast,
            curtailment=False,
        )

        assert generator.name == "test_generator"
        assert generator.power_production is None

    def test_generator_invalid_forecast_length(self):
        """Test generator with invalid forecast length."""
        with pytest.raises(ValueError, match="forecast length"):
            Generator(
                name="test_generator",
                period=3600,
                n_periods=3,
                forecast=[1000, 1500],  # Wrong length
                curtailment=True,
            )


class TestNet:
    """Test the Net class."""

    def test_net_initialization(self):
        """Test net initialization."""
        net = Net(
            name="test_net",
            period=3600,
            n_periods=3,
        )

        assert net.name == "test_net"
        assert net.period == 3600
        assert net.n_periods == 3
        assert net.power_consumption is None
        assert net.power_production is None


class TestNetwork:
    """Test the Network class."""

    def test_network_initialization(self):
        """Test network initialization."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=24,
        )

        assert network.name == "test_network"
        assert network.period == 3600
        assert network.n_periods == 24
        assert len(network.elements) == 0

    def test_add_battery(self):
        """Test adding a battery to the network."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=24,
        )

        battery = network.add(ELEMENT_TYPE_BATTERY, "test_battery", capacity=10000, initial_charge_percentage=50)

        assert isinstance(battery, Battery)
        assert battery.name == "test_battery"
        assert "test_battery" in network.elements
        assert network.elements["test_battery"] == battery

    def test_add_grid(self):
        """Test adding a grid to the network."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        grid = network.add(
            ELEMENT_TYPE_GRID,
            "test_grid",
            import_limit=10000,
            export_limit=5000,
            price_import=[0.1, 0.2, 0.15],
            price_export=[0.05, 0.08, 0.06],
        )

        assert isinstance(grid, Grid)
        assert grid.name == "test_grid"
        assert "test_grid" in network.elements

    def test_add_load(self):
        """Test adding a load to the network."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        load = network.add(
            ELEMENT_TYPE_LOAD_FORECAST,
            "test_load",
            forecast=[1000, 1500, 2000],
        )

        assert isinstance(load, LoadForecast)
        assert load.name == "test_load"
        assert "test_load" in network.elements

    def test_add_generator(self):
        """Test adding a generator to the network."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        generator = network.add(
            ELEMENT_TYPE_GENERATOR,
            "test_generator",
            forecast=[1000, 1500, 2000],
            curtailment=True,
        )

        assert isinstance(generator, Generator)
        assert generator.name == "test_generator"
        assert "test_generator" in network.elements

    def test_add_net(self):
        """Test adding a net to the network."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        net = network.add(ELEMENT_TYPE_NET, "test_net")

        assert isinstance(net, Net)
        assert net.name == "test_net"
        assert "test_net" in network.elements

    def test_connect_entities(self):
        """Test connecting entities in the network."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        # Add entities
        network.add(ELEMENT_TYPE_BATTERY, "battery1", capacity=10000, initial_charge_percentage=50)
        network.add(
            ELEMENT_TYPE_GRID,
            "grid1",
            import_limit=10000,
            export_limit=5000,
            price_import=[0.1, 0.2, 0.15],
            price_export=[0.05, 0.08, 0.06],
        )

        # Connect them
        connection = network.add(
            ELEMENT_TYPE_CONNECTION,
            "battery1_to_grid1",
            source="battery1",
            target="grid1",
            min_power=0,
            max_power=5000,
        )

        assert connection is not None
        assert connection.name == "battery1_to_grid1"
        assert connection.source == "battery1"
        assert connection.target == "grid1"
        assert len(connection.power) == 3
        # Check that the connection element was added
        connection_name = "battery1_to_grid1"
        assert connection_name in network.elements
        assert isinstance(network.elements[connection_name], Connection)
        assert len(connection.power) == 3

    def test_connect_nonexistent_entities(self):
        """Test connecting nonexistent entities."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )
        network.add(ELEMENT_TYPE_CONNECTION, "bad_connection", source="nonexistent", target="also_nonexistent")

        with pytest.raises(ValueError, match="Source element 'nonexistent' not found"):
            network.validate()

    def test_connect_nonexistent_target_entity(self):
        """Test connecting to nonexistent target entity."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )
        # Add only source entity
        network.add(ELEMENT_TYPE_BATTERY, "battery1", capacity=10000, initial_charge_percentage=50)
        # Try to connect to nonexistent target
        network.add(ELEMENT_TYPE_CONNECTION, "bad_connection", source="battery1", target="nonexistent")

        with pytest.raises(ValueError, match="Target element 'nonexistent' not found"):
            network.validate()

    def test_connection_with_negative_power_bounds(self):
        """Test connection with negative power bounds for bidirectional flow."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        # Add entities
        network.add(ELEMENT_TYPE_BATTERY, "battery1", capacity=10000, initial_charge_percentage=50)
        network.add(
            ELEMENT_TYPE_GRID,
            "grid1",
            import_limit=10000,
            export_limit=5000,
            price_import=[0.1, 0.2, 0.15],
            price_export=[0.05, 0.08, 0.06],
        )

        # Create bidirectional connection
        connection = network.add(
            ELEMENT_TYPE_CONNECTION,
            "battery_grid_bidirectional",
            source="battery1",
            target="grid1",
            min_power=-2000,  # Allow reverse flow up to 2000W
            max_power=3000,  # Allow forward flow up to 3000W
        )

        assert connection is not None
        assert connection.name == "battery_grid_bidirectional"
        assert connection.source == "battery1"
        assert connection.target == "grid1"
        assert len(connection.power) == 3

        # Verify power variables have correct bounds
        for power_var in connection.power:
            assert power_var.lowBound == -2000
            assert power_var.upBound == 3000

    def test_connection_power_balance_with_negative_flow(self):
        """Test that power balance works correctly with negative power flows."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        # Add entities
        network.add(ELEMENT_TYPE_BATTERY, "battery1", capacity=10000, initial_charge_percentage=50)
        network.add(
            ELEMENT_TYPE_GRID,
            "grid1",
            import_limit=10000,
            export_limit=5000,
            price_import=[0.1, 0.2, 0.15],
            price_export=[0.05, 0.08, 0.06],
        )

        # Create bidirectional connection
        network.add(
            ELEMENT_TYPE_CONNECTION,
            "battery_grid_bidirectional",
            source="battery1",
            target="grid1",
            min_power=-2000,  # Allow reverse flow
            max_power=3000,  # Allow forward flow
        )

        # Validate the network (should pass)
        network.validate()

        # Run optimization
        cost = network.optimize()

        # Should complete without errors
        assert isinstance(cost, (int, float))

        # Access optimization results
        battery = network.elements["battery1"]
        from pulp import value

        # Check that power variables exist and have values
        for power_var in battery.power_consumption:
            val = value(power_var)
            assert isinstance(val, (int, float))

    def test_connection_with_none_bounds(self):
        """Test connection with None bounds (should use None for infinite bounds)."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        # Add entities
        network.add(ELEMENT_TYPE_BATTERY, "battery1", capacity=10000, initial_charge_percentage=50)
        network.add(
            ELEMENT_TYPE_GRID,
            "grid1",
            import_limit=10000,
            export_limit=5000,
            price_import=[0.1, 0.2, 0.15],
            price_export=[0.05, 0.08, 0.06],
        )

        # Create connection with None bounds (unlimited power)
        connection = network.add(
            ELEMENT_TYPE_CONNECTION,
            "unlimited_connection",
            source="battery1",
            target="grid1",
            min_power=None,  # Should remain None for infinite lower bound
            max_power=None,  # Should remain None for infinite upper bound
        )

        assert connection is not None
        assert len(connection.power) == 3

        # Verify power variables have None bounds (infinite)
        for power_var in connection.power:
            assert power_var.lowBound is None  # Should be None for infinite lower bound
            assert power_var.upBound is None  # Should be None for infinite upper bound

    def test_connect_source_is_connection(self):
        """Test connecting when source is a connection element."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )
        # Add entities and a connection
        network.add(ELEMENT_TYPE_BATTERY, "battery1", capacity=10000, initial_charge_percentage=50)
        network.add(
            ELEMENT_TYPE_GRID,
            "grid1",
            import_limit=10000,
            export_limit=5000,
            price_import=[0.1, 0.2, 0.15],
            price_export=[0.05, 0.08, 0.06],
        )
        network.add(ELEMENT_TYPE_CONNECTION, "conn1", source="battery1", target="grid1")

        # Try to create another connection using the connection as source
        network.add(ELEMENT_TYPE_CONNECTION, "bad_connection", source="conn1", target="battery1")

        with pytest.raises(ValueError, match="Source element 'conn1' is a connection"):
            network.validate()

    def test_connect_target_is_connection(self):
        """Test connecting when target is a connection element."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )
        # Add entities and a connection
        network.add(ELEMENT_TYPE_BATTERY, "battery1", capacity=10000, initial_charge_percentage=50)
        network.add(
            ELEMENT_TYPE_GRID,
            "grid1",
            import_limit=10000,
            export_limit=5000,
            price_import=[0.1, 0.2, 0.15],
            price_export=[0.05, 0.08, 0.06],
        )
        network.add(ELEMENT_TYPE_CONNECTION, "conn1", source="battery1", target="grid1")

        # Try to create another connection using the connection as target
        network.add(ELEMENT_TYPE_CONNECTION, "bad_connection", source="battery1", target="conn1")

        with pytest.raises(ValueError, match="Target element 'conn1' is a connection"):
            network.validate()

    def test_simple_optimization(self):
        """Test a simple optimization scenario."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        # Add a simple grid and load
        network.add(
            ELEMENT_TYPE_GRID,
            "grid",
            import_limit=10000,
            export_limit=5000,
            price_import=[0.1, 0.2, 0.15],
            price_export=[0.05, 0.08, 0.06],
        )
        network.add("load", "load", forecast=[1000, 1500, 2000])
        network.add(ELEMENT_TYPE_NET, "net")

        # Connect them: grid -> net <- load
        network.add(ELEMENT_TYPE_CONNECTION, "grid_to_net", source="grid", target="net")
        network.add(ELEMENT_TYPE_CONNECTION, "net_to_load", source="net", target="load")

        # Run optimization
        cost = network.optimize()

        assert isinstance(cost, (int, float))


class TestScenarios:
    """Test realistic energy optimization scenarios."""

    def test_battery_solar_grid_storage_cycle(self):
        """Test a scenario with grid, battery, and solar with storage and discharge cycles.

        Uses square wave patterns to force energy storage during high generation
        and discharge during high demand periods.
        """
        network = Network(
            name="storage_cycle_test",
            period=3600,  # 1 hour periods
            n_periods=8,  # 8 hour test
        )

        # Solar generation with square wave pattern: high generation for 4 hours, then none
        solar_forecast = [5000, 5000, 5000, 5000, 0, 0, 0, 0]

        # Load demand with inverse square wave: low for 4 hours, then high
        load_forecast = [1000, 1000, 1000, 1000, 4000, 4000, 4000, 4000]

        # Grid pricing: cheap during high solar, expensive during low solar
        import_prices = [0.05, 0.05, 0.05, 0.05, 0.20, 0.20, 0.20, 0.20]
        export_prices = [0.03, 0.03, 0.03, 0.03, 0.15, 0.15, 0.15, 0.15]

        # Add entities
        network.add(
            ELEMENT_TYPE_GENERATOR, "solar", forecast=solar_forecast, curtailment=True, price_production=[0] * 8
        )  # Solar has no fuel cost

        network.add("load", "load", forecast=load_forecast)

        network.add(
            ELEMENT_TYPE_BATTERY,
            "battery",
            capacity=10000,  # 10 kWh
            initial_charge_percentage=50,
            min_charge_percentage=20,
            max_charge_percentage=90,
            max_charge_power=3000,  # 3 kW charge rate
            max_discharge_power=3000,  # 3 kW discharge rate
            efficiency=0.95,
        )

        network.add(
            ELEMENT_TYPE_GRID,
            "grid",
            import_limit=10000,
            export_limit=10000,
            price_import=import_prices,
            price_export=export_prices,
        )

        network.add(ELEMENT_TYPE_NET, "net")

        # Connect everything through the net
        network.add(ELEMENT_TYPE_CONNECTION, "solar_to_net", source="solar", target="net")
        network.add(ELEMENT_TYPE_CONNECTION, "battery_to_net", source="battery", target="net")
        network.add(ELEMENT_TYPE_CONNECTION, "grid_to_net", source="grid", target="net")
        network.add(ELEMENT_TYPE_CONNECTION, "net_to_load", source="net", target="load")

        # Run optimization
        cost = network.optimize()

        # Verify the solution makes economic sense
        assert isinstance(cost, (int, float))
        assert cost > 0  # Should have some cost

    def test_optimization_failure(self):
        """Test optimization failure handling."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        # Create an infeasible optimization problem by adding conflicting constraints
        # Add a battery with impossible constraints
        network.add(
            ELEMENT_TYPE_BATTERY,
            "battery",
            capacity=1000,
            initial_charge_percentage=50,
            min_charge_percentage=90,  # Impossible - starting charge is below minimum
            max_charge_power=0,  # Can't charge
            max_discharge_power=0,  # Can't discharge
        )

        # This should result in an infeasible optimization problem
        with pytest.raises(ValueError, match="Optimization failed with status"):
            network.optimize()

    def test_solar_curtailment_negative_pricing(self):
        """Test solar curtailment during negative export pricing periods.

        This scenario tests the system's ability to curtail solar generation
        when export prices are negative (grid operator pays to take power).
        """
        network = Network(
            name="curtailment_test",
            period=3600,
            n_periods=6,
        )

        # High solar generation throughout the test period
        solar_forecast = [6000, 6000, 6000, 6000, 6000, 6000]

        # Low load - creates excess generation that needs to be exported
        load_forecast = [1000, 1000, 1000, 1000, 1000, 1000]

        # Grid pricing with negative export prices in the middle periods
        import_prices = [0.10, 0.10, 0.10, 0.10, 0.10, 0.10]
        export_prices = [0.05, 0.05, -0.02, -0.02, 0.05, 0.05]  # Negative pricing in periods 2-3

        # Add entities
        network.add(
            ELEMENT_TYPE_GENERATOR,
            "solar",
            forecast=solar_forecast,
            curtailment=True,  # Allow curtailment
            price_production=[0] * 6,
        )  # No fuel cost for solar

        network.add("load", "load", forecast=load_forecast)

        network.add(
            ELEMENT_TYPE_GRID,
            "grid",
            import_limit=10000,
            export_limit=10000,
            price_import=import_prices,
            price_export=export_prices,
        )

        network.add(ELEMENT_TYPE_NET, "net")

        # Connect entities
        network.add(ELEMENT_TYPE_CONNECTION, "solar_to_net", source="solar", target="net")
        network.add(ELEMENT_TYPE_CONNECTION, "grid_to_net", source="grid", target="net")
        network.add(ELEMENT_TYPE_CONNECTION, "net_to_load", source="net", target="load")

        # Run optimization
        cost = network.optimize()

        # Verify solution
        assert isinstance(cost, (int, float))

        # Access optimization results directly from elements
        solar = network.elements["solar"]

        from pulp import value

        # Helper function to safely extract numeric values from PuLP variables
        def extract_value(var):
            """Extract numeric value from PuLP variable."""
            if var is None:
                return 0.0
            val = value(var)
            if val is None:
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            # Handle LpVariable case
            if hasattr(val, "value"):
                return float(val.value()) if val.value() is not None else 0.0
            return 0.0

        # Get solar production values
        solar_production = []

        if solar.power_production is not None:
            solar_production = [extract_value(p) for p in solar.power_production]

        # During negative pricing periods (indices 2-3), solar should be curtailed
        normal_periods = [0, 1, 4, 5]  # Positive export pricing
        negative_periods = [2, 3]  # Negative export pricing

        # Solar should produce less during negative pricing periods
        avg_solar_normal = sum(solar_production[i] for i in normal_periods) / len(normal_periods)
        avg_solar_negative = sum(solar_production[i] for i in negative_periods) / len(negative_periods)

        assert avg_solar_negative < avg_solar_normal, "Solar should be curtailed during negative pricing"

        # Verify that curtailment is actually happening (solar production < forecast)
        for i in negative_periods:
            assert solar_production[i] < solar_forecast[i], f"Solar should be curtailed in period {i}"
