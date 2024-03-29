import re

from lxml import etree

from .bases import Series, Chapter, Downloader
from .. import kao_utils
from ..loggers import Logger


class WebtoonDownloader(Downloader):
    """
    Downloader to scrape Webtoon.com series or chapters
    """
    platform = "Webtoon"

    def __init__(self, base_dir: str, loggers: list[Logger] = None):
        super().__init__(base_dir, loggers)
        self._set_cookies(dict(pagGDPR='true'))

    @staticmethod
    def is_a_series_link(link: str) -> bool:
        return re.search(r"https?://(www\.)?webtoons\.com/\w{2}/[\w\-%]+/[\w\-%]+/list\?title_no=\d+$",
                         link) is not None

    @staticmethod
    def is_a_chapter_link(link: str) -> bool:
        return re.search(
            r"https?://(www\.)?webtoons\.com/\w{2}/[\w\-%]+/[\w\-%]+/[a-zA-Z\d-]+/viewer\?title_no=\d*&episode_no=\d+$",
            link) is not None

    @staticmethod
    def extract_pictures_links_from_webpage(dom: etree._Element) -> list[str]:
        img_html_elements = dom.xpath("/html/body/div[1]/div[2]/div[3]/div[1]/div/div/img")
        pictures_links = []
        for element in img_html_elements:
            if element.get('data-url').find("https://webtoon-phinf.pstatic.net/") != -1:
                link = element.get('data-url').replace("?type=q90", "")
                pictures_links.append(link)

        return pictures_links

    def create_series(self, link: str) -> Series:
        soup, dom = self._get_page_content(link)

        base_link = link.split("/list?title_no")[0]
        series_id = link.split("title_no=")[1]
        last_ep_number = \
            dom.xpath("/html/body/div[1]/div[3]/div/div[2]/div[2]/div[1]/ul/li[1]/a")[0].get("href").split(
                "&episode_no=")[1]

        series_title = self._clear_name(soup.find("h1", {"class": "subj"}).text)

        series = self._generate_series(series_title, link)

        # get all website url of the series
        for chap_number in range(1, int(last_ep_number) + 1):
            url = f"{base_link}/ep{chap_number}/viewer?title_no={series_id}&episode_no={chap_number}"
            series.add_chapter_link(url)

        return series

    def download_series(self, series: Series, force_re_dl: bool = False, keep_img: bool = False,
                        full_logs: bool = False) -> Series:
        kao_utils.log(self.loggers, "[Info][{}][Series] Get HTML content".format(self.platform))

        self._download_chapters_from_series(series, force_re_dl, keep_img)

        kao_utils.log(self.loggers, "[Info][{}][series] '{}': completed".format(self.platform, series.get_name()))

        return series

    def download_chapter(self, link: str, force_re_dl: bool = False, keep_img: bool = False,
                         full_logs: bool = False) -> Chapter:
        soup, dom = self._get_page_content(link)

        series_title = self._clear_name(dom.xpath('//*[@id="toolbar"]/div[1]/div/a')[0].text)
        series_chapter = self._clear_name(dom.xpath('//*[@id="toolbar"]/div[1]/div/h1')[0].text)

        return self._download_chapter_files(dom, series_title, series_chapter, 'https://www.webtoons.com', force_re_dl,
                                            keep_img, full_logs)
