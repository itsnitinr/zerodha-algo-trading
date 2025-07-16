# Configuration System Documentation

## Overview

The Nifty Shop Strategy now includes a powerful configuration system that allows you to customize trading parameters without modifying code. This system provides:

- **Interactive Setup**: First-time configuration with prompts and validation
- **Persistent Storage**: Settings are saved and automatically loaded
- **Easy Reconfiguration**: Change settings anytime with command-line flags
- **Validation**: Built-in validation ensures parameters are reasonable

## Configurable Parameters

Currently, you can configure these trading parameters:

| Parameter             | Description                          | Default | Range                             |
| --------------------- | ------------------------------------ | ------- | --------------------------------- |
| **Daily Trade Limit** | Maximum new stocks to buy per day    | 1       | 1-10 (with confirmation for >10)  |
| **Profit Threshold**  | Profit percentage to trigger selling | 5.0%    | >0% (with confirmation for >50%)  |
| **Loss Threshold**    | Loss percentage to trigger averaging | -3.0%   | <0% (with confirmation for <-20%) |

## Getting Started

### First Run Setup

When you run the strategy for the first time, you'll automatically be prompted to configure your parameters:

```bash
uv run python main.py
```

This will start an interactive configuration wizard that walks you through setting up each parameter.

### Configuration-Only Mode

To just configure parameters without running the strategy:

```bash
uv run python main.py --config-only
```

This is useful when you want to set up your configuration in advance.

## Reconfiguration

### Using Command Line

To reconfigure existing settings:

```bash
uv run python main.py --reconfigure
```

This forces the interactive setup even if configuration already exists.

### Interactive Demo

To safely explore the configuration system without affecting your settings:

```bash
uv run python demo_config.py
```

This runs a demonstration of the configuration process.

## Configuration File

Settings are stored in `config/strategy_config.json`. The file structure looks like:

```json
{
  "daily_trade_limit": 1,
  "profit_threshold_for_selling": 5.0,
  "loss_threshold_for_averaging": -3.0,
  "config_version": "1.0",
  "last_updated": "2025-01-16T21:38:35.123456"
}
```

### Important Notes

- The `config/` directory is excluded from git (in `.gitignore`)
- Configuration is validated on load
- Missing parameters are filled with defaults
- Invalid configurations fall back to defaults with warnings

## Validation Rules

The system includes built-in validation:

### Daily Trade Limit

- Must be greater than 0
- Warning prompt for values > 10

### Profit Threshold

- Must be positive (> 0%)
- Warning prompt for values > 50%

### Loss Threshold

- Must be negative (< 0%)
- Warning prompt for values < -20%

## Testing the Configuration

### Quick Test

```bash
uv run python test_config.py
```

This tests the configuration system without requiring authentication.

### Interactive Demo

```bash
uv run python demo_config.py
```

This provides a full interactive demonstration of the configuration process.

## Command Line Options

| Option                         | Description                                               |
| ------------------------------ | --------------------------------------------------------- |
| `python main.py`               | Run with existing config (prompts for setup on first run) |
| `python main.py --config-only` | Configure parameters only, don't run strategy             |
| `python main.py --reconfigure` | Force reconfiguration of existing settings                |
| `python main.py --help`        | Show all available options                                |

## Impact on Strategy Behavior

The configured parameters directly affect strategy execution:

### Daily Trade Limit

- Controls how many new positions can be opened per day
- Once limit is reached, no new stocks are purchased
- Averaging existing positions is still allowed

### Profit Threshold

- Determines when profitable positions are sold
- Only applies to Nifty 50 holdings
- Positions above this threshold are automatically sold

### Loss Threshold

- Triggers averaging down on existing positions
- Only applies to Nifty 50 holdings
- Must be a negative percentage (e.g., -3.0 for 3% loss)

## Troubleshooting

### Configuration Not Loading

- Check if `config/strategy_config.json` exists
- Verify JSON format is valid
- Configuration will fall back to defaults if corrupted

### Validation Errors

- Ensure daily trade limit is > 0
- Ensure profit threshold is positive
- Ensure loss threshold is negative

### Permission Issues

- Ensure write permissions to `config/` directory
- Configuration will work with read-only mode (no saving)

## Future Enhancements

The configuration system is designed to be extensible. Future versions may include:

- Capital allocation strategies
- Technical analysis parameters
- Risk management settings
- Market condition filters
- Sector exposure limits

## Support

For issues with the configuration system:

1. Run `uv run python test_config.py` to verify system health
2. Check log files for detailed error messages
3. Use `--reconfigure` to reset problematic configurations
4. Configuration always falls back to safe defaults
