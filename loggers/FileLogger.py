import os
from os import path

from loggers.Logger import Logger


class FileLogger(Logger):
    def __init__(self, file_name: str, extension: str):
        self.file = "{}.{}".format(file_name, extension)
        if path.exists(self.file):
            os.remove(self.file)

    def log(self, msg: str) -> None:
        with open(self.file, "a") as file_object:
            # Append 'hello' at the end of file
            file_object.write("{message}\n".format(message=msg))
