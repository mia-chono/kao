import os
import argparse
import sys
from typing import Iterator

import validators

from kao import utils
from kao import Chapter
from kao import Downloader
from kao import Manga18Downloader
from kao import ManhuascanDownloader
from kao import PersonalDownloader
from kao import ReaperScansDownloader
from kao import WebtoonDownloader
from kao import ConsoleLogger
from kao import FileLogger

if __name__ != "__main__":
    print("not executed by main")
    exit(0)

full_logs = False
base_dir = os.path.join(".", "downloads")
loggers = [
    ConsoleLogger(),
    FileLogger("kao", "log")
]
list_downloaders: [Downloader] = [
    PersonalDownloader(base_dir, loggers),
    WebtoonDownloader(base_dir, loggers),
    Manga18Downloader(base_dir, loggers),
    ManhuascanDownloader(base_dir, loggers),
    ReaperScansDownloader(base_dir, loggers)
]


def download_series(series_to_download: list[dict[str, str]], force_re_dl: bool, keep_img: bool,
                    full_logs: bool = False) -> Iterator[Chapter]:
    for obj in series_to_download:
        for downloader in list_downloaders:
            if downloader.platform == obj.get("platform"):
                series = downloader.download_series(obj.get("link"), force_re_dl, keep_img, full_logs)
                for chapter in series.get_chapters():
                    yield chapter


def download_chapters(chapter_to_download: list[dict[str, str]], force_re_dl: bool, keep_img: bool,
                      full_logs: bool = False) -> Iterator[Chapter]:
    for downloader in list_downloaders:
        for obj in chapter_to_download:
            if downloader.platform == obj.get("platform"):
                yield downloader.download_chapter(obj.get("link"), force_re_dl, keep_img, full_logs)


def get_series_and_chapters_from_links(links: list[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    correct_links = []
    series_to_download = []
    chapters_to_download = []

    for link in links:
        for downloader in list_downloaders:
            if downloader.is_a_series_link(link):
                series_to_download.append({"platform": downloader.platform, "link": link})
                correct_links.append(link)
                break
            elif downloader.is_a_chapter_link(link):
                chapters_to_download.append({"platform": downloader.platform, "link": link})
                correct_links.append(link)
                break

    links_not_available = set(correct_links) ^ set(links)
    if links_not_available:
        links_not_available = list(map(lambda x: "<{}>".format(x), links_not_available))
        for logger in loggers:
            logger.log("Invalid link(s), please give links from {}\n{}".format(
                ", ".join(x.platform for x in list_downloaders),
                "\n".join(link_not_available for link_not_available in links_not_available)
            ))

    return series_to_download, chapters_to_download


def download_all_chapters(series_to_download: list[dict[str, str]], chapters_to_download: list[dict[str, str]],
                          force_re_dl: bool, keep_img: bool, full_logs: bool = False) -> list[Chapter]:
    chapters = []
    for chapter in download_series(series_to_download, force_re_dl, keep_img, full_logs):
        chapters.append(chapter)

    for chapter in download_chapters(chapters_to_download, force_re_dl, keep_img, full_logs):
        chapters.append(chapter)

    return chapters


def download_links(links_to_dl: list[str], force_re_dl: bool, keep_img: bool, full_logs: bool = False) -> None:
    series_links, chapters_links = get_series_and_chapters_from_links(links_to_dl)
    download_all_chapters(series_links, chapters_links, force_re_dl, keep_img, full_logs)
    for logger in loggers:
        logger.log("[Success] downloads completed")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Downloader of manwha or manga scans')

    # hidden argument
    parser.add_argument("--log",
                        dest="log",
                        help=argparse.SUPPRESS,
                        action="store_true",
                        default=False)

    parser.add_argument("-l",
                        "--links",
                        nargs="+",
                        dest="links",
                        help="Give chapters or series links (example2: py __main__.py -l link1 link2) "
                             "(example2: py __main__.py -l link1 link2 -r file -m)")
    parser.add_argument("-k",
                        "--keep-img",
                        dest="keep_img",
                        help="If you want keep all images after download (example: py __main__.py -fkl link) "
                             "(example2: py __main__.py -l link -r file -m)",
                        action=argparse.BooleanOptionalAction,
                        default=False)
    parser.add_argument("-f",
                        "--force",
                        dest="force_re_dl",
                        help="Download again the scan (example: py __main__.py -fkl link) "
                             "(example2: py __main__.py -l link -r file -m)",
                        action=argparse.BooleanOptionalAction,
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
                        action=argparse.BooleanOptionalAction,
                        default=False)

    args = parser.parse_args()

    if args.support:
        print("Supported websites:\n\t{}".format(", ".join([downloader.platform for downloader in list_downloaders])))

    # TODO add in the folder of each manga a file "downloaded_chapters.txt" with the name of the downloaded chapters
    #  or the link...
    if args.links:
        links_cli = args.links
        for index, tmp_link in enumerate(links_cli):
            if tmp_link[-1] == '"':
                links_cli[index] = tmp_link[:-1]
        download_links(links_cli, args.force_re_dl, args.keep_img, args.log)

    if args.read_file is not False:
        file_with_links = os.path.abspath(
            args.read_file if args.read_file is not None else "list url.txt")

        with open(file_with_links) as f:
            lines = [line.rstrip() for line in f]

        download_links(lines, args.force_re_dl, args.keep_img, args.log)

    if args.move_pdf is not False:
        if args.move_pdf is not None and validators.url(args.move_pdf):
            base_path = os.path.abspath(base_dir)
        else:
            base_path = os.path.abspath(args.move_pdf if args.move_pdf is not None else base_dir)
        destination_dir = os.path.join(base_path, "pdf")

        utils.move_pdf_files_from_folder(base_path, destination_dir, loggers)
