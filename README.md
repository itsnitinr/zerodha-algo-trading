# Nifty Trading Framework

A Python-based algorithmic trading framework for implementing and executing various trading strategies through the Zerodha platform.

## 🎯 Framework Overview

This trading framework provides a robust foundation for developing and executing algorithmic trading strategies with:

- **Modular Strategy Design**: Easy-to-extend strategy framework
- **Secure Authentication**: TOTP-based 2FA integration with Zerodha
- **Real-time Data**: Live market data and historical data fetching
- **Portfolio Management**: Automated trade execution and monitoring
- **Beautiful UI**: Rich console output with progress tracking

## 🏗️ Project Structure

```
nifty/
├── client/
│   └── zerodha.py          # Zerodha API client with 2FA authentication
├── strategy/
│   └── nifty_shop.py       # Example strategy implementation
├── utils/
│   ├── __init__.py
│   └── logger.py           # Comprehensive logging utilities
├── main.py                 # Application entry point
├── pyproject.toml          # Project dependencies and metadata
└── README.md              # This file
```

## 🚀 Features

### Trading Framework

- **Strategy Interface**: Standardized strategy development pattern
- **Technical Analysis**: Built-in support for technical indicators
- **Portfolio Management**: Position tracking and automated execution
- **Risk Controls**: Configurable trade limits and position sizing
- **Market Data**: Real-time and historical data integration

### Infrastructure

- **Secure Authentication**: TOTP-based 2FA for Zerodha login
- **Comprehensive Logging**: Rich console output with progress tracking
- **Error Handling**: Robust network and API error management
- **Session Management**: Persistent authenticated sessions

### User Experience

- **Beautiful Console Output**: Rich tables and progress bars
- **Detailed Logging**: Step-by-step execution tracking
- **Error Recovery**: Graceful handling of network issues
- **Extensible Design**: Easy to add new strategies

## 📋 Prerequisites

- Python 3.12 or higher
- Active Zerodha trading account
- TOTP setup for 2FA authentication
- Internet connection for real-time data

## 🛠️ Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd zerodha-algo-trading
   ```

2. **Install dependencies using uv:**

   ```bash
   uv sync
   ```

   Or with pip:

   ```bash
   pip install -e .
   ```

## ⚙️ Configuration

1. **Create a `.env` file in the root directory:**

   ```bash
   USER_ID=your_zerodha_user_id
   PASSWORD=your_zerodha_password
   TOTP_KEY=your_totp_secret_key
   ```

2. **Environment Variables:**
   - `USER_ID`: Your Zerodha user ID
   - `PASSWORD`: Your Zerodha password
   - `TOTP_KEY`: Your TOTP secret key for 2FA

## 🎮 Usage

### Basic Usage

Run the trading application:

```bash
python main.py
```

### Framework Execution Flow

1. **Authentication**: Secure login to Zerodha with 2FA
2. **Strategy Initialization**: Load and configure selected trading strategy
3. **Data Collection**: Fetch required market data for analysis
4. **Strategy Execution**: Run the strategy's trading logic
5. **Trade Management**: Execute buy/sell decisions through Zerodha API
6. **Monitoring**: Track performance and log all activities

## 📊 Dependencies

- **dotenv**: Environment variable management
- **pandas**: Data analysis and manipulation
- **pyotp**: TOTP-based 2FA authentication
- **requests**: HTTP client for API calls
- **rich**: Beautiful console output and formatting

## 🔧 Adding New Strategies

### Strategy Development

1. **Create a new strategy file** in the `strategy/` directory
2. **Implement the strategy interface** with required methods:

   - `__init__(self, zerodha_client)`: Initialize with client
   - `execute_strategy(self)`: Main execution logic
   - `get_name(self)`: Return strategy name

3. **Example strategy structure:**

   ```python
   class MyStrategy:
       def __init__(self, zerodha_client):
           self.client = zerodha_client
           # Strategy initialization

       def execute_strategy(self):
           # Your trading logic here
           pass

       def get_name(self):
           return "MyStrategy"
   ```

4. **Update main.py** to use your new strategy:
   ```python
   from strategy.my_strategy import MyStrategy
   strategy = MyStrategy(client)
   ```

## ⚠️ Important Disclaimers

### Trading Risks

- **Financial Risk**: Trading involves substantial risk of loss
- **Market Risk**: Past performance does not guarantee future results
- **Strategy Risk**: No strategy guarantees profits

### Technical Considerations

- **Real Money**: This application places actual trades with real money
- **Testing**: Always test thoroughly in a paper trading environment first
- **Monitoring**: Monitor all trades and system behavior closely
- **Backup Plans**: Have manual override procedures ready

### Legal and Compliance

- **Regulation**: Ensure compliance with local trading regulations
- **Broker Terms**: Review and comply with Zerodha's terms of service
- **Tax Implications**: Consult tax professionals for trading tax obligations

## 🔧 Development

### Running in Development Mode

```bash
# Install development dependencies
uv sync --dev

# Run with verbose logging
python main.py
```

### Code Structure

- **`client/zerodha.py`**: Handles all Zerodha API interactions
- **`strategy/`**: Directory for all trading strategy implementations
- **`utils/logger.py`**: Provides comprehensive logging functionality
- **`main.py`**: Orchestrates the complete application flow

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Failures**

   - Verify TOTP_KEY is correct
   - Check USER_ID and PASSWORD
   - Ensure stable internet connection

2. **API Rate Limits**

   - Zerodha has API rate limits
   - The application includes appropriate delays

3. **Missing Data**
   - Some stocks may have limited historical data
   - The framework gracefully handles missing data

### Debug Mode

Enable detailed logging by modifying the logger configuration in `utils/logger.py`.

## 📄 License

This project is provided as-is for educational and personal use. Users are responsible for compliance with all applicable laws and regulations.

---

**⚠️ IMPORTANT**: This software is for educational purposes. Always conduct thorough testing before using with real money. The authors are not responsible for any financial losses incurred through the use of this software.
