import glob
import re
import os
import shutil
import time
from os import path
from pathlib import Path
from typing import Optional

import cloudscraper
import unidecode
from PIL import Image
from bs4 import BeautifulSoup
from lxml import etree

from .Chapter import Chapter
from .Series import Series
from .. import utils
from ..loggers import Logger


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

        utils.create_directory(chapter_path)

    @staticmethod
    def _pdf_exists(chapter_path: str, pdf_file_name: str) -> Optional[str]:
        if path.exists(path.join(chapter_path, f"{pdf_file_name}.pdf")):
            return path.join(chapter_path, f"{pdf_file_name}.pdf")
        return None

    def extract_pictures_links_from_webpage(dom: etree._Element) -> list[str]:
        raise "Not Implemented"

    @staticmethod
    def _clear_images(chapter_path: str):
        for file_to_delete in glob.glob("{}/*.*".format(chapter_path)):
            if not file_to_delete.lower().endswith("pdf"):
                os.remove(file_to_delete)

    @staticmethod
    def _is_chapter_already_downloaded(series_path: str, chapter_name: str,
                                       file_name: str = "downloaded_chapters.txt") -> bool:

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
        file_path = path.join(series_path, file_name)

        if not path.exists(series_path):
            utils.create_directory(series_path)

        if not path.exists(file_path):
            with open(file_path, "w") as f:
                f.write(chapter_name + "\n")
        else:
            with open(file_path, "a") as f:
                f.write(chapter_name + "\n")

    def _set_cookies(self, cookies):
        self.cookies = cookies

    def _download_pictures(self, chapter_path: str, pictures_links: list[str], referer: str,
                           full_logs: bool = False) -> None:
        counter = 1
        total_pictures = len(pictures_links)
        headers = {
            'User-Agent': utils.user_agent,
            'referer': referer
        }
        for link in pictures_links:
            img_response = self.scraper.get(link, headers=headers, cookies=self.cookies)
            img_content = img_response.content
            img_path = path.join(chapter_path, str(counter).zfill(len(str(total_pictures))) + ".jpg")
            img_is_too_large_or_small = utils.img_is_too_small(img_content) \
                                        or utils.img_is_too_large(img_content)
            try:
                if img_is_too_large_or_small:
                    if full_logs:
                        utils.log(self.loggers,
                                  "[Info][{}][Chapter][Download] Image {} from {} is too small".format(self.platform,
                                                                                                       counter,
                                                                                                       os.path.basename(
                                                                                                           chapter_path)))
                    continue
                if utils.img_has_alpha_channel(img_content):
                    utils.log(self.loggers,
                              "[Info][{}][Chapter][Download] Image ".format(self.platform, img_path))
                    # save image file after removing alpha channel
                    utils.force_image_rgb(img_content=img_content, img_path=img_path)
                else:
                    # save image file
                    with open(img_path, "wb") as f:
                        f.write(img_content)

            except Exception as e:
                utils.log(self.loggers,
                          "[Error][{}][Chapter][Download] message: {}".format(self.platform, e))
                utils.log(self.loggers,
                          "[Info][{}][Chapter][Download] Image {} corrupted".format(self.platform, counter))
                corrupted_img_path = os.path.join(Path(__file__).parent.parent, 'corrupted_picture.jpg')
                img = Image.open(corrupted_img_path)
                img.save(img_path)  # save the corrupted image
            counter += 1

    def _get_page_content(self, link: str) -> tuple[BeautifulSoup, etree._Element]:
        response = self.scraper.get(link, cookies=self.cookies)
        soup = BeautifulSoup(response.content, "html.parser")
        dom = etree.HTML(str(soup))
        return soup, dom

    def download_series(self, link: str, force_re_dl: bool = False, keep_img: bool = False,
                        full_logs: bool = False) -> Series:
        raise "Not Implemented"

    def generate_series(self, series_title: str, link: str) -> Series:
        utils.log(self.loggers, "[Info][{}][Series] Creating object".format(self.platform))

        series = Series(series_title, link)
        series.set_platform(self.platform)

        utils.log(self.loggers,
                  "[Info][{}][series] Getting chapters' links from '{}'".format(self.platform, series.get_name()))

        return series

    def _download_chapters_from_series(self, series_to_download: Series, force_re_dl: bool = False,
                                       keep_img: bool = False, full_logs: bool = False) -> Series:
        retry_download = 0
        total_chapters = len(series_to_download.get_chapters_links())
        retry = True
        utils.log(self.loggers,
                  "[Info][{}][Series] Start downloading {} chaps from '{}'".format(self.platform, total_chapters,
                                                                                   series_to_download.name))
        for index in range(0, total_chapters):
            while retry:
                try:
                    utils.log(self.loggers,
                              "[Info][{}][Series] Get Chapter {} / {}\t(retry {})".format(self.platform, index + 1,
                                                                                          total_chapters,
                                                                                          retry_download))
                    if retry_download > 3:
                        retry_download = 0
                        utils.log(self.loggers, "[Error][{}][Series][Download] '{}' => <{}>".format(self.platform,
                                                                                                    series_to_download.name,
                                                                                                    series_to_download.get_chapter_link(
                                                                                                        index)))
                        retry = False
                        continue

                    chapter = self.download_chapter(series_to_download.get_chapter_link(index), force_re_dl, keep_img,
                                                    full_logs)
                    series_to_download.add_chapter(chapter)
                    time.sleep(1.5)
                    retry = False
                except Exception as e:
                    retry_download += 1
                    utils.log(self.loggers, "[Error][{}][Series][Download][Exception] <{}> : {}".format(self.platform,
                                                                                                        series_to_download.get_chapter_link(
                                                                                                            index), e))
            retry = True
        return series_to_download

    def download_chapter(self, link: str, force_re_dl: bool = False, keep_img: bool = False,
                         full_logs: bool = False) -> Chapter:
        raise "Not Implemented"

    @staticmethod
    def _clear_name(name: str, list_of_char_to_replace) -> str:
        new_name = utils.remove_dots_end_of_file_name(unidecode.unidecode(name))
        new_name = utils.replace_char_in_string(new_name, list_of_char_to_replace, "")
        # return re.sub(r'[A-Za-z0-9\s\-.°§+¦"@*#ç%&¬|¢()=]+', '', new_name).strip()
        return new_name.strip()

    def _download_chapter_files(self, dom: etree._Element, series_title: str, series_chapter: str, referer: str,
                                force_re_dl: bool = False, keep_img: bool = False, full_logs: bool = False) -> Chapter:
        series_name = self._clear_name(series_title, utils.invalid_directory_name_chars)
        chapter_name = self._clear_name(series_chapter, utils.invalid_file_name_chars)
        print(series_name, chapter_name)
        series_path = path.join(self.base_dir, series_name)
        chapter_path = path.join(series_path, chapter_name)

        chapter = Chapter(series_name, chapter_name, self.platform)

        if self._is_chapter_already_downloaded(series_path, chapter.chapter_name) and not force_re_dl:
            utils.log(self.loggers,
                      "[Info][{}][Chapter][Download] Chapter {} from {} is already downloaded".format(self.platform,
                                                                                                      chapter.get_full_name(),
                                                                                                      series_name))
            pdf_path = self._pdf_exists(chapter_path, chapter.get_full_name())
            chapter.set_pdf_path(pdf_path)
            return chapter

        try:
            self._create_skeleton(chapter_path)
        except Exception as e:
            utils.log(self.loggers, "[Error][{}][Chapter][Download] {}".format(self.platform, e))
            raise

        utils.log(self.loggers,
                  "[Info][{}][Chapter] Downloading pictures...".format(self.platform, chapter.get_full_name()))

        pictures_links = self.extract_pictures_links_from_webpage(dom)

        self._download_pictures(chapter_path, pictures_links, referer, full_logs)

        utils.log(self.loggers, "[Info][{}][Chapter] '{}': Creating pdf".format(self.platform, chapter.get_full_name()))

        pdf_path = utils.convert_to_pdf(chapter_path, chapter.get_name(), self.loggers, full_logs)
        chapter.set_pdf_path(pdf_path)

        self._add_chapter_to_downloaded_chapters(series_path, chapter.get_name())
        utils.log(self.loggers, "[Info][{}][Chapter] '{}': Complete".format(self.platform, chapter.get_full_name()))

        if keep_img is False:
            self._clear_images(chapter_path)

        return chapter
