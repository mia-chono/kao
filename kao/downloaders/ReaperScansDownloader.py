import re

from .Downloader import Downloader
from .. import utils


class ReaperScansDownloader(Downloader):
    platform = "ReaperScans"

    def __init__(self, base_dir: str, logger=None):
        super().__init__(base_dir, logger)

    @staticmethod
    def is_a_series_link(link: str) -> bool:
        return re.search(r"https?://(www\.)?reaperscans\.fr/series?/[^/?]+/?$", link) is not None

    @staticmethod
    def is_a_chapter_link(link: str) -> bool:
        return re.search(r"https?://(www\.)?reaperscans\.fr/series?/[^/]+/chapitre-\d+/?$", link) is not None

    @staticmethod
    def extract_pictures_links_from_webpage(dom) -> list[str]:
        img_tags = dom.xpath('//*[@class="reading-content"]//img')

        pictures_links = list(map(lambda img_tag: img_tag.get("src").replace("\n", ""), img_tags))

        return pictures_links

    def download_series(self, link: str, force_re_dl: bool = False, keep_img: bool = False, full_logs: bool = False):
        if link[len(link) - 1] != "/":
            link += "/"

        utils.log(self.loggers, "[Info][{}][Series] Get HTML content".format(self.platform))

        soup, dom = self._get_page_content(link)

        series_title = self._clear_name(soup.find("div", {"class": "post-title"}).find("h1").text)

        series = self.generate_series(series_title, link)

        # get all website url of the series
        for chapter_tag in soup.find_all("div", {"class": "chapter-link"}):
            series.add_chapter_link(chapter_tag.find("a").attrs["href"])
        series.get_chapters_links().reverse()

        series = self._download_chapters_from_series(series, force_re_dl, keep_img, full_logs)

        utils.log(self.loggers, "[Info][{}][series] '{}': completed".format(self.platform, series.get_name()))

        return series

    def download_chapter(self, link: str, force_re_dl: bool = False, keep_img: bool = False, full_logs: bool = False):
        soup, dom = self._get_page_content(link)

        series_title = self._clear_name(soup.select_one(".breadcrumb > li:nth-child(2)").text)
        series_chapter = self._clear_name(soup.select_one(".breadcrumb > .active").text)

        return self._download_chapter_files(dom, series_title, series_chapter, 'https://reaperscans.fr/', force_re_dl,
                                            keep_img, full_logs)
