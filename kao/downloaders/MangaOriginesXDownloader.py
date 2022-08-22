import re
import unidecode

from bs4 import BeautifulSoup

from .Downloader import Downloader
from .. import utils


class MangaOriginesXDownloader(Downloader):
    platform = "Manga-Origines-X"

    def __init__(self, base_dir: str, logger=None):
        super().__init__(base_dir, logger)

    @staticmethod
    def is_a_series_link(link: str) -> bool:
        return re.search(r"https?://(www\.)?x\.mangas-origines\.fr/oeuvre/(\w*-*\d*%*)+/?$", link) is not None

    @staticmethod
    def is_a_chapter_link(link: str) -> bool:
        return re.search(
            r"https?://(www\.)?x\.mangas-origines\.fr/oeuvre/(\w*-*\d*%*)+/chapitre-\d+/?(\?style=(list|paged))?$",
            link) is not None

    @staticmethod
    def extract_pictures_links_from_webpage(dom) -> list[str]:
        img_tags = dom.xpath('//*[@class="reading-content"]//img')

        pictures_links = list(map(lambda img_tag: img_tag.get("data-src").strip(), img_tags))

        return pictures_links

    def _get_chapters_from_series(self, link: str) -> BeautifulSoup:
        headers = {
            'User-Agent': utils.user_agent,
            'referer': link
        }
        response = self.scraper.post("{}ajax/chapters/".format(link), headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup

    def download_series(self, link: str, force_re_dl: bool = False, keep_img: bool = False, full_logs: bool = False):
        if link[len(link) - 1] != "/":
            link += "/"

        utils.log(self.loggers, "[Info][{}][Series] Get HTML content".format(self.platform))
        soup, _ = self._get_page_content(link)
        soup_chapters = self._get_chapters_from_series(link)

        series_title = unidecode.unidecode(soup.find("div", {"class": "post-title"}).find("h1").text.rstrip().replace("\n", ""))

        series = self.generate_series(series_title, link)

        # get all website url of the series
        for chapter_tag in soup_chapters.select(".wp-manga-chapter > a"):
            series.add_chapter_link(chapter_tag.attrs["href"])
        series.get_chapters_links().reverse()

        series = self._download_chapters_from_series(series, force_re_dl, keep_img, full_logs)

        utils.log(self.loggers, "[Info][{}][series] '{}': completed".format(self.platform, series.get_name()))

        return series

    def download_chapter(self, link: str, force_re_dl: bool = False, keep_img: bool = False, full_logs: bool = False):
        if "?style=list" not in link:
            link += "?style=list"

        soup, dom = self._get_page_content(link)

        series_title = soup.select_one(".breadcrumb > li:nth-child(3)").text.rstrip().replace("\n", "")
        series_chapter = soup.select_one(".breadcrumb > .active").text.rstrip().replace("\n", "")

        return self._download_chapter_files(dom, series_title, series_chapter, 'https://x.mangas-origines.fr/',
                                            force_re_dl, keep_img, full_logs)
