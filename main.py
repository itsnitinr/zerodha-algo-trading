from client.zerodha import ZerodhaClient
from strategy.nifty_shop import NiftyShopStrategy
from utils.logger import log_success, log_error, log_info, log_step, log_api_call, app_logger
import requests

NIFTY_50_SYMBOLS = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT",
    "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV",
    "BEL", "BHARTIARTL", "CIPLA", "COALINDIA", "DRREDDY",
    "EICHERMOT", "ETERNAL", "GRASIM", "HCLTECH", "HDFCBANK",
    "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR",
    "ICICIBANK", "INDUSINDBK", "INFY", "ITC", "JIOFIN",
    "JSWSTEEL", "KOTAKBANK", "LT", "M&M", "MARUTI", "NESTLEIND",
    "NTPC", "ONGC", "POWERGRID", "RELIANCE", "SBILIFE",
    "SBIN", "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS",
    "TATASTEEL", "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO"
]

def main():
    """Main application entry point with comprehensive logging."""
    
    log_step("Application Start", "🚀 Starting Nifty Trading Application")
    
    try:
        # Initialize and authenticate
        log_step("Client Setup", "Initializing Zerodha client")
        client = ZerodhaClient()
        
        log_step("Authentication", "Starting authentication process")
        session = client.login()
        
        log_success("Authentication completed! Session is ready for trading operations")
        
        # Initialize and run strategy
        log_step("Strategy Setup", "Initializing Nifty Shop Strategy")
        strategy = NiftyShopStrategy(client)
        
        log_step("Strategy Execution", "Running complete strategy: analysis + trading logic")
        strategy.execute_strategy()
        
        # Final application summary
        log_success("🎯 Nifty Shop Strategy execution completed!")
        log_info("Strategy has analyzed stocks, checked holdings, and executed trading logic")
        log_info("Check the output above for detailed results and any trades placed")
        
        
    except ValueError as e:
        log_error(f"Configuration error: {str(e)}")
        log_error("Please check your credentials and try again")
        return 1
        
    except requests.RequestException as e:
        log_error(f"Network error: {str(e)}")
        log_error("Please check your internet connection and try again")
        return 1
        
    except Exception as e:
        log_error(f"Unexpected error: {str(e)}")
        app_logger.exception("Full error traceback:")
        return 1
    
    log_info("Application finished successfully")
    return 0


if __name__ == "__main__":
    exit(main())
