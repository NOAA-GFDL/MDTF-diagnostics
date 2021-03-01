import logging

# Initialize package logging tree
# Real loggers should be configured by scripts that import this package; see 
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger(__name__).addHandler(logging.NullHandler())
