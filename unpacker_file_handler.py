import os
import shutil
import hashlib
import sys
import mmap

import bdt_unpacker

UNPACKED_DIRS = [
    "chr", "event", "facegen", "font", "map", "menu", "msg", "mtd", 
    "obj", "other", "param", "paramdef", "parts", "remo", "script", 
    "sfx", "shader", "sound"
]
BACKUP_DIR = "unpackDS-backup"

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
    If the file is some unknown DARKSOULS.exe, then status is "Unexpected".
    If no DARKSOULS.exe is found, but DATA.exe is, then status is "GFWL".
    If no DARKSOULS.exe or DATA.exe is found, status is "None".
    """
    
    EXE_CHECKSUM = "67bcab513c8f0ed6164279d85f302e06b1d8a53abff5df7f3d10e1d4dfd81459"
    MOD_EXE_CHECKSUM = "52877d26431ae4f543c97a8fbe2d0eb0b836de29e8946556f99cf05c94a670b5"
    DEBUG_EXE_CHECKSUM = "b6958f3f0db5fdb7ce6f56bff14353d8d81da8bae3456795a39dbe217c1897cf"
    MOD_DEBUG_EXE_CHECKSUM = "13e5333bbf11cdcc1a20d9c53ca822ce872ce0405c6cc8cc5eaa04174f991fd0"
    EXE_FILENAME = "DARKSOULS.exe"
    GFWL_FILENAME = "DATA.exe"
    
    if os.path.isfile(EXE_FILENAME):
        checksum = get_checksum(EXE_FILENAME)
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
    elif os.path.isfile(GFWL_FILENAME):
        return (GFWL_FILENAME, "GFWL")
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
            if get_checksum(k) == FILE_CHECKSUMS[k]:
                has_matching_checksum.append(k)
        else:
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

def check_backup_dir_exists():
    """Checks to see if the backup directory exists."""
    
    return os.path.isdir(BACKUP_DIR)

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
    """Modifies filename by searching through it for Unicode strings 
     "dvdbndI:" and replacing them with "dvdroot:", where I is 
     either 0, 1, 2 or 3. Prints progress.
    """
    
    with open(filename, "rb+") as f:
        mm = mmap.mmap(f.fileno(), 0)
        
        REPLACEMENTS = {"dvdbnd0": ("d\x00v\x00d\x00b\x00n\x00d\x000\x00:\x00", "d\x00v\x00d\x00r\x00o\x00o\x00t\x00:\x00"), \
                        "dvdbnd1": ("d\x00v\x00d\x00b\x00n\x00d\x001\x00:\x00", "d\x00v\x00d\x00r\x00o\x00o\x00t\x00:\x00"), \
                        "dvdbnd2": ("d\x00v\x00d\x00b\x00n\x00d\x002\x00:\x00", "d\x00v\x00d\x00r\x00o\x00o\x00t\x00:\x00"), \
                        "dvdbnd3": ("d\x00v\x00d\x00b\x00n\x00d\x003\x00:\x00", "d\x00v\x00d\x00r\x00o\x00o\x00t\x00:\x00")
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
            sys.stdout.flush()
        mm.flush()
        mm.close()
    return
    
def unpack_archives():
    """Uses bdt_unpacker to unpack the Dark Souls archive files. Prints progress."""
    
    for i in [0, 1, 2, 3]:
        header_file = "dvdbnd" + str(i) + ".bhd5"
        data_file = "dvdbnd" + str(i) + ".bdt"
        
        print " - Unpacking archive file " + str(data_file) + " using header file " + str(header_file)
        bdt_unpacker.unpack_archive(header_file, data_file, os.getcwd())
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
    
def yes_no(answer):
    """Prompts the user answer and returns True / False for a Yes / No 
     response, respectively.
    """
    
    yes = set(['yes','y', 'ye'])
    no = set(['no','n'])
     
    while True:
        choice = raw_input(answer).lower()
        if choice in yes:
           return True
        elif choice in no:
           return False
        else:
           print "Unknown response. Respond [Y]es / [N]o."
		   
def wait_before_exit(exit_code):
    """Displays a message before exiting with exit code exit_code"""
    
    raw_input("Exiting. Press any key to continue...")
    sys.exit(exit_code)

def attempt_unpack():
    """Searches for and attempts to unpack the Dark Souls archive files
     in the current directory. Also searches for and modifies the Dark Souls
     executable so that it reads from the unpacked files instead of the archives.
     Prints progress.
    """
    
    print "Preparing to unpack Dark Souls for modding..."
    print "Examining current directory..."
    
    already_unpacked = check_for_unpacked_dir()
    
    print " - Examining Dark Souls executable...",
    (exe_name, exe_status) = check_exe()
    if exe_status != "Expected" and exe_status != "Unpacked" and exe_status != "Unpacked Debug" and exe_status != "Expected Debug":
        print ""
        if exe_status == "Unexpected":
            if not yes_no("Executable does not match expected checksum. Continue anyway? [Y]es / [N]o  "):
                wait_before_exit(1)
        elif exe_status == "GFWL":
            if not yes_no("Detected executable DATA.exe (GFWL version) is not supported. Continue anyway? [Y]es / [N]o  "):
                wait_before_exit(1)
        else:
            print "Executable DARKSOULS.exe was not found. Check current directory and try again."
            wait_before_exit(1)
    else:
        print "Done."
    
    print " - Examining data archives..."
    (arc_exists, arc_has_good_checksum, arc_missing) = check_archives()
    if len(arc_missing) > 0:
        if len(arc_exists) == 0 and exe_status == "Unpacked" and len(already_unpacked) == len(UNPACKED_DIRS) and check_backup_dir_exists():
            print "Unpacking appears to be have been previously completed. Exiting."
            wait_before_exit(0)
        print "The following archive files are missing. Check current directory and try again."
        for f in arc_missing:
            print " * " + f
        wait_before_exit(1)
    for f in arc_exists:
        if f not in arc_has_good_checksum:
            if not yes_no("Archive file \"" + f + "\" does not match expected checksum. Continue anyway? [Y]es / [N]o  "):
                wait_before_exit(1)
    
    print " - Examining directory contents..."
    if len(already_unpacked) > 0:
        print "The following destination directories already exist and will be deleted before unpacking begins."
        for d in already_unpacked:
            print " * " + d
        if not yes_no("The current contents of these directories WILL be lost. Continue anyway? [Y]es / [N]o  "):
            wait_before_exit(1)
    
    should_make_backups = True
    if check_backup_dir_exists():
        if yes_no("Backup directory \"" + BACKUP_DIR + "\" already exists. " + \
                "Backed-up copies of current files will not be created. Continue anyway? [Y]es / [N]o  "):
            should_make_backups = False
        else:
            wait_before_exit(1)
    
    print "Done."   
    
    if should_make_backups:
        print "Making backups..."
        files_to_backup = [exe_name] + arc_exists
        make_backups(files_to_backup)
        print "Done."
    else:
        print "Skipping backing-up important files."
        
    
    if exe_status == "Unpacked":
        print "Skipping modifying .exe file (checksum matches processed .exe)"
    else:
        print "Modifying .exe file..."
        modify_exe(exe_name)
        if exe_status == "Expected":
            print "Done. Verifying modifications...",
            (_, mod_exe_status) = check_exe()
            if mod_exe_status == "Unpacked":
                print "Done."
            else:
                print ""
                if not yes_no("Modified .exe does not match expected checksum. Continue anyway? [Y]es / [N]o  "):
                    wait_before_exit(1)
        elif exe_status == "Expected Debug":
            print "Done. Verifying modifications...",
            (_, mod_exe_status) = check_exe()
            if mod_exe_status == "Unpacked Debug":
                print "Done."
            else:
                print ""
                if not yes_no("Modified .exe does not match expected checksum. Continue anyway? [Y]es / [N]o  "):
                    wait_before_exit(1)
        else:
            print "Done. Skipping checksum verification of non-standard .exe."
        
    if len(already_unpacked) > 0:
        print "Deleting existing unpacked archive directories...",
        remove_unpacked_dirs(already_unpacked)
        print "Done."
    
    print "Unpacking archives..."
    create_unpacked_dirs()
    unpack_archives()
    print "Done."

    print "Removing archives...",
    remove_archives()
    print "Done."
        
    print "Unpacking completed. \[T]/"
    wait_before_exit(0)

    return
