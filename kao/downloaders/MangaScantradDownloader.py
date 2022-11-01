import re

from bs4 import BeautifulSoup
from lxml import etree

from . import downloader_utils
from .bases import Series, Chapter, Downloader
from .. import kao_utils
from ..loggers import Logger


class MangaScantradDownloader(Downloader):
    """
    Downloader to scrape Manga-scantrad series or chapters
    """
    platform = "Manga-Scantrad"

    def __init__(self, base_dir: str, loggers: list[Logger] = None):
        super().__init__(base_dir, loggers)

    @staticmethod
    def is_a_series_link(link: str) -> bool:
        return re.search(r"https?://(www\.)?manga-scantrad\.net/manga/[\w\-%]+/?$", link) is not None

    @staticmethod
    def is_a_chapter_link(link: str) -> bool:
        return re.search(
            r"https?://(www\.)?manga-scantrad\.net/manga/[\w\-%]+/(chapitre|ch)-\d+[\w\-%]+?/?(\?style=(list|paged))?$",
            link) is not None

    @staticmethod
    def extract_pictures_links_from_webpage(dom: etree._Element) -> list[str]:
        img_tags = dom.xpath('//*[@class="reading-content"]//img')
        pictures_links = []

        for img_tag in img_tags:
            img_link = img_tag.get("data-src").strip()
            pictures_links.append(img_link)

        return pictures_links

    def _get_chapters_from_series(self, link: str) -> BeautifulSoup:
        """
        Manga-scantrad has a pagination system for the chapters list.
        :param link: str - the link of the series
        :return: BeautifulSoup - the html content of the chapters list page
        """
        headers = {
            'User-Agent': downloader_utils.user_agent,
            'referer': link
        }
        response = self.scraper.post("{}ajax/chapters/".format(link), headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup

    def create_series(self, link: str) -> Series:
        if link[len(link) - 1] != "/":
            link += "/"

        kao_utils.log(self.loggers, "[Info][{}][Series] Get HTML content".format(self.platform))
        soup, _ = self._get_page_content(link)
        soup_chapters = self._get_chapters_from_series(link)

        series_title = self._clear_name(soup.find("div", {"class": "post-title"}).find("h1").text)

        series = self._generate_series(series_title, link)

        # get all website url of the series
        for chapter_tag in soup_chapters.select(".wp-manga-chapter > a"):
            series.add_chapter_link(chapter_tag.attrs["href"])
        series.get_all_chapter_links().reverse()

        return series

    def download_series(self, series: Series, force_re_dl: bool = False, keep_img: bool = False,
                        full_logs: bool = False) -> Series:

        self._download_chapters_from_series(series, force_re_dl, keep_img, full_logs)

        kao_utils.log(self.loggers, "[Info][{}][series] '{}': completed".format(self.platform, series.get_name()))

        return series

    def download_chapter(self, link: str, force_re_dl: bool = False, keep_img: bool = False,
                         full_logs: bool = False) -> Chapter:
        if "?style=list" not in link:
            link += "?style=list"

        soup, dom = self._get_page_content(link)

        series_title = self._clear_name(soup.select_one(".breadcrumb > li:nth-child(2)").text)
        series_chapter = self._clear_name(soup.select_one(".breadcrumb > .active").text)

        return self._download_chapter_files(dom, series_title, series_chapter, 'https://manga-scantrad.net/',
                                            force_re_dl, keep_img, full_logs)
