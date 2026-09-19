import logging
from sovereign.infrastructure.logging import setup_logging, get_logger

def test_setup_logging(monkeypatch):
    import sovereign.infrastructure.logging as infra_logging
    infra_logging._logger_initialized = False # reset
    
    setup_logging()
    
    assert infra_logging._logger_initialized is True
    
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) >= 2 # console and file

def test_get_logger():
    logger = get_logger("test.logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.logger"
