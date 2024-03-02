import logging

from json import dump, load
from json.decoder import JSONDecodeError

logging.basicConfig(format=u'[%(asctime)s][%(levelname)s] ::: %(filename)s(%(lineno)d) -> %(message)s',
                    level="INFO", filename='logs/all.log')
logger = logging.getLogger('logger')


class JsonStore:

    def __init__(self, file_path: str, json_store_name: str):
        self.file_path = file_path
        self.json_store_name = json_store_name
        self.data = self.get_data()

    def get_data(self) -> dict:
        data = {}
        try:
            with open(self.file_path) as json_file:
                data = load(json_file)
        except FileNotFoundError:
            logger.debug(f"{self.json_store_name}: json file {self.file_path} not found, creating new...")
            with open(self.file_path, 'w') as json_file:
                dump(data, json_file, indent=4, ensure_ascii=False)
        except JSONDecodeError:
            logger.warning(f"{self.json_store_name}: cant read {self.file_path}; clearing old data.")
            with open(self.file_path, 'w') as json_file:
                dump({}, json_file, indent=4, ensure_ascii=False)

        return data

    def update_data(self, new_data: dict):
        with open(self.file_path, "w") as file:
            dump(new_data, file, indent=4, ensure_ascii=False)
