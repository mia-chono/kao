import re

from lxml import etree

from .bases import Series, Chapter, Downloader
from .. import kao_utils
from ..loggers import Logger


class ReaperScansDownloader(Downloader):
    platform = "ReaperScans"

    def __init__(self, base_dir: str, loggers: list[Logger] = None):
        super().__init__(base_dir, loggers)

    @staticmethod
    def is_a_series_link(link: str) -> bool:
        return re.search(r"https?://(www\.)?reaperscans\.fr/series?/[^/?]+/?$", link) is not None

    @staticmethod
    def is_a_chapter_link(link: str) -> bool:
        return re.search(r"https?://(www\.)?reaperscans\.fr/series?/[^/]+/chapitre-\d+/?$", link) is not None

    @staticmethod
    def extract_pictures_links_from_webpage(dom: etree._Element) -> list[str]:
        img_tags = dom.xpath('//*[@class="reading-content"]//img')

        pictures_links = list(map(lambda img_tag: img_tag.get("src").replace("\n", ""), img_tags))

        return pictures_links

    def create_series(self, link: str) -> Series:
        if link[len(link) - 1] != "/":
            link += "/"

        kao_utils.log(self.loggers, "[Info][{}][Series] Get HTML content".format(self.platform))

        soup, dom = self._get_page_content(link)

        series_title = self._clear_name(soup.find("div", {"class": "post-title"}).find("h1").text)

        series = self._generate_series(series_title, link)

        # get all website url of the series
        for chapter_tag in soup.find_all("div", {"class": "chapter-link"}):
            series.add_chapter_link(chapter_tag.find("a").attrs["href"])
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

        series_title = self._clear_name(soup.select_one(".breadcrumb > li:nth-child(2)").text)
        series_chapter = self._clear_name(soup.select_one(".breadcrumb > .active").text)

        return self._download_chapter_files(dom, series_title, series_chapter, 'https://reaperscans.fr/', force_re_dl,
                                            keep_img, full_logs)
