import base64
import re

from downloaders.Downloader import Downloader
from downloaders.Series import Series


class Manga18Downloader(Downloader):
    platform = "Manga18.club"

    def __init__(self, base_dir: str, logger=None):
        super().__init__(base_dir, logger)

    @staticmethod
    def is_a_series_link(link: str) -> bool:
        return re.search(r"https://manga18\.club/manhwa/((\w*-*)+\d*)/?$", link) is not None

    @staticmethod
    def is_a_chapter_link(link: str) -> bool:
        return re.search(r"https://manga18\.club/manhwa/.+/(\w+-)?\d+/?$", link) is not None

    @staticmethod
    def _extract_pictures_links_from_webpage(dom) -> list[str]:
        js_scpipt_with_pictures = dom.xpath('/html/body/div[3]/div[5]/script[1]')[0].text

        js_array_of_pictures = re.search(r'var slides_p_path = \[((("\w+(=?)*")+,)+)\];',
                                         js_scpipt_with_pictures).group(0)

        pictures_base64 = js_array_of_pictures.split('= [')[1].split(']')[0].replace('"', '')[:-1]

        pictures_links = []
        for picture_base64 in pictures_base64.split(","):
            link = base64.b64decode(picture_base64).decode('utf-8')
            if link[link.rfind(".") + 1:].lower() in ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif']:
                pictures_links.append(link)

        return pictures_links

    def download_series(self, link: str):
        if link[len(link) - 1] != "/":
            link += "/"

        for logger in self.loggers:
            logger.log("[Info][{}][Series] Get HTML content".format(self.platform))

        soup, dom = self._get_page_content(link)

        series_title = soup.find('div', {'class': 'detail_name'}).find('h1').text

        series = self.generate_series(series_title, link)

        # get all website url of the series
        for chapter_tags in soup.find("div", {"class": "chapter_box"}).find_all("li"):
            series.add_chapter_link("https://manga18.club" + chapter_tags.find("a").attrs["href"])
        series.get_chapters_links().reverse()

        series = self._download_chapters_from_series(series)

        for logger in self.loggers:
            logger.log("[Info][{}][series] '{}': completed".format(self.platform, series.get_name()))

        return series

    def download_chapter(self, link: str, force_re_dl: bool = False):
        soup, dom = self._get_page_content(link)

        series_title = soup.find('div', {'class': 'story_name'}).find('h1').text
        series_chapter = soup.find('div', {'class': 'chapter_name'}).find('span').text

        return self._download_chapter_files(dom, series_title, series_chapter, 'https://manga18.club', force_re_dl)
