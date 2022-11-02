import os
import argparse
import time
from pathlib import Path
from typing import Optional, Iterator
import shutil
from zipfile import ZipFile

import img2pdf

from .downloaders import Downloader
from .downloaders import PersonalDownloader
from .downloaders import downloader_utils
from .downloaders import Series
from .downloaders import Chapter
from .loggers import Logger


def log(loggers: list[Logger], message: str) -> None:
    """
    Call all loggers to log a message
    :param loggers: list[Logger] - list of loggers
    :param message: str - message to log
    :return: None
    """
    for logger in loggers:
        logger.log(message)


def move_pdf_files_from_folder(folder_path: str, destination_path: str, loggers: list[Logger]) -> None:
    """
    Move all pdf files from a folder to another
    :param folder_path: str - path of the source folder
    :param destination_path: str - path of the destination folder
    :param loggers: list[Logger] - list of loggers
    :return: None
    """
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


def create_parser() -> argparse.ArgumentParser:
    """
    All arguments for the program
    :return: argparse.ArgumentParser - parser with all arguments
    """
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
    parser.add_argument("-e",
                        "--extension",
                        type=str,
                        dest="ext_file",
                        help="define witch file do you want after download: pdf, zip, cbz"
                             " (example: py __main__.py -fkl link -e pdf) ",
                        default="")
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


def download(list_downloaders: dict[str, Downloader], series: list[Series], chapters: list[dict[str, str]],
             loggers: list[Logger], ext_file: str, force_re_dl: bool, keep_img: bool, full_logs: bool = False,
             time_to_sleep: int = 0) -> None:
    """
    Download all chapters from a list of series and all chapters from a list of chapters
    :param list_downloaders: dict[str, Downloader] - all downloaders to use
    :param series: list[Series] - list of series to download
    :param chapters: list[dict[str, str]] - list of dictionary with platform and link of chapters to download
    :param loggers: list[Logger] - list of loggers
    :param ext_file: str - file extension to create
    :param force_re_dl: bool - if True, download again the scan
    :param keep_img: bool - if True, keep all images after download
    :param full_logs: bool - if True, display all logs
    :param time_to_sleep: int - time in seconds to sleep between each download
    :return: tuple[Iterator[Series], Iterator[Chapter]] - iterator of downloaded series and chapters
    """
    for s in download_series(list_downloaders, series, force_re_dl, keep_img, full_logs):
        log(loggers, "[Info][{}][Chapter] '{}': creating {}...".format(s.platform, s.name, ext_file))
        for c in s.chapters:
            concat_chapter_to(list_downloaders, c, ext_file, force_re_dl, loggers, full_logs)
        log(loggers, "[Info][{}][Chapter] '{}': all {} created".format(s.platform, s.name, ext_file))
        time.sleep(time_to_sleep)

    for c in download_chapters(list_downloaders, chapters, force_re_dl, keep_img, full_logs):
        # full_logs = True because we want to see the logs of the chapters
        concat_chapter_to(list_downloaders, c, ext_file, force_re_dl, loggers, True)
        time.sleep(time_to_sleep)


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


def concat_chapter_to(list_downloaders: dict[str, Downloader], chapter: Chapter, ext_file: str, force_re_dl: bool,
                      loggers: list[Logger], full_logs: bool) -> None:
    """
    Concatenate all images of a chapter to create a specific file
    :param list_downloaders: dict[str, Downloader] - all downloaders to use
    :param chapter: Chapter - chapter to build
    :param ext_file: str - file extension to create (works only for PDF, ZIP, CBZ)
    :param force_re_dl: bool - if True, make again the action the selected action
    :param loggers: list[Logger] - list of loggers
    :param full_logs: bool - if True, display all logs
    :return: None
    """
    allowed_ext = ["pdf", "zip", "cbz"]

    if ext_file == "":
        return

    if not ext_file.lower() in allowed_ext:
        log(loggers,
            "[Error][{}][Chapter] '{}': {} is not a valid format".format(chapter.platform, chapter.get_full_name(),
                                                                         ext_file))
        return

    series_path = get_series_path(list_downloaders, chapter)
    chapter_path = get_chapter_path(series_path, chapter)
    chapter.set_path(chapter_path)

    file = os.path.join(chapter_path, "{}.{}".format(chapter.get_name(), ext_file))
    file_already_created = os.path.exists(file)

    if force_re_dl and file_already_created:
        os.remove(file)
    elif file_already_created:
        log(loggers,
            "[Info][{}][Chapter] '{}': {} already created".format(chapter.platform, chapter.get_full_name(), ext_file))
        return

    log(loggers,
        "[Info][{}][Chapter] '{}': Creating {}".format(chapter.platform, chapter.get_full_name(), ext_file))

    images = get_img_from_folder(chapter_path, loggers, full_logs)
    if not images:
        log(loggers, "[Error][{}][Chapter] '{}': No images found".format(chapter.platform, chapter.get_full_name()))
        return

    if full_logs:
        log(loggers, '[Info][{}] creating'.format(ext_file.capitalize()))

    for ext in allowed_ext:
        if ext == ext_file.lower():
            # call the function to create the file
            globals()['create_{}'.format(ext)](file, images)
            break

    if full_logs:
        log(loggers, '[Info][{}] created'.format(ext_file.capitalize()))

    log(loggers,
        "[Info][{}][Chapter] '{}': {} completed".format(chapter.platform, chapter.get_full_name(), ext_file))


def get_series_path(list_downloaders: dict[str, Downloader], chapter: Chapter, ) -> str:
    """
    Get the path of the series of a chapter
    :param list_downloaders: dict[str, Downloader] - all downloaders to use
    :param chapter: Chapter - chapter to get the series path
    :return: str - path of the series
    """
    series_path = os.path.join(list_downloaders[chapter.platform].base_dir, chapter.series_name)
    if list_downloaders[chapter.platform].platform == PersonalDownloader.platform:
        series_path = chapter.get_path().rsplit(os.sep, 1)[0]
    return series_path


def get_chapter_path(series_path: str, chapter: Chapter) -> str:
    """
    Get the path of a chapter
    :param series_path: str - path of the series
    :param chapter: Chapter - chapter to get the name
    :return: str - path of the chapter
    """
    return os.path.join(series_path, chapter.get_name())


def get_img_from_folder(path: str, loggers: list[Logger],
                        full_logs: bool = False) -> list[str]:
    """
    Get all images from a folder
    :param path: str - path of the folder
    :param loggers: list[Logger] - list of loggers
    :param full_logs: bool - if True, display all logs
    :return: list[str] - list of images
    """
    images_list = []
    try:

        for element in os.listdir(path):
            if os.path.join(path, element) is not None:
                images_list.append(os.path.join(path, element))
        images_list.sort()

        img_to_remove = []

        images_list = downloader_utils.keep_only_images_paths(images_list)

        for i in range(0, len(images_list)):
            img_is_too_large_or_small = downloader_utils.img_is_too_small(open(images_list[i], 'rb').read()) \
                                        or downloader_utils.img_is_too_large(open(images_list[i], 'rb').read())

            if full_logs:
                log(loggers, '[Info][Image] {}'.format(images_list[i]))

            if img_is_too_large_or_small:
                img_to_remove.append(i)
                if full_logs:
                    log(loggers,
                        '[Info][Image][Skip] Img too large or small, skipped: {}'.format(images_list[i]))
                continue
            if downloader_utils.test_is_image(images_list[i]) is None:
                log(loggers, '[Warning][Image] Corrupted: {}'.format(images_list[i]))
                images_list[i] = os.path.join(Path(__file__).parent, 'corrupted_picture.jpg')

        # Remove unwanted images
        [images_list.pop(x) for x in img_to_remove]
    except Exception as e:
        images_list = []
        log(loggers, '[Error][Images]  {error}'.format(error=e))
    finally:
        return images_list


def create_pdf(path: str, images_list: list[str]) -> None:
    """
    Create a PDF file from a list of images
    :param path: str - path of the PDF file
    :param images_list: list[str] - list of images
    :return: None
    """
    with open(path, 'wb') as f:
        f.write(img2pdf.convert(images_list))


def create_zip(path: str, images_list: list[str]) -> None:
    """
    Create a ZIP file from a list of images
    :param path: str - path of the ZIP file
    :param images_list: list[str] - list of images
    :return: None
    """
    with ZipFile(path, 'w') as zipObj:
        for img in images_list:
            zipObj.write(img, img.split(os.sep)[-1])


def create_cbz(path: str, images_list: list[str]) -> None:
    """
    Create a CBZ file from a list of images
    :param path: str - path of the CBZ file
    :param images_list: list[str] - list of images
    :return: None
    """
    create_zip(path, images_list)
