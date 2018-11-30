import logging

logging.basicConfig(level=logging.DEBUG,
    format='%(threadName)s %(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S')
