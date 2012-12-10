'''
s3dfile

Python .S3D file support for zonewalk
(c) gsk 2012


Copyright (c) 2012, Gedolian Soft Kram
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided 
that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this list of conditions 
    and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions 
    and the following disclaimer in the documentation and/or other materials provided with the distribution.
    Neither the name of the <ORGANIZATION> nor the names of its contributors may be used to endorse or 
    promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, 
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY 
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


'''

import sys
import struct
import zlib
from operator import attrgetter

class S3DDirEntry():
    
    def __init__(self):
        self.SIZE = 12
        
        # these are loaded from the disk file ( see unpack() below)
        self.crc = 0                          # u32 filename CRC calculated using the IEEE 802.3 Ethernet CRC-32 algorithm 
        self.data_offset = 0               # u32 offset into the compressed data loaded from the s3d file
        self.data_length_inflated = 0   # u32 length of data once inflated

    def unpack(self, data, start):
        (self.crc, self.data_offset, self.data_length_inflated) = struct.unpack('<III', data[start:start+self.SIZE])
        
        
class S3DFileEntry():

    def __init__(self):
        self.filename = None
        self.size = 0
        self.data = ''
        
        
class S3DFile():

    def __init__(self, filename):
        self.name = filename
        self.direntries = []
        self.fileentries = []
        self.files_by_name = {}
        
    def load(self):
        s3dfile_name = self.name+'.s3d'
        # print 'loading zone s3dfile: ' + s3dfile_name
        
        s3dfile = None
        try:
            s3dfile = open(self.name+'.s3d', 'rb')
        except:
            return -1
            
        s3d_data = s3dfile.read()
        s3dfile.close()
        
        # S3D HEADER
        # extract header data: 12 bytes containing 
        # u32 diroffset 
        # 4 bytes string magic cookie
        # u32 unknown_always_131072
        (diroffset, cookie, unknown) = struct.unpack('<I4sI', s3d_data[0:12])
        # print 'directory offset:', str(diroffset), ' magic:', cookie, ' unknown_131072: ', str(unknown)

        # S3D Directory Entries
        # get number of directory entries: stored as a 32 bit int at diroffset
        (num_direntries,) = struct.unpack('<i', s3d_data[diroffset:diroffset+4])
        # print 'number of directory entries in the s3d file:', str(num_direntries), ', loading ...'
        
        # load all directory entries: these are sorted by the filename crc
        diroffset += 4
        dirent = []
        for i in range(0, num_direntries):
            dir = S3DDirEntry()
            dir.unpack(s3d_data, diroffset)
            dirent.append(dir)
            # print 'direntry: crc=', str(dir.crc), ' data_offset=', str(dir.data_offset), ' inflated_length=', str(dir.data_length_inflated)
            diroffset += dir.SIZE
                
        # change sort key to data_offset so that this matches the file names listing and then store
        self.direntries = sorted(dirent, key=attrgetter('data_offset'))
        
        # now assemble the files from data blocks we loaded from the s3d file
        high_offset = 0
        file_listing_entry = None
        
        for dir in self.direntries:
            # print 'processing direentry with crc=', dir.crc
            
            entry = S3DFileEntry()
            self.fileentries.append(entry)
            
            # read the data blocks for this directory entry: each block consists of a block header followed by the compressed block data
            offset = dir.data_offset

            # we need to remember the highest offset we encounter because the last directory object in the file is the file name listing
            # which we'll need a bit further below
            if (offset > high_offset): 
                high_offset = offset   
                file_listing_entry = entry
                
            inflated_length_read = 0
            n_blocks = 0
            while inflated_length_read < dir.data_length_inflated:
                # S3D BLOCK HEADER: get block header data
                (deflated_length, inflated_length) = struct.unpack('<ii', s3d_data[offset:offset+8])
                offset += 8
                # print 'block', str(n_blocks), ' deflated_length=', str(deflated_length), ' inflated_length=', str(inflated_length)

                # get the block data and inflate: note that we actually just extract a string variable containing the original binary and still z compressed data here
                # in order to actually use them,  these need to be a.) decompressed and b.) unmarshalled (using struct.unpack) in case of numbers
                # see the treatment of the filename lengths inside the filename listing code further below
                format = '<'+str(deflated_length)+'s'
                (blockdata,) = struct.unpack(format, s3d_data[offset:offset+deflated_length])
                entry.data = entry.data+zlib.decompress(blockdata)   # decompress & store
                
                offset += deflated_length
                inflated_length_read += inflated_length
                entry.size += inflated_length
                n_blocks += 1
                
        # load the file listing which is contained in the entry with the highest offset (at the end of the disk file)
        # We have stored this last file entry into file_listing_entry in the decompress loop above
        # the listing itself. as it appears in the S3D file, is sorted by data_offset of the underlying files
        data = file_listing_entry.data
        (n_filenames,) = struct.unpack('<i', data[0:4])
        # print 'number of file names in file listing:', str(n_filenames), ', loading ...'
        
        offset = 4
        for i in range(0, n_filenames):
            # each entry here is a u32 length field followed by the filename string (including a superfluous C style NULL terminator)
            (name_len,) = struct.unpack('<i', data[offset:offset+4])
            offset += 4
            # print 'name_len:', name_len

            format = '<'+str(name_len-1)+'s'
            (filename,) = struct.unpack(format, data[offset:offset+name_len-1])     # strip the \0 terminator
            offset += name_len

            self.fileentries[i].filename = filename
            self.files_by_name[filename] = self.fileentries[i]      # insert into filename keyed directory for easy retrieval
            
            # print 'filename:', filename, ' for file with size:', self.fileentries[i].size
            
        print 'S3DFile load complete.'
        # self.dump_listing()       
        return 0
            
    def getFile(self, name):
        try:
            file = self.files_by_name[name.lower()]
            return file
        except:
            return None
        
    def dumpListing(self):
        n_entries = len(self.fileentries)
        for i in range(0, n_entries):
            f = self.fileentries[i]
            d = self.direntries[i]
            print 'file:', f.filename,  ' size:', f.size
   
# ------------------------------------------------------------------------------
# main
#
# can use this module standalone as an s3d directory dump tool
# ------------------------------------------------------------------------------



def main():
    fname = sys.argv[1]
    print 'loading', fname
    f = S3DFile(fname)
    f.load()
    f.dumpListing()

if __name__ == "__main__":
    main()

    
    