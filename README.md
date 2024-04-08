# PT-media-manager
For the English version, click [readme](https://github.com/shengt25/PT-Media-Manager/tree/main#info) or scroll down.

当PT/BT下载完媒体之后，你可能想在做种的同时：  
1.修改媒体名称  
2.覆盖nfo，jpg等非主要文件  
3.使用tinyMediaManager刮削（会覆盖nfo，jpg文件）  
...  

但是这样做的话，会导致部分文件名发生变化，nfo，jpg等文件被覆盖，就无法继续做种。
此工具就是用来解决这个问题的，它会建立一个媒体库，并将文件链接至媒体库中： 

1.原文件保持不变，用于做种  
2.媒体库中的文件，可以随意改名，不影响原文件  
3.非媒体文件不会被添加，你可以在媒体库中创建新的jpg，nfo等文件  
4.放心，由于其原理是使用硬连接，媒体库中的文件不会额外占用硬盘空间  

# 使用方法

Clone 此项目，使用终端运行：

Step 1: `python3 ptmm.py -a`，添加新的媒体库分类（分类名称、原路径和目标路径），例如电影，电视剧，音乐  

Step 2: `python3 ptmm.py -s`，在原路径中扫描新增或删除的媒体，同步至媒体库  

Step 3: `python3 ptmm.py -l`，列出媒体库的内容  

如果需要修改、删除媒体库分类等其他操作，运行`python3 ptmm.py -参数`，详见下列表  

常用命令：
| 选项                  | 描述                                                         |
| --------------------- | :----------------------------------------------------------- |
| -a             | 添加一个媒体库分类                                         |
| -s             | 扫描新增和删除的媒体，并同步修改媒体库           |
| -l             | 列出媒体库的所有内容                                         |
|                |                                                              |
| -e             | 编辑媒体库分类（媒体库文件将被移动）） |
| -d             | 删除一个媒体库分类（媒体库的整个分类将被删除，原数据不会被删除） |

其他命令：
| 选项                  | 描述                                                         |
| --------------------- | :----------------------------------------------------------- |
| -ss         | 静默扫描新增和删除的媒体，并同步修改媒体库（无需确认）       |
| -lp         | 列出所有媒体库分类的路径                                     |
| -c          | 检查目标路径是否存在inode错误                                |
| -dm         | 手动删除指定媒体                                             |
| -h          | 显示此帮助                                                   |



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
/download/movies/1/1.mkv   ->   /media/video-lib/movies/1.mkv
................../1.nfo        忽略(文件类型)

/download/movies/2/2.avi   ->   /media/video-lib/movies/2.avi
................../2.jpg        忽略(文件类型)

/download/tv/1/s1e1.mkv    ->   /media/video-lib1/tv/s1e1.mkv
............../s1e2.mkv    ->   /media/video-lib1/tv/s1e2.mkv
............../s1e3.mkv    ->   /media/video-lib1/tv/s1e3.mkv
............../1.nfo            忽略(文件类型)
............../1.png            忽略(文件类型)

/download/music/a1/1.mp3        忽略(目录包含未完成文件)
................../2.mp3.part   忽略(目录包含未完成文件)
                                (备注：整个a1文件夹被忽略，因为包含未完成文件夹)

/download/other/test.zip        忽略(无对应分类规则)
/download/document/1.docx       忽略(无对应分类规则)
```


# Info

After PT/BT has downloaded the media, you may want to:  
1. Modify the media name  
2. Replace other files such as nfo, jpg, etc  
3. Use tinyMediaManager to scrape (nfo, jpg files will be overwritten)

However, doing so will cause some filenames change; jpg, nfo and other files being overwritten, making it impossible to continue seeding.  

This tool is designed to solve this problem. It will create a media library and link the files to the media library:  
1. The original file remains unchanged and is used for seeding  
2. The files in the media library can be renamed, without affecting the original files   
3. Non-media files will not be added, you can create new jpg, nfo and other files in the media library  
4. Don’t worry, since it use hard link, the files in the media library will not occupy additional hard disk space  


# Usage

Clone this repository, run with terminal:  

Step 1: `python3 ptmm.py -a`, add a new media library category (category name, original path and target path), such as movies, TV series, music  

Step 2: `python3 ptmm.py -s`, scan the original path for new or deleted media, and synchronize with media library  

Step 3: `python3 ptmm.py -l`, lists the contents of the media library  

If you need to modify, delete and do other operations, run `python3 ptmm.py -parameter` as listed below:  

Common commands:
| options            | description                                                   |
| --------------------- | :----------------------------------------------------------- |
| -a          | Add media entry                                         |
| -s               | Scan (add and delete) media, and sync with library           |
| -l                | List all media                                         |
|                       |                                                              |
| -e          | Edit an entry（file in library will be moved as well）） |
| -d           | Delete an entry (will delete specific entry-path in library, source file will NOT be deleted) |

Other commands:
| options            | description                                          |
| --------------------- | :----------------------------------------------------------- |
| -ss      | Silently scan (add and del) media, and sync to library       |
| -lp         | List all entry-path in library                            |
| -c           | Check are there inode errors in library                     |
| -dm          | Delete specific media in library manually                    |
| -h                 | Show this help message                                      |


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
/download/movies/1/1.mkv   ->   /media/video-lib/movies/1.mkv
................../1.nfo        ignore(file type)

/download/movies/2/2.avi   ->   /media/video-lib/movies/2.avi
................../2.jpg        ignore(file type)

/download/tv/1/s1e1.mkv    ->   /media/video-lib1/tv/s1e1.mkv
............../s1e2.mkv    ->   /media/video-lib1/tv/s1e2.mkv
............../s1e3.mkv    ->   /media/video-lib1/tv/s1e3.mkv
............../1.nfo            ignore(file type)
............../1.png            ignore(file type)

/download/music/a1/1.mp3        ignore(folder include incomplete file)
................../2.mp3.part   ignore(folder include incomplete file
                                (note: entire folder a1 was ignored for containing incomplete file)

/download/other/test.zip        ignore(no rule)
/download/document/1.docx       ignore(no rule)
```
