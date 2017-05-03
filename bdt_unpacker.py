import os
import sys
import struct

import name_hash_handler

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

def parse_header_to_dict(header):
    """Parses a .bhd5 Dark Souls archive header file into a dictionary
     that indexes files in a .bdt Dark Souls archive file.
     
    Returns a dictionary whose keys are hashed filepaths, and whose
     elements are tuples (offset, length) that determine the binary
     data of that file inside the associated .bdt file.
    """
    
    with open(header, 'rb') as h:
        header_str = h.read()
    hash_table = {}
    
    BIN_SIZE = struct.calcsize("<II")
    
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
            hash_table[record_hash] = (record_offset, record_size)
    return hash_table

def unpack_archive(header, data, basepath):
    """Unpacks the .bdt file data using the .bhd5 file header.
     
    Recursively creates directories relative to basepath for the unpacked
    files. Prints progress.
    """
    
    hash_table = parse_header_to_dict(header)
    num_of_files = len(hash_table.keys())
    print "   - Found " + str(num_of_files) + " records in header file."
    
    name_hash_dict = name_hash_handler.build_name_hash_dict()
    
    with open(data, 'rb') as d:
        HEADER_STRING = "BDF307D7R6\x00\x00\x00\x00\x00\x00"
        HEADER_OFFSET = len(HEADER_STRING)
        
        d.seek(0)
        if d.read(HEADER_OFFSET) != HEADER_STRING:
            raise ValueError("Header of data file is missing. Data file is possibly corrupt or malformed.")
        
        count = 0
        for name_hash in hash_table:
            try:
                name = name_hash_dict[name_hash]
            except KeyError:
                raise ValueError("Name hash " + hex(name_hash) + " was not found in the name hash dictionary.")
            f = create_file(fix_filename(basepath, name))
            (record_offset, record_size) = hash_table[name_hash]
            d.seek(record_offset)
            f.write(d.read(record_size))
            f.flush()
            f.close()
            count += 1
            print "\r   - Unpacking files from archive (" + str(count) + "/" + str(num_of_files) + ")...",
            sys.stdout.flush()
        print "Done."
    
    return
