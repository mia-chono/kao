import os
import validators

from . import downloader_utils
from .bases import Series, Chapter, Downloader
from .. import kao_utils
from ..loggers import Logger


class PersonalDownloader(Downloader):
    """
    Downloader to convert a folder of images to a pdf
    """
    platform = "PersonalDownloader"

    def __init__(self, base_dir: str, loggers: list[Logger] = None):
        super().__init__(base_dir, loggers)

    @staticmethod
    def is_a_series_link(link: str) -> bool:
        if validators.url(link):
            return False
        return not downloader_utils.folder_contains_files([os.path.join(link, p) for p in os.listdir(link)])

    @staticmethod
    def is_a_chapter_link(link: str) -> bool:
        if validators.url(link):
            return False
        return downloader_utils.folder_contains_files([os.path.join(link, p) for p in os.listdir(link)])

    def create_series(self, link: str) -> Series:
        series_title = link[link.rfind(os.sep) + 1:]
        series = self._generate_series(series_title, link)

        series_folders = downloader_utils.find_all_sub_folders(link)

        for folder in series_folders:
            series.add_chapter_link(folder)

        return series

    def download_series(self, series: Series, force_re_dl: bool = False, keep_img: bool = False,
                        full_logs: bool = False) -> Series:

        total_chapters = len(series.get_all_chapter_links())

        for index in range(0, total_chapters):
            folder = series.get_chapter_link(index)
            chapter = self.download_chapter(folder, force_re_dl, keep_img, full_logs)
            series.add_chapter(chapter)

        return series

    def download_chapter(self, link: str, force_re_dl: bool = False, keep_img: bool = False,
                         full_logs: bool = False) -> Chapter:
        path = os.path.abspath(os.path.join(link, os.pardir))
        series_name = path[path.rfind(os.sep) + 1:]
        chap_name = link[link.rfind(os.sep) + 1:]

        if series_name is None:
            series_name = "Custom Series"
        if chap_name is None:
            chap_name = "unknown chap"
        chapter = Chapter(series_name, chap_name, self.platform)
        chapter.set_path(link)

        kao_utils.log(self.loggers, "[Info][{}][Chapter] '{}': Complete".format(self.platform, chapter.get_full_name()))

        return chapter
