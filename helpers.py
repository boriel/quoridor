# -*- coding: utf-8 -*-


class LogLevel:
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3

    @classmethod
    def name(cls, level: int) -> str:
        assert cls.DEBUG <= level <= cls.ERROR, "Invalid Log level {}".format(level)
        return ("DEBUG", "INFO", "WARNING", "ERROR")[level]


LOG_LEVEL = LogLevel.INFO


def log(msg: str, severity: int = LogLevel.INFO) -> None:
    """ Simple system logger.
    """
    global LOG_LEVEL

    if severity >= LOG_LEVEL:
        print('{}: {}'.format(LogLevel.name(severity), msg))
