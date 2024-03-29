from typing import Optional

from . import Chapter


class Series:
    def __init__(self, name: str, series_link: str):
        self.series_link: str = series_link
        self.name: str = name
        self.platform: str | None = None
        self.chapters: list[Chapter] = []
        self.chapters_links: list[str] = []

    def set_name(self, name: str) -> None:
        self.name = name

    def get_name(self) -> Optional[str]:
        return self.name

    def add_chapter(self, chapter: Chapter) -> None:
        self.chapters.append(chapter)

    def add_chapter_link(self, link: str) -> None:
        self.chapters_links.append(link)

    def get_all_chapter_links(self) -> list[str]:
        return self.chapters_links

    def get_chapter_link(self, index: int) -> str:
        return self.chapters_links[index]

    def get_chapters(self) -> list[Chapter]:
        return self.chapters

    def total_chapters(self) -> int:
        return len(self.chapters)

    def set_platform(self, platform: str) -> None:
        self.platform = platform

    def witch_platform(self) -> Optional[str]:
        return self.platform
