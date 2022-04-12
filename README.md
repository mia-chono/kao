# KAO
## Console Help
```bash
usage: main.py [-h] [-l LINKS [LINKS ...]] [-f | --force | --no-force] [-s | --support | --no-support]

Downloader of manwha or manga scans

options:
  -h, --help            show this help message and exit
  -l LINKS [LINKS ...], --links LINKS [LINKS ...]
                        Give chapters or series links
  -f, --force, --no-force
                        Download again the scan (default: False)
  -s, --support, --no-support
                        Said supported websites (default: False)
```

## Sites Supported
> last update 2022.02.16
  > last update 2022.02.16
* Manga18.club
* Manhuascan
* ReaperScans
* Webtoon
  * Manga18.club
  * Manhuascan
  * ReaperScans
  * Webtoon

> *information*: you can download again a same scan with force parameter

## Personal folders
  > last update 2022.04.12
  We now have the possibility to convert downloaded pictures to pdf!

### Example 1: Folder with image
  example:
  ```
  /path/to/manga/chap-01
   |_ 01.png
   |_ 02.png
   |_ 03.jpg
  ```

  execute the next line `py main.py -l /path/to/manga/chap-01`, it will create inside the same folder a new pdf file with the parent folder name -> `chap-01.pdf`

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

  The script will creates a pdf inside each sub-folders
  
### Errors messages
  After the next log => `[Info][PDF] creating`    
  if you have the following message :   
    Image contains an alpha channel which will be stored as a separate soft mask (/SMask) image in PDF.
      
  One of your images has a special property... if you still want convert to PDF, you have to convert your picture to remove the mask.
  (example jpg to jpg... yes 😂)    
  [image converter online](https://convertio.co/image-converter/)
