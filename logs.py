import logging
import datetime
import pytz
time_zone = pytz.timezone('Europe/Chisinau')
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',  # Blue
        'INFO': '\033[92m',   # Green
        'WARNING': '\033[93m', # Yellow
        'ERROR': '\033[91m',   # Red
        'CRITICAL': '\033[91m\033[1m', # Bold Red
        'RESET': '\033[0m'    # Reset color
    }

    def format(self, record):
        # Format without the levelname, which we'll add separately with color
        formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Get the log message without the level
        log_message = formatter.format(record)
        
        # Add the colored level tag
        colored_level = f"{self.COLORS.get(record.levelname, self.COLORS['RESET'])}[{record.levelname}]{self.COLORS['RESET']}"
        
        # Insert the colored level at the position after the timestamp
        parts = log_message.split(' | ', 1)
        if len(parts) == 2:
            return f"{parts[0]} | {colored_level} {parts[1]}"
        return log_message
    

console_formatter = ColoredFormatter(
    '%(asctime)s.%(msecs)03d | [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(console_formatter)
logging.Formatter.converter = lambda *args: \
    datetime.datetime.now(time_zone).timetuple()

# Attach our colored console handler to the root logger if not already attached
root_logger = logging.getLogger()
if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
    root_logger.addHandler(console_handler)
root_logger.setLevel(logging.INFO)

def send_logs(message, type):
    """Centralized logging wrapper. type can be 'info','warning','error','critical'."""
    if type == 'info':
        logging.info(message)
    elif type == 'warning':
        logging.warning(message)
    elif type == 'error':
        logging.error(message)
    elif type == 'critical':
        logging.critical(message)
    else:
        logging.info(message)