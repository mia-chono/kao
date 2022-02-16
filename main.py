import os
import argparse

from downloaders.Chapter import Chapter
from downloaders.Downloader import Downloader
from downloaders.Manga18Downloader import Manga18Downloader
from downloaders.ManhuascanDownloader import ManhuascanDownloader
from downloaders.ReaperScansDownloader import ReaperScansDownloader
from downloaders.WebtoonDownloader import WebtoonDownloader
from loggers.ConsoleLogger import ConsoleLogger
from loggers.FileLogger import FileLogger

if __name__ != "__main__":
    print("not executed by main")
    exit(0)

base_dir = os.path.join(".", "downloads")
loggers = [
    ConsoleLogger(),
    FileLogger("kao", "log")
]
list_downloaders: [Downloader] = [
    WebtoonDownloader(base_dir, loggers),
    Manga18Downloader(base_dir, loggers),
    ManhuascanDownloader(base_dir, loggers),
    ReaperScansDownloader(base_dir, loggers)
]


def download_series(series_to_download: list[str]) -> Chapter:
    for obj in series_to_download:
        for downloader in list_downloaders:
            if downloader.platform == obj.get("platform"):
                series = downloader.download_series(obj.get("link"))
                for chapter in series.get_chapters():
                    yield chapter


def download_chapters(chapter_to_download: list[str]) -> Chapter:
    for downloader in list_downloaders:
        for obj in chapter_to_download:
            if downloader.platform == obj.get("platform"):
                yield downloader.download_chapter(obj.get("link"))


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


def download_all_chapters(series_to_download: list[str], chapters_to_download: list[str]) -> list[str]:
    chapters = []
    for chapter in download_chapters(chapters_to_download):
        chapters.append(chapter)

    for chapter in download_series(series_to_download):
        chapters.append(chapter)

    return chapters


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Downloader of manwha or manga scans')
    parser.add_argument("-l",
                        "--links",
                        nargs="+",
                        dest="links",
                        help="Give chapters or series links")
    parser.add_argument("-s",
                        "--support",
                        dest="support",
                        help="Said supported websites",
                        action=argparse.BooleanOptionalAction,
                        default=False)

    args = parser.parse_args()

    if args.support:
        print("Supported websites:\n\t{}".format(", ".join([downloader.platform for downloader in list_downloaders])))
    if not args.links:
        exit(1)

    links = args.links

    series_links, chapters_links = get_series_and_chapters_links(links)
    download_all_chapters(series_links, chapters_links)
    for logger in loggers:
        logger.log("[Success] downloads completed")
