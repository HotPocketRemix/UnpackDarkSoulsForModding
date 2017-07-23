import mmap
import os
import sys
import struct

import name_hash_handler
import dcx_uncompresser

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
    
def extract_strz(content, offset):
    extracted = ''
    while content[offset] != '\x00':
        extracted = extracted + content[offset]
        offset += 1
    return extracted

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
    
def appears_bhd(header):
    """ Determines if the given file has the magic bytes of a *bhd header.
    """
    with open(header, 'rb') as h:
        return h.read(12) == "BHF307D7R6\x00\x00"

def parse_bhd_header_to_dict(header):
    """Parses a *bhd Dark Souls archive header file into a dictionary
     that indexes files in a *bdt Dark Souls archive file.
     
    Returns a dictionary whose keys are filepaths, and whose
     elements are tuples (offset, length) that determine the binary
     data of that file inside the associated *bdt file.
    """
    
    with open(header, 'rb') as h:
        content = h.read()
    return_dict = {}
    
    master_offset = 0
    master_offset = consume_byte(content, master_offset, 'B', 1)
    master_offset = consume_byte(content, master_offset, 'H', 1)
    master_offset = consume_byte(content, master_offset, 'F', 1)
    master_offset = consume_byte(content, master_offset, '3', 1)
    master_offset = consume_byte(content, master_offset, '0', 1)
    master_offset = consume_byte(content, master_offset, '7', 1)
    master_offset = consume_byte(content, master_offset, 'D', 1)
    master_offset = consume_byte(content, master_offset, '7', 1)
    master_offset = consume_byte(content, master_offset, 'R', 1)
    master_offset = consume_byte(content, master_offset, '6', 1)
    master_offset = consume_byte(content, master_offset, '\x00', 1)
    master_offset = consume_byte(content, master_offset, '\x00', 1)
    
    # Skip the version number.
    master_offset = 0x0c
    (magic_flag, num_of_records) = struct.unpack_from("<II", content, offset=master_offset)
    master_offset += struct.calcsize("<II")
    if not (magic_flag != 0x74 or magic_flag != 0x54):
        raise ValueError("File has unknown BHD3 magic flag: " + hex(magic_flag))
    
    # Skip to the records.
    master_offset = 0x20
    
    for _ in xrange(num_of_records):
        (record_sep, filedata_size, filedata_offset, file_id, 
         filename_offset, dummy_filedata_size) = struct.unpack_from("<IIIIII", content, offset=master_offset)
        master_offset += struct.calcsize("<IIIIII")
        if filedata_size != dummy_filedata_size:
            raise ValueError("File has malformed record structure. File data size " + 
             str(filedata_size) + " does not match dummy file data size " + 
             str(dummy_filedata_size) + ".")
        if record_sep != 0x40:
            raise ValueError("File has malformed record structure. Record" + 
            " has unknown record separator " + hex(record_sep))
            
        filename = extract_strz(content, filename_offset).replace('\\', '/')
        return_dict[filename] = (filedata_offset, filedata_size)
    return return_dict
    
def appears_bhd5(header):
    """ Determines if the given file has the magic byte of a .bhd5 header.
    """
    with open(header, 'rb') as h:
        return h.read(4) == "BHD5"

def parse_bhd5_header_to_dict(header):
    """Parses a .bhd5 Dark Souls archive header file into a dictionary
     that indexes files in a .bdt Dark Souls archive file.
     
    Returns a dictionary whose keys are filepaths, and whose
     elements are tuples (offset, length) that determine the binary
     data of that file inside the associated .bdt file.
    """
    
    name_hash_dict = name_hash_handler.build_name_hash_dict()
    
    with open(header, 'rb') as h:
        header_str = h.read()
    return_dict = {}
    
    master_offset = 0
    master_offset = consume_byte(header_str, master_offset, 'B', 1)
    master_offset = consume_byte(header_str, master_offset, 'H', 1)
    master_offset = consume_byte(header_str, master_offset, 'D', 1)
    master_offset = consume_byte(header_str, master_offset, '5', 1)
    master_offset = consume_byte(header_str, master_offset, '\xff', 1)
    master_offset = consume_byte(header_str, master_offset, '\x00', 3)
    master_offset = consume_byte(header_str, master_offset, '\x01', 1)
    master_offset = consume_byte(header_str, master_offset, '\x00', 3)
    
    (file_size,) = struct.unpack_from("<I", header_str, offset=master_offset)
    master_offset += struct.calcsize("<I")
    (bin_count, bin_offset) = struct.unpack_from("<II", header_str, offset=master_offset)
    master_offset += struct.calcsize("<II")
            
    for _ in xrange(bin_count):
        (bin_record_count, bin_record_offset) = struct.unpack_from("<II", header_str, offset=master_offset)
        master_offset += struct.calcsize("<II")
        for _ in xrange(bin_record_count):
            (record_hash, record_size, record_offset, zero) = struct.unpack_from("<IIII", header_str, offset=bin_record_offset)
            bin_record_offset += struct.calcsize("<IIII")
            if zero != 0:
                raise ValueError("Required record terminator is non-zero. Actual value is " + str(zero) + ".")
            try:
                name = name_hash_dict[record_hash]
            except KeyError:
                raise ValueError("Name hash " + hex(name_hash) + " was not found in the name hash dictionary.")
            return_dict[name] = (record_offset, record_size)
    return return_dict

def unpack_archive(header, data, basepath):
    """Unpacks the .bdt file data using the .bhd5/.bhd file header.
     
    Recursively creates directories relative to basepath for the unpacked
    files. Prints progress. Returns a list of files created. Automatically
    decompresses .dcx files into their original form.
    """
    
    created_file_list = []
    
    if appears_bhd(header):
        file_dict = parse_bhd_header_to_dict(header)
    elif appears_bhd5(header):
        file_dict = parse_bhd5_header_to_dict(header)
    else:
        raise ValueError("Header file does not match known formats.")

    num_of_files = len(file_dict.keys())
    print "   - Found " + str(num_of_files) + " records in header file."
    
    with open(data, 'rb') as d:
        HEADER_STRING = "BDF307D7R6\x00\x00\x00\x00\x00\x00"
        HEADER_OFFSET = len(HEADER_STRING)
        
        d.seek(0)
        if d.read(HEADER_OFFSET) != HEADER_STRING:
            raise ValueError("Header of data file is missing. Data file is possibly corrupt or malformed.")
        
        count = 0
        for name in file_dict:
            (record_offset, record_size) = file_dict[name]            
            d.seek(record_offset)
            content = d.read(record_size)
            if dcx_uncompresser.appears_dcx(content):
                content = dcx_uncompresser.uncompress_dcx_content(content)
                if name[-4:] == ".dcx":
                    name = name[:-4]
            filename = fix_filename(basepath, name)
            created_file_list.append(filename)
            f = create_file(filename)
            f.write(content)
            f.close()
            
            count += 1
            print "\r   - Unpacking files from archive (" + str(count) + "/" + str(num_of_files) + ")...",
            sys.stdout.flush()
        print "Done."
    
    return created_file_list
