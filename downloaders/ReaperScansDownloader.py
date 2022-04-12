import re

from downloaders.Downloader import Downloader


class ReaperScansDownloader(Downloader):
    platform = "ReaperScans"

    def __init__(self, base_dir: str, logger=None):
        super().__init__(base_dir, logger)

    @staticmethod
    def is_a_series_link(link: str) -> bool:
        return re.search(r"https?://(www\.)?reaperscans\.fr/manga/((\w*-*)+\d*)/?$", link) is not None

    @staticmethod
    def is_a_chapter_link(link: str) -> bool:
        return re.search(r"https?://(www\.)?reaperscans\.fr/((\w*-*)+\d*)/?$", link) is not None

    @staticmethod
    def _extract_pictures_links_from_webpage(dom) -> list[str]:
        img_tags = dom.xpath("//*[@id='readerarea']//img")

        pictures_links = list(map(lambda img_tag: img_tag.get("src"), img_tags))

        return pictures_links

    def download_series(self, link: str, force_re_dl: bool = False):
        if link[len(link) - 1] != "/":
            link += "/"

        for logger in self.loggers:
            logger.log("[Info][{}][Series] Get HTML content".format(self.platform))

        soup, dom = self._get_page_content(link)

        series_title = soup.find("h1", {"class": "entry-title"})

        series = self.generate_series(series_title, link)

        # get all website url of the series
        for chapter_tag in soup.find("div", {"id": "chapterlist"}).find_all("li"):
            series.add_chapter_link(chapter_tag.find("a").attrs["href"])
        series.get_chapters_links().reverse()

        series = self._download_chapters_from_series(series, force_re_dl)

        for logger in self.loggers:
            logger.log("[Info][{}][series] '{}': completed".format(self.platform, series.get_name()))

        return series

    def download_chapter(self, link: str, force_re_dl: bool = False):
        soup, dom = self._get_page_content(link)

        series_title = dom.xpath("/html/body/div[2]/div[2]/div[1]/div/article/div[1]/div/a")[0].text
        series_chapter = soup.find("div", {"class": "daw chpnw"}).text.rstrip()

        return self._download_chapter_files(dom, series_title, series_chapter, 'http://reaperscans.fr/', force_re_dl)
