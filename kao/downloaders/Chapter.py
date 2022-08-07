from typing import Optional


class Chapter:
    def __init__(self, series_name: str, chapter_name: str, platform: str):
        self.series_name = series_name
        self.chapter_name = chapter_name
        self.platform = platform
        self.pdf_path = None

    def get_name(self) -> str:
        return self.chapter_name

    def get_series_name(self) -> str:
        return self.series_name

    def get_full_name(self) -> str:
        return "{} - {}".format(self.series_name, self.chapter_name)

    def which_platform(self) -> str:
        return self.platform

    def set_pdf_path(self, pdf_path: str) -> None:
        self.pdf_path = pdf_path

    def get_pdf_path(self) -> Optional[str]:
        return self.pdf_path
