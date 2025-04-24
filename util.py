import os
import logging

logger = logging.getLogger()

if logger.hasHandlers():
    logger.setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


def read_cb_key_file():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    key_file_path = os.path.join(dir_path, 'cb.key')
    
    try:
        with open(key_file_path, 'r') as file:
            content = file.read().strip().split('\n\n')
            if len(content) != 2:
                raise ValueError("File format is incorrect")
            api_key = content[0].strip()
            api_secret = content[1].strip()
            return api_key, api_secret
    except Exception as e:
        logger.error(f"Unable to read coinbase api key: {e}")
        raise