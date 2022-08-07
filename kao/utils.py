import imghdr
import io
import os
import img2pdf

from os import path
from pathlib import Path
from typing import Optional

from PIL import ImageFile, Image

from .loggers import Logger

user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'

invalid_file_name_chars = [
    chr(0), chr(1), chr(2), chr(3), chr(4), chr(5), chr(6), chr(7), chr(8), chr(9), chr(10), chr(11),
    chr(12), chr(13), chr(14), chr(15), chr(16), chr(17), chr(18), chr(19), chr(20), chr(21), chr(22), chr(23), chr(24),
    chr(25), chr(26), chr(27), chr(28), chr(29), chr(30), chr(31), chr(34), chr(60), chr(62), chr(124), ':', '*', '?',
    '\\', '/'
]
invalid_directory_name_chars = [
    '|', '\0', chr(1), chr(2), chr(3), chr(4), chr(5), chr(6), chr(7), chr(8), chr(9), chr(10), chr(11),
    chr(12), chr(13), chr(14), chr(15), chr(16), chr(17), chr(18), chr(19), chr(20), chr(21), chr(22), chr(23), chr(24),
    chr(25), chr(26), chr(27), chr(28), chr(29), chr(30), chr(31), ':', '*', '?', '\\', '/'
]


def replace_char_in_string(string: str, list_of_char: list[str], string_replace: str) -> str:
    temp_string_list = list(string)
    for i in range(0, len(string)):
        if string[i] in list_of_char:
            temp_string_list[i] = string_replace

    return "".join(temp_string_list)


def img_is_too_small(img_content: bytes, min_height: int = 10):
    img_parser = ImageFile.Parser()
    img_parser.feed(img_content)
    width, height = img_parser.image.size
    return height < min_height


def convert_to_pdf(episode_dir: str, file_name: str, loggers: list[Logger], check_img: bool = False) -> Optional[str]:
    try:
        for logger in loggers:
            logger.log("[Info][PDF] creating")
        images_list = [path.join(episode_dir, element) for element in os.listdir(episode_dir)]
        images_list.sort()
        info_name = ""

        img_to_remove = []

        for i in range(0, len(images_list)):
            if check_img is True and img_is_too_small(open(images_list[i], 'rb').read()):
                img_to_remove.append(i)
                for logger in loggers:
                    logger.log("[Info][PDF] Img too small, skipped: {}".format(images_list[i]))
                continue

            if "pdf" in images_list[i]:
                continue

            if imghdr.what(images_list[i]) is None:
                for logger in loggers:
                    logger.log("[Info][PDF] Img corrupted")
                info_name = "[has_corrupted_images]"
                images_list[i] = path.join("..", "corrupted_picture.jpg")

        # Remove small img
        [images_list.pop(x) for x in img_to_remove]

        # When is personal folder, we need to ensure that all images are images
        if check_img is True:
            for img in images_list:
                ensure_is_image(img)

        pdf_content = img2pdf.convert(images_list)
        pdf_path = path.join(episode_dir, f"{info_name}{file_name}.pdf")

        if path.exists(pdf_path):
            os.remove(pdf_path)

        for logger in loggers:
            logger.log(f"[Info][PDF] {pdf_path}")
        file = open(pdf_path, "wb")
        file.write(pdf_content)
        file.close()

        for logger in loggers:
            logger.log("[Info][PDF] created")
        return pdf_path
    except Exception as e:
        for logger in loggers:
            logger.log("[Error][PDF] {error}".format(error=e))
        return


def folder_contains_files(list_of_path: list[str]) -> bool:
    for file_name in list_of_path:
        if os.path.isfile(file_name):
            return True
    return False


def ensure_is_image(img_path: str, alternative_file_name: Optional[str] = None) -> None:
    file_data = Path(img_path)
    file_path = file_data.parent
    file_name = file_data.name

    img = Image.open(img_path)
    rgb_img = img.convert('RGB')
    rgb_img.save(path.join(file_path, alternative_file_name if alternative_file_name is not None else file_name))
