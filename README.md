# UnpackDarkSoulsForModding
Unpacks Dark Souls 1 archive files for easier modding.

Instructions:

* Make a backup of any saved games. (The tool should not modify or delete these files.)
* Install and set up DSFix or other dll-based mods. Some users have reported that installing these mods after unpacking causes crashes.
* Download `dist/UnpackDarkSoulsForModding.exe` and place in your Dark Souls `DATA` directory (with `DARKSOULS.exe`)
* Run `UnpackDarkSoulsForModding.exe` by double-clicking on it. A command prompt window should appear.
* If you are using a standard installation of Dark Souls 1 from Steam, the tool will run without user input. Do not close the window until the prompt indicating that the process has completed.
* If you are not using a standard installation, the tool will prompt you for input if it discovers irregularities. Choosing to continue will attempt unpacking, but may crash or produce incorrect results, especially if the archive files are non-standard. For best results if this occurs, re-install / verify cache in Steam, installing dll mods as above if needed.

Technical Details:

This unpacker makes only minor .exe modifications, and as such does not make more extensive modifications, such as DCX unpacking. The resultant files are still DCX compressed, requiring use of a rebuilder to unpack and repack these files to make modifications.

The .exe was prepared using pyinstaller using onefile mode without supressing console output. The .ico file is included. 
