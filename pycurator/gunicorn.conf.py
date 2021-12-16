"""Common configuration settings for Gunicorn servers."""

# pylint: disable=invalid-name

# t: date of the request
# r: status line (e.g. `GET / HTTP/1.1`)
# s: status
access_logformat = "%(t)s %(r)s %(s)s"
log_level = "info"
logger_class = "pycurator.common.logger.GunicornLogger"
pythonpath = "../../"
