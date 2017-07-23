import struct
import zlib
import sys
import os

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
    
def appears_dcx(content):
    """Checks if the magic bytes at the start of content indicate that it
    is a .dcx file.
    """
    return content[0:4] == "DCX\x00"
   
def uncompress_dcx_content(content):
    """Decompress the file content from a .dcx file. Returns the uncompressed
    content. Raising ValueError if the header does not match the required format.
    """
    master_offset = 0
    master_offset = consume_byte(content, master_offset, 'D', 1)
    master_offset = consume_byte(content, master_offset, 'C', 1)
    master_offset = consume_byte(content, master_offset, 'X', 1)
    master_offset = consume_byte(content, master_offset, '\x00', 1)
    
    (req_1,) = struct.unpack_from("<I", content, offset=master_offset)
    master_offset += struct.calcsize("<I")
    (req_2, req_3, req_4) = struct.unpack_from(">III", content, offset=master_offset)
    master_offset += struct.calcsize(">III")
    if req_1 != 0x100:
        raise ValueError("Expected DCX header int 0x100, but received " + hex(req_1))
    if req_2 != 0x18:
        raise ValueError("Expected DCX header int 0x18, but received " + hex(req_2))
    if req_3 != 0x24:
        raise ValueError("Expected DCX header int 0x24, but received " + hex(req_3))
    if req_4 != 0x24:
        raise ValueError("Expected DCX header int 0x24, but received " + hex(req_4))
    
    (header_length,) = struct.unpack_from(">I", content, offset=master_offset)
    master_offset += struct.calcsize(">I")
    
    master_offset = consume_byte(content, master_offset, 'D', 1)
    master_offset = consume_byte(content, master_offset, 'C', 1)
    master_offset = consume_byte(content, master_offset, 'S', 1)
    master_offset = consume_byte(content, master_offset, '\x00', 1)
    
    (uncomp_size, comp_size) = struct.unpack_from(">II", content, offset=master_offset)
    master_offset += struct.calcsize(">II")
    
    master_offset = consume_byte(content, master_offset, 'D', 1)
    master_offset = consume_byte(content, master_offset, 'C', 1)
    master_offset = consume_byte(content, master_offset, 'P', 1)
    master_offset = consume_byte(content, master_offset, '\x00', 1)
    master_offset = consume_byte(content, master_offset, 'D', 1)
    master_offset = consume_byte(content, master_offset, 'F', 1)
    master_offset = consume_byte(content, master_offset, 'L', 1)
    master_offset = consume_byte(content, master_offset, 'T', 1)
    
    # Skip the portion of the header whose meaning is unknown.
    master_offset += 0x18
    master_offset = consume_byte(content, master_offset, 'D', 1)
    master_offset = consume_byte(content, master_offset, 'C', 1)
    master_offset = consume_byte(content, master_offset, 'A', 1)
    master_offset = consume_byte(content, master_offset, '\x00', 1)
    (comp_header_length,) = struct.unpack_from(">I", content, offset=master_offset)
    master_offset += struct.calcsize(">I")
    
    master_offset = consume_byte(content, master_offset, '0x78', 1)
    master_offset = consume_byte(content, master_offset, '0xDA', 1)
    comp_size -= 2  # The previous two bytes are included in the compressed data, for some reason.
    
    decomp_obj = zlib.decompressobj(-15)
    return decomp_obj.decompress(content[master_offset:master_offset + comp_size], uncomp_size)
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: " + str(sys.argv[0]) + " <DCX File>"
    else:
        filename = sys.argv[1]
        if filename[-4:] == ".dcx":
            uncomp_filename = filename[:-4]
        else:
            uncomp_filename = filename + ".undcx"
        with open(filename, "rb") as f, open(uncomp_filename, "wb") as g:
            file_content = f.read()
            g.write(uncompress_dcx_content(file_content))
            g.close()
            
    

    
    
     

