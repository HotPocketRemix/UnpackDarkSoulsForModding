import logging
import colorama
log = logging.getLogger(__name__)

import unpacker_file_handler

if __name__ == '__main__':
    LOG_FILE = "unpackDS-latestlog.txt"
    
    colorama.init()
    with open(LOG_FILE, "w") as f:
        logging.basicConfig(stream=f, level=logging.INFO)
        try:
            unpacker_file_handler.attempt_unpack()
        except Exception:
            log.exception("Encountered critical error in unpacking.")
