"""
Nifty Shop Strategy - Finds stocks trading below their 20-day moving average.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional
import pandas as pd
import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel

from client.zerodha import ZerodhaClient
from utils.logger import log_success, log_error, log_info, log_step, log_warning, get_logger


class NiftyShopStrategy:
    """Strategy to identify Nifty 50 stocks trading below their 20-day moving average."""
    
    def __init__(self, zerodha_client: ZerodhaClient):
        """
        Initialize the strategy with a Zerodha client.
        
        Args:
            zerodha_client: Authenticated Zerodha client instance
        """
        self.logger = get_logger("nifty_shop_strategy")
        self.client = zerodha_client
        self.session = None
        self.instrument_tokens = {}
        self.console = Console()
        
        # Trading configuration
        self.daily_trade_limit = 1  # Maximum new stocks to buy per day
        
        # Mock trade management (in real implementation, this would come from actual broker/database)
        self.mock_trades = []  # List of mock trades to simulate holdings
        
        # Nifty 50 symbols (same as in main.py but imported here for strategy independence)
        self.symbols = [
            "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
            "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BEL", "BHARTIARTL",
            "CIPLA", "COALINDIA", "DRREDDY", "EICHERMOT", "ETERNAL",
            "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO",
            "HINDALCO", "HINDUNILVR", "ICICIBANK", "ITC", "INDUSINDBK",
            "INFY", "JSWSTEEL", "JIOFIN", "KOTAKBANK", "LT",
            "M&M", "MARUTI", "NTPC", "NESTLEIND", "ONGC",
            "POWERGRID", "RELIANCE", "SBILIFE", "SHRIRAMFIN", "SBIN",
            "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS", "TATASTEEL",
            "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO"
        ]
        
        # Display strategy initialization in a beautiful panel
        panel = Panel(
            f"[bold cyan]Nifty Shop Strategy[/bold cyan]\n\n"
            f"💰 Sell Logic: Holdings with >5% profit\n"
            f"📈 Buy Logic: Find stocks trading below 20-day moving average\n"
            f"🎯 Universe: Nifty 50 ({len(self.symbols)} stocks)\n"
            f"📊 Target: Top 5 stocks with highest deviation below 20DMA\n"
            f"⚡ Execution: Sell → Analysis → Buy",
            title="[bold green]🚀 Strategy Initialized[/bold green]",
            border_style="bright_blue"
        )
        self.console.print(panel)
    
    def get_name(self) -> str:
        """Get strategy name for logging."""
        return "NiftyShopStrategy"
    
    def _get_authenticated_session(self) -> requests.Session:
        """Get authenticated session from Zerodha client."""
        if self.session is None:
            log_step("Session Setup", "Getting authenticated session from Zerodha client")
            self.session = self.client.get_authenticated_session()
            log_success("Session ready for API calls")
        return self.session
    
    def _fetch_instrument_tokens(self) -> bool:
        """
        Fetch instrument tokens for all Nifty 50 symbols.
        
        Returns:
            bool: True if successful, False otherwise
        """
        log_step("Instrument Mapping", "Fetching instrument tokens for Nifty 50 symbols")
        
        try:
            session = self._get_authenticated_session()
            
            # Fetch instruments list
            instruments_url = "https://api.kite.trade/instruments"
            headers = {"X-Kite-Version": "3"}
            
            response = session.get(instruments_url, headers=headers)
            response.raise_for_status()
            
            # Parse CSV response
            lines = response.text.strip().split('\n')
            headers_line = lines[0].split(',')
            
            # Find relevant column indices
            token_idx = headers_line.index('instrument_token')
            symbol_idx = headers_line.index('tradingsymbol')
            exchange_idx = headers_line.index('exchange')
            instrument_type_idx = headers_line.index('instrument_type')
            
            # Extract NSE equity instruments
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) > max(token_idx, symbol_idx, exchange_idx, instrument_type_idx):
                    exchange = parts[exchange_idx]
                    instrument_type = parts[instrument_type_idx]
                    symbol = parts[symbol_idx]
                    
                    if exchange == 'NSE' and instrument_type == 'EQ' and symbol in self.symbols:
                        token = parts[token_idx]
                        self.instrument_tokens[symbol] = token
            
            found_count = len(self.instrument_tokens)
            
            if found_count == 0:
                log_error("No instrument tokens found for any Nifty 50 symbols")
                return False
            
            # Display instrument mapping results in a table
            table = Table(title="📋 Instrument Token Mapping Results")
            table.add_column("Symbol", style="cyan", no_wrap=True)
            table.add_column("Instrument Token", style="magenta")
            table.add_column("Status", style="green")
            
            for symbol in self.symbols:
                if symbol in self.instrument_tokens:
                    table.add_row(symbol, self.instrument_tokens[symbol], "✅ Found")
                else:
                    table.add_row(symbol, "N/A", "❌ Not Found")
            
            self.console.print(table)
            log_success(f"Successfully mapped {found_count} out of {len(self.symbols)} symbols to instrument tokens")
            
            return True
            
        except Exception as e:
            log_error(f"Error fetching instrument tokens: {str(e)}")
            return False
    
    def _get_historical_data(self, symbol: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a symbol using Zerodha API.
        
        Args:
            symbol: Stock symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        if symbol not in self.instrument_tokens:
            log_warning(f"No instrument token found for symbol: {symbol}")
            return None
        
        try:
            session = self._get_authenticated_session()
            token = self.instrument_tokens[symbol]
            
            # Format dates for API (YYYY-MM-DD format without time)
            from_date = start_date.strftime("%Y-%m-%d")
            to_date = end_date.strftime("%Y-%m-%d")
            
            # Construct API URL and parameters based on reference implementation
            url = f"https://kite.zerodha.com/oms/instruments/historical/{token}/day"
            params = {
                "from": from_date,
                "to": to_date,
                "continuous": 0,
                "oi": 0
            }
            
            # Zerodha API requires X-Kite-Version header
            headers = {"X-Kite-Version": "3"}
            
            # Reduced logging since we now have progress bar
            # log_info(f"Fetching data for {symbol} (token: {token}) from {from_date} to {to_date}")
            
            response = session.get(url, params=params, headers=headers)
            
            # Better error handling to see what's wrong
            if response.status_code != 200:
                log_error(f"HTTP {response.status_code} error for {symbol}")
                log_error(f"Response: {response.text}")
                return None
            
            data = response.json()
            
            if data.get('status') != 'success':
                log_error(f"API error for {symbol}: {data}")
                return None
            
            if 'data' not in data or 'candles' not in data['data']:
                log_warning(f"No data structure found for {symbol}: {data}")
                return None
            
            candles = data['data']['candles']
            if not candles:
                log_warning(f"No candle data found for {symbol}")
                return None
            
            # Convert to DataFrame following the reference format
            records = []
            for candle in candles:
                record = {
                    "date": pd.to_datetime(candle[0]),
                    "open": candle[1],
                    "high": candle[2], 
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5]
                }
                records.append(record)
            
            df = pd.DataFrame(records)
            df.set_index('date', inplace=True)
            
            # Rename columns to match expected format
            df.rename(columns={'close': 'Close'}, inplace=True)
            
            # Reduced logging since we now have progress bar showing status
            return df
            
        except Exception as e:
            log_error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def get_eligible_stocks_for_today(self) -> List[str]:
        """
        Calculate price fall percentage from 20DMA and select top 5 stocks.
        
        Returns:
            List of top 5 stock symbols that are trading below their 20DMA
        """
        log_step("Strategy Execution", "Starting eligible stocks identification for today")
        
        # Fetch instrument tokens if not already done
        if not self.instrument_tokens:
            if not self._fetch_instrument_tokens():
                log_error(f"{self.get_name()}: Error while fetching instrument tokens. Skipping strategy")
                return []
        
        if len(self.symbols) == 0:
            log_error(f"{self.get_name()}: Error while fetching stock list from Nifty universe. Skipping strategy")
            return []
        
        results = []
        end_date = date.today()
        start_date = end_date - timedelta(days=60)  # To ensure we have at least 20 days of data
        
        # Create analysis info panel
        analysis_panel = Panel(
            f"[bold]Analysis Period:[/bold] {start_date} to {end_date}\n"
            f"[bold]Stocks to Process:[/bold] {len(self.symbols)}\n"
            f"[bold]Looking for:[/bold] Stocks trading below 20-day moving average",
            title="📊 Analysis Configuration",
            border_style="yellow"
        )
        self.console.print(analysis_panel)
        
        # Create a progress bar for processing stocks
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Processing stocks...", total=len(self.symbols))
            
            for symbol in self.symbols:
                progress.update(task, description=f"Processing [cyan]{symbol}[/cyan]...")
                
                try:
                    df = self._get_historical_data(symbol, start_date, end_date)
                    
                    if df is None or df.empty or 'Close' not in df.columns:
                        progress.console.print(f"  [yellow]⚠️  {symbol}: No valid data[/yellow]")
                        progress.advance(task)
                        continue
                    
                    # Sort by date and calculate 20DMA
                    df = df.sort_index()
                    df['20DMA'] = df['Close'].rolling(window=20).mean()
                    
                    latest_close = df['Close'].iloc[-1]
                    latest_dma = df['20DMA'].iloc[-1]
                    
                    if pd.isna(latest_dma):
                        progress.console.print(f"  [yellow]⚠️  {symbol}: No valid 20DMA[/yellow]")
                        progress.advance(task)
                        continue
                    
                    # Calculate deviation percentage
                    deviation = ((latest_close - latest_dma) / latest_dma) * 100
                    
                    # Only consider stocks below their 20DMA
                    if latest_close < latest_dma:
                        results.append((symbol, deviation, latest_close, latest_dma))
                        progress.console.print(f"  [green]✅ {symbol}: {deviation:.2f}% below 20DMA[/green]")
                    else:
                        progress.console.print(f"  [dim]📈 {symbol}: {deviation:.2f}% above 20DMA[/dim]")
                    
                except Exception as e:
                    progress.console.print(f"  [red]❌ {symbol}: Error - {str(e)}[/red]")
                
                progress.advance(task)
        
        # Sort by deviation ascending (more negative = farther below 20DMA)
        sorted_results = sorted(results, key=lambda x: x[1])
        
        # Extract just the top 5 symbols
        top_5_symbols = [symbol for symbol, _, _, _ in sorted_results[:5]]
        
        # Create results summary
        if results:
            # Create results table
            results_table = Table(title="🎯 Analysis Results - Stocks Below 20DMA")
            results_table.add_column("Rank", style="bold cyan", width=6)
            results_table.add_column("Symbol", style="bold yellow", width=12)
            results_table.add_column("Current Price", style="white", width=12)
            results_table.add_column("20DMA", style="blue", width=12)
            results_table.add_column("Deviation %", style="red", width=12)
            results_table.add_column("Status", style="green", width=15)
            
            for i, (symbol, deviation, close_price, dma_price) in enumerate(sorted_results, 1):
                status = "🏆 TOP 5" if i <= 5 else "📊 Below 20DMA"
                rank_style = "bold red" if i <= 5 else "dim"
                
                results_table.add_row(
                    f"[{rank_style}]{i}[/{rank_style}]",
                    symbol,
                    f"₹{close_price:.2f}",
                    f"₹{dma_price:.2f}",
                    f"{deviation:.2f}%",
                    status
                )
            
            self.console.print(results_table)
            
            if top_5_symbols:
                # Create final summary panel
                summary_text = "\n".join([
                    f"[bold cyan]{i}. {symbol}[/bold cyan] - [red]{sorted_results[i-1][1]:.2f}%[/red] below 20DMA"
                    for i, symbol in enumerate(top_5_symbols, 1)
                ])
                
                summary_panel = Panel(
                    summary_text,
                    title="[bold green]🏆 Top 5 Eligible Stocks[/bold green]",
                    border_style="bright_green"
                )
                self.console.print(summary_panel)
                
                log_success(f"Strategy completed! Found {len(top_5_symbols)} eligible stocks for trading")
            else:
                self.console.print(Panel(
                    "[yellow]No stocks found in top 5 range, but some stocks are below 20DMA[/yellow]",
                    title="📊 Results Summary",
                    border_style="yellow"
                ))
        else:
            # No stocks below 20DMA
            self.console.print(Panel(
                "[red]No stocks found trading below their 20-day moving average today.[/red]\n\n"
                "[yellow]This could indicate:[/yellow]\n"
                "• Strong market conditions\n"
                "• All Nifty 50 stocks are performing well\n"
                "• Consider adjusting strategy parameters",
                title="📈 No Eligible Stocks Found",
                border_style="red"
            ))
            log_info("No stocks found trading below their 20DMA today")
        
        # Final execution summary
        execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_panel = Panel(
            f"[bold]Execution completed at:[/bold] {execution_time}\n"
            f"[bold]Stocks analyzed:[/bold] {len(self.symbols)}\n"
            f"[bold]Stocks below 20DMA:[/bold] {len(results)}\n"
            f"[bold]Top 5 selected:[/bold] {len(top_5_symbols)}\n\n"
            f"[dim]Strategy: NiftyShopStrategy | Status: ✅ Complete[/dim]",
            title="📊 Execution Summary",
            border_style="bright_magenta"
        )
        self.console.print(final_panel)
        
        return top_5_symbols
    
    # ==================== TRADING LOGIC METHODS ====================
    
    def _get_current_holdings(self) -> List[dict]:
        """
        Get current holdings from Zerodha API.
        
        Returns:
            List of holdings with symbol, entry price, and timestamp
        """
        try:
            log_step("Holdings Fetch", "Fetching current holdings from Zerodha API")
            
            session = self._get_authenticated_session()
            holdings_url = "https://kite.zerodha.com/oms/portfolio/holdings"
            headers = {"X-Kite-Version": "3"}
            
            response = session.get(holdings_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'success':
                log_error(f"API error while fetching holdings: {data}")
                return []
            
            if 'data' not in data:
                log_warning("No holdings data found in API response")
                return []
            
            holdings_data = data['data']
            
            # Convert Zerodha holdings format to our internal format
            converted_holdings = []
            for holding in holdings_data:
                # Only include holdings with quantity > 0
                if holding.get('quantity', 0) > 0:
                    converted_holding = {
                        'tradingSymbol': holding.get('tradingsymbol', ''),
                        'entry': holding.get('average_price', 0.0),
                        'quantity': holding.get('quantity', 0),
                        'createTimestamp': datetime.now(),  # Zerodha doesn't provide exact purchase date in holdings
                        'pnl': holding.get('pnl', 0.0),
                        'last_price': holding.get('last_price', 0.0)
                    }
                    converted_holdings.append(converted_holding)
            
            log_success(f"Successfully fetched {len(converted_holdings)} holdings from Zerodha")
            
            # Display holdings summary
            if converted_holdings:
                holdings_summary_table = Table(title="💼 Current Holdings from Zerodha")
                holdings_summary_table.add_column("Symbol", style="cyan")
                holdings_summary_table.add_column("Qty", style="white") 
                holdings_summary_table.add_column("Avg Price", style="yellow")
                holdings_summary_table.add_column("LTP", style="green")
                holdings_summary_table.add_column("P&L", style="red")
                
                for holding in converted_holdings:
                    pnl_color = "green" if holding['pnl'] >= 0 else "red"
                    holdings_summary_table.add_row(
                        holding['tradingSymbol'],
                        str(holding['quantity']),
                        f"₹{holding['entry']:.2f}",
                        f"₹{holding['last_price']:.2f}",
                        f"[{pnl_color}]₹{holding['pnl']:.2f}[/{pnl_color}]"
                    )
                
                self.console.print(holdings_summary_table)
            
            return converted_holdings
            
        except Exception as e:
            log_error(f"Error fetching holdings from Zerodha API: {str(e)}")
            log_warning("Falling back to mock trades for this session")
            return self.mock_trades
    
    def _get_cmp(self, symbol: str) -> Optional[float]:
        """
        Get current market price for a symbol.
        In real implementation, this would fetch live price from broker.
        For now, using mock prices based on recent historical data.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current market price or None if failed
        """
        try:
            # For demonstration, we'll fetch the latest close price from historical data
            # In real implementation, this would use live price feeds
            end_date = date.today()
            start_date = end_date - timedelta(days=5)  # Get recent data
            
            df = self._get_historical_data(symbol, start_date, end_date)
            
            if df is None or df.empty or 'Close' not in df.columns:
                log_warning(f"Could not fetch current price for {symbol}")
                return None
            
            current_price = df['Close'].iloc[-1]
            return float(current_price)
            
        except Exception as e:
            log_error(f"Error fetching current price for {symbol}: {str(e)}")
            return None
    
    def _place_sell_order(self, symbol: str, holding: dict) -> bool:
        """
        Mock implementation of placing a sell order.
        In real implementation, this would place actual sell orders through broker.
        
        Args:
            symbol: Stock symbol to sell
            holding: Holding information with entry price, quantity, etc.
            
        Returns:
            bool: True if order placed successfully, False otherwise
        """
        try:
            current_price = self._get_cmp(symbol)
            
            if current_price is None:
                log_error(f"Cannot place sell order for {symbol}: Price unavailable")
                return False
            
            # Calculate profit
            entry_price = holding['entry']
            profit_amount = (current_price - entry_price) * holding['quantity']
            profit_pct = ((current_price - entry_price) / entry_price) * 100
            
            # Display sell order confirmation
            self.console.print(f"[bold red]💰 MOCK SELL ORDER PLACED[/bold red]")
            self.console.print(f"[cyan]Symbol:[/cyan] {symbol}")
            self.console.print(f"[cyan]Quantity:[/cyan] {holding['quantity']}")
            self.console.print(f"[cyan]Entry Price:[/cyan] ₹{entry_price:.2f}")
            self.console.print(f"[cyan]Current Price:[/cyan] ₹{current_price:.2f}")
            self.console.print(f"[cyan]Profit:[/cyan] [bold green]₹{profit_amount:.2f} ({profit_pct:.2f}%)[/bold green]")
            self.console.print(f"[cyan]Time:[/cyan] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.console.print(f"[yellow]Note: This is a mock order - no real trade executed[/yellow]\n")
            
            log_success(f"Mock sell order placed for {symbol} at ₹{current_price:.2f} with {profit_pct:.2f}% profit")
            return True
            
        except Exception as e:
            log_error(f"Error placing mock sell order for {symbol}: {str(e)}")
            return False

    def _place_new_trade(self, symbol: str) -> bool:
        """
        Mock implementation of placing a buy order.
        In real implementation, this would place actual orders through broker.
        
        Args:
            symbol: Stock symbol to buy
            
        Returns:
            bool: True if order placed successfully, False otherwise
        """
        try:
            current_price = self._get_cmp(symbol)
            
            if current_price is None:
                log_error(f"Cannot place trade for {symbol}: Price unavailable")
                return False
            
            # Create mock trade record
            mock_trade = {
                'tradingSymbol': symbol,
                'entry': current_price,
                'createTimestamp': datetime.now()
            }
            
            # Add to mock holdings
            self.mock_trades.append(mock_trade)
            
            # Display buy order confirmation
            self.console.print(f"[bold green]🛒 MOCK BUY ORDER PLACED[/bold green]")
            self.console.print(f"[cyan]Symbol:[/cyan] {symbol}")
            self.console.print(f"[cyan]Price:[/cyan] ₹{current_price:.2f}")
            self.console.print(f"[cyan]Time:[/cyan] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.console.print(f"[yellow]Note: This is a mock order - no real trade executed[/yellow]\n")
            
            log_success(f"Mock buy order placed for {symbol} at ₹{current_price:.2f}")
            return True
            
        except Exception as e:
            log_error(f"Error placing mock trade for {symbol}: {str(e)}")
            return False
    
    def initiate_sell(self) -> int:
        """
        Check holdings for stocks with >5% profit and sell them.
        
        Returns:
            int: Number of stocks sold
        """
        log_step("Sell Logic", "Checking holdings for profitable positions (>5% profit)")
        
        # Get current holdings
        current_holdings = self._get_current_holdings()
        
        if not current_holdings:
            log_info("No holdings found - skipping sell logic")
            return 0
        
        # Display sell configuration
        sell_config_panel = Panel(
            f"[bold]Profit Threshold:[/bold] >5% from average buy price\n"
            f"[bold]Current Holdings:[/bold] {len(current_holdings)} stocks\n"
            f"[bold]Action:[/bold] Sell profitable positions",
            title="💰 Sell Logic Configuration",
            border_style="red"
        )
        self.console.print(sell_config_panel)
        
        # Analyze holdings for profit
        profitable_holdings = []
        sell_analysis_table = Table(title="📈 Sell Analysis - Holdings Profit Check")
        sell_analysis_table.add_column("Symbol", style="cyan")
        sell_analysis_table.add_column("Quantity", style="white")
        sell_analysis_table.add_column("Avg Price", style="yellow")
        sell_analysis_table.add_column("Current Price", style="green")
        sell_analysis_table.add_column("Profit %", style="red")
        sell_analysis_table.add_column("Status", style="magenta")
        
        for holding in current_holdings:
            symbol = holding['tradingSymbol']
            entry_price = holding['entry']
            quantity = holding['quantity']
            
            try:
                current_price = self._get_cmp(symbol)
                
                if current_price is None:
                    sell_analysis_table.add_row(
                        symbol,
                        str(quantity),
                        f"₹{entry_price:.2f}",
                        "N/A",
                        "N/A",
                        "❌ Price Error"
                    )
                    continue
                
                # Calculate profit percentage
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                
                if profit_pct > 5.0:
                    profitable_holdings.append((holding, profit_pct))
                    status = "🎯 SELL TARGET"
                    status_style = "bold green"
                    profit_style = "bold green"
                else:
                    status = "📊 Hold"
                    status_style = "dim"
                    profit_style = "red" if profit_pct < 0 else "yellow"
                
                sell_analysis_table.add_row(
                    symbol,
                    str(quantity),
                    f"₹{entry_price:.2f}",
                    f"₹{current_price:.2f}",
                    f"[{profit_style}]{profit_pct:.2f}%[/{profit_style}]",
                    f"[{status_style}]{status}[/{status_style}]"
                )
                
            except Exception as e:
                log_error(f"Error analyzing {symbol} for selling: {str(e)}")
                sell_analysis_table.add_row(
                    symbol,
                    str(quantity),
                    f"₹{entry_price:.2f}",
                    "Error",
                    "Error",
                    "❌ Analysis Error"
                )
        
        self.console.print(sell_analysis_table)
        
        # Execute sell orders for profitable holdings
        stocks_sold = 0
        
        if profitable_holdings:
            # Sort by profit percentage (highest first)
            profitable_holdings.sort(key=lambda x: x[1], reverse=True)
            
            sell_opportunity_panel = Panel(
                f"[bold green]💰 PROFITABLE POSITIONS FOUND![/bold green]\n\n"
                f"[cyan]Holdings above 5% profit:[/cyan] {len(profitable_holdings)}\n"
                f"[cyan]Proceeding with sell orders...[/cyan]",
                title="🎯 Sell Opportunities",
                border_style="green"
            )
            self.console.print(sell_opportunity_panel)
            
            for holding, profit_pct in profitable_holdings:
                symbol = holding['tradingSymbol']
                log_info(f"{self.get_name()}: Initiating SELL for profitable stock: {symbol} (Profit: {profit_pct:.2f}%)")
                
                if self._place_sell_order(symbol, holding):
                    stocks_sold += 1
        
        else:
            no_sell_panel = Panel(
                f"[yellow]No holdings found with >5% profit[/yellow]\n\n"
                f"• All holdings are below 5% profit threshold\n"
                f"• No sell orders will be placed\n"
                f"• Proceeding to buy logic...",
                title="📊 No Sell Opportunities",
                border_style="yellow"
            )
            self.console.print(no_sell_panel)
            log_info(f"{self.get_name()}: No holdings above 5% profit threshold - no sell orders placed")
        
        # Sell summary
        if stocks_sold > 0:
            sell_summary_panel = Panel(
                f"[bold green]✅ Successfully placed {stocks_sold} sell orders[/bold green]\n"
                f"[yellow]Profitable positions liquidated[/yellow]\n"
                f"[cyan]Proceeding to buy logic...[/cyan]",
                title="💰 Sell Orders Completed",
                border_style="green"
            )
            self.console.print(sell_summary_panel)
            log_success(f"Sell logic completed: {stocks_sold} profitable positions sold")
        
        return stocks_sold
    
    def initiate_buy(self, stock_list: List[str]) -> None:
        """
        Main buying logic that checks holdings and decides what to buy.
        
        Args:
            stock_list: List of eligible stocks (top 5 from strategy)
        """
        log_step("Trade Execution", "Starting buy logic for eligible stocks")
        
        # Get current holdings from Zerodha
        current_holdings = self._get_current_holdings()
        
        # Display current configuration
        config_panel = Panel(
            f"[bold]Daily Trade Limit:[/bold] {self.daily_trade_limit} new stocks\n"
            f"[bold]Eligible Stocks:[/bold] {len(stock_list)}\n"
            f"[bold]Current Holdings:[/bold] {len(current_holdings)} stocks\n"
            f"[bold]Averaging Threshold:[/bold] -3% from last buy price",
            title="🎯 Trading Configuration",
            border_style="blue"
        )
        self.console.print(config_panel)
        
        new_stocks_bought = 0
        
        # Check each stock in the eligible list
        for stock in stock_list:
            is_part_of_holding = False
            
            # Check if stock is already in holdings
            for holding in current_holdings:
                if stock == holding['tradingSymbol']:
                    is_part_of_holding = True
                    break
            
            # If the Stock is not in our holding, initiate buy
            if not is_part_of_holding:
                if new_stocks_bought < self.daily_trade_limit:
                    log_info(f"{self.get_name()}: Initiating Buy for stock: {stock}")
                    
                    if self._place_new_trade(stock):
                        new_stocks_bought += 1
                    
                else:
                    log_warning(f"Daily trade limit ({self.daily_trade_limit}) reached. Skipping {stock}")
        
        # If there has been any buy, then return
        if new_stocks_bought > 0:
            summary_panel = Panel(
                f"[bold green]✅ Successfully placed {new_stocks_bought} new buy orders[/bold green]\n"
                f"[yellow]Total holdings after today: {len(current_holdings) + new_stocks_bought} stocks[/yellow]",
                title="🎉 New Stocks Purchased",
                border_style="green"
            )
            self.console.print(summary_panel)
            return
        
        log_info(f"{self.get_name()}: No new Stocks - All Stocks screened are already part of holding. "
                 "Checking existing holdings for averaging..")
        
        # If all the 5 eligible Stocks are already part of our holding, then
        # we will check all stocks that we are holding and find out which ones have fallen
        # further by -3%. Choose the one that has fallen the most and buy it for averaging
        
        df = pd.DataFrame()
        
        try:
            for holding in current_holdings:
                try:
                    new_row = {
                        'Symbol': holding['tradingSymbol'], 
                        'Price': holding['entry'], 
                        'Date': holding['createTimestamp']
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                except Exception as e:
                    log_error(f"{self.get_name()}: Error while constructing Averaging Dataset: {str(e)}")
        except Exception as e:
            log_error(f"{self.get_name()}: Error while building holdings DataFrame: {str(e)}")
            return
        
        # Summarise trades based on Symbol, identify min previously bought price
        # Add current market price, find percent change (fall)
        # Buy the stocks that have the highest fall since last buy (minimum should have fallen by -3%)
        
        try:
            if not df.empty:
                # Get latest buy price for each symbol
                df = df.loc[df.groupby(['Symbol'])["Date"].idxmax()]
                df.columns = ['Symbol', 'LastBuyPrice', 'Date']
                
                # Create averaging analysis table
                averaging_table = Table(title="📉 Averaging Analysis - Current Holdings")
                averaging_table.add_column("Symbol", style="cyan")
                averaging_table.add_column("Last Buy Price", style="white")
                averaging_table.add_column("Current Price", style="yellow")
                averaging_table.add_column("Change %", style="red")
                averaging_table.add_column("Status", style="green")
                
                for i, row in df.iterrows():
                    cmp = self._get_cmp(row['Symbol'])
                    if cmp is None:
                        averaging_table.add_row(
                            row['Symbol'], 
                            f"₹{row['LastBuyPrice']:.2f}", 
                            "N/A", 
                            "N/A", 
                            "❌ Price Error"
                        )
                        continue
                    
                    df.at[i, 'Close'] = cmp
                    change = cmp - row['LastBuyPrice']
                    
                    if row['LastBuyPrice'] != 0:
                        change_pct = round((change * 100) / row['LastBuyPrice'], 2)
                        df.at[i, 'ChangePct'] = change_pct
                    else:
                        df.at[i, 'ChangePct'] = 0.0
                        change_pct = 0.0
                    
                    # Determine status for averaging
                    if change_pct <= -3:
                        status = "🎯 Eligible for Averaging"
                        status_style = "bold green"
                    else:
                        status = "📈 Above Threshold"
                        status_style = "dim"
                    
                    averaging_table.add_row(
                        row['Symbol'],
                        f"₹{row['LastBuyPrice']:.2f}",
                        f"₹{cmp:.2f}",
                        f"{change_pct:.2f}%",
                        f"[{status_style}]{status}[/{status_style}]"
                    )
                
                self.console.print(averaging_table)
                
                # Filter stocks that have fallen further than 3% since last buy
                df = df[df['ChangePct'] <= -3]
                
        except Exception as e:
            log_error(f"{self.get_name()}: Error while consolidating Stocks for averaging: {str(e)}")
            return
        
        if not df.empty:
            # Sort by change percentage (most negative first)
            df.sort_values(['ChangePct'], ascending=True, inplace=True)
            
            averaging_symbol = df['Symbol'].iloc[0]
            averaging_change = df['ChangePct'].iloc[0]
            
            log_info(f"{self.get_name()}: Eligible Stock - For Averaging - for today is {averaging_symbol} "
                    f"Change {averaging_change}%")
            
            # Place averaging buy order
            averaging_panel = Panel(
                f"[bold yellow]📉 AVERAGING OPPORTUNITY FOUND[/bold yellow]\n\n"
                f"[cyan]Stock:[/cyan] {averaging_symbol}\n"
                f"[cyan]Price Change:[/cyan] {averaging_change:.2f}%\n"
                f"[cyan]Action:[/cyan] Place averaging buy order",
                title="🎯 Averaging Trade",
                border_style="yellow"
            )
            self.console.print(averaging_panel)
            
            if self._place_new_trade(averaging_symbol):
                log_success(f"Averaging buy order placed for {averaging_symbol}")
            return
        
        # If in both scenarios there were no eligible Stocks for today, then we don't trade that day
        no_trade_panel = Panel(
            f"[yellow]No eligible stocks found for trading today:[/yellow]\n\n"
            f"• All top 5 stocks already in holdings\n"
            f"• No holdings have fallen below -3% threshold\n"
            f"• No new trades will be placed today",
            title="📊 No Trading Opportunity",
            border_style="yellow"
        )
        self.console.print(no_trade_panel)
        
        log_info(f"{self.get_name()}: No Stocks in holding have fallen below threshold. "
                 "So No Stock Buy Trades for today")
    
    def execute_strategy(self) -> None:
        """
        Complete strategy execution: analyze stocks, execute sell logic, then buy logic.
        """
        log_step("Complete Strategy", "Executing Nifty Shop Strategy: Sell → Analysis → Buy")
        
        # Step 1: Execute sell logic first
        stocks_sold = self.initiate_sell()
        
        # Step 2: Get eligible stocks for buying
        eligible_stocks = self.get_eligible_stocks_for_today()
        
        if not eligible_stocks:
            # Even if no eligible stocks, show what sell actions were taken
            if stocks_sold > 0:
                self.console.print(Panel(
                    f"[yellow]No eligible stocks found for buying today.[/yellow]\n"
                    f"[green]However, {stocks_sold} profitable positions were sold.[/green]",
                    title="📊 Strategy Results",
                    border_style="yellow"
                ))
            else:
                self.console.print(Panel(
                    "[red]No eligible stocks found from analysis.[/red]\n"
                    "[yellow]No trading opportunities found today.[/yellow]",
                    title="❌ No Trading Opportunities",
                    border_style="red"
                ))
            return
        
        # Step 3: Execute buy logic
        self.initiate_buy(eligible_stocks)
        
        # Get final holdings count
        final_holdings = self._get_current_holdings()
        
        # Final summary
        execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_summary = Panel(
            f"[bold]Strategy Execution Completed[/bold]\n\n"
            f"[cyan]Execution Time:[/cyan] {execution_time}\n"
            f"[cyan]Sell Orders Placed:[/cyan] {stocks_sold} profitable positions\n"
            f"[cyan]Eligible Stocks Found:[/cyan] {len(eligible_stocks)}\n"
            f"[cyan]Current Total Holdings:[/cyan] {len(final_holdings)}\n"
            f"[cyan]Strategy:[/cyan] NiftyShopStrategy\n\n"
            f"[dim]Note: All orders are mocked for demonstration[/dim]",
            title="🏁 Execution Complete",
            border_style="bright_magenta"
        )
        self.console.print(final_summary)
        
        log_success("Nifty Shop Strategy execution completed successfully!")
