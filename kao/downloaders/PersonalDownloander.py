import os
import validators

from kao import utils
from .Series import Series
from .Chapter import Chapter
from .Downloader import Downloader


class PersonalDownloader(Downloader):
    platform = "PersonalDownloader"

    def __init__(self, base_dir: str, logger=None):
        super().__init__(base_dir, logger)

    @staticmethod
    def is_a_series_link(link: str) -> bool:
        if validators.url(link):
            return False
        return not utils.folder_contains_files([os.path.join(link, p) for p in os.listdir(link)])

    @staticmethod
    def is_a_chapter_link(link: str) -> bool:
        if validators.url(link):
            return False
        return utils.folder_contains_files([os.path.join(link, p) for p in os.listdir(link)])

    def download_series(self, link: str, force_re_dl: bool = False, keep_img: bool = False,
                        full_logs: bool = False) -> Series:
        series_title = link[link.rfind(os.sep) + 1:]
        series = self.generate_series(series_title, link)

        series_folders = utils.find_all_sub_folders(link)

        for folder in series_folders:
            series.add_chapter_link(folder)
            series.add_chapter(self.download_chapter(folder, force_re_dl, keep_img, full_logs))

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

        utils.log(self.loggers, "[Info][{}][Chapter] '{}': Creating pdf".format(self.platform, chapter.get_full_name()))

        pdf_path = utils.convert_to_pdf(link, chapter.get_name(), self.loggers, True, full_logs)
        chapter.set_pdf_path(pdf_path)

        utils.log(self.loggers, "[Info][{}][Chapter] '{}': Complete".format(self.platform, chapter.get_full_name()))

        return chapter
