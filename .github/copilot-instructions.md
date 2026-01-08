# Copilot Instructions for raspyrfm-client

This document provides guidance for GitHub Copilot when working with the raspyrfm-client repository.

## Project Overview

`raspyrfm-client` is a Python library for generating and sending 433/868 MHz RF signals to control smart home devices through gateways like RaspyRFM. The library provides:

- A high-level `RaspyRFMClient` façade for device control
- Extensible gateway implementations for different hardware manufacturers
- Control unit implementations for various RF receiver devices (switches, dimmers, etc.)
- Home Assistant integration components

### Repository Structure

```
.
├── custom_components/              # Home Assistant integration (optional)
├── docs/                           # Sphinx documentation project
├── example*.py                     # Usage examples
├── raspyrfm_client/                # Main Python package
│   ├── client.py                   # High-level RaspyRFMClient façade
│   └── device_implementations/     # Gateway and control-unit specifics
│       ├── controlunit/            # RF receiver device implementations
│       │   ├── base.py             # ControlUnit base class
│       │   ├── actions.py          # Action enum (ON, OFF, etc.)
│       │   └── manufacturer/       # Manufacturer-specific implementations
│       └── gateway/                # RF gateway implementations
│           ├── base.py             # Gateway base class
│           └── manufacturer/       # Gateway-specific implementations
└── tests/                          # pytest-based test suite
```

## Python Version and Dependencies

- **Minimum Python version**: 3.10
- **Supported versions**: 3.10, 3.11, 3.12, 3.13
- **Package manager**: Poetry (see `pyproject.toml`)
- **Testing**: pytest
- **Linting**: flake8

## Development Workflow

### Setting Up the Environment

```bash
# Install Poetry if needed
pip install poetry

# Install dependencies
poetry install --with test

# Activate the virtual environment
poetry shell
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific tests
poetry run pytest -k "test_pattern"

# Run with verbose output
poetry run pytest -vv
```

### Linting

```bash
# Install flake8
pip install flake8

# Check for critical errors
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Full check with warnings
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

### Building Documentation

```bash
cd docs
make html  # or .\make.bat html on Windows
# View docs/_build/html/index.html
```

## Coding Conventions

### General Style

- Follow PEP 8 guidelines with a **maximum line length of 127 characters**
- Use descriptive variable names
- Include docstrings for classes and non-trivial methods
- Use type hints for method parameters and return values where appropriate

### Import Style

- Organize imports: standard library, third-party, local imports
- Use absolute imports from the `raspyrfm_client` package
- Import enums where they're used (see examples below)

Example from control unit implementations:
```python
from raspyrfm_client.device_implementations.controlunit.actions import Action
from raspyrfm_client.device_implementations.controlunit.base import ControlUnit
from raspyrfm_client.device_implementations.manufacturer_constants import Manufacturer
from raspyrfm_client.device_implementations.controlunit.controlunit_constants import ControlUnitModel
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `RaspyRFMClient`, `ControlUnit`, `RCS1000NComfort`)
- **Methods/Functions**: snake_case (e.g., `get_channel_config`, `send_code`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `_GATEWAY_IMPLEMENTATIONS_DICT`)
- **Private members**: Prefix with underscore (e.g., `_manufacturer`, `_channel`)

### Enums

- Manufacturer and model constants are defined as enums
- Import enum classes locally in `__init__` methods to avoid circular imports:

```python
def __init__(self):
    from raspyrfm_client.device_implementations.manufacturer_constants import Manufacturer
    from raspyrfm_client.device_implementations.controlunit.controlunit_constants import ControlUnitModel
    super().__init__(Manufacturer.BRENNENSTUHL, ControlUnitModel.RCS_1000_N_COMFORT)
```

## Architecture Patterns

### Dynamic Class Loading

The library uses dynamic import to discover all gateway and control unit implementations at runtime. When creating new implementations:

1. **No manual registration needed** - classes are discovered automatically via `__import_submodules()`
2. **Inheritance-based discovery** - all subclasses of `Gateway` and `ControlUnit` are loaded
3. **Opt-out mechanism** - add `DISABLED = True` class field to exclude WIP implementations

### Control Unit Implementation Pattern

When creating a new control unit:

1. **Extend `ControlUnit` base class** from `raspyrfm_client.device_implementations.controlunit.base`
2. **Place in manufacturer directory** under `raspyrfm_client/device_implementations/controlunit/manufacturer/`
3. **Implement required methods**:
   - `__init__()` - call super with manufacturer and model enums
   - `get_supported_actions()` - return list of supported Action enum values
   - `get_channel_config_args()` - return dict of config keys with validation regexes
   - `get_pulse_data()` or `get_bit_data()` - return RF signal data

Example structure:
```python
class YourDevice(ControlUnit):
    def __init__(self):
        from raspyrfm_client.device_implementations.manufacturer_constants import Manufacturer
        from raspyrfm_client.device_implementations.controlunit.controlunit_constants import ControlUnitModel
        super().__init__(Manufacturer.YOUR_MANUFACTURER, ControlUnitModel.YOUR_MODEL)
    
    def get_supported_actions(self) -> [Action]:
        return [Action.ON, Action.OFF]
    
    def get_channel_config_args(self):
        return {
            'id': '^[A-F]$',      # Channel ID A-F
            'channel': '^[1-4]$'   # Channel number 1-4
        }
    
    def get_pulse_data(self, action: Action):
        # Return pulse pairs, repetitions, and timebase
        return [[high, low], [high, low]], repetitions, timebase
```

### Gateway Implementation Pattern

When creating a new gateway:

1. **Extend `Gateway` base class** from `raspyrfm_client.device_implementations.gateway.base`
2. **Place in manufacturer directory** under `raspyrfm_client/device_implementations/gateway/manufacturer/`
3. **Implement required methods**:
   - `get_manufacturer()` and `get_model()` - return enum values
   - `get_search_response_regex_literal()` - regex for discovery responses
   - `create_from_broadcast()` - instantiate from discovery data
   - `generate_code()` - transform device/action to gateway-specific payload

### Channel Configuration

- Channel configs are **keyed dictionaries** with string keys
- Validation uses **regex patterns** defined in `get_channel_config_args()`
- Config is validated in `set_channel_config()` before being stored

Example:
```python
device.set_channel_config(**{
    '1': '1',     # DIP switch 1 = ON
    '2': '0',     # DIP switch 2 = OFF
    '3': '1',
    '4': '1',
    '5': '0',
    'CH': 'A'     # Channel A
})
```

## Testing Guidelines

### Test Structure

- Tests are located in the `tests/` directory
- Primary test file: `tests/automatic_test.py`
- Tests use `unittest.TestCase` framework
- Tests validate random configurations against all device implementations

### Test Patterns

The main test suite (`automatic_test.py`) validates:

1. **Manufacturer and model retrieval** - ensures enums are properly defined
2. **Supported actions** - verifies action lists are non-empty
3. **Channel configuration** - tests 50 random valid configurations per device
4. **Code generation** - ensures gateways can generate codes for all device/action pairs

### Writing New Tests

When adding new device implementations, the existing test suite will automatically cover them. For additional specific tests:

```python
import unittest
from raspyrfm_client import RaspyRFMClient
from raspyrfm_client.device_implementations.manufacturer_constants import Manufacturer
from raspyrfm_client.device_implementations.controlunit.controlunit_constants import ControlUnitModel

class TestNewDevice(unittest.TestCase):
    def test_device_behavior(self):
        client = RaspyRFMClient()
        device = client.get_controlunit(Manufacturer.YOUR_MANUFACTURER, ControlUnitModel.YOUR_MODEL)
        # Add specific assertions
        self.assertIsNotNone(device)
```

## Adding New Implementations

### Adding a Control Unit

1. **Create manufacturer directory** if it doesn't exist:
   ```
   raspyrfm_client/device_implementations/controlunit/manufacturer/yourmanufacturer/
   ```

2. **Add `__init__.py`** to make it a package

3. **Create implementation file** (e.g., `yourmodel.py`) with class extending `ControlUnit`

4. **Register enums** if needed:
   - Add manufacturer to `manufacturer_constants.py` if new
   - Add model to `controlunit_constants.py`

5. **Test** - run `pytest` to verify automatic discovery and validation

### Adding a Gateway

1. **Create manufacturer directory** if it doesn't exist:
   ```
   raspyrfm_client/device_implementations/gateway/manufacturer/yourmanufacturer/
   ```

2. **Add `__init__.py`** to make it a package

3. **Create implementation file** with class extending `Gateway`

4. **Register enums** in `gateway_constants.py` if needed

5. **Test** - verify discovery, code generation, and UDP communication

## Common Patterns and Best Practices

### Pattern: HX2262 Compatible Devices

Many devices use the HX2262 chip. Use `HX2262Compatible` base class for these:

```python
from raspyrfm_client.device_implementations.controlunit.manufacturer.universal.HX2262Compatible import HX2262Compatible

class YourDevice(HX2262Compatible):
    _l = 'f'  # Low bit representation
    _h = '0'  # High bit representation
    _on = [_l, _l]
    _off = [_l, _h]
    _repetitions = 5
```

### Pattern: Bit Calculation Utilities

Use `calc_match_bits()` helper for channel encoding:

```python
ch = ord(cfg['CH']) - ord('A')  # Convert 'A'-'E' to 0-4
bits += self.calc_match_bits(ch, 5, (self._l, self._h))
```

### Anti-Pattern: Manual Class Registration

❌ **Don't** manually register implementations - the client discovers them automatically

❌ **Don't** import implementations in `__init__.py` - the dynamic loader handles this

✅ **Do** ensure your class properly extends `ControlUnit` or `Gateway`

✅ **Do** call `super().__init__()` with correct manufacturer/model enums

### Anti-Pattern: Hardcoded Values

❌ **Don't** hardcode IP addresses or ports in implementations

❌ **Don't** use magic numbers without constants or comments

✅ **Do** use manufacturer/model enums for identification

✅ **Do** define default ports in gateway implementations

## Documentation

### Docstring Style

Use clear, concise docstrings with parameter descriptions:

```python
def get_channel_config_args(self):
    """
    Returns required config arguments and their validation regexes.
    
    :return: dictionary mapping config keys to regex patterns
    
    Example: {"ID": "^[A-F]$", "CH": "^[1-4]$"}
    """
```

### Code Comments

- Add comments for complex bit manipulation logic
- Explain protocol-specific encoding schemes
- Document RF timing values and their significance
- Reference hardware datasheets when applicable

## Common Tasks

### Listing Supported Devices

```python
rfm_client = RaspyRFMClient()
rfm_client.list_supported_gateways()
rfm_client.list_supported_controlunits()
```

### Sending a Command

```python
# Get gateway and device
gateway = client.get_gateway(Manufacturer.SEEGEL_SYSTEME, GatewayModel.RASPYRFM, "192.168.1.100")
device = client.get_controlunit(Manufacturer.BRENNENSTUHL, ControlUnitModel.RCS_1000_N_COMFORT)

# Configure device
device.set_channel_config(**{'1': '1', '2': '0', '3': '1', '4': '1', '5': '0', 'CH': 'A'})

# Send command
client.send(gateway, device, Action.ON)
```

### Debugging Device Discovery

```python
# Search for gateways on the network
gateways = client.search()
for gateway in gateways:
    print(f"Found: {gateway}")
```

## Security and Network Considerations

- **UDP broadcast**: Discovery uses UDP broadcast on port 49880
- **No authentication**: Most gateways don't require authentication (be mindful of network security)
- **Fire-and-forget**: UDP is unreliable; consider sending commands multiple times
- **Local network only**: Designed for LAN operation, not internet-facing

## Home Assistant Integration

The `custom_components/raspyrfm` directory contains a Home Assistant custom integration. When working on this:

- Follows Home Assistant integration patterns and structure
- Uses the same `raspyrfm_client` library as core package
- Provides UI for code learning and device management
- Exposes control units as Home Assistant entities

## Error Handling

- **Channel config validation**: `set_channel_config()` raises `ValueError` with descriptive messages
- **Missing implementations**: Client prints error if manufacturer/model not found
- **Network errors**: UDP operations may timeout; wrap in try/except for socket operations
- **Import errors**: If implementations aren't discovered, call `reload_implementation_classes()`

## Performance Considerations

- **Dynamic loading**: Happens once per `RaspyRFMClient()` instantiation
- **Code generation**: Lightweight bit manipulation, no significant overhead
- **Network latency**: UDP transmission is typically < 10ms on LAN
- **Multiple commands**: Add small delays (0.1-0.5s) between repeated commands

## Additional Resources

- **MANUAL.md**: Comprehensive repository manual with detailed examples
- **README.rst**: PyPI/GitHub project description
- **docs/**: Sphinx-generated API documentation
- **example*.py**: Working code samples for common use cases
- **tests/automatic_test.py**: Reference for testing patterns

## Getting Help

- Check existing device implementations for similar hardware
- Review test suite for usage patterns
- Consult MANUAL.md for detailed workflow guidance
- Search the issue tracker on GitHub for similar problems
