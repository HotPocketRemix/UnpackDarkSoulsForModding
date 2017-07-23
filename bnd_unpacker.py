import os
import sys
import struct

def consume_byte(content, offset, byte, length=1):
    """Consume length bytes from content, starting at offset. If they
     are not all byte, raises a ValueError.
    """
    
    for i in xrange(0, length-1):
        if content[offset + i] != byte:
            raise ValueError("Expected byte '" + byte.encode("hex") + "' at offset " +\
                    hex(offset + i) + " but received byte '" +\
                    content[offset + i].encode("hex") + "'.")
    return offset + length
    
def relativize_filename(filename, basepath, n_basepath):
    """Fixes the given filename and joins it with the appropriate basepath, 
    depending on if it is relative to DATA or N:
    """
    
    if len(filename) >= 2 and filename[0:2].upper() == "N:":
        return fix_filename(n_basepath, filename[2:])
    else:
        return fix_filename(basepath, filename)
    
def fix_filename(base, filepath):
    """Joins filepath to base, and converts to the system's path separator."""
    
    # Append ./ to filepath so that it is correctly joined with base.
    #  If filepath begins with /, this prevents base from being ignored.
    return os.path.normpath(os.path.join(base, "./" + filepath))

def create_file(filename):
    """Attempts to create filename."""
    
    path = os.path.dirname(filename)
    
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
    
    f = open(filename, "wb+")
    return f
    
def extract_strz(content, offset):
    extracted = ''
    while content[offset] != '\x00':
        extracted = extracted + content[offset]
        offset += 1
    return extracted
    
def appears_bnd(content):
    """Checks if the magic bytes at the start of content indicate that it
    is a BND3-packed file.
    """
    return content[0:4] == "BND3"

def unpack_bnd(content, basepath, n_basepath):
    """Unpacks the *bnd file content from a BND3-packed file.
     
    Recursively creates directories relative to basepath for the unpacked
    files. Files that have a full N: path are instead placed relative to n_basepath.
    Returns a list of files created.
    """
    
    created_file_list = []
       
    master_offset = 0
    master_offset = consume_byte(content, master_offset, 'B', 1)
    master_offset = consume_byte(content, master_offset, 'N', 1)
    master_offset = consume_byte(content, master_offset, 'D', 1)
    master_offset = consume_byte(content, master_offset, '3', 1)
    
    # Skip the version number.
    master_offset = 0x0c
    (magic_flag, num_of_records, filename_end_offset) = struct.unpack_from("<III", content, offset=master_offset)
    master_offset += struct.calcsize("<III")
    if not (magic_flag == 0x74 or magic_flag == 0x54 or magic_flag == 0x70):
        raise ValueError("File has unknown BND3 magic flag: " + hex(magic_flag))
    
    # Skip to the records.
    master_offset = 0x20
    
    count = 0
    for _ in xrange(num_of_records):
        if magic_flag == 0x74 or magic_flag == 0x54:
            (record_sep, filedata_size, filedata_offset, file_id, 
             filename_offset, dummy_filedata_size) = struct.unpack_from("<IIIIII", content, offset=master_offset)
            master_offset += struct.calcsize("<IIIIII")
            if filedata_size != dummy_filedata_size:
                raise ValueError("File has malformed record structure. File data size " + 
                 str(filedata_size) + " does not match dummy file data size " + 
                 str(dummy_filedata_size) + ".")
        else: # magic_flag == 0x70
            (record_sep, filedata_size, filedata_offset, file_id, 
             filename_offset) = struct.unpack_from("<IIIII", content, offset=master_offset)
            master_offset += struct.calcsize("<IIIII")
        
        if record_sep != 0x40:
            raise ValueError("File has malformed record structure. Record" + 
            " has unknown record separator " + hex(record_sep))
            
        filename = extract_strz(content, filename_offset).replace('\\', '/')
        filedata = content[filedata_offset:filedata_offset + filedata_size]
        filename_to_use = relativize_filename(filename, basepath, n_basepath)
            
        created_file_list.append(filename_to_use)
        f = create_file(filename_to_use)
        f.write(filedata)
        f.flush()
        f.close()
        count += 1
    return created_file_list
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: " + str(sys.argv[0]) + " <BND3 File>"
    else:
        filepath = sys.argv[1]
        (directory, filename) = os.path.split(os.path.abspath(filepath))
        with open(filepath, 'rb') as f:
            file_content = f.read()
            file_list = unpack_bnd(file_content, 
             os.path.join(directory, filename + '.extract'), 
             os.path.join(directory, filename + '.n_extract'), filename)
        print "  - Created file list:"
        for filename in file_list:
            print "  - " + str(filename)
