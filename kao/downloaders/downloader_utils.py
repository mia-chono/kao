import imghdr
import mimetypes
import os
from pathlib import Path
from typing import Optional

from PIL import ImageFile, Image


ImageFile.LOAD_TRUNCATED_IMAGES = True
user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'

invalid_chars = [
    chr(0), chr(1), chr(2), chr(3), chr(4), chr(5), chr(6), chr(7), chr(8), chr(9), chr(10), chr(11),
    chr(12), chr(13), chr(14), chr(15), chr(16), chr(17), chr(18), chr(19), chr(20), chr(21), chr(22), chr(23), chr(24),
    chr(25), chr(26), chr(27), chr(28), chr(29), chr(30), chr(31), chr(34), chr(60), chr(62), chr(124), chr(127), '\0',
    ':', '*', '?', '\\', '/', '"', '<', '>', '|', '«', '»', "\n", "\t"
]


def remove_dots_end_of_file_name(file_name: str) -> str:
    tmp_name = file_name
    while tmp_name.endswith('.'):
        tmp_name = tmp_name[:-1]

    return tmp_name


def replace_char_in_string(string: str, list_of_char: list[str], string_replace: str) -> str:
    temp_string_list = list(string)
    for i in range(0, len(string)):
        if string[i] in list_of_char:
            temp_string_list[i] = string_replace

    return ''.join(temp_string_list)


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


def force_image_rgb(img_path: str, img_content: Optional[str] = None) -> None:
    if img_content is not None and get_img_extension(img_content) == 'png':
        return
    if get_img_extension(open(img_path, 'rb').read()) == 'png':
        return

    img = Image.open(img_path if img_content is None else img_content)
    rgb_img = img.convert('RGB')
    rgb_img.save(img_path)


def get_img_extension(img_content) -> str:
    img_parser = ImageFile.Parser()
    img_parser.feed(img_content)
    return img_parser.image.format


def keep_only_images_paths(images_list: [str]) -> [str]:
    images = list(filter(lambda elem: test_is_image(elem), images_list))
    # When is personal folder, we need to ensure that all images are images
    for img in images_list:
        force_image_rgb(img)

    return images


def create_directory(directory_path: str) -> None:
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def find_images_in_tree(folder_path: str) -> list[str]:
    images_list = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if test_is_image(file):
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
            if test_is_image(file_path):
                dir_path = str(Path(file_path).parent.absolute())
                if dir_path not in sub_folders:
                    sub_folders.append(dir_path)

    return sub_folders


def clear_white_characters(text: str) -> str:
    return text.rstrip().replace('\r', '').replace('\n', '').replace('\t', '')


def test_is_image(file_path: str) -> bool:
    return imghdr.what(file_path) is not None or 'image/jpeg' == mimetypes.MimeTypes().guess_type(file_path)[0]