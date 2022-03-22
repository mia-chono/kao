import os
import validators

import utils
from downloaders.Chapter import Chapter
from downloaders.Downloader import Downloader


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

    @staticmethod
    def _extract_pictures_links_from_webpage(dom) -> list[str]:
        img_tags = dom.xpath("//*[@id='readerarea']//img")

        pictures_links = list(map(lambda img_tag: img_tag.get("src"), img_tags))

        return pictures_links

    def download_series(self, link: str):
        series_title = link[link.rfind(os.sep):]
        series = self.generate_series(series_title, link)
        folders = [os.path.join(link, p) for p in os.listdir(link)]

        for folder in folders:
            series.add_chapter_link(folder)
            series.add_chapter(self.download_chapter(folder))

        return series

    def download_chapter(self, link: str, force_re_dl: bool = False):
        name = os.path.abspath(os.path.join(link, os.pardir))[link.rfind(os.sep):]
        chapter = Chapter("Custom Series", name, self.platform)

        for logger in self.loggers:
            logger.log("[Info][{}][Chapter] '{}': Creating pdf".format(self.platform, chapter.get_full_name()))

        pdf_path = utils.convert_to_pdf(link, chapter.get_full_name(), self.loggers)
        chapter.set_pdf_path(pdf_path)

        for logger in self.loggers:
            logger.log("[Info][{}][Chapter] '{}': Complete".format(self.platform, chapter.get_full_name()))

        return chapter
