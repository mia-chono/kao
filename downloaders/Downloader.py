import glob
import io
import os
import shutil
import time
from os import path
from typing import Optional

import cloudscraper
from PIL import ImageFile, Image
from bs4 import BeautifulSoup
from lxml import etree

import utils
from downloaders.Chapter import Chapter
from downloaders.Series import Series
from loggers.Logger import Logger


class Downloader:
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
        self.last_response = None

    @staticmethod
    def is_a_series_link(link: str) -> bool:
        raise "Not Implemented"

    @staticmethod
    def is_a_chapter_link(link: str) -> bool:
        raise "Not Implemented"

    @staticmethod
    def _create_skeleton(chapter_path: str) -> None:
        # remove folder with possible corrupted img and skeleton
        if path.exists(chapter_path):
            shutil.rmtree(chapter_path)

        os.makedirs(chapter_path)

    @staticmethod
    def _pdf_exists(chapter_path: str, pdf_file_name: str) -> Optional[str]:
        if path.exists(path.join(chapter_path, f"{pdf_file_name}.pdf")):
            return path.join(chapter_path, f"{pdf_file_name}.pdf")
        return None

    @staticmethod
    def _img_is_too_small(img_content: bytes, min_height: int = 10):
        img_parser = ImageFile.Parser()
        img_parser.feed(img_content)
        width, height = img_parser.image.size
        return height < min_height

    @staticmethod
    def _extract_pictures_links_from_webpage(dom: etree._Element) -> list[str]:
        raise "Not Implemented"

    @staticmethod
    def _clear_images(chapter_path: str):
        for file_to_delete in glob.glob("{}/*.*".format(chapter_path)):
            if not file_to_delete.lower().endswith("pdf"):
                os.remove(file_to_delete)

    def _set_cookies(self, cookies):
        self.cookies = cookies

    def _download_pictures(self, chapter_path: str, pictures_links: list[str], referer: str):
        counter = 1
        for link in pictures_links:
            headers = {
                'User-Agent': utils.user_agent,
                'referer': referer
            }
            img_response = self.scraper.get(link, headers=headers, cookies=self.cookies)
            if self._img_is_too_small(img_response.content):
                continue
            image_bytes = io.BytesIO(img_response.content)
            image = Image.open(image_bytes)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(path.join(chapter_path, str(counter).zfill(3) + ".jpg"))
            counter += 1

    def _get_page_content(self, link: str) -> tuple[BeautifulSoup, etree._Element]:
        response = self.scraper.get(link, cookies=self.cookies)
        soup = BeautifulSoup(response.content, "html.parser")
        dom = etree.HTML(str(soup))
        return soup, dom

    def download_series(self, link: str) -> Series:
        raise "Not Implemented"

    def generate_series(self, series_title: str, link: str) -> Series:
        for logger in self.loggers:
            logger.log("[Info][{}][Series] Creating object".format(self.platform))

        series = Series(series_title, link)
        series.set_platform(self.platform)

        for logger in self.loggers:
            logger.log("[Info][{}][series] Getting chapters' links from '{}'".format(self.platform, series.get_name()))

        return series

    def _download_chapters_from_series(self, series_to_download: Series):
        retry_download = 0
        total_chapters = len(series_to_download.get_chapters_links())
        retry = True
        for logger in self.loggers:
            logger.log("[Info][{}][Series] Start downloading {} chaps from '{}'".format(self.platform, total_chapters,
                                                                                        series_to_download.name))
        for index in range(0, total_chapters):
            while retry:
                try:
                    for logger in self.loggers:
                        logger.log(
                            "[Info][{}][Series] Get Chapter {} / {}\t(retry {})".format(self.platform, index + 1,
                                                                                        total_chapters, retry_download))
                    if retry_download > 3:
                        retry_download = 0
                        for logger in self.loggers:
                            logger.log(
                                "[Error][{}][Series][Download] '{}' => <{}>".format(self.platform,
                                                                                    series_to_download.name,
                                                                                    series_to_download.get_chapter_link(
                                                                                        index)))
                        retry = False
                        continue

                    chapter = self.download_chapter(series_to_download.get_chapter_link(index))
                    series_to_download.add_chapter(chapter)
                    time.sleep(1.5)
                    retry = False
                except Exception as e:
                    retry_download += 1
                    for logger in self.loggers:
                        logger.log("[Error][{}][Series][Download][Exception] <{}> : {}".format(self.platform,
                                                                                               series_to_download.get_chapter_link(
                                                                                                   index), e))
            retry = True
        return series_to_download

    def download_chapter(self, link: str) -> Chapter:
        raise "Not Implemented"

    def _download_chapter_files(self, dom: etree._Element, series_title: str, series_chapter: str, referer: str,
                                force_re_dl: bool = False) -> Chapter:
        series_name = utils.replace_char_in_string(series_title, utils.invalid_directory_name_chars, "")
        chapter_name = utils.replace_char_in_string(series_chapter, utils.invalid_directory_name_chars, "")

        chapter_path = path.join(self.base_dir, series_name, chapter_name)

        chapter = Chapter(series_name, chapter_name, self.platform)

        pdf_path = self._pdf_exists(chapter_path, chapter.get_full_name())

        if pdf_path is None or force_re_dl is True:
            for logger in self.loggers:
                logger.log("[Info][{}][Chapter] Creating structure...".format(self.platform))

            self._create_skeleton(chapter_path)
        else:
            for logger in self.loggers:
                logger.log("[Info][{}][Chapter] '{}': PDF exists".format(self.platform, chapter.get_full_name()))
            chapter.set_pdf_path(pdf_path)
            return chapter

        for logger in self.loggers:
            logger.log("[Info][{}][Chapter] Downloading pictures...".format(self.platform, chapter.get_full_name()))

        pictures_links = self._extract_pictures_links_from_webpage(dom)

        self._download_pictures(chapter_path, pictures_links, referer)

        for logger in self.loggers:
            logger.log("[Info][{}][Chapter] '{}': Creating pdf".format(self.platform, chapter.get_full_name()))

        pdf_path = utils.convert_to_pdf(chapter_path, chapter.get_full_name(), self.loggers)
        chapter.set_pdf_path(pdf_path)

        for logger in self.loggers:
            logger.log("[Info][{}][Chapter] '{}': Complete".format(self.platform, chapter.get_full_name()))

        self._clear_images(chapter_path)

        return chapter
