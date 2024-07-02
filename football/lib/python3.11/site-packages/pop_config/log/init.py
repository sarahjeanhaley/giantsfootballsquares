"""
This sub is used to set up logging for pop projects and injects logging
options into conf making it easy to add robust logging
"""
import logging


class LogCleanup:
    """
    Provides a logging registry, tracking the log handlers added by the hub.

    This allows cleanup of hub log files. This is mainly useful in tests, where
    many hubs are created and deleted. Prior to this, some test suites were
    running out of file handles.
    """

    def __init__(self):
        self.handlers = []

    def addHandler(self, handler):
        self.handlers.append(handler)

    def __del__(self):
        for handler in self.handlers:
            logging.getLogger().removeHandler(handler)


def __init__(hub):
    """
    Set up variables used by the log subsystem
    """
    logging.addLevelName(5, "TRACE")
    hub.log.LEVEL = {
        "notset": logging.NOTSET,
        "trace": 5,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARN,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "fatal": logging.FATAL,
        "critical": logging.CRITICAL,
    }
    log = logging.getLogger(__name__)

    # These should be overwritten by the integrated logger, but here's a contingency
    hub.log.INT_LEVEL = log.getEffectiveLevel()
    hub.log.log = log.log
    hub.log.trace = lambda msg, *args, **kwargs: log.log(5, msg, *args, **kwargs)
    hub.log.debug = log.debug
    hub.log.info = log.info
    hub.log.critical = log.critical
    hub.log.warning = log.warning
    hub.log.error = log.error

    # Provides a way for loggers to be cleaned up on hub deletion. This is mostly exercised in test suites.
    hub.log.handlers = LogCleanup()
