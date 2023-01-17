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
    """
    Remove dots at the end of the file name
    :param file_name: str - The file name to remove dots at the end
    :return: str - cleaned file name
    """
    tmp_name = file_name
    while tmp_name.endswith('.'):
        tmp_name = tmp_name[:-1]

    return tmp_name


def replace_char_in_string(string: str, list_of_char: list[str], string_replace: str) -> str:
    """
    Replace all char in a string by a string
    :param string: str - The string to replace char
    :param list_of_char: list[str] - The list of char to replace
    :param string_replace: str - The string to replace char
    :return: str - cleaned string
    """
    temp_string_list = list(string)
    for i in range(0, len(string)):
        if string[i] in list_of_char:
            temp_string_list[i] = string_replace

    return ''.join(temp_string_list)


def folder_contains_files(list_of_path: list[str]) -> bool:
    """
    Check if a folder contains files
    :param list_of_path: list[str] - The list of path to check
    :return: bool - True if the folder contains files, False otherwise
    """
    for file_name in list_of_path:
        if os.path.isfile(file_name):
            return True
    return False


def get_img_size(img_content: bytes) -> tuple[int, int]:
    """
    Get the size of an image
    :param img_content: bytes - The image content
    :return: tuple[int, int] - The size of the image
    """
    img_parser = ImageFile.Parser()
    img_parser.feed(img_content)
    return img_parser.image.size


def img_is_too_small(img_content: bytes, min_height: int = 10, min_width: int = 10) -> bool:
    """
    Check if an image is too small
    :param img_content: bytes - The image content
    :param min_height: int - The minimum height of the image
    :param min_width: int - The minimum width of the image
    :return: bool - True if the image is too small, False otherwise
    """
    width, height = get_img_size(img_content)
    return height < min_height or width < min_width


def img_is_too_large(img_content: bytes, max_height: int = 144000, max_width: int = 144000) -> bool:
    """
    Check if an image is too large
    :param img_content: bytes - The image content
    :param max_height: int - The maximum height of the image
    :param max_width: int - The maximum width of the image
    :return: bool - True if the image is too large, False otherwise
    """
    width, height = get_img_size(img_content)
    return height > max_height or width > max_width


def img_has_alpha_channel(img_content: bytes) -> bool:
    """
    Check if an image has an alpha channel
    :param img_content: bytes - The image content
    :return: bool - True if the image has an alpha channel, False otherwise
    """
    img_parser = ImageFile.Parser()
    img_parser.feed(img_content)
    return img_parser.image.mode == 'RGBA'


def force_image_rgb(img_path: str, img_content: Optional[str] = None) -> None:
    """
    Force an image to be RGB (remove alpha channel)
    :param img_path: str - The path to the image
    :param img_content: Optional[str] - The image content
    :return: None
    """
    if img_content is not None and get_img_extension(img_content) == 'png':
        return
    if get_img_extension(open(img_path, 'rb').read()) == 'png':
        return

    img = Image.open(img_path if img_content is None else img_content)
    rgb_img = img.convert('RGB')
    rgb_img.save(img_path)


def get_img_extension(img_content) -> str:
    """
    Get the extension of an image
    :param img_content: bytes - The image content
    :return: str - The extension of the image (Capitalized)
    """
    img_parser = ImageFile.Parser()
    img_parser.feed(img_content)
    return img_parser.image.format


def keep_only_images_paths(images_list: list[str]) -> list[str]:
    """
    Keep only images paths in a list of paths
    :param images_list: list[str] - The list of paths
    :return: list[str] - The list of images paths
    """
    images = list(filter(lambda elem: not os.path.isdir(elem), images_list))
    images = list(filter(lambda elem: test_is_image(elem), images))
    # When is personal folder, we need to ensure that all images are images
    for img in images:
        force_image_rgb(img)

    return images


def create_directory(directory_path: str) -> None:
    """
    Create all directories needed until the destination directory
    :param directory_path: str - The path to the destination directory
    :return: None
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def find_images_in_tree(folder_path: str) -> list[str]:
    """
    Find all images in a folder and subfolders
    :param folder_path: str - The path to the folder
    :return: list[str] - The list of images paths
    """
    images_list = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if test_is_image(file):
                images_list.append(os.path.join(root, file))

    return images_list


def find_all_sub_folders(folder_path: str) -> list[str]:
    """
    Find all sub folders in a folder and skip folders that contains a pdf file
    :param folder_path: str - The path to the folder
    :return: list[str] - The list of sub folders paths
    """
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
    """
    Clear white characters in a string
    :param text: str - The string to clear
    :return: str - cleaned string
    """
    return text.rstrip().replace('\r', '').replace('\n', '').replace('\t', '')


def test_is_image(file_path: str) -> bool:
    """
    Test if a file is an image
    :param file_path: str - The path to the file
    :return: bool - True if the file is an image, False otherwise
    """
    return imghdr.what(file_path) is not None or 'image/jpeg' == mimetypes.MimeTypes().guess_type(file_path)[0]
