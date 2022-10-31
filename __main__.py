import os

import validators

from kao import ConsoleLogger
from kao import FileLogger
from kao import kao_utils
from kao import Downloader
from kao import Manga18Downloader
from kao import ManhuascanDownloader
from kao import PersonalDownloader
from kao import ReaperScansDownloader
from kao import WebtoonDownloader
from kao import MangaOriginesDownloader
from kao import MangaOriginesXDownloader

if __name__ != "__main__":
    print("not executed by main")
    exit(0)

interval_between_download = 0  # seconds
base_dir = os.path.join(".", "downloads")
loggers = [
    ConsoleLogger(),
    FileLogger("kao", "log")
]

list_downloaders: dict[str, Downloader] = {
    PersonalDownloader.platform: PersonalDownloader(base_dir, loggers),
    WebtoonDownloader.platform: WebtoonDownloader(base_dir, loggers),
    Manga18Downloader.platform: Manga18Downloader(base_dir, loggers),
    ManhuascanDownloader.platform: ManhuascanDownloader(base_dir, loggers),
    ReaperScansDownloader.platform: ReaperScansDownloader(base_dir, loggers),
    MangaOriginesDownloader.platform: MangaOriginesDownloader(base_dir, loggers),
    MangaOriginesXDownloader.platform: MangaOriginesXDownloader(base_dir, loggers),
}

args = kao_utils.create_parser().parse_args()

links = []
series = []
chapters_dict = []

if args.support:
    print("Supported websites:\n\t{}".format(", ".join(str(platform) for platform in list_downloaders.values())))
    exit(0)

if args.links:
    links.extend(args.links)
    for index, tmp_link in enumerate(links):
        if tmp_link[-1] == '"':
            args.links[index] = tmp_link[:-1]

if args.read_file is not False:
    file_with_links = os.path.abspath(
        args.read_file if args.read_file is not None else "list url.txt")

    with open(file_with_links) as f:
        links.extend(line.rstrip() for line in f)

tmp_series, tmp_chapters = kao_utils.get_series_and_chapters_from_links(list_downloaders, links, loggers)
series.extend(kao_utils.get_series_from_dict(list_downloaders, tmp_series))
chapters_dict.extend(tmp_chapters)

kao_utils.download(list_downloaders, series, chapters_dict, loggers, args.make_pdf, args.force_re_dl, args.keep_img,
                   args.logs, interval_between_download)

if args.move_pdf is not False:
    if args.move_pdf is not None and validators.url(args.move_pdf):
        base_path = os.path.abspath(base_dir)
    else:
        base_path = os.path.abspath(args.move_pdf if args.move_pdf is not None else base_dir)
    destination_dir = os.path.join(base_path, "pdf")

    kao_utils.move_pdf_files_from_folder(base_path, destination_dir, loggers)
