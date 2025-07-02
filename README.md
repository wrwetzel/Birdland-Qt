# ![saxophone](Documentation/Images/Saxophone_64.png) Birdland-Qt                  

Birdland is a multimedia music viewer and library manager for music books
in PDF form with specific attention to fakebooks.  It displays a page of
music by searching a database of titles and other metadata.  It also
displays non-indexed PDF files but without metadata searching.  Birdland
ships with index data from 9 sources covering over 100 books and over
20,000 titles.

Answering the *Let's hear how it goes* question, search results also
include links to audio files, MIDI files, ChordPro files, and JJazzLab
songs from your media library, and and relevant YouTube videos.

The *Lite* version includes indexes for many popular fake books compiled
from several sources but does not include *Index Management* tools to
create or manage your own indexes.  These tools will be included in a
future release.

*Birdland-Qt* is a cross-platform application that runs on Windows, macOS, and Linux.

*Birdland* does not include any media (fake books, audio files, MIDI
files, ChordPro files, etc.) Such media is available from many online
sources, which we leave to you to discover.

## Download
<a href=https://birdland-qt.wrwetzel.com>Project site</a>

## Terminology
* *Music* - You look at music.
* *Audio* - You listen audio.
* *Canonical Name* - standardized fake book names that identify music files in *Birdland* indexes.
* *Indexes* - contains the relationship between song titles (and other metadata) and the canonical name and page number in fake books and other media (audio, MIDI, etc.).
* *Source* / *Src* - identifies the origin of index data, which comes from individual contributors, libraries, publishers, and from programmatic extraction.

## Documentation:
The *Birdland Guide* describes all of the configuration options. 
Calling it *Configuration Guide* or *Settings Guide* or *Options Guide* was not possible on the macOS platform.

The *Documentation* file is from *Birdland 2022*, out of date, and will be revised in a later release. It
may help with some of the concepts but keep in mind that it discusses index management, which is not presently
incuded, and it figures are for the older *Birdland*.

```
Help->Documentation
Help->Birdland Guide
Help->Quick-Start Guide
```

## Helper Applications
Birdland works fine right out of the box for searching and viewing your music files. 
Some helper applications are needed to use all of its features:

* VideoLan (VLC) - Birdland used the VLC library for the built-in audio
and MIDI player.  While the VLC library is included in Birdland on all
platforms, on Windows and macOS the VLC library requires additional libraries
that cannot be included and which are part of the VLC package. When installing on Windows
be sure to install it in the default location *C:\Program Files* so it can be found.
You can also use VLC as an external audio and MIDI player If you prefer.
* ChordPro - is required only if you want to convert ChordPro files to
readable text for viewing.  Tell Birdland the location of the ChordPro
executable with a configuration option.
* MuseScore - is required only if you want to engrave MIDI files to music
notation for viewing.  Tell Birdland the location of the MuseScore
executable with a configuration option.

## Configuration

Tell Birdland where your media files are located using the *Configuration Options* window. 
See the *Birdland Guide* in the Help menu for a description of all options.

```
File->Settings (Windows, Linux)
Birdaland-Qt->Preferences* (macOS)
```

To find your music files, Birdland needs to know how the names of
*your* music files correspond to the *Canonical Names* in the indexes.                            
The *Canonical2File* map, which you create using tools in
the *Edit Canonical->File* tab or manually, contains this information. An example file is included to
get you started. 

You can type in folder and file
names directly in the *Configuration Options* window or right click to show a selector for many of the options.
After changing the settings for media files you have to rebuild the internal database. 

```
Database->Rebuild All Tables
```
## Building the *Canonical->File* Map
Birdland needs to know how the
name of each book in *your* music library corresponds
to the canonical name used in the Birdland indexes before it can find music via a search. 
The *Canonical->File* map contains this information. It is located in the configuration directory (see
the table below for the location).

The browsers on the *Media Browsers* tab in the left panel do not require the *Canonical->File* map
and can be used once their corresponding configuration options are set.

### With the *Edit Canonical->File* Tab
The Canonical->File tab shows three tables: the *Canonical Name*, the *Canonical File*, and the *Canonical->File Map* tables. The latter shows the linkage between the canonical names and file
names.

Before beginning be sure that you have entered values for the configuration options:
- *Root of music files*
- *Folders containing music files permitting Canon->File editing*

The files described by these options are shown in the *Canonical Files* tables when you click the *Load Tables* button. You can now proceed to build the *Canonical->File* map.

- Select *Edit Canonical->File* Tab
- Click the *Load Tables* button
- Select a canonical name in the *Canonical Name* table
- Select a filename in the *File Name* table
- Click the *Link Canonical to File* button
  The link will be created in the *Canonical->File Map* table if it does not exist
  or updated if it does exist.
- Select a row in the Canonical->File and click *Clear One Link* when you make a mistake
- Click the *Save* button to save the Canonical->File table in your configuration folder.

### By Hand
The Canonical->File file is an ordinary text file that you can create with your favorite editor.
It consists of two columns separated with a vertical bar. For example:
```
New Real Book Vol 1 - Chuck Sher | Fake Books/New Real Book Vol 1.pdf
Firehouse Jazz Band - Unknown | Fake Books/Firehouse Jazz Band Commercial Dixieland Fake Book.pdf
```
The first colum is the *Canonical Name* of the book.     
The second column is *your* filename of the book relative to the *Root of music files:* configuration
option.
Select the menu item below for a list of all canonical names.

```
Reports->Canonical Names
```

## Using Birdland
- Enter a full or partial title in the green *Title:* box in the upper left.
- Press return or click *Search*.
- Click on a row in the *Music Index* to view music in your collection matching the title.
- Right-click on a row to search again for just the title or composer.
- With the cursor in the PDF viewer press *Down-Arrow* to show a zoom window of the music. Press again to close.
  A *Status Bar* indicator shows to remind you of zoom window should it hide behind the main window. Click
  on the indicator or press ESC to bring it to the front.
- A *Status Bar* indicator shows if the title matches audio or MIDI in your collection. Click on the
  indicator to go to the matching entry in the *TOC/Media Data* tab.
- Click on a row in the *Music Files*, *Audio*, *MIDI*, *ChordPro*, *JJazzLab*, 
  or *YouTube* tabs to open or play the media.
- Right-click on a row in the *MIDI* table to engrave the score and more search options and the *Audio* 
  or *ChordPro* tables for more search options.

## Keyboard Shortcuts

The following shortcuts apply when *Music Viewer* has focus:

| Key                       | Action                                     |
| -----------------         | --------------------------------------------- |
| Down-Arrow                | Toggle the PDF to a Zoom window, which can be resized and moved to a second monitor |
| H                         | Fit PDF to available width             |
| V                         | Fit PDF to available height            |
| Up-Arrow                  | Toggle fit between available width and height |
| Space / Right-Arrow       | Scroll down within a page |
| Backspace / Left-Arrow    | Scroll up within a page |
| Home                      | First page                   |
| Page-Up                   | Previous page                      |
| Page_Down                 | Next page                   |
| End                       | Last page                      |

The following shortcuts apply globally:

| Key  | Action                                                       |
| ---- | ------------------------------------------------------------ |
| ESC  | Bring the Zoom window to front, helpful if hiding behind main window, same as *Zoom* button |


## File Locations

| Platform | Content       | Location                                      |
| -------- | ------------- | --------------------------------------------- |
| Linux    | Configuration | ~/.config/birdland_qt                         |
|          | Data          | ~/.local/share/birdland_qt                    |
|          |               |                                               |
| Window   | Configuration | C:\Users\\\<user>\AppData\Roaming\birdland_qt |
|          | Data          | C:\Users\\\<user>\AppData\Local\birdland_qt   |
|          |               |                                               |
| MacOS    | Configuration | ~/Library/Preferences/birdland_qt             |
|          | Data          | ~/Library/Application Support/birdland_qt     |

