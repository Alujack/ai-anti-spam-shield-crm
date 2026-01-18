"""
Professional Logging Configuration
Centralized logging with file rotation, multiple handlers, and formatting
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Log directory configuration
LOG_DIR = os.getenv('LOG_DIR', str(Path(__file__).parent.parent.parent.parent / 'logs' / 'model-service'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 20 * 1024 * 1024))  # 20MB
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 14))

# Ensure log directory exists
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[1;31m' # Bold Red
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname_colored = f"{color}{record.levelname:<8}{self.RESET}"
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record):
        import json
        log_obj = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_obj['data'] = record.extra_data

        return json.dumps(log_obj)


def setup_logging(
    name: str = 'ai-anti-spam-shield',
    level: Optional[str] = None,
    log_dir: Optional[str] = None,
    json_format: bool = False
) -> logging.Logger:
    """
    Set up professional logging configuration

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Custom log directory
        json_format: Use JSON format for file logs

    Returns:
        Configured logger instance
    """
    log_level = getattr(logging, level or LOG_LEVEL, logging.INFO)
    log_directory = log_dir or LOG_DIR

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.handlers = []  # Clear existing handlers

    # File format
    file_format = '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
    file_formatter = JsonFormatter() if json_format else logging.Formatter(
        file_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console format with colors
    console_format = '%(asctime)s | %(levelname_colored)s | %(message)s'
    console_formatter = ColoredFormatter(console_format, datefmt='%H:%M:%S')

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Combined log file (rotating)
    combined_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_directory, 'combined.log'),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )
    combined_handler.setLevel(logging.DEBUG)
    combined_handler.setFormatter(file_formatter)
    logger.addHandler(combined_handler)

    # Error log file (rotating)
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_directory, 'error.log'),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)

    # Access log file (rotating) for HTTP requests
    access_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_directory, 'access.log'),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(file_formatter)

    # Create separate access logger
    access_logger = logging.getLogger(f'{name}.access')
    access_logger.setLevel(logging.INFO)
    access_logger.handlers = []
    access_logger.addHandler(access_handler)
    access_logger.addHandler(console_handler)

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance with the given name"""
    base_name = 'ai-anti-spam-shield'
    if name:
        return logging.getLogger(f'{base_name}.{name}')
    return logging.getLogger(base_name)


class SecurityLogger:
    """Dedicated security event logger"""

    def __init__(self, log_dir: str = LOG_DIR):
        self.logger = logging.getLogger('ai-anti-spam-shield.security')
        self.logger.setLevel(logging.INFO)

        # Security log file
        handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'security.log'),
            maxBytes=LOG_MAX_BYTES,
            backupCount=30  # Keep security logs longer
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | SECURITY | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(handler)

    def log(self, event: str, **kwargs):
        """Log a security event"""
        import json
        extra = json.dumps(kwargs) if kwargs else ''
        self.logger.info(f'{event} {extra}'.strip())


class AuditLogger:
    """Dedicated audit trail logger"""

    def __init__(self, log_dir: str = LOG_DIR):
        self.logger = logging.getLogger('ai-anti-spam-shield.audit')
        self.logger.setLevel(logging.INFO)

        # Audit log file
        handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'audit.log'),
            maxBytes=LOG_MAX_BYTES,
            backupCount=90  # Keep audit logs for 90 rotations
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | AUDIT | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(handler)

    def log(self, action: str, user_id: str, resource: str, **kwargs):
        """Log an audit event"""
        import json
        extra = json.dumps(kwargs) if kwargs else ''
        self.logger.info(f'action={action} user={user_id} resource={resource} {extra}'.strip())


# Initialize default logger on module import
logger = setup_logging()
security_logger = SecurityLogger()
audit_logger = AuditLogger()


def log_request(request, response_time: float, status_code: int):
    """Log HTTP request details"""
    access_logger = logging.getLogger('ai-anti-spam-shield.access')
    client_ip = request.client.host if request.client else 'unknown'
    access_logger.info(
        f'{request.method} {request.url.path} {status_code} {response_time:.2f}ms '
        f'client={client_ip} user_agent="{request.headers.get("user-agent", "unknown")}"'
    )
