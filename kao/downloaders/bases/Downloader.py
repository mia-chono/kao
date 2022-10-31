import os
import shutil
from os import path
from pathlib import Path

import cloudscraper
import unidecode
from PIL import Image
from bs4 import BeautifulSoup
from lxml import etree

from . import Series, Chapter
from .. import downloader_utils
from ... import kao_utils
from ...loggers import Logger


class Downloader:
    """
    Abstract class to download scans from a website
    """
    platform = None

    def __init__(self, base_dir: str, loggers: list[Logger] = None):
        self.base_dir = os.path.join(base_dir, self.platform)
        self.loggers = loggers
        self.cookies = None
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'firefox',
                'platform': 'windows',
                'mobile': False
            },
        )

    @staticmethod
    def is_a_series_link(link: str) -> bool:
        """
        Check if the given link is a link of a series
        :param link: str - https://myWebsite.com/series/seriesName
        :return: bool - True if the link is a link of a series
        """
        raise "Not Implemented"

    @staticmethod
    def is_a_chapter_link(link: str) -> bool:
        """
        Check if the given link is a link of a chapter
        :param link: str - https://myWebsite.com/series/seriesName/chapterName
        :return: bool - True if the link is a chapter link
        """
        raise "Not Implemented"

    @staticmethod
    def _create_skeleton(chapter_path: str) -> None:
        """
        Create the skeleton of the chapter
        Remove the chapter folder if it already exists
        :param str - chapter_path: path to the chapter
        :return: None
        """
        # remove folder with all its content if it already exists
        if path.exists(chapter_path):
            shutil.rmtree(chapter_path)

        downloader_utils.create_directory(chapter_path)

    @staticmethod
    def extract_pictures_links_from_webpage(dom: etree._Element) -> list[str]:
        """
        Extract the pictures links from the webpage
        :param dom: etree._Element - the dom of the webpage
        :return: list[str] - list of pictures links
        """
        raise "Not Implemented"

    @staticmethod
    def _clear_images(chapter_path: str) -> None:
        """
        Remove all images from the chapter folder to save space
        :param chapter_path: str - path to the chapter
        :return: None
        """
        for file_to_delete in downloader_utils.find_images_in_tree(chapter_path):
            os.remove(file_to_delete)

    @staticmethod
    def _is_chapter_already_downloaded(series_path: str, chapter_name: str,
                                       file_name: str = "downloaded_chapters.txt") -> bool:
        """
        Check if the chapter is already downloaded
        :param series_path: str - path to the series
        :param chapter_name: str - name of the chapter
        :param file_name: str - name of the file containing the downloaded chapters
        :return: bool - True if the chapter is already downloaded
        """
        file_path = path.join(series_path, file_name)

        if path.exists(file_path) and path.isfile(file_path):
            with open(file_path, "r") as f:
                for line in f:
                    if line.strip() == chapter_name:
                        return True
        return False

    @staticmethod
    def _add_chapter_to_downloaded_chapters(series_path: str, chapter_name: str,
                                            file_name: str = "downloaded_chapters.txt") -> None:
        """
        Add the chapter to the downloaded chapters file
        :param series_path: str - path to the series
        :param chapter_name: str - name of the chapter
        :param file_name: str - name of the file containing the downloaded chapters
        :return: None
        """
        file_path = path.join(series_path, file_name)

        if not path.exists(series_path):
            downloader_utils.create_directory(series_path)

        if not path.exists(file_path):
            with open(file_path, "w") as f:
                f.write(chapter_name + "\n")
        else:
            with open(file_path, "a") as f:
                f.write(chapter_name + "\n")

    def _set_cookies(self, cookies: dict) -> None:
        """
        Set the cookies to use for the scraper
        :param cookies: dict - cookies to use
        :return: None
        """
        self.cookies = cookies

    def _download_pictures(self, chapter_path: str, pictures_links: list[str], referer: str,
                           full_logs: bool = False) -> None:
        """
        Download all pictures from the list of pictures links
        :param chapter_path: str - path to the chapter
        :param pictures_links: list[str] - list of pictures links
        :param referer: str - referer to use for the request (ex: myWebsite.com for myWebsite.com/series/seriesName)
        :param full_logs: bool - True to display full logs
        :return: None
        """
        counter = 1
        total_pictures = len(pictures_links)
        zfill_required = len(str(total_pictures))
        headers = {
            'User-Agent': downloader_utils.user_agent,
            'referer': referer
        }
        for link in pictures_links:
            img_number = str(counter).zfill(zfill_required)
            if full_logs:
                kao_utils.log(self.loggers, "[Info][{platform}][Chapter][Image] {which_image}/{total_pictures}: {link}"
                              .format(platform=self.platform, which_image=img_number, total_pictures=total_pictures,
                                      link=link))

            img_response = self.scraper.get(link, headers=headers, cookies=self.cookies)
            img_content = img_response.content
            # check img_content is OK because some sites return 200 even if the img is a fake img
            # Example: when Scantrad put on their site images from Webtoons, the last img of the chapter is a fake img
            # with an "OK" content
            if img_response.status_code != 200:
                if full_logs:
                    kao_utils.log(self.loggers, "[Error][{}][Chapter] Error while downloading picture '{}'"
                                  .format(self.platform, link))
                continue
            if img_content == b'OK' or b'Bad Request' in img_content:
                if full_logs:
                    kao_utils.log(self.loggers,
                                  "[Warning][{}][chapter] Image '{}' is a fake img, content: \"{}\"".format(
                                      self.platform, link, img_content))
                continue

            img_extension = downloader_utils.get_img_extension(img_content)
            img_path = path.join(chapter_path, img_number + "." + img_extension)
            try:
                img_is_too_large_or_small = downloader_utils.img_is_too_small(
                    img_content) or downloader_utils.img_is_too_large(img_content)

                if img_is_too_large_or_small:
                    if full_logs:
                        kao_utils.log(self.loggers, "[Info][{}][Chapter][Download] Image {} from {} is too small"
                                      .format(self.platform, counter, os.path.basename(chapter_path)))
                    continue
                if downloader_utils.img_has_alpha_channel(img_content) and img_extension.lower() != "png":
                    kao_utils.log(self.loggers, "[Info][{}][Chapter][Download] Image {}"
                                  .format(self.platform, img_path))
                    # save image file after removing alpha channel
                    downloader_utils.force_image_rgb(img_content=img_content, img_path=img_path)
                else:
                    # save image file
                    with open(img_path, "wb") as f:
                        f.write(img_content)

            except Exception as e:
                kao_utils.log(self.loggers, "[Error][{}][Chapter][Download] message: {}".format(self.platform, e))
                corrupted_img_path = os.path.join(Path(__file__).parent.parent, 'corrupted_picture.jpg')
                img = Image.open(corrupted_img_path)
                img.save(img_path)  # save the corrupted image
            counter += 1

    def _get_page_content(self, link: str) -> tuple[BeautifulSoup, etree._Element]:
        """
        get the html content of the page
        :param link: str - link of the page
        :return: tuple[BeautifulSoup, etree._Element] - (html content, xml content)
        """
        response = self.scraper.get(link, cookies=self.cookies)
        soup = BeautifulSoup(response.content, "html.parser")
        dom = etree.HTML(str(soup))
        return soup, dom

    def create_series(self, link: str) -> Series:
        """
        Create a series with all its chapters from the link
        :param link: str - link of the series
        :return: Series - series created
        """
        raise NotImplementedError

    def download_series(self, series: Series, force_re_dl: bool = False, keep_img: bool = False,
                        full_logs: bool = False) -> Series:
        """
        Download the series from the link
        :param series: Series - series object to download
        :param force_re_dl: bool - True to force the re-download of the series
        :param keep_img: bool - True to keep the images after the download on the chapter folder
        :param full_logs: bool - True to display full logs
        :return: Series - the downloaded series
        """
        raise "Not Implemented"

    def _generate_series(self, series_title: str, link: str, full_logs: bool = False) -> Series:
        """
        Generate a Series object with minimal information
        :param series_title: str - title of the series
        :param link: str - link of the series
        :param full_logs: bool - True to display full logs
        :return: Series - the generated series
        """
        if full_logs:
            kao_utils.log(self.loggers, "[Info][{}][Series] Creating object".format(self.platform))

        series = Series(series_title, link)
        series.set_platform(self.platform)

        if full_logs:
            kao_utils.log(self.loggers, "[Info][{}][series] Getting chapters' links from '{}'"
                          .format(self.platform, series.get_name()))

        return series

    def _download_chapters_from_series(self, series: Series, force_re_dl: bool = False,
                                       keep_img: bool = False, full_logs: bool = False) -> Series:
        """
        Download all chapters from the series object
        :param series: Series - series to download
        :param force_re_dl: bool - True to force the re-download of the series
        :param keep_img: bool - True to keep the images after the download on the chapter folder
        :param full_logs: bool - True to display full logs
        :return: Series - the downloaded series
        """
        retry_download = 0
        total_chapters = len(series.get_all_chapter_links())
        retry = True
        kao_utils.log(self.loggers, "[Info][{}][Series] Start downloading {} chaps from '{}'"
                      .format(self.platform, total_chapters, series.name))
        for index in range(0, total_chapters):
            while retry:
                try:
                    kao_utils.log(self.loggers, "[Info][{}][Series] Get Chapter {} / {}\t(retry {})"
                                  .format(self.platform, index + 1, total_chapters, retry_download))
                    if retry_download > 3:
                        retry_download = 0
                        kao_utils.log(self.loggers, "[Error][{}][Series][Download] '{}' : {}"
                                      .format(self.platform, series.name, series.get_chapter_link(index)))
                        retry = False
                        continue

                    chapter = self.download_chapter(series.get_chapter_link(index), force_re_dl, keep_img, full_logs)
                    series.add_chapter(chapter)
                    retry = False
                except Exception as e:
                    retry_download += 1
                    kao_utils.log(self.loggers, "[Error][{}][Series][Download][Exception] '{}' : {}"
                                  .format(self.platform, series.get_chapter_link(index), e))
            retry = True
        return series

    def download_chapter(self, link: str, force_re_dl: bool = False, keep_img: bool = False,
                         full_logs: bool = False) -> Chapter:
        """
        Download the chapter from the link
        :param link: str - link of the chapter
        :param force_re_dl: bool - True to force the re-download of the series
        :param keep_img: bool - True to keep the images after the download on the chapter folder
        :param full_logs: bool - True to display full logs
        :return: Chapter - the downloaded chapter
        """
        raise "Not Implemented"

    @staticmethod
    def _clear_name(name: str) -> str:
        """
        remove all special characters from the name and remove white spaces at the end and the beginning
        :param name: str - name to clean
        :return: str - cleaned name
        """
        new_name = downloader_utils.remove_dots_end_of_file_name(unidecode.unidecode(name))
        new_name = downloader_utils.replace_char_in_string(new_name, downloader_utils.invalid_chars, "")

        return downloader_utils.clear_white_characters(new_name.strip())

    def _download_chapter_files(self, dom: etree._Element, series_title: str, series_chapter: str, referer: str,
                                force_re_dl: bool = False, keep_img: bool = False, full_logs: bool = False) -> Chapter:
        """
        Download all the images from the chapter
        :param dom: etree._Element - xml content of the chapter webpage
        :param series_title: str - title of the series
        :param series_chapter: str - title of the chapter
        :param referer: str - referer of the chapter link (ex: myWebSite.com when the link is myWebSite.com/chapter)
        :param force_re_dl: bool - True to force the re-download of the series
        :param keep_img: bool - True to keep the images after the download on the chapter folder
        :param full_logs: bool - True to display full logs
        :return: Chapter - the downloaded chapter
        """
        series_name = self._clear_name(series_title)
        chapter_name = self._clear_name(series_chapter)
        kao_utils.log(self.loggers, "[Info][{platform}][Chapter][Download] {series} - {chapter}"
                      .format(platform=self.platform, series=series_name, chapter=chapter_name))

        series_path = path.join(self.base_dir, series_name)
        chapter_path = path.join(series_path, chapter_name)

        chapter = Chapter(series_name, chapter_name, self.platform)

        if self._is_chapter_already_downloaded(series_path, chapter.name) and not force_re_dl:
            kao_utils.log(self.loggers, "[Info][{}][Chapter] Chapter '{}' from '{}' is already downloaded"
                          .format(self.platform, chapter.get_full_name(), series_name))
            return chapter

        try:
            self._create_skeleton(chapter_path)
        except Exception as e:
            kao_utils.log(self.loggers, "[Error][{}][Chapter] Error when creating the chapter skeleton: {}"
                          .format(self.platform, e))
            raise "Error when creating the chapter skeleton"

        kao_utils.log(self.loggers, "[Info][{}][Chapter] Downloading pictures...".format(self.platform))

        pictures_links = self.extract_pictures_links_from_webpage(dom)

        self._download_pictures(chapter_path, pictures_links, referer, full_logs)

        self._add_chapter_to_downloaded_chapters(series_path, chapter.get_name())
        kao_utils.log(self.loggers, "[Info][{}][Chapter] '{}': Complete".format(self.platform, chapter.get_full_name()))

        if keep_img is False:
            self._clear_images(chapter_path)

        return chapter
