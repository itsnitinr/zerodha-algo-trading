"""
Configuration Manager for Nifty Shop Strategy
Handles interactive setup and persistent storage of strategy parameters.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.prompt import Prompt, FloatPrompt, IntPrompt, Confirm
from rich.panel import Panel
from rich.table import Table

from utils.logger import log_success, log_error, log_info


class ConfigManager:
    """Manages strategy configuration with interactive setup and persistence."""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory to store configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "strategy_config.json"
        self.console = Console()
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        
        # Default configuration values
        self.default_config = {
            "daily_trade_limit": 1,
            "profit_threshold_for_selling": 5.0,
            "loss_threshold_for_averaging": -3.0,
            "config_version": "1.0",
            "last_updated": None
        }
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or return defaults.
        
        Returns:
            Dictionary containing configuration parameters
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Merge with defaults to handle any missing keys
                merged_config = {**self.default_config, **config}
                log_success(f"Configuration loaded from {self.config_file}")
                return merged_config
            else:
                log_info("No existing configuration found, using defaults")
                return self.default_config.copy()
        
        except Exception as e:
            log_error(f"Error loading configuration: {str(e)}")
            log_info("Using default configuration")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from datetime import datetime
            
            # Add timestamp
            config["last_updated"] = datetime.now().isoformat()
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            log_success(f"Configuration saved to {self.config_file}")
            return True
        
        except Exception as e:
            log_error(f"Error saving configuration: {str(e)}")
            return False
    
    def is_first_run(self) -> bool:
        """
        Check if this is the first run (no config file exists).
        
        Returns:
            bool: True if first run, False otherwise
        """
        return not self.config_file.exists()
    
    def interactive_setup(self, force_reconfigure: bool = False) -> Dict[str, Any]:
        """
        Interactive setup of strategy parameters.
        
        Args:
            force_reconfigure: Force reconfiguration even if config exists
            
        Returns:
            Dictionary containing configured parameters
        """
        # Load existing config
        current_config = self.load_config()
        
        # Show welcome message
        if self.is_first_run() or force_reconfigure:
            welcome_title = "🎯 First Time Setup" if self.is_first_run() else "🔧 Reconfiguration"
            
            welcome_panel = Panel(
                f"[bold cyan]Welcome to Nifty Shop Strategy Configuration![/bold cyan]\n\n"
                f"Let's configure your trading parameters for optimal performance.\n"
                f"You can change these settings anytime by running with --reconfigure flag.\n\n"
                f"[yellow]Current settings will be shown as defaults in brackets.[/yellow]",
                title=welcome_title,
                border_style="bright_blue"
            )
            self.console.print(welcome_panel)
        
        # Show current configuration if it exists
        if not self.is_first_run():
            self._display_current_config(current_config)
        
        # Interactive parameter collection
        self.console.print("\n[bold green]📊 Trading Parameters Configuration[/bold green]\n")
        
        # 1. Daily Trade Limit
        daily_trade_limit = IntPrompt.ask(
            "[cyan]Maximum new stocks to buy per day[/cyan]",
            default=current_config["daily_trade_limit"]
        )
        
        # 2. Profit Threshold for Selling
        profit_threshold = FloatPrompt.ask(
            "[cyan]Profit percentage threshold for selling (e.g., 5.0 for 5%)[/cyan]",
            default=current_config["profit_threshold_for_selling"]
        )
        
        # 3. Loss Threshold for Averaging
        loss_threshold = FloatPrompt.ask(
            "[cyan]Loss percentage threshold for averaging (e.g., -3.0 for -3%)[/cyan]",
            default=current_config["loss_threshold_for_averaging"]
        )
        
        # Build new configuration
        new_config = {
            "daily_trade_limit": daily_trade_limit,
            "profit_threshold_for_selling": profit_threshold,
            "loss_threshold_for_averaging": loss_threshold,
            "config_version": self.default_config["config_version"]
        }
        
        # Validate configuration
        if self._validate_config(new_config):
            # Show summary and confirm
            if self._confirm_configuration(new_config):
                # Save configuration
                if self.save_config(new_config):
                    self.console.print(Panel(
                        "[bold green]✅ Configuration saved successfully![/bold green]\n"
                        "[yellow]Your strategy is now ready to run with these settings.[/yellow]",
                        title="🎉 Setup Complete",
                        border_style="green"
                    ))
                    return new_config
                else:
                    self.console.print("[red]❌ Failed to save configuration. Using current session settings.[/red]")
                    return new_config
            else:
                self.console.print("[yellow]⚠️  Configuration cancelled. Using existing settings.[/yellow]")
                return current_config
        else:
            self.console.print("[red]❌ Invalid configuration. Using existing settings.[/red]")
            return current_config
    
    def _display_current_config(self, config: Dict[str, Any]) -> None:
        """Display current configuration in a table."""
        config_table = Table(title="📋 Current Configuration")
        config_table.add_column("Parameter", style="cyan")
        config_table.add_column("Current Value", style="yellow")
        config_table.add_column("Description", style="green")
        
        config_table.add_row(
            "Daily Trade Limit",
            str(config["daily_trade_limit"]),
            "Max new stocks to buy per day"
        )
        config_table.add_row(
            "Profit Threshold",
            f"{config['profit_threshold_for_selling']}%",
            "Profit % to trigger selling"
        )
        config_table.add_row(
            "Loss Threshold",
            f"{config['loss_threshold_for_averaging']}%",
            "Loss % to trigger averaging"
        )
        
        if config.get("last_updated"):
            config_table.add_row(
                "Last Updated",
                config["last_updated"][:19].replace("T", " "),
                "Configuration timestamp"
            )
        
        self.console.print(config_table)
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration parameters.
        
        Args:
            config: Configuration to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Daily trade limit should be positive
            if config["daily_trade_limit"] <= 0:
                self.console.print("[red]❌ Daily trade limit must be greater than 0[/red]")
                return False
            
            # Profit threshold should be positive
            if config["profit_threshold_for_selling"] <= 0:
                self.console.print("[red]❌ Profit threshold must be greater than 0[/red]")
                return False
            
            # Loss threshold should be negative
            if config["loss_threshold_for_averaging"] >= 0:
                self.console.print("[red]❌ Loss threshold should be negative (e.g., -3.0)[/red]")
                return False
            
            # Reasonable ranges
            if config["daily_trade_limit"] > 10:
                if not Confirm.ask(f"Daily trade limit of {config['daily_trade_limit']} seems high. Continue?"):
                    return False
            
            if config["profit_threshold_for_selling"] > 50:
                if not Confirm.ask(f"Profit threshold of {config['profit_threshold_for_selling']}% seems high. Continue?"):
                    return False
            
            if config["loss_threshold_for_averaging"] < -20:
                if not Confirm.ask(f"Loss threshold of {config['loss_threshold_for_averaging']}% seems very low. Continue?"):
                    return False
            
            return True
        
        except Exception as e:
            log_error(f"Error validating configuration: {str(e)}")
            return False
    
    def _confirm_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Show configuration summary and get user confirmation.
        
        Args:
            config: Configuration to confirm
            
        Returns:
            bool: True if confirmed, False otherwise
        """
        self.console.print("\n[bold]📋 Configuration Summary[/bold]")
        
        summary_table = Table()
        summary_table.add_column("Parameter", style="cyan", no_wrap=True)
        summary_table.add_column("Value", style="yellow", no_wrap=True)
        summary_table.add_column("Impact", style="green")
        
        summary_table.add_row(
            "Daily Trade Limit",
            str(config["daily_trade_limit"]),
            f"Will buy max {config['daily_trade_limit']} new stocks per day"
        )
        summary_table.add_row(
            "Profit Threshold",
            f"{config['profit_threshold_for_selling']}%",
            f"Will sell holdings with >{config['profit_threshold_for_selling']}% profit"
        )
        summary_table.add_row(
            "Loss Threshold",
            f"{config['loss_threshold_for_averaging']}%",
            f"Will average down when stock falls by {config['loss_threshold_for_averaging']}%"
        )
        
        self.console.print(summary_table)
        
        return Confirm.ask("\n[bold]Save this configuration?[/bold]", default=True)
    
    def get_config_status(self) -> Dict[str, Any]:
        """
        Get current configuration status for display.
        
        Returns:
            Dictionary with configuration status information
        """
        config = self.load_config()
        
        return {
            "is_configured": not self.is_first_run(),
            "config_file_exists": self.config_file.exists(),
            "config_file_path": str(self.config_file),
            "current_config": config
        } 