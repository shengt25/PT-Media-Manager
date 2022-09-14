# PT-media-manager

这是PT下载文件库的管理工具，通过创建和管理硬连接，避免PT下载的文件不便改名、移动或覆盖nfo内容等问题，方便配合tinyMediaManager刮削本地nfo。程序基于python3.  



# 使用方法

Clone 此项目，使用终端运行：

Step 1: `python3 ptmm.py -a`，添加媒体库分类规则。（分类名称、原路径和目标路径）

Step 2: `python3 ptmm.py -s`，将扫描新增或删除的媒体，自动同步媒体库。

Step 3: `python3 ptmm.py -l`，试试看，列出目前媒体库的内容吧。

如果需要修改、删除媒体库分类等其他操作，运行`python3 ptmm.py -参数`，详见下列表。

| 参数                  | 描述                                                         |
| --------------------- | :----------------------------------------------------------- |
| -a / --add-entry      | 添加一个媒体库分类（名称、原路径，媒体库分类路径）           |
| -s / --scan           | 扫描新增和删除的媒体，并同步修改媒体库（需要确认）           |
| -l / --list           | 列出媒体库的所有内容                                         |
|                       |                                                              |
| -ss / --scan-silently | 静默扫描新增和删除的媒体，并同步修改媒体库（无需确认）       |
| -e / --edit-entry     | 编辑媒体库分类（名称，原路径，媒体库分类路径（目标文件将被移动）） |
| -d / --del-entry      | 删除一个媒体库分类（媒体库的整个分类将被删除，原数据不会被删除） |
|                       |                                                              |
| -lp / --list-path     | 列出所有媒体库分类的路径                                     |
| -c / --check-link     | 检查目标路径是否存在inode错误                                |
| -dm / --del-media     | 手动删除指定媒体                                             |
| -h / --help           | 显示此帮助                                                   |



# 配置文件

配置文件为 ptmm.conf，配置主要有以下两条：

`ignore-ext`：链接媒体文件时，忽略的文件类型，用逗号分隔。

`incomplete-ext`：未完成下载的文件拓展名，用逗号分隔。添加媒体库时将忽略此文件夹，完成后才会入库。

（`wecom`相关的功能暂未完成，保留`wecom = no`即可）

默认配置如下，按需添加拓展名。

```conf
[common]
ignore-ext = .jpg, .txt, .nfo
incomplete-ext = .part, .!qB
```

# 原理

由于（PT/BT）下载完成后，如果要做种，原文件不能有任何修改。这时候如果你需要改名，修改nfo文件等操作，就可以使用本程序。

此程序将建立一个新的媒体库，创建分类规则，就可以自动检查原目录，在库目录中创建/删除硬连接。经过硬连接的文件不占用额外空间，可以改名、删除，不影响原文件。并且可以在新目录创建nfo文件等，不用担心重名。
**注意！** 不可以编辑硬连接之后的文件，因为本质上原文件和硬连接指向同一块数据，修改任何一方，硬连接和原文件都会同步。如果需要修改，请复制原文件，而不是创建硬连接。
并且，硬连接必须和原文件在同一块硬盘之下。

例如，使用默认配置，并建立如下分类规则：

| 名称   | 原目录                 | 库目录                  |
| ------ | ---------------------- | ----------------------- |
| movies | /download/movies | /media/video-lib/movies |
| tv     | /download/tv     | /media/video-lib/tv/    |
| music  | /download/music  | /media/lib/music        |

扫描后，将按照如下方式建立硬连接。

```
/download/movies/1/1.mkv -----------> /media/video-lib/movies/1.mkv
................../1.nfo

/download/movies/2/2.avi -----------> /media/video-lib/movies/2.avi
................../2.jpg

/download/tv/1/s1e1.mkv ------------> /media/video-lib1/tv/s1e1.mkv
............../s1e2.mkv ------------> /media/video-lib1/tv/s1e2.mkv
............../s1e3.mkv ------------> /media/video-lib1/tv/s1e3.mkv
............../1.nfo
............../1.png

/download/music/a1/1.mp3
................../2.mp3.part
（整个a1文件夹被忽略，因为包含未完成文件）

/download/other/test.zip
/download/document/1.docx
（忽略，因为没有对应分类规则）
```


# Info

This is a tool for managing the PT download library.  
By creating and managing hard links, it avoids the inconvenience of renaming, moving or overwriting the nfo content of the files downloaded from PT. And it is convenient to cooperate with tinyMediaManager to scrape local nfo.  
The program is based on python3.



# Usage

Clone this repository, run with terminal:

Step 1: `python3 ptmm.py -a`, Add media entry. (name, source entry-path, library entry-path)

Step 2: `python3 ptmm.py -s`, Scan (add and delete) media, and sync with library.

Step 3: `python3 ptmm.py -l`, Have a try, list all media.

If you need to modify, delete and do other operations, run `python3 ptmm.py -parameter` as listed below:

| parameters            | description                                                  |
| --------------------- | :----------------------------------------------------------- |
| -a / --add-entry      | Add media entry (name, source entry-path, library entry-path) |
| -s / --scan           | Scan (add and delete) media, and sync with library           |
| -l / --list           | List all media                                               |
|                       |                                                              |
| -ss / --scan-silently | Silently scan (add and del) media, and sync to library       |
| -e / --edit-entry     | Edit an entry (name, source path, library entry-path)        |
| -d / --del-entry      | Delete an entry (will delete specific entry-path in library, source file will NOT be deleted) |
|                       |                                                              |
| -lp / --list-path     | List all entry-path in library                               |
| -c / --check-link     | Check are there inode errors in library                      |
| -dm / --del-media     | Delete specific media in library manually                    |
| -h / --help           | Show this help message                                       |



# Config

The config file is ptmm.conf, main parameters are these two:

`ignore-ext`: Files with these extensions will be ignored when adding to library.  

`incomplete-ext`: The extensions of incomplete files, the folders(tasks) with those files will be ignored unless they are finished.

( wecom related function is not finished yet, just leave `wecom = no` there)

The default config is as below, add extensions as you wish.

```conf
[common]
ignore-ext = .jpg, .txt, .nfo
incomplete-ext = .part, .!qB
```



# How it works

After finished a torrent, in order to seed, you have to keep all origin files. You can't even modify the filename, or modify other unimportant files like .nfo file.

This program aims to create an **media library via hard link**. You can create new rules for media entry. After that, the program will automatically check new files and absent files under the rule, and sync them with the library. 

(The library is made of hard links, they don't use extra space in disk and can be renamed or deleted without influencing the original files. And, you can also add any new files such as .nfo file in the library.)

**ATTENTION**:  
The hard links should NOT be edited directly, because the hard link and original file point to the same data block in disk, editing one of them means editing all. If you want to do so, please make a copy of original file instead of making hard link.  
Plus, the hard links and original files should be in the same disk.

For example, with default config, given the following entries:

| name   | source path            | library path            |
| ------ | ---------------------- | ----------------------- |
| movies | /download/movies | /media/video-lib/movies |
| tv     | /download/tv     | /media/video-lib/tv/    |
| music  | /download/music  | /media/lib/music        |

After scanning, the program will create hard links:

```
/download/movies/1/1.mkv -----------> /media/video-lib/movies/1.mkv
................../1.nfo

/download/movies/2/2.avi -----------> /media/video-lib/movies/2.avi
................../2.jpg

/download/tv/1/s1e1.mkv ------------> /media/video-lib1/tv/s1e1.mkv
............../s1e2.mkv ------------> /media/video-lib1/tv/s1e2.mkv
............../s1e3.mkv ------------> /media/video-lib1/tv/s1e3.mkv
............../1.nfo
............../1.png

/download/music/a1/1.mp3
................../2.mp3.part
(entire folder a1 ignored for containing incomplete file)

/download/other/test.zip
/download/document/1.docx
(ignored for no entry for these folders)
```
