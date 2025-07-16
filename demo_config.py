#!/usr/bin/env python3
"""
Interactive Configuration Demo
Demonstrates the configuration system with interactive prompts
"""

from utils.config_manager import ConfigManager
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
import sys

def demo_interactive_config():
    """Demonstrate interactive configuration setup."""
    console = Console()
    
    # Welcome message
    welcome_panel = Panel(
        "[bold cyan]🎯 Interactive Configuration Demo[/bold cyan]\n\n"
        "This demo will walk you through the configuration process.\n"
        "You'll be able to set up your trading parameters interactively.\n\n"
        "[yellow]Note: This is a safe demo - no actual trading will occur.[/yellow]",
        title="🚀 Configuration Demo",
        border_style="bright_blue"
    )
    console.print(welcome_panel)
    
    # Ask if user wants to proceed
    if not Confirm.ask("\n[bold]Would you like to proceed with the interactive setup?[/bold]", default=True):
        console.print("[yellow]Demo cancelled by user.[/yellow]")
        return
    
    try:
        # Initialize config manager
        config_manager = ConfigManager()
        
        # Show current status
        console.print("\n[bold]Current Configuration Status:[/bold]")
        if config_manager.is_first_run():
            console.print("• Status: [yellow]First time setup[/yellow]")
        else:
            console.print("• Status: [green]Configuration exists[/green]")
        
        # Run interactive setup
        console.print("\n[bold cyan]Starting Interactive Configuration...[/bold cyan]\n")
        
        config = config_manager.interactive_setup(force_reconfigure=True)
        
        # Show final configuration
        final_panel = Panel(
            f"[bold green]✅ Configuration Complete![/bold green]\n\n"
            f"[cyan]Your configured parameters:[/cyan]\n"
            f"• Daily Trade Limit: [yellow]{config['daily_trade_limit']}[/yellow] stocks per day\n"
            f"• Profit Threshold: [yellow]{config['profit_threshold_for_selling']}%[/yellow] for selling\n"
            f"• Loss Threshold: [yellow]{config['loss_threshold_for_averaging']}%[/yellow] for averaging\n\n"
            f"[dim]Configuration saved to: config/strategy_config.json[/dim]",
            title="🎉 Setup Complete",
            border_style="green"
        )
        console.print(final_panel)
        
        # Show how to use
        usage_panel = Panel(
            "[bold]How to use your configured strategy:[/bold]\n\n"
            "[cyan]1. Run strategy with your settings:[/cyan]\n"
            "   [dim]uv run python main.py[/dim]\n\n"
            "[cyan]2. Reconfigure anytime:[/cyan]\n"
            "   [dim]uv run python main.py --reconfigure[/dim]\n\n"
            "[cyan]3. Just configure without running:[/cyan]\n"
            "   [dim]uv run python main.py --config-only[/dim]",
            title="📖 Usage Instructions",
            border_style="blue"
        )
        console.print(usage_panel)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Configuration interrupted by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Error during configuration: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    demo_interactive_config() 