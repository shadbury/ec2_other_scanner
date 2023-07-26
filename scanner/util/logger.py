import logging
import os

# Custom formatter class to handle color formatting
class ColoredFormatter(logging.Formatter):
    '''
    Custom formatter class to handle color formatting

    Args:
        logging.Formatter (class): Logging formatter class

    Returns:
        None
    '''
    COLORS = {
        "INFO": "32",      # Green
        "WARNING": "33",   # Yellow
        "ERROR": "31",     # Red
    }

    def format(self, record):
        '''
        Format the log message with color

        Args:
            record (str): Log message

        Returns:
            str: Formatted log message
        '''
        levelname = record.levelname
        color_code = self.COLORS.get(levelname, "0")
        log_message = super().format(record)
        return f"\x1b[{color_code}m{log_message}\x1b[0m"

class FileHandler(logging.Handler):
    '''
    Custom logging handler that forwards INFO messages to a file

    Args:
        logging.Handler (class): Logging handler class

    Returns:
        None
    '''
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def emit(self, record):
        log_message = self.format(record)
        with open(self.filename, "a") as file:
            file.write(log_message + "\n")


class ConsoleHandler(logging.Handler):
    '''
    Custom logging handler that forwards WARNING and ERROR messages to the console

    Args:
        logging.Handler (class): Logging handler class

    Returns:
        None
    '''
    def emit(self, record):
        log_message = self.format(record)
        if record.levelname in ("INFO", "WARNING", "ERROR"):
            print(log_message)


def configure_logger(log_filename):
    '''
    Configure the logger to send logs to the logger.py file

    Args:
        log_filename (str): Log file name

    Returns:
        logging.Logger: Logger object
    '''
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


def get_logger():
    '''
    Get the logger object

    Args:
        None

    Returns:
        logging.Logger: Logger object
    '''
    return logging.getLogger("application_log")
