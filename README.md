# KAO
## Console Help
```bash
usage: __main__.py [-h] [-l LINKS [LINKS ...]] [-k | --keep-img | --no-keep-img] [-f | --force | --no-force] [-m [MOVE_PDF]] [-r [READ_FILE]] [-s | --support | --no-support]

Downloader of manwha or manga scans

options:
  -h, --help            show this help message and exit
  -l LINKS [LINKS ...], --links LINKS [LINKS ...]
                        Give chapters or series links (example2: py __main__.py -l link1 link2) (example2: py __main__.py -l link1 link2 -r file -m)
  -k, --keep-img, --no-keep-img
                        If you want keep all images after download (example: py __main__.py -fkl link) (example2: py __main__.py -l link -r file -m) (default: False)
  -f, --force, --no-force
                        Download again the scan (example: py __main__.py -fkl link) (example2: py __main__.py -l link -r file -m) (default: False)
  -m [MOVE_PDF], --move-pdf [MOVE_PDF]
                        Move all pdf files to pdf folder (folder will be created if not exists at the root of the downloads folder), put ALWAYS at the end of command to move all pdf files
  -r [READ_FILE], --Read-file [READ_FILE]
                        Read given file to get urls, default is './list url.txt' but you can specify another (example: py __main__.py -fkr file) (example2: py __main__.py -l link -r file -m)
  -s, --support, --no-support
                        Said supported websites (default: False)

```

## Supported Sites
> last update 2022.02.16
* Manga18.club
* Manhuascan
* ReaperScans
* Webtoon

> *information*: you can download again a same scan with force parameter
## Group all PDF in one directory
* update 2022.08.07  
When you use the property --move-pdf, all pdf files will be moved to a folder named pdf.    
the pdf folder will be created if not exists at the root of the downloads folder if you don't give a path.  
   
if you give a specific path to move all pdf (including sub-folders), the pdf folder will be created if not exists at the path given earlier.

### Example 1 - no given path
Example for `py __main__.py -m "/path/to"`:
```
/path/to/manga/chap-01
 |_ chap-01.pdf
/path/to/manga/chap-02
 |_ chap-02.pdf
/path/to/manga2/chap-01
 |_ chap-01.pdf
```
> pdf files will be moved to the folder `pdf` at the root of the downloads folder.

Result of `py __main__.py -m "/path/to"`:
```
/downloads/pdf/manga
 |_ chap-01.pdf
 |_ chap-02.pdf
/downloads/pdf/manga2
 |_ chap-01.pdf
```
### Example 2 - given path

Example for `py __main__.py -m "/path/to/manga"`:
```
/path/to/manga/chap-01
 |_ chap-01.pdf
/path/to/manga/chap-02
 |_ chap-02.pdf
```
> pdf files will be moved to the folder `pdf` at the path given earlier.

Result of `py __main__.py -m "/path/to/manga"`:
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

execute the next line `py __main__.py -l /path/to/manga/chap-01`, it will create inside the same folder a new pdf file with the parent folder name -> `chap-01.pdf`

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
  `py __main__.py -kl /path/to/manga/chap-01`

But if the problem persists...  
One of your images has a special property... if you still want convert to PDF, you have to convert your picture to remove the mask.
(example jpg to jpg... yes 😂)    
[image converter online](https://convertio.co/image-converter/)
