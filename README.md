# UnpackDarkSoulsForModding
Unpacks Dark Souls 1 archive files for easier modding. This allows mods to be distributed as raw files, rather than as packed dvdbnd archives.

Instructions:

It is **highly recommended** that you start from a fresh installation of Dark Souls 1. If you have previously unpacked your Dark Souls 1 archive files by hand
(through hex-editing `DARKSOULS.exe` & Wulf's BND Rebuilder) or automatically (using a previous version of UDSFM), it is recommended that
you erase and re-install Dark Souls 1 before using UDSFM. However, if you do not wish to do so, it is still possible to use UDSFM by following the
second, more complicated set of instructions below.

Note: The Dark Souls 1 data directory `DATA` is usually located at `C:\Program Files (x86)\Steam\SteamApps\common\Dark Souls Prepare to Die Edition\DATA`, but it may be in
a different location depending on your Steam installation. Note that UDSFM only supports the Steam version of the game, not the GFWL version nor pirated versions.

Before beginning, make sure you have at least 10GB of free hard-disk space and 1GB of available RAM.

If your archive files *are not* already unpacked:

* Make a backup of any saved games. (The tool should not modify or delete these files.)
* Install and set up DSFix or other .dll-based mods. Some users have reported that installing these mods after unpacking causes crashes.
* Download `dist/UnpackDarkSoulsForModding.exe` and place in your Dark Souls `DATA` directory.
* Run `UnpackDarkSoulsForModding.exe` by double-clicking on it. A command prompt window should appear.
* Do not close the window until the prompt indicates that the process has completed. Make sure you read any prompts carefully before answering.
* If you are not using a standard installation, the tool will prompt you for input if it discovers irregularities. Choosing to continue will attempt unpacking, but may crash or produce incorrect results, especially if the archive files are non-standard. For best results if this occurs, re-install / verify cache in Steam, installing .dll mods as above if needed.

If your archive files *are* already unpacked:

* Find the original copies of `dvdbnd#.bdt` and `dvdbnd#.bdt5`, where `#` is `1`,`2`,`3`,`4` and place them in your `DATA `directory. (They may be in `DATA` already, or in another directory, e.g. `unpackDS-backup`.) If you cannot find these files, you will need to re-install Dark Souls 1.
* If possible, find the original vanilla copy of `DARKSOULS.exe` and place it in your `DATA` directory. UDSFM can tolerate a non-standard .exe, but will prompt for confirmation before continuing and will not be able to verify its modifications.
* Make sure that no important data that you would like to preserve is being stored in any subdirectory of `DATA`. Many of these subdirectories will be deleted and re-created.
* Make a backup of any saved games. (The tool should not modify or delete these files.)
* Install and set up DSFix or other .dll-based mods. Some users have reported that installing these mods after unpacking causes crashes.
* Download `dist/UnpackDarkSoulsForModding.exe` and place in your Dark Souls `DATA` directory.
* Run `UnpackDarkSoulsForModding.exe` by double-clicking on it. A command prompt window should appear.
* Do not close the window until the prompt indicates that the process has completed. Make sure you read any prompts carefully before answering.
* You may be prompted to allow the tool to continue, especially if you are not using a vanilla .exe. Choosing to continue will attempt unpacking, but may crash or produce incorrect results, especially if the archive files are non-standard. For best results if this occurs, re-install / verify cache in Steam, installing .dll mods as above if needed.

Once the tool completes, your Dark Souls 1 installation will now be reading from files in the `DATA` directory, allowing for easier modding.

Technical Details:

Unlike the previous version of UDSFM, this tool disables DCX compression while unpacking the archives. This allows for easier modding, but also increases the size of the files-on-disk slightly. Load times should not be noticeably different.

During the course of unpacking, UDSFM unpacks all *bnd files to search for more files that need to be DCX-decompressed. Since these files are of use to those who wish to make mods, UDSFM has the option of not removing these
usually-temporarily unpacked files and provide a manifest of what each *bnd file yields. This allows modders to examine the contents of every *bnd file without needing to unpack each one individually. However, it does use
hard-disk space if these files are not removed. Most users will have no need for these unpacked temporary files.

If you have a different .exe (for debugging, perhaps) that you would like to patch to use the unpacked files, place it -- making sure it is named `DARKSOULS.exe` -- and UDSFM in an empty directory, and run UDSFM.
Once you agree to the modification, UDSFM will patch the .exe and then abort without attempting to unpack any archive files. The patched .exe can then be swapped out for the .exe in `DATA` at your discretion.

The .exe was prepared using pyinstaller using onefile mode without supressing console output. The .ico file is included.