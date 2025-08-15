import logging, sys, os
from logging.handlers import RotatingFileHandler

def setup_logger():
    logger = logging.getLogger("virastary")
    logger.setLevel(logging.INFO)

    # stdout
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(sh)

    # file rotation
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    logdir = os.path.join(base, "logs")
    os.makedirs(logdir, exist_ok=True)
    fh = RotatingFileHandler(os.path.join(logdir, "bot.log"), maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
    fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(fh)

    return logger
