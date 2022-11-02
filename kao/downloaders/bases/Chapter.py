from typing import Optional


class Chapter:
    def __init__(self, series_name: str, name: str, platform: str):
        self.series_name = series_name
        self.name = name
        self.platform = platform
        self.path = None

    def get_name(self) -> str:
        return self.name

    def get_series_name(self) -> str:
        return self.series_name

    def get_full_name(self) -> str:
        return "{} - {}".format(self.series_name, self.name)

    def which_platform(self) -> str:
        return self.platform

    def set_path(self, pdf_path: str) -> None:
        self.path = pdf_path

    def get_path(self) -> Optional[str]:
        return self.path
