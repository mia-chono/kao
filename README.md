# KAO
## Console Help
```bash
usage: __main__.py [-h] [-l LINKS [LINKS ...]] [-k] [-f] [-e EXT_FILE] [-m [MOVE_FILES]] [-r [READ_FILE]] [-s]

Downloader of manwha or manga scans

options:
  -h, --help            show this help message and exit
  -l LINKS [LINKS ...], --links LINKS [LINKS ...]
                        Give chapters or series links (example: py __main__.py -l link1 link2) (example2: py __main__.py -l link1 link2 -r file -m)
  -k, --keep-img        If you want keep all images after download (example: py __main__.py -kl link) (example2: py __main__.py -kl link -r file -m)
  -f, --force           Download again the scan (example: py __main__.py -fl link) (example2: py __main__.py -fkl link -r file -f)
  -e EXT_FILE, --extension EXT_FILE
                        define witch file do you want create after download: pdf, zip, cbz (example: py __main__.py -fkl link -e pdf)
  -m [MOVE_FILES], --move-files [MOVE_FILES]
                        Move all specific files to the folder with the same extension name, dont forget to use -e (folder will be created if not exists at the root of the downloads folder), put ALWAYS at the end of command to move  
                        all pdf files (example: py __main__.py -fkl link -e pdf -m) (example2: py __main__.py -fkl link -e pdf -m ./myFolder)
  -r [READ_FILE], --Read-file [READ_FILE]
                        Read given file to get urls, default is './list url.txt' but you can specify another (example: py __main__.py -fkr file) (example2: py __main__.py -fkl link -r file -m)
  -s, --support         Said supported websites (example: py __main__.py -s)

```

## Supported Sites
> last update 2022.11.01
* Manga18.club
* Manhuascan
* ReaperScans
* Webtoon
* Mangas-Origines
* Mangas-Origines-X
* Manga-scantrad

> *information*: you can download again a same scan with force parameter
## Group all PDF, ZIP, CBZ in one directory
* update 2022.08.07  
When you use the property --move-pdf with --extension, all files with your extension will be moved to a folder named "your_extension".    
the "extension" folder will be created if not exists at the root of the downloads folder if you don't give a path.  
   
if you give a specific path to move all files with your extension (including sub-folders), the "extension" folder will be created if not exists at the path given earlier.

### Example 1 - no given path
Example for `py __main__.py -m "/path/to" -e pdf`:
```
/path/to/manga/chap-01
 |_ chap-01.pdf
/path/to/manga/chap-02
 |_ chap-02.pdf
/path/to/manga2/chap-01
 |_ chap-01.pdf
```
> pdf files will be moved to the folder `pdf` at the root of the downloads folder.

Result of `py __main__.py -m "/path/to" -e pdf`:
```
/downloads/pdf/manga
 |_ chap-01.pdf
 |_ chap-02.pdf
/downloads/pdf/manga2
 |_ chap-01.pdf
```
### Example 2 - given path

Example for `py __main__.py -m "/path/to/manga -e pdf"`:
```
/path/to/manga/chap-01
 |_ chap-01.pdf
/path/to/manga/chap-02
 |_ chap-02.pdf
```
> pdf files will be moved to the folder `pdf` at the path given earlier.

Result of `py __main__.py -m "/path/to/manga -e pdf"`:
```
/path/to/manga
 |_ /chap-01
 |_ /chap-02
 |_ /pdf
     |_ chap-01.pdf
     |_ chap-02.pdf
```
## Personal folders
* update 2022.08.07  
Fix image conversion to pdf. Now we ensure image format.
* update 2022.04.12  
We now have the possibility to convert downloaded pictures to pdf!

### Example 1: Folder with image
example:
```
/path/to/manga/chap-01
 |_ 01.png
 |_ 02.png
 |_ 03.jpg
```

execute the next line `py __main__.py -l /path/to/manga/chap-01 -e pdf`, it will create inside the same folder a new pdf file with the parent folder name -> `chap-01.pdf`

### Example 2: Folder with subfolders 
We can also give a path to a folder containing several folders:
example:
```
/path/to/manga/
  |_ chap-01/
     |_ 01.png
     |_ 02.png
     |_ 03.jpg
  |_ chap-02/
     |_ 01.jpg
     |_ 02.jpg
     |_ 03.jpg
  |_ chap-03/
     |_ 01.jpg
     |_ 02.jpg
     |_ 03.jpg
```

The script will create a pdf inside each sub-folders
  
### Errors messages
After the next log => `[Info][PDF] creating`    
If you have the following message :   
> Image contains an alpha channel which will be stored as a separate soft mask (/SMask) image in PDF.

Retry with the following command:  
  `py __main__.py -kl /path/to/manga/chap-01 -e pdf --force`

But if the problem persists...  
One of your images has a special property... if you still want convert to PDF, you have to convert your picture to remove the mask.
(example jpg to jpg... yes 😂)    
[image converter online](https://convertio.co/image-converter/)
