import logging
log = logging.getLogger(__name__)

import os
import shutil
import hashlib
import sys
import mmap

import bdt_unpacker
import bnd_unpacker
import c4110_replacement

UNPACKED_DIRS = [
    "chr", "event", "facegen", "font", "map", "menu", "msg", "mtd", 
    "obj", "other", "param", "paramdef", "parts", "remo", "script", 
    "sfx", "shader", "sound"
]
BACKUP_DIR = "unpackDS-backup"

TEMP_FRPG_DIR = "unpackDS-BND"
TEMP_FRPG_DATA_SUBDIR = "content-DATA"
TEMP_FRPG_N_SUBDIR = "content-N"

ANSI_BRIGHT_RED = "\x1b[31;1m"
ANSI_BRIGHT_YELLOW = "\x1b[33;1m"
ANSI_END = "\x1b[0m"
ANSI_CLEAR_LINE = "\x1b[K"
ANSI_CURSOR_UP_LINE = "\x1b[1A"

def get_checksum(filename, blocksize=65536):
    """Computes the SHA256 checksum of filename, read in of chunks of blocksize bytes."""
    
    hash_string = hashlib.sha256()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash_string.update(block)
    return hash_string.hexdigest()

def check_exe():
    """Searches for known Dark Souls .exe files and computes their checksum.
    
    Returns a tuple (filename, status).
    If the file is the known unmodified Steam version, status is "Expected".
    If the file is the known modified (i.e. patched) Steam version, then
     status is "Unpacked".
    If the file is the known debug version, status is "Expected Debug".
    If the file is the known modified debug version, then status is 
     "Unpacked Debug".
    If the file is some unknown DARKSOULS.exe, then status is "Unexpected".
    If no DARKSOULS.exe is found, status is "None".
    """
    
    EXE_CHECKSUM =           "67bcab513c8f0ed6164279d85f302e06b1d8a53abff5df7f3d10e1d4dfd81459"
    MOD_EXE_CHECKSUM =       "903a946273bfe123fe5c85740c3613374e2cf538564bb661db371c6cb5a421ff"
    DEBUG_EXE_CHECKSUM =     "b6958f3f0db5fdb7ce6f56bff14353d8d81da8bae3456795a39dbe217c1897cf"
    MOD_DEBUG_EXE_CHECKSUM = "473de70f0dd03048ca5dea545508f6776206424494334a9da091fb27c8e5a23f"
    
    EXE_FILENAME = "DARKSOULS.exe"
    
    if os.path.isfile(EXE_FILENAME):
        checksum = get_checksum(EXE_FILENAME)
        log.info(".exe checksum is " + checksum)
        if checksum == EXE_CHECKSUM:
            return (EXE_FILENAME, "Expected")
        elif checksum == DEBUG_EXE_CHECKSUM:
            return (EXE_FILENAME, "Expected Debug")
        elif checksum == MOD_EXE_CHECKSUM:
            return (EXE_FILENAME, "Unpacked")
        elif checksum == MOD_DEBUG_EXE_CHECKSUM:
            return (EXE_FILENAME, "Unpacked Debug")
        else:
            return (EXE_FILENAME, "Unexpected")
    else:
        return ("", "None")

def check_archives(): 
    """Computes each of the Dark Souls archives checksums, and classifies them. Prints progress.
    
    Returns a tuple (existing_files, has_matching_checksum, missing_files)
    Of the 8 archive files, their names will either be in the list existing_files,
     or in the list missing_files. For each archive file in existing_file,
     its name will also be in the list has_matching_checksum if its checksum
     matches the known Steam version.
    """
    
    FILE_CHECKSUMS = {
        "dvdbnd0.bdt":  "5ba004380a984a08acbe7e231a26ebe5aeafba68cf2803ee76d5b73e61cfd41b",
        "dvdbnd1.bdt":  "c3d7827642e76564c4c13eccb0280e105896f88c0b3f68c58025cce051e9c98f", 
        "dvdbnd2.bdt":  "3d085778404185881a60c12dadaaca6041af643efbbf63f2da15a7ab6af45e0a", 
        "dvdbnd3.bdt":  "13578a204b1fb3efa246b63bd15ed45006017d416a91b06659b4d3c3ee5f8a89", 
        "dvdbnd0.bhd5": "48f8df35af7dbece0805994fe699e6e8ff99351022d135b0ea49e1a119078107", 
        "dvdbnd1.bhd5": "a1d814182df2f71be406aab5dc6da7bca696028d1ae7dfad12666d0f7c6cd9e0", 
        "dvdbnd2.bhd5": "e4fb6eec5f38225c4f785f0172128bcd885605a49ee2acb5d8def513c3a14b83", 
        "dvdbnd3.bhd5": "a0e0d0255e375838dc4a0ccff85b21f4896e01a06f43a4e78282dc4e3cba5de6"
    }

    existing_files = []
    missing_files = []
    has_matching_checksum = []
    for k in sorted(FILE_CHECKSUMS.keys()):
        print "   - Computing checksum of archive file \"" + k + "\"...",
        sys.stdout.flush()
        if os.path.isfile(k):
            existing_files.append(k)
            checksum = get_checksum(k)
            log.info("Checksum of '" + k + "' is " + str(checksum))
            if checksum == FILE_CHECKSUMS[k]:
                log.info("Checksum of '" + k + "' matches known.")
                has_matching_checksum.append(k)
        else:
            log.info("Archive '" + k + "' is missing.")
            missing_files.append(k)
        print "Done."
        sys.stdout.flush()
    return (existing_files, has_matching_checksum, missing_files)

def check_for_unpacked_dir():
    """Checks the current directory for any directories matching the
     names of those that are unpacked from the Dark Souls archives.
     
    Returns a list of these directories that are present.
    """
    
    already_unpacked_dirs = []
    for d in UNPACKED_DIRS:
        if os.path.isdir(d):
            already_unpacked_dirs.append(d)
    return already_unpacked_dirs

def check_dir_exists(dir_to_check):
    """Checks to see if the given directory exists."""
    
    return os.path.isdir(dir_to_check)

def make_backups(filelist):
    """Makes a backup of the files in filelist into BACKUP_DIR and prints progress."""
    
    try:
        shutil.rmtree(BACKUP_DIR)
    except OSError:
        if os.path.isdir(BACKUP_DIR):
            raise
    
    try: 
        os.makedirs(BACKUP_DIR)
    except OSError:
        if not os.path.isdir(BACKUP_DIR):
            raise
    for f in filelist:
        print " - Backing up file \"" + f + "\"...",
        sys.stdout.flush()
        shutil.copy2(f, BACKUP_DIR)
        print "Done."
        
def remove_unpacked_dirs(dirs):
    """Remove any directory in dirs and any subdirectories."""
    
    for d in dirs:
        try:
            shutil.rmtree(d)
        except OSError:
            if not os.path.isdir(d):
                raise

def create_unpacked_dirs():
    """Creates all directories in UNPACKED_DIRS."""
    
    for d in UNPACKED_DIRS:
        try: 
            os.makedirs(d)
        except OSError:
            if not os.path.isdir(d):
                raise
    
def modify_exe(filename):
    """Modifies filename by searching through it for Unicode strings and
     replacing them with corresponding strings. Also disables .dcx loading
     by patching a certain byte. Prints progress.
    """
    
    with open(filename, "rb+") as f:
        mm = mmap.mmap(f.fileno(), 0)
        
        REPLACEMENTS = {"dvdbnd0": ("d\x00v\x00d\x00b\x00n\x00d\x000\x00:\x00", "d\x00v\x00d\x00r\x00o\x00o\x00t\x00:\x00"),
                        "dvdbnd1": ("d\x00v\x00d\x00b\x00n\x00d\x001\x00:\x00", "d\x00v\x00d\x00r\x00o\x00o\x00t\x00:\x00"),
                        "dvdbnd2": ("d\x00v\x00d\x00b\x00n\x00d\x002\x00:\x00", "d\x00v\x00d\x00r\x00o\x00o\x00t\x00:\x00"),
                        "dvdbnd3": ("d\x00v\x00d\x00b\x00n\x00d\x003\x00:\x00", "d\x00v\x00d\x00r\x00o\x00o\x00t\x00:\x00"),
                        "hkxbnd": ("h\x00k\x00x\x00b\x00n\x00d\x00:\x00", "m\x00a\x00p\x00h\x00k\x00x\x00:\x00"),
                        "tpfbnd": ("t\x00p\x00f\x00b\x00n\x00d\x00:\x00", "m\x00a\x00p\x00:\x00/\x00t\x00x\x00"),
                        "%stpf": ("%\x00s\x00t\x00p\x00f\x00", "c\x00h\x00r\x00\x00\x00\x00\x00")
        }
        
        for name in sorted(REPLACEMENTS.keys()):
            mm.seek(0)
            count = 0
            find_replace = REPLACEMENTS[name]
            find_str = find_replace[0]
            replace_str = find_replace[1]
            
            next_pos = mm.find(find_str)
            while next_pos != -1:
                mm.seek(next_pos)
                mm.write(replace_str)
                count += 1
                next_pos = mm.find(find_str)
            print " - Transmuted " + str(count) + " occurances of \"" + name + "\" in .exe."
            log.info(str(count) + "x replacements of \"" + name + "\" in .exe.")
            sys.stdout.flush()
        
        # Disable .dcx loading.
        exe_type_byte = mm[0x80]
        if exe_type_byte == "\x54": # Release .exe
            log.info("Release .exe .dcx loading disabled.")
            mm.seek(0x8fb816)
            mm.write("\xeb\x12")
        elif exe_type_byte == "\xb4": # Debug .exe
            log.info("Debug .exe .dcx loading disabled.")
            mm.seek(0x8fb726)
            mm.write("\xeb\x12")
        else:
            raise ValueError("Unknown .exe version byte.")
        print " - Disabled .dcx loading in .exe."
            
        mm.flush()
        mm.close()
    return
    
def build_bdt_bhd_pairing(file_list):
    bdt_list = [f for f in file_list if os.path.splitext(f)[1][-3:] == "bdt"]
    bhd_list = [f for f in file_list if os.path.splitext(f)[1][-3:] == "bhd"]
    
    return_dict = {bdt_file: [] for bdt_file in bdt_list}
    for bdt_file in bdt_list:
        (_, bdt_filename) = os.path.split(os.path.abspath(bdt_file))
        trimmed_bdt_filename = bdt_filename[:-3]
        for bhd_file in bhd_list:
            (_, bhd_filename) = os.path.split(os.path.abspath(bhd_file))
            trimmed_bhd_filename = bhd_filename[:-3]
            if trimmed_bdt_filename == trimmed_bhd_filename:
                return_dict[bdt_file].append(bhd_file)
        log.info("bdt/bhd pairing dict entry for '" + str(bdt_file) + "':")
        for f in return_dict[bdt_file]:
            log.info(" " + str(f))
    return return_dict
            
def unpack_archives():
    """Uses bdt_unpacker to unpack the Dark Souls archive files. Prints progress."""
    
    BND_MANIFEST_FILE = "bnd_manifest.txt"
    BND_MANIFEST_HEADER = "This manifest records the source *bnd file locations and their \n" + \
     "corresponding list of included files. Use this manifest and the \n" + \
     "unpacked files in this directory to examine the contents of all the \n" + \
     "*bnd files directly and then unpack/modify/repack the associated *bnd \n" + \
     "file for any given unpacked file.\n\n" + \
     "Note that the files in this directory are not read by the game and \n" + \
     "modifying them has no effect, but can be useful for finding what \n" + \
     "file should be modified.\n\n\nMANIFEST:\n\n"
         
    created_file_list = []
    for i in [0, 1, 2, 3]:
        header_file = "dvdbnd" + str(i) + ".bhd5"
        data_file = "dvdbnd" + str(i) + ".bdt"
        
        print " - Unpacking archive " + str(data_file) + " using header " + str(header_file)
        log.info("Unpack " + str(data_file) + " via " + str(header_file))
        new_files = bdt_unpacker.unpack_archive(header_file, data_file, os.getcwd())
        log.info(" Unpacking yielded " + str(len(new_files)) + " new files.")
        created_file_list += new_files
        
    # Convert to set and back to remove duplicates.
    created_file_list = list(set(created_file_list))
        
    print " - Unpacking BND archives."
    bnd_list = [f for f in created_file_list if os.path.splitext(f)[1][-3:] == "bnd"]
    log.info("Found " + str(len(bnd_list)) + " *bnd files.")
    msg_len = 0
    manifest_string_list = []
    for count, filepath in enumerate(sorted(bnd_list)):
        log.info("Unpack " + str(filepath))
        (directory, filename) = os.path.split(os.path.abspath(filepath))
        
        rel_directory = os.path.relpath(directory)
        
        with open(filepath, 'rb') as f:
            file_content = f.read()
            new_file_list = bnd_unpacker.unpack_bnd(file_content, 
             os.path.join(os.getcwd(), TEMP_FRPG_DIR, TEMP_FRPG_DATA_SUBDIR, rel_directory),
             os.path.join(os.getcwd(), TEMP_FRPG_DIR, TEMP_FRPG_N_SUBDIR))
            log.info(" Unpacking yielded " + str(len(new_file_list)) + " new files.")
            created_file_list += new_file_list
            
            if len(new_file_list) > 0:
                manifest_string_list.append(os.path.join(rel_directory, filename))
                for new_file in new_file_list:
                    new_file_rel = os.path.relpath(new_file, os.path.join(os.getcwd(), TEMP_FRPG_DIR))
                    manifest_string_list.append(" " + new_file_rel)
        
        
        print "\r" + " " * msg_len,
        msg = "\r  - (" + str(count+1) + "/" + str(len(bnd_list)) + ") Unpacking BND file " + str(filename) + "..."
        print msg,
        msg_len = len(msg)
        sys.stdout.flush()
    print "Done."
    
    print " - Writing custom copy of missing file(s)...",
    log.info("Write reconstructed file(s).")
    manifest_string_list.append("-- Custom --")
    filepath = c4110_replacement.PATH.replace('\\', '/')
    filepath_to_use = bnd_unpacker.relativize_filename(filepath, 
     os.getcwd(), os.path.join(os.getcwd(), TEMP_FRPG_DIR, TEMP_FRPG_N_SUBDIR))
    f = bnd_unpacker.create_file(filepath_to_use)
    f.write(c4110_replacement.DATA)
    f.close()
    created_file_list.append(filepath_to_use)
    new_file_rel = os.path.relpath(filepath_to_use, os.path.join(os.getcwd(), TEMP_FRPG_DIR))
    manifest_string_list.append(" " + new_file_rel)
    print "Done."
    
    # Write out manifest, now that all *bnd-related files have been unpacked / created.
    log.info("Write manifest.")
    with open(os.path.join(os.getcwd(), TEMP_FRPG_DIR, BND_MANIFEST_FILE), 'w') as g:
        g.write(BND_MANIFEST_HEADER)
        g.write('\n'.join(manifest_string_list))
        g.close()
    
    log.info("Build bdt/bhd pairing.")
    print " - Examining unpacked files for BDT/BHD pairs...",
    pairing_dict = build_bdt_bhd_pairing(list(set(created_file_list)))
    for bdt_file in pairing_dict:
        if len(pairing_dict[bdt_file]) == 0:
            raise ValueError("BDT File \"" + str(bdt_file) + "\" has no corresponding header file.")
    print "Done."
    
    total_pairs = len(pairing_dict.keys())
    for count, bdt_file in enumerate(sorted(pairing_dict.keys())):
        print "\r - (" + str(count+1) + "/" + str(total_pairs) + ") Unpacking BDT/BHD pairs... "
        (_, bdt_filename) = os.path.split(os.path.abspath(bdt_file))
        matching_bhd_file = pairing_dict[bdt_file][0]
        (_, bhd_filename) = os.path.split(os.path.abspath(matching_bhd_file))
        
        print "  - Unpacking archive " + str(bdt_filename) + " using header " + str(bhd_filename)
        log.info("Unpack " + str(bdt_filename) + " via " + str(bhd_filename))
        
        # Redirect the output of the file depending on its extension, so that
        #  the .exe modifications make sense.
        (_, bdt_file_ext) = os.path.splitext(bdt_filename)
        if bdt_file_ext == ".chrtpfbdt":
            rel_directory = "chr"
        elif bdt_file_ext == ".hkxbdt":
            rel_directory = "map"
        elif bdt_file_ext == ".tpfbdt":
            rel_directory = os.path.join("map", "tx")
        else:
            raise ValueError("Unrecognized *bdt file extension: \"" + bdt_file_ext + "\".")
        directory = os.path.abspath(os.path.join(os.getcwd(), rel_directory))
        bdt_unpacker.unpack_archive(matching_bhd_file, bdt_file, directory)
        print "\r" + (ANSI_CURSOR_UP_LINE + ANSI_CLEAR_LINE)*4, # Erase the previous three lines.
    print "\r - (" + str(total_pairs) + "/" + str(total_pairs) + ") Unpacking BDT/BHD pairs... Done."
     
    print " - Removing BDT/BHD pairs... ",
    log.info("Remove bdt/bhd pairs.")
    for bdt_file in pairing_dict.keys(): 
        matching_bhd_file = pairing_dict[bdt_file][0]
        try:
            os.remove(bdt_file)
        except OSError:
            if not os.path.isfile(bdt_file):
                raise
        try:
            os.remove(matching_bhd_file)
        except OSError:
            if not os.path.isfile(matching_bhd_file):
                raise
    print "Done."
    return
    
def remove_archives():
    """Removes any Dark Souls archive files from the current directory."""
    
    for i in [0, 1, 2, 3]:
        header_file = "dvdbnd" + str(i) + ".bhd5"
        data_file = "dvdbnd" + str(i) + ".bdt"
        
        try:
            os.remove(header_file)
        except OSError:
            if not os.path.isfile(header_file):
                raise
        
        try:
            os.remove(data_file)
        except OSError:
            if not os.path.isfile(data_file):
                raise
    return
    
def remove_temp_dir():
    """Removes the temporary directory where *bnd files are unpacked."""
    try:
        shutil.rmtree(TEMP_FRPG_DIR)
    except OSError:
        if not os.path.isdir(TEMP_FRPG_DIR):
            raise
    
def yes_no(answer):
    """Prompts the user answer and returns True / False for a Yes / No 
     response, respectively.
    """
    
    yes = set(['yes','y', 'ye'])
    no = set(['no','n'])
     
    while True:
        choice = raw_input(answer).lower()
        if choice in yes:
            log.info("User chose Y for question '" + answer + "'.")
            return True
        elif choice in no:
            log.info("User chose N for question '" + answer + "'.")
            return False
        else:
            print "Unknown response. Respond [Y]es / [N]o.  "

def wait_before_exit(exit_code):
    """Displays a message before exiting with exit code exit_code"""
    
    raw_input("Exiting. Press ENTER to continue... ")
    log.info("Exited with exit code " + str(exit_code)) 
    sys.exit(exit_code)

def attempt_unpack():
    """Searches for and attempts to unpack the Dark Souls archive files
     in the current directory. Also searches for and modifies the Dark Souls
     executable so that it reads from the unpacked files instead of the archives.
     Prints progress.
    """
    log.info("Beginning unpack.")
    
    print "Preparing to unpack Dark Souls for modding..."
    print "Examining current directory..."
    
    already_unpacked = check_for_unpacked_dir()
    log.info("Existing used directories: " + str(already_unpacked))
    
    log.info(".exe check.")
    print " - Examining Dark Souls executable...",
    (exe_name, exe_status) = check_exe()
    log.info(".exe status: " + exe_status)
    if exe_status != "Expected" and exe_status != "Unpacked" and exe_status != "Expected Debug":
        print ""
        if exe_status == "Unexpected":
            if not yes_no(ANSI_BRIGHT_YELLOW + "WARNING: " + ANSI_END + 
             "Executable does not match expected checksum.\n  Continue anyway? [Y]es / [N]o  "):
                wait_before_exit(1)
        else:
            print (ANSI_BRIGHT_RED + "ERROR: " + ANSI_END + 
             "Executable DARKSOULS.exe was not found.\n  Check current directory and try again.")
            log.info("No .exe found.")
            wait_before_exit(1)
    else:
        print "Done."
    
    only_modify_exe = False
    log.info(".dvdbdt check.")
    print " - Examining data archives..."
    (arc_exists, arc_has_good_checksum, arc_missing) = check_archives()
    log.info("Archives missing: " + str(arc_missing))
    log.info("Archives existing: " + str(arc_exists))
    log.info("Archives good checksum: " + str(arc_has_good_checksum))
    if len(arc_missing) > 0:
        if (len(arc_exists) == 0 and (exe_status == "Unpacked" or exe_status == "Unpacked Debug") 
         and len(already_unpacked) == len(UNPACKED_DIRS) and check_dir_exists(BACKUP_DIR)):
            print "Unpacking appears to be have been previously completed. Exiting."
            log.info("Already completed.")
            wait_before_exit(0)
        elif len(arc_exists) == 0 and exe_status != "Unpacked" and exe_status != "Unpacked Debug":
            print ("No archives present, but unmodified .exe found.\n  " + ANSI_BRIGHT_YELLOW + 
             "WARNING: " + ANSI_END + "Patching the .exe alone will not unpack Dark Souls fully.")
            if yes_no("  Patch .exe? Unpacking will abort after this step. [Y]es / [N]o  "):
                only_modify_exe = True
            else:
                wait_before_exit(1)
        if not only_modify_exe:
            print (ANSI_BRIGHT_RED + "ERROR: " + ANSI_END + 
             "The following archive files are missing.\n  Check current directory and try again.")
            for f in arc_missing:
                print " * " + f
            wait_before_exit(1)
    if not only_modify_exe:
        for f in arc_exists:
            if f not in arc_has_good_checksum:
                if not yes_no(ANSI_BRIGHT_YELLOW + "WARNING: " + ANSI_END + 
                 "Archive file \"" + f + "\" does not match expected checksum.\n  Continue anyway? [Y]es / [N]o  "):
                    wait_before_exit(1)
                    
    log.info("DATA check.")
    if not only_modify_exe:
        print " - Examining directory contents..."
        if len(already_unpacked) > 0:
            log.info("DATA has used directories.")
            print "The following destination directories already exist\n  and will be deleted before unpacking begins."
            for d in already_unpacked:
                print " * " + d
            if not yes_no(ANSI_BRIGHT_YELLOW + "  WARNING: " + ANSI_END + 
             "The current contents of these directories " + ANSI_BRIGHT_YELLOW + 
             "WILL" + ANSI_END + " be lost.\n  Continue anyway? [Y]es / [N]o  "):
                wait_before_exit(1)
    
    log.info("BACKUP_DIR check.")
    should_make_backups = True
    if check_dir_exists(BACKUP_DIR):
        if yes_no("Backup directory \"" + BACKUP_DIR + "\" already exists.\n" + 
         ANSI_BRIGHT_YELLOW + "  WARNING: " + ANSI_END + "Backed-up copies of current files " +
         ANSI_BRIGHT_YELLOW + "WILL NOT" + ANSI_END + " be created.\n  Continue anyway? [Y]es / [N]o  "):
            should_make_backups = False
        else:
            wait_before_exit(1)
    
    log.info("TEMP_FRPG_DIR check.")
    if not only_modify_exe:
        if check_dir_exists(TEMP_FRPG_DIR):
            if not yes_no("Temporary unpacking directory \"" + TEMP_FRPG_DIR + "\" already exists.\n" + 
                    ANSI_BRIGHT_YELLOW + "  WARNING: " + ANSI_END + "The current contents of this directory " +
                    ANSI_BRIGHT_YELLOW + "WILL" + ANSI_END + " be lost.\n  Continue anyway? [Y]es / [N]o  "):
                wait_before_exit(1)
        should_remove_temp_dir = True
        if not yes_no("Remove temporarily unpacked *bnd directory when completed?\n" + 
         "  This directory is useful for making mods only.\n  (Answer Yes if unsure.)  [Y]es / [N]o  "):
            should_remove_temp_dir = False
    print "Done." 
    
    log.info("Make backup")
    if should_make_backups:
        print "Making backups..."
        if only_modify_exe:
            files_to_backup = [exe_name]
        else:
            files_to_backup = [exe_name] + arc_exists
        make_backups(files_to_backup)
        print "Done."
    else:
        print "Skipping backing-up important files."
        
    log.info(".exe modifications.")
    if exe_status == "Unpacked":
        print "Skipping modifying .exe file (checksum matches processed .exe)"
        log.info("Skipping .exe modifications; already processed.")
    else:
        print "Modifying .exe file..."
        modify_exe(exe_name)
        if exe_status == "Expected" or exe_status == "Expected Debug":
            print "Done. Verifying modifications...",
            (_, mod_exe_status) = check_exe()
            if ((exe_status == "Expected" and mod_exe_status == "Unpacked") or 
             (exe_status == "Expected Debug" and mod_exe_status == "Unpacked Debug")):
                print "Done."
                log.info("Appears to have verifiably worked.")
            else:
                print ""
                if not yes_no(ANSI_BRIGHT_YELLOW + "WARNING: " + ANSI_END + 
                 "Modified .exe does not match expected checksum.\n  Continue anyway? [Y]es / [N]o  "):
                    wait_before_exit(1)
        else:
            print "Done. Skipping checksum verification of non-standard .exe."
            log.info("Appears to have non-verifiably worked.")
            
    if only_modify_exe:
        print "Aborting unpacking after .exe modification."
        log.info("Aborting due to only .exe")
        wait_before_exit(0)
        
    if len(already_unpacked) > 0:
        print "Deleting existing unpacked archive directories...",
        log.info("Deleting used directories.")
        remove_unpacked_dirs(already_unpacked)
        print "Done."
    
    log.info("Unpacking dvdbnds.")
    print "Unpacking archives..."
    create_unpacked_dirs()
    unpack_archives()
    print "Done."

    log.info("Removing dvdbnds.")
    print "Removing archives...",
    remove_archives()
    print "Done."
    
    if should_remove_temp_dir:
        log.info("Removing TEMP_FRPG_DIR.")
        print "Removing temporary directories...",
        remove_temp_dir()
        print "Done."
        
    log.info("Done.")
    print "Unpacking completed. \[T]/"
    wait_before_exit(0)

    return
