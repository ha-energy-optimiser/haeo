"""Test the model components."""

import pytest
from custom_components.haeo.model import Network
from custom_components.haeo.model.battery import Battery
from custom_components.haeo.model.grid import Grid
from custom_components.haeo.model.load import Load
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


class TestLoad:
    """Test the Load class."""

    def test_load_initialization(self):
        """Test load initialization."""
        forecast = [1000, 1500, 2000]

        load = Load(
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

    def test_load_invalid_forecast_length(self):
        """Test load with invalid forecast length."""
        with pytest.raises(ValueError, match="forecast length"):
            Load(
                name="test_load",
                period=3600,
                n_periods=3,
                forecast=[1000, 1500],  # Wrong length
            )


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
        assert len(network.entities) == 0
        assert len(network.connections) == 0

    def test_add_battery(self):
        """Test adding a battery to the network."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=24,
        )

        battery = network.add("battery", "test_battery", capacity=10000, initial_charge_percentage=50)

        assert isinstance(battery, Battery)
        assert battery.name == "test_battery"
        assert "test_battery" in network.entities
        assert network.entities["test_battery"] == battery

    def test_add_grid(self):
        """Test adding a grid to the network."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        grid = network.add(
            "grid",
            "test_grid",
            import_limit=10000,
            export_limit=5000,
            price_import=[0.1, 0.2, 0.15],
            price_export=[0.05, 0.08, 0.06],
        )

        assert isinstance(grid, Grid)
        assert grid.name == "test_grid"
        assert "test_grid" in network.entities

    def test_add_load(self):
        """Test adding a load to the network."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        load = network.add(
            "load",
            "test_load",
            forecast=[1000, 1500, 2000],
        )

        assert isinstance(load, Load)
        assert load.name == "test_load"
        assert "test_load" in network.entities

    def test_add_generator(self):
        """Test adding a generator to the network."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        generator = network.add(
            "generator",
            "test_generator",
            forecast=[1000, 1500, 2000],
            curtailment=True,
        )

        assert isinstance(generator, Generator)
        assert generator.name == "test_generator"
        assert "test_generator" in network.entities

    def test_add_net(self):
        """Test adding a net to the network."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        net = network.add("net", "test_net")

        assert isinstance(net, Net)
        assert net.name == "test_net"
        assert "test_net" in network.entities

    def test_connect_entities(self):
        """Test connecting entities in the network."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        # Add entities
        network.add("battery", "battery1", capacity=10000, initial_charge_percentage=50)
        network.add(
            "grid",
            "grid1",
            import_limit=10000,
            export_limit=5000,
            price_import=[0.1, 0.2, 0.15],
            price_export=[0.05, 0.08, 0.06],
        )

        # Connect them
        connection = network.connect("battery1", "grid1", min_power=0, max_power=5000)

        assert connection is not None
        assert ("battery1", "grid1") in network.connections
        assert len(connection.power) == 3

    def test_connect_nonexistent_entities(self):
        """Test connecting nonexistent entities."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        with pytest.raises(ValueError, match="Source entity 'nonexistent' not found"):
            network.connect("nonexistent", "also_nonexistent")

    def test_simple_optimization(self):
        """Test a simple optimization scenario."""
        network = Network(
            name="test_network",
            period=3600,
            n_periods=3,
        )

        # Add a simple grid and load
        network.add(
            "grid",
            "grid",
            import_limit=10000,
            export_limit=5000,
            price_import=[0.1, 0.2, 0.15],
            price_export=[0.05, 0.08, 0.06],
        )
        network.add("load", "load", forecast=[1000, 1500, 2000])
        network.add("net", "net")

        # Connect them: grid -> net <- load
        network.connect("grid", "net")
        network.connect("net", "load")

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
            "generator", "solar", forecast=solar_forecast, curtailment=True, price_production=[0] * 8
        )  # Solar has no fuel cost

        network.add("load", "load", forecast=load_forecast)

        network.add(
            "battery",
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
            "grid",
            "grid",
            import_limit=10000,
            export_limit=10000,
            price_import=import_prices,
            price_export=export_prices,
        )

        network.add("net", "net")

        # Connect everything through the net
        network.connect("solar", "net")
        network.connect("battery", "net")
        network.connect("grid", "net")
        network.connect("net", "load")

        # Run optimization
        cost = network.optimize()

        # Verify the solution makes economic sense
        assert isinstance(cost, (int, float))
        assert cost > 0  # Should have some cost

        # Access optimization results directly from entities
        battery = network.entities["battery"]

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

        # Get battery power and energy values with proper type handling
        battery_charge = []
        battery_discharge = []
        battery_energy = []

        if battery.power_consumption is not None:
            battery_charge = [extract_value(p) for p in battery.power_consumption]
        if battery.power_production is not None:
            battery_discharge = [extract_value(p) for p in battery.power_production]
        if battery.energy is not None:
            battery_energy = [extract_value(e) for e in battery.energy]

        # Verify we have data
        assert len(battery_charge) == 8, "Should have 8 periods of charge data"
        assert len(battery_discharge) == 8, "Should have 8 periods of discharge data"
        assert len(battery_energy) == 8, "Should have 8 periods of energy data"

        # During high solar periods, battery should be charging (positive consumption)
        # or at least not discharging much
        high_solar_charge = sum(battery_charge[:4])
        low_solar_charge = sum(battery_charge[4:])

        # During high demand periods, battery should be discharging (positive production)
        low_solar_discharge = sum(battery_discharge[4:])
        high_solar_discharge = sum(battery_discharge[:4])

        # Verify energy storage behavior
        assert high_solar_charge >= low_solar_charge, "Battery should charge more during high solar"
        assert low_solar_discharge >= high_solar_discharge, "Battery should discharge more during high demand"

        # Verify energy conservation - battery energy should increase during charging periods
        initial_energy = battery_energy[0]
        mid_energy = battery_energy[3]  # End of charging period
        assert mid_energy >= initial_energy, "Battery energy should increase during charging period"

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
            "generator",
            "solar",
            forecast=solar_forecast,
            curtailment=True,  # Allow curtailment
            price_production=[0] * 6,
        )  # No fuel cost for solar

        network.add("load", "load", forecast=load_forecast)

        network.add(
            "grid",
            "grid",
            import_limit=10000,
            export_limit=10000,
            price_import=import_prices,
            price_export=export_prices,
        )

        network.add("net", "net")

        # Connect entities
        network.connect("solar", "net")
        network.connect("grid", "net")
        network.connect("net", "load")

        # Run optimization
        cost = network.optimize()

        # Verify solution
        assert isinstance(cost, (int, float))

        # Access optimization results directly from entities
        solar = network.entities["solar"]

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
