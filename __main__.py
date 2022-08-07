import os
import argparse

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


def download_series(series_to_download: list[str], force_re_dl: bool, keep_img: bool) -> Chapter:
    for obj in series_to_download:
        for downloader in list_downloaders:
            if downloader.platform == obj.get("platform"):
                series = downloader.download_series(obj.get("link"), force_re_dl, keep_img)
                for chapter in series.get_chapters():
                    yield chapter


def download_chapters(chapter_to_download: list[str], force_re_dl: bool, keep_img: bool) -> Chapter:
    for downloader in list_downloaders:
        for obj in chapter_to_download:
            if downloader.platform == obj.get("platform"):
                yield downloader.download_chapter(obj.get("link"), force_re_dl, keep_img)


def get_series_and_chapters_links(links: list[str]) -> tuple[list[str], list[str]]:
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
                "\n".join(link for link in links_not_available)
            ))

    return series_to_download, chapters_to_download


def download_all_chapters(series_to_download: list[str], chapters_to_download: list[str], force_re_dl: bool,
                          keep_img: bool) -> list[str]:
    chapters = []
    for chapter in download_chapters(chapters_to_download, force_re_dl, keep_img):
        chapters.append(chapter)

    for chapter in download_series(series_to_download, force_re_dl, keep_img):
        chapters.append(chapter)

    return chapters


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Downloader of manwha or manga scans')
    parser.add_argument("-l",
                        "--links",
                        nargs="+",
                        dest="links",
                        help="Give chapters or series links")
    parser.add_argument("-k",
                        "--keep-img",
                        dest="keep_img",
                        help="If you want keep all images",
                        action=argparse.BooleanOptionalAction,
                        default=False)
    parser.add_argument("-f",
                        "--force",
                        dest="force_re_dl",
                        help="Download again the scan",
                        action=argparse.BooleanOptionalAction,
                        default=False)
    parser.add_argument("-p",
                        "--pdf",
                        dest="move_pdf",
                        help="Move all pdf files to pdf folder (folder will be created if not exists at the root of the downloads folder)",
                        action=argparse.BooleanOptionalAction,
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

    if args.links:
        links = args.links
        for index, link in enumerate(links):
            if link[-1] == '"':
                links[index] = link[:-1]

        series_links, chapters_links = get_series_and_chapters_links(links)
        download_all_chapters(series_links, chapters_links, args.force_re_dl, args.keep_img)
        for logger in loggers:
            logger.log("[Success] downloads completed")

    if args.move_pdf:
        destination_dir = os.path.join(base_dir, "pdf")
        utils.create_directory(destination_dir)
        utils.move_pdf_files_from_folder(base_dir, destination_dir, loggers)
