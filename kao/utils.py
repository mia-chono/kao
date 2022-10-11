import imghdr
import mimetypes
import os
import shutil
from pathlib import Path
from typing import Optional

import img2pdf
from PIL import ImageFile, Image

from .loggers import Logger

ImageFile.LOAD_TRUNCATED_IMAGES = True
user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'

invalid_file_name_chars = [
    chr(0), chr(1), chr(2), chr(3), chr(4), chr(5), chr(6), chr(7), chr(8), chr(9), chr(10), chr(11),
    chr(12), chr(13), chr(14), chr(15), chr(16), chr(17), chr(18), chr(19), chr(20), chr(21), chr(22), chr(23), chr(24),
    chr(25), chr(26), chr(27), chr(28), chr(29), chr(30), chr(31), chr(34), chr(60), chr(62), chr(124), ':', '*', '?',
    '\\', '/', '"'
]
invalid_directory_name_chars = [
    '|', '\0', chr(1), chr(2), chr(3), chr(4), chr(5), chr(6), chr(7), chr(8), chr(9), chr(10), chr(11),
    chr(12), chr(13), chr(14), chr(15), chr(16), chr(17), chr(18), chr(19), chr(20), chr(21), chr(22), chr(23), chr(24),
    chr(25), chr(26), chr(27), chr(28), chr(29), chr(30), chr(31), ':', '*', '?', '\\', '/', '"'
]


def remove_dots_end_of_file_name(file_name: str) -> str:
    tmp_name = file_name
    while tmp_name.endswith('.'):
        tmp_name = tmp_name[:-1]

    return tmp_name


def log(loggers: list[Logger], message: str) -> None:
    for logger in loggers:
        logger.log(message)


def replace_char_in_string(string: str, list_of_char: list[str], string_replace: str) -> str:
    temp_string_list = list(string)
    for i in range(0, len(string)):
        if string[i] in list_of_char:
            temp_string_list[i] = string_replace

    return ''.join(temp_string_list)


def convert_to_pdf(episode_dir: str, file_name: str, loggers: list[Logger], check_img: bool = False,
                   full_logs: bool = False) -> Optional[str]:
    try:
        if full_logs:
            log(loggers, '[Info][PDF] creating')

        images_list = []
        for element in os.listdir(episode_dir):
            if os.path.join(episode_dir, element) is not None:
                images_list.append(os.path.join(episode_dir, element))
        images_list.sort()

        info_name = ''
        img_to_remove = []

        # When is personal folder, we need to ensure that all images are images
        if check_img is True:
            images_list = keep_only_images_paths(images_list, full_logs)

        for i in range(0, len(images_list)):
            img_is_too_large_or_small = img_is_too_small(open(images_list[i], 'rb').read()) \
                                        or img_is_too_large(open(images_list[i], 'rb').read())

            if full_logs:
                log(loggers, '[Info][PDF][Image] {}'.format(images_list[i]))

            if check_img is True and img_is_too_large_or_small:
                img_to_remove.append(i)
                if full_logs:
                    log(loggers, '[Info][PDF][Skip] Img too large or small, skipped: {}'.format(images_list[i]))
                continue
            if imghdr.what(images_list[i]) is None:
                if full_logs:
                    log(loggers, '[Info][PDF] Img corrupted')
                info_name = '[has_corrupted_images]'
                images_list[i] = os.path.join(Path(__file__).parent, 'corrupted_picture.jpg')

        # Remove unwanted images
        [images_list.pop(x) for x in img_to_remove]

        pdf_path = os.path.join(episode_dir, f'{info_name}{file_name}.pdf')

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


def folder_contains_files(list_of_path: list[str]) -> bool:
    for file_name in list_of_path:
        if os.path.isfile(file_name):
            return True
    return False


def get_img_size(img_content: bytes) -> tuple[int, int]:
    img_parser = ImageFile.Parser()
    img_parser.feed(img_content)
    return img_parser.image.size


def img_is_too_small(img_content: bytes, min_height: int = 10, min_width: int = 10) -> bool:
    width, height = get_img_size(img_content)
    return height < min_height or width < min_width


def img_is_too_large(img_content: bytes, max_height: int = 144000, max_width: int = 144000) -> bool:
    width, height = get_img_size(img_content)
    return height > max_height or width > max_width


def img_has_alpha_channel(img_content: bytes) -> bool:
    img_parser = ImageFile.Parser()
    img_parser.feed(img_content)
    return img_parser.image.mode == 'RGBA'


def convert_img_to_jpeg(img_path: str, alternative_file_name: Optional[str] = None) -> None:
    if 'image/jpeg' == mimetypes.MimeTypes().guess_type(img_path)[0] and not img_has_alpha_channel(
            open(img_path, 'rb').read()):
        return

    temp_path = Path(img_path)
    file_path = os.path.join(temp_path.parent,
                             alternative_file_name if alternative_file_name is not None else temp_path.name)
    force_image_rgb(img_path=file_path)


def force_image_rgb(img_path: str, img_content: Optional[str] = None) -> None:
    img = Image.open(img_path if img_content is None else img_content)
    rgb_img = img.convert('RGB')
    rgb_img.save(img_path)


def keep_only_images_paths(images_list: [str], alternative_file_name: Optional[str] = None) -> [str]:
    images = list(filter(lambda elem: imghdr.what(elem) is not None, images_list))
    # When is personal folder, we need to ensure that all images are images
    for img in images_list:
        convert_img_to_jpeg(img)

    return images


def create_directory(directory_path: str) -> None:
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


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
                create_directory(os.path.join(destination_path, folder_name))
                shutil.move(os.path.join(root, file), os.path.join(destination_path, folder_name, file))

    log(loggers, '[Info] all pdf files moved')


def find_images_in_tree(folder_path: str) -> list[str]:
    images_list = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if imghdr.what(file) is not None:
                images_list.append(os.path.join(root, file))

    return images_list


def find_all_sub_folders(folder_path: str) -> list[str]:
    sub_folders = []
    for root, dirs, files in os.walk(folder_path):
        if 'pdf' in root:
            # print('[Info] Skipped folder: {}'.format(root))
            continue
        for file in files:
            file_path = os.path.join(root, file)
            if imghdr.what(file_path) is not None or 'image/jpeg' == mimetypes.MimeTypes().guess_type(file_path)[0]:
                dir_path = str(Path(file_path).parent.absolute())
                if dir_path not in sub_folders:
                    sub_folders.append(dir_path)

    return sub_folders
