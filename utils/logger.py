"""
Best-in-class logging configuration with colors and emojis.
"""
import logging
import sys
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install


class ColoredEmojiFormatter(logging.Formatter):
    """Custom formatter that adds emojis and maintains rich formatting."""
    
    LEVEL_EMOJIS = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "🚨"
    }
    
    def format(self, record):
        # Add emoji to the message
        emoji = self.LEVEL_EMOJIS.get(record.levelno, "📝")
        record.emoji = emoji
        
        # Use the parent formatter
        return super().format(record)


def setup_logger(
    name: str = "nifty",
    level: int = logging.INFO,
    show_time: bool = True,
    show_path: bool = False
) -> logging.Logger:
    """
    Set up a beautiful logger with rich formatting, colors, and emojis.
    
    Args:
        name: Logger name
        level: Logging level (default: INFO)
        show_time: Whether to show timestamps
        show_path: Whether to show file paths
        
    Returns:
        Configured logger instance
    """
    # Install rich traceback handler for beautiful error traces
    install(show_locals=True)
    
    # Create console with custom styling
    console = Console(
        force_terminal=True,
        color_system="auto",
        width=120
    )
    
    # Create rich handler
    rich_handler = RichHandler(
        console=console,
        show_time=show_time,
        show_path=show_path,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True
    )
    
    # Set format with emoji
    rich_handler.setFormatter(
        ColoredEmojiFormatter("%(emoji)s %(message)s")
    )
    
    # Configure logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    logger.addHandler(rich_handler)
    logger.propagate = False
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. If no name provided, returns the main app logger.
    
    Args:
        name: Logger name (optional)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name or "nifty")


# Create the main application logger
app_logger = setup_logger()


# Convenience functions for common logging patterns
def log_success(message: str, **kwargs):
    """Log a success message with green color."""
    app_logger.info(f"[green]✅ {message}[/green]", **kwargs)


def log_error(message: str, **kwargs):
    """Log an error message with red color."""
    app_logger.error(f"[red]{message}[/red]", **kwargs)


def log_warning(message: str, **kwargs):
    """Log a warning message with yellow color."""
    app_logger.warning(f"[yellow]{message}[/yellow]", **kwargs)


def log_info(message: str, **kwargs):
    """Log an info message with blue color."""
    app_logger.info(f"[blue]{message}[/blue]", **kwargs)


def log_debug(message: str, **kwargs):
    """Log a debug message with dim color."""
    app_logger.debug(f"[dim]{message}[/dim]", **kwargs)


def log_step(step: str, message: str, **kwargs):
    """Log a step in a process with special formatting."""
    app_logger.info(f"[bold cyan]🔄 Step: {step}[/bold cyan] - {message}", **kwargs)


def log_api_call(method: str, url: str, status_code: Optional[int] = None, **kwargs):
    """Log API calls with special formatting."""
    if status_code:
        if 200 <= status_code < 300:
            color = "green"
            emoji = "✅"
        elif 400 <= status_code < 500:
            color = "yellow" 
            emoji = "⚠️"
        else:
            color = "red"
            emoji = "❌"
        
        app_logger.info(
            f"[{color}]{emoji} API {method.upper()} {url} → {status_code}[/{color}]",
            **kwargs
        )
    else:
        app_logger.info(f"[cyan]🌐 API {method.upper()} {url}[/cyan]", **kwargs) 