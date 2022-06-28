import logging


log_dir = "log.log"
Log_Format = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename=log_dir,
                    filemode="w",
                    format=Log_Format,
                    level=logging.DEBUG)

logger = logging.getLogger()
