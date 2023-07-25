import logging
import os

# Custom formatter class to handle color formatting
class ColoredFormatter(logging.Formatter):
    COLORS = {
        "INFO": "32",      # Green
        "WARNING": "33",   # Yellow
        "ERROR": "31",     # Red
    }

    def format(self, record):
        levelname = record.levelname
        color_code = self.COLORS.get(levelname, "0")
        log_message = super().format(record)
        return f"\x1b[{color_code}m{log_message}\x1b[0m"

# Create a custom logging handler that writes to the log file
class FileHandler(logging.Handler):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def emit(self, record):
        log_message = self.format(record)
        with open(self.filename, "a") as file:
            file.write(log_message + "\n")

# Create a custom logging handler that forwards INFO messages to the console (CLI)
class ConsoleHandler(logging.Handler):
    def emit(self, record):
        log_message = self.format(record)
        if record.levelname in ("INFO", "WARNING", "ERROR"):
            print(log_message)

# Configure the root logger with the custom FileHandler and ConsoleHandler
def configure_logger(log_filename):
    logs_folder = "logs"
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)

    log_filepath = os.path.join(logs_folder, log_filename)

    # Remove existing handlers to avoid duplicated logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Create a logger
    logger = logging.getLogger("application_log")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = FileHandler(log_filepath)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = ConsoleHandler()
    console_handler.setLevel(logging.DEBUG)  # Use DEBUG level for console to show all log levels
    color_formatter = ColoredFormatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)

    return logger

# Function to get the logger
def get_logger():
    return logging.getLogger("application_log")
