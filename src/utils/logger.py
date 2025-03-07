import logging


class ColoredFormatter(logging.Formatter):
    # ANSI escape codes for colors
    LEVEL_COLORS = {
        "DEBUG": "\033[34m",  # Blue
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"  # Reset color to default

    def format(self, record):
        # Get the original log level name
        levelname = record.levelname
        # Apply color to the log level if it exists in LEVEL_COLORS
        if levelname in self.LEVEL_COLORS:
            colored_levelname = f"{self.LEVEL_COLORS[levelname]}{levelname}{self.RESET}"
            record.levelname = colored_levelname
        # Let the parent class handle the rest of the formatting
        return super().format(record)


# Create and configure the logger
logger = logging.getLogger("ptepg")
logger.setLevel(logging.DEBUG)  # Capture all log levels

# Create a console handler
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

# Set the format to match "INFO:     Waiting for application shutdown."
# Use 5 spaces after the colon to align with the example
formatter = ColoredFormatter("%(levelname)s:     %(message)s")
handler.setFormatter(formatter)

# Attach the handler to the logger
logger.addHandler(handler)
