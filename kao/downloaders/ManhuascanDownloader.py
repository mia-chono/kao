import re

from lxml import etree

from .bases import Series, Chapter, Downloader
from .. import kao_utils
from ..loggers import Logger


class ManhuascanDownloader(Downloader):
    """
    Downloader to scrape Manhuascan series or chapters
    """
    platform = "Manhuascan"

    def __init__(self, base_dir: str, loggers: list[Logger] = None):
        super().__init__(base_dir, loggers)

    @staticmethod
    def is_a_series_link(link: str) -> bool:
        return re.search(r"https?://(www\.)?manhuascan\.us/manga/[\w\-%]+/?$", link) is not None

    @staticmethod
    def is_a_chapter_link(link: str) -> bool:
        return re.search(r"https?://(www\.)?manhuascan\.us/manga/.+/([\w\-%]+)?\d+/?$", link) is not None

    @staticmethod
    def extract_pictures_links_from_webpage(dom: etree._Element) -> list[str]:
        img_tags = dom.xpath('/html/body/div[2]/div[2]/div[1]/div/article/div[3]/div[5]/img')

        pictures_links = list(map(lambda img_tag: img_tag.get("src"), img_tags))

        return pictures_links

    def create_series(self, link: str) -> Series:
        if link[len(link) - 1] != "/":
            link += "/"

        kao_utils.log(self.loggers, "[Info][{}][Series] Get HTML content".format(self.platform))

        soup, dom = self._get_page_content(link)

        series_title = self._clear_name(
            dom.xpath("/html/body/div[2]/div/div[2]/article/div[1]/div[2]/div[1]/div[1]/div/h1")[0].text)

        series = self._generate_series(series_title, link)

        # get all website url of the series
        for chapter_tags in soup.find_all("div", {"class": "chbox"}):
            series.add_chapter_link(chapter_tags.find("a").attrs["href"])
        series.get_all_chapter_links().reverse()

        return series

    def download_series(self, series: Series, force_re_dl: bool = False, keep_img: bool = False,
                        full_logs: bool = False) -> Series:

        self._download_chapters_from_series(series, force_re_dl, keep_img, full_logs)

        kao_utils.log(self.loggers, "[Info][{}][series] '{}': completed".format(self.platform, series.get_name()))

        return series

    def download_chapter(self, link: str, force_re_dl: bool = False, keep_img: bool = False,
                         full_logs: bool = False) -> Chapter:
        soup, dom = self._get_page_content(link)

        series_title = self._clear_name(dom.xpath("/html/body/div[2]/div[2]/div[1]/div/article/div[1]/div/a")[0].text)
        series_chapter = self._clear_name(dom.xpath("//*[@id='chapter']//option[@selected='selected']")[0].text)

        return self._download_chapter_files(dom, series_title, series_chapter, 'https://manhuascan.us', force_re_dl,
                                            keep_img, full_logs)
