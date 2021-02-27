import logging

logger = logging.getLogger("chatbot")


def setup_logger(debug: bool, log_file: str):
    logger.setLevel(logging.DEBUG)

    # logFormatter = logging.Formatter("%(asctime)s [%(name)s][%(levelname)-5.5s]  %(message)s")
    # fileHandler = logging.FileHandler(log_file, mode='w')
    # fileHandler.setLevel(logging.DEBUG)
    # fileHandler.setFormatter(logFormatter)
    # logger.addHandler(fileHandler)

    log_formatter = logging.Formatter("%(asctime)s [%(name)s][%(levelname)-5.5s]  %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    if debug:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
