import os
import argparse
import time
from pathlib import Path
from typing import Optional, Iterator
import shutil

import img2pdf

from .downloaders import Downloader
from .downloaders import PersonalDownloader
from .downloaders import downloader_utils
from .downloaders import Series
from .downloaders import Chapter
from .loggers import Logger


def log(loggers: list[Logger], message: str) -> None:
    for logger in loggers:
        logger.log(message)


def move_pdf_files_from_folder(folder_path: str, destination_path: str, loggers: list[Logger]) -> None:
    log(loggers, '[Info] moving all pdf files from \'{}\' to \'{}\''.format(folder_path, destination_path))

    # Move all pdf files from folder_path to destination_path by series name
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if 'pdf' in root:
                continue
            folder_path = Path(root).parent
            folder_name = Path(folder_path).name
            if file.endswith('.pdf'):
                downloader_utils.create_directory(os.path.join(destination_path, folder_name))
                shutil.move(os.path.join(root, file), os.path.join(destination_path, folder_name, file))

    log(loggers, '[Info] all pdf files moved')


def convert_to_pdf(chapter_dir: str, file_name: str, loggers: list[Logger], check_img: bool = False,
                   full_logs: bool = False) -> Optional[str]:
    try:
        if full_logs:
            log(loggers, '[Info][PDF] creating')

        images_list = []
        for element in os.listdir(chapter_dir):
            if os.path.join(chapter_dir, element) is not None:
                images_list.append(os.path.join(chapter_dir, element))
        images_list.sort()

        info_name = ''
        img_to_remove = []

        # When is personal folder, we need to ensure that all images are images
        if check_img is True:
            images_list = downloader_utils.keep_only_images_paths(images_list)

        for i in range(0, len(images_list)):
            img_is_too_large_or_small = downloader_utils.img_is_too_small(open(images_list[i], 'rb').read()) \
                                        or downloader_utils.img_is_too_large(open(images_list[i], 'rb').read())

            if full_logs:
                log(loggers, '[Info][PDF][Image] {}'.format(images_list[i]))

            if img_is_too_large_or_small:
                img_to_remove.append(i)
                if full_logs:
                    log(loggers, '[Info][PDF][Skip] Img too large or small, skipped: {}'.format(images_list[i]))
                continue
            if downloader_utils.test_is_image(images_list[i]) is None:
                if full_logs:
                    log(loggers, '[Info][PDF] Img corrupted')
                info_name = '[has_corrupted_images]'
                images_list[i] = os.path.join(Path(__file__).parent, 'corrupted_picture.jpg')

        # Remove unwanted images
        [images_list.pop(x) for x in img_to_remove]

        pdf_path = os.path.join(chapter_dir, f'{info_name}{file_name}.pdf')

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        with open(pdf_path, 'wb') as f:
            f.write(img2pdf.convert(images_list))

        if full_logs:
            log(loggers, '[Info][PDF] created')

        return pdf_path
    except Exception as e:
        log(loggers, '[Error][PDF] {error}'.format(error=e))
        return


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Downloader of manwha or manga scans')

    # hidden argument
    parser.add_argument("--log",
                        dest="logs",
                        help=argparse.SUPPRESS,
                        action="store_true",
                        default=False)

    parser.add_argument("-l",
                        "--links",
                        nargs="+",
                        dest="links",
                        help="Give chapters or series links (example: py __main__.py -l link1 link2) "
                             "(example2: py __main__.py -l link1 link2 -r file -m)")
    parser.add_argument("-k",
                        "--keep-img",
                        dest="keep_img",
                        help="If you want keep all images after download (example: py __main__.py -fkl link) "
                             "(example2: py __main__.py -l link -r file -m)",
                        action="store_true",
                        default=False)
    parser.add_argument("-f",
                        "--force",
                        dest="force_re_dl",
                        help="Download again the scan (example: py __main__.py -fkl link) "
                             "(example2: py __main__.py -l link -r file -m)",
                        action="store_true",
                        default=False)
    parser.add_argument("-p",
                        "--pdf",
                        dest="make_pdf",
                        help="Create pdf after download (example: py __main__.py -fkpl link) ",
                        action="store_true",
                        default=False)
    parser.add_argument("-m",
                        "--move-pdf",
                        dest="move_pdf",
                        nargs="?",
                        help="Move all pdf files to pdf folder (folder will be created if not exists at the root of "
                             "the downloads folder), put ALWAYS at the end of command to move all pdf files",
                        default=False)
    parser.add_argument("-r",
                        "--Read-file",
                        dest="read_file",
                        nargs="?",
                        help="Read given file to get urls, default is './list url.txt' but you can specify another "
                             "(example: py __main__.py -fkr file) (example2: py __main__.py -l link -r file -m)",
                        default=False)
    parser.add_argument("-s",
                        "--support",
                        dest="support",
                        help="Said supported websites",
                        action="store_true",
                        default=False)

    return parser


def get_series_and_chapters_from_links(list_downloaders: dict[str, Downloader], links: list[str],
                                       loggers: list[Logger]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """
    Get a tuple of series and chapters with their platform from a list of links
    :param list_downloaders: all downloaders to use
    :param links: list of links to get series and chapters
    :param loggers: list of loggers
    :return: tuple of series and chapters with their platform like
     {platform: 'myWeb', link: 'https://myWeb.example/series/...'}
    """
    functional_links = []
    series_to_download = []
    chapters_to_download = []
    # extract all downloaders
    downloaders = list(list_downloaders.values())

    for link in links:
        for downloader in downloaders:
            if downloader.is_a_series_link(link):
                series_to_download.append({"platform": downloader.platform, "link": link})
                functional_links.append(link)
                break
            elif downloader.is_a_chapter_link(link):
                chapters_to_download.append({"platform": downloader.platform, "link": link})
                functional_links.append(link)
                break

    links_not_available = set(functional_links) ^ set(links)
    if links_not_available:
        links_not_available = list(map(lambda x: "<{}>".format(x), links_not_available))

        platforms = ", ".join(x.platform for x in downloaders)
        links_to_display = "\n\t".join(link_not_available for link_not_available in links_not_available)
        log(loggers, "Invalid link(s), please give links from {platforms}\nInvalid links:\n\t{links}"
            .format(platforms=platforms, links=links_to_display))

    return series_to_download, chapters_to_download


def get_series_from_dict(list_downloaders: dict[str, Downloader], series_links: list[dict[str, str]]) -> list[Series]:
    """
    Get a list of series from a list of series links
    :param list_downloaders: all downloaders to use
    :param series_links: list of series to get chapters
    :return: list[Series] - list of series to download
    """
    series = []
    for obj in series_links:
        platform = obj["platform"]
        downloader = list_downloaders[platform]
        series.append(downloader.create_series(obj["link"]))

    return series


def get_all_chapters_from_series(list_downloaders: dict[str, Downloader],
                                 series_links: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Get all chapters from a list of series
    :param list_downloaders: all downloaders to use
    :param series_links: list of series to get chapters
    :return: list of chapters with their platform like
     {platform: 'myWeb', link: 'https://myWeb.example/series/...'}
    """
    chapters_to_download: list[dict[str, str]] = []
    for series in series_links:
        platform = series["platform"]
        downloader = list_downloaders[platform]
        series = downloader.create_series(series["link"])
        chapters_to_download.extend({'platform': platform, 'link': link} for link in series.get_all_chapter_links())

    return chapters_to_download


def download_chapters(list_downloaders: dict[str, Downloader], chapters: list[dict[str, str]], force_re_dl: bool,
                      keep_img: bool, full_logs: bool = False) -> Iterator[Chapter]:
    """
    Download all chapters from a list of chapters with their platform
    :param list_downloaders: dict[str, Downloader] - all downloaders to use
    :param chapters: list[dict[str, str]] - list of dictionary with platform and link of chapters to download
    :param force_re_dl: bool - if True, download again the scan
    :param keep_img: bool - if True, keep all images after download
    :param full_logs: bool - if True, display all logs
    :return: Iterator[Chapter] - iterator of downloaded chapters
    """
    for chapter in chapters:
        platform = chapter["platform"]
        downloader = list_downloaders[platform]
        yield downloader.download_chapter(chapter["link"], force_re_dl, keep_img, full_logs)


def download_series(list_downloaders: dict[str, Downloader], series: list[Series], force_re_dl: bool,
                    keep_img: bool,
                    full_logs: bool = False) -> Iterator[Series]:
    """
    Download all chapters from a list of series
    :param list_downloaders: dict[str, Downloader] - all downloaders to use
    :param series: list[Series] - list of series to download
    :param force_re_dl: bool - if True, download again the scan
    :param keep_img: bool - if True, keep all images after download
    :param full_logs: bool - if True, display all logs
    :return: Iterator[Series] - iterator of downloaded series
    """
    for s in series:
        platform = s.platform
        downloader = list_downloaders[platform]
        yield downloader.download_series(s, force_re_dl, keep_img, full_logs)


def pdf_exists(chapter_path: str, pdf_file_name: str) -> Optional[str]:
    """
    Check if a pdf file exists
    :param chapter_path: str - path of the chapter
    :param pdf_file_name: str - name of the pdf file
    :return: str - path of the pdf file if exists, None otherwise
    """
    if os.path.exists(os.path.join(chapter_path, "{}.pdf".format(pdf_file_name))):
        return os.path.join(chapter_path, "{}.pdf".format(pdf_file_name))
    return None


def create_pdf_from_chapter(list_downloaders: dict[str, Downloader], chapter: Chapter, force_re_dl: bool,
                            loggers: list[Logger], full_logs: bool) -> None:
    """
    Create a pdf file from a chapter
    :param list_downloaders: dict[str, Downloader] - all downloaders to use
    :param chapter: Chapter - chapter to convert
    :param force_re_dl: bool - if True, re-create the pdf file
    :param loggers: list[Logger] - list of loggers
    :param full_logs: bool - if True, display all logs
    :return: None
    """
    series_path = os.path.join(list_downloaders[chapter.platform].base_dir, chapter.series_name)
    chapter_path = os.path.join(series_path, chapter.get_name())

    if full_logs:
        log(loggers, "[Info][{}][Chapter] '{}': Creating pdf".format(chapter.platform, chapter.get_full_name()))

    # Personal Downloader is a special use case
    if list_downloaders[chapter.platform].platform == PersonalDownloader.platform:
        series_path = chapter.get_pdf_path().rsplit(os.sep, 2)[0]
        chapter_path = os.path.join(series_path, chapter.get_name())
        if pdf_exists(chapter_path, chapter.get_name()) and not force_re_dl:
            return
        convert_to_pdf(chapter_path, chapter.get_name(), loggers, True, full_logs)
    else:
        pdf_path = pdf_exists(chapter_path, chapter.get_full_name())
        if not pdf_path or force_re_dl:
            pdf_path = convert_to_pdf(chapter_path, chapter.get_name(), loggers, False, full_logs)
        chapter.set_pdf_path(pdf_path)

    if full_logs:
        log(loggers, "[Info][{}][Chapter] '{}': pdf completed".format(chapter.platform, chapter.get_full_name()))


def chapter_builder(list_downloaders: dict[str, Downloader], chapter: Chapter, make_pdf: bool, force_re_dl: bool,
                    loggers: list[Logger], full_logs: bool) -> None:
    """
    Build a chapter as a pdf file or other format if needed
    :param list_downloaders: dict[str, Downloader] - all downloaders to use
    :param chapter: Chapter - chapter to build
    :param make_pdf: bool - if True, create a pdf file
    :param force_re_dl: bool - if True, make again the action the selected action
    :param loggers: list[Logger] - list of loggers
    :param full_logs: bool - if True, display all logs
    :return: None
    """
    if make_pdf:
        create_pdf_from_chapter(list_downloaders, chapter, force_re_dl, loggers, full_logs)


def download(list_downloaders: dict[str, Downloader], series: list[Series], chapters: list[dict[str, str]],
             loggers: list[Logger], make_pdf: bool, force_re_dl: bool, keep_img: bool, full_logs: bool = False,
             time_to_sleep: int = 0) -> None:
    """
    Download all chapters from a list of series and all chapters from a list of chapters
    :param list_downloaders: dict[str, Downloader] - all downloaders to use
    :param series: list[Series] - list of series to download
    :param chapters: list[dict[str, str]] - list of dictionary with platform and link of chapters to download
    :param loggers: list[Logger] - list of loggers
    :param make_pdf: bool - if True, create a pdf for each chapter
    :param force_re_dl: bool - if True, download again the scan
    :param keep_img: bool - if True, keep all images after download
    :param full_logs: bool - if True, display all logs
    :param time_to_sleep: int - time in seconds to sleep between each download
    :return: tuple[Iterator[Series], Iterator[Chapter]] - iterator of downloaded series and chapters
    """
    for s in download_series(list_downloaders, series, force_re_dl, keep_img, full_logs):
        log(loggers, "[Info][{}][Chapter] '{}': creating pdf...".format(s.platform, s.name))
        for c in s.chapters:
            chapter_builder(list_downloaders, c, make_pdf, force_re_dl, loggers, full_logs)
        log(loggers, "[Info][{}][Chapter] '{}': all pdf created".format(s.platform, s.name))
        time.sleep(time_to_sleep)

    for c in download_chapters(list_downloaders, chapters, force_re_dl, keep_img, full_logs):
        # full_logs = True because we want to see the logs of the chapters
        chapter_builder(list_downloaders, c, make_pdf, force_re_dl, loggers, True)
        time.sleep(time_to_sleep)
