'''
wldfile

Python .WLD file support for zonewalk

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



-------------------------------------------------------------------------------
WLD REFERENCE:
-------------------------------------------------------------------------------

--------------------
WLD File structure
--------------------
    HEADER              [ 7 * u32 dword = 28 bytes ]
        MAGIC           [ 0x54503D02 ]
        VERSION         [ 0x00015500 or  0x1000C800 ]
        MAX_FRAGMENT    [ dword ]
        UNKNOWN         [ dword ]
        UNKNOWN         [ dword ]
        NAMEHASHLEN     [ dword ]
        UNKNOWN         [ dword ]
    NAMEHASH            [ len = namehashlen ]
    FRAGMENTS           [ n fragments with n = max_fragment + 1 ]


--------------------
Fragments reference
--------------------

Fragment types

0x03 - Texture Bitmap Name(s)
0x04 - Texture Bitmap Info
0x05 - Texture Bitmap Info Reference
0x06 - Two-dimensional Object
0x07 - Two-dimensional Object Reference
0x08 - Camera
0x09 - Camera Reference
0x10 - Skeleton Track Set
0x11 - Skeleton Track Set Reference
0x12 - Mob Skeleton Piece Track
0x13 - Mob Skeleton Piece Track Reference
0x14 - Static or Animated Model Reference/Player Info
0x15 - Object Location
0x16 - Zone Unknown
0x17 - Polygon Animation?
0x18 - Polygon Animation Reference?
0x1B - Light Source
0x1C - Light Source Reference
0x21 - BSP Tree
0x22 - BSP Region
0x28 - Light Info
0x29 - Region Flag
0x2A - Ambient Light
0x2C - Alternate Mesh
0x2D - Mesh Reference
0x2F - Mesh Animated Vertices Reference
0x30 - Texture
0x31 - Texture List
0x32 - Vertex Color
0x33 - Vertex Color Reference
0x35 - First Fragment
0x36 - Mesh
0x37 - Mesh Animated Vertices

Fragment Structures

FRAGMENT
    FRAGLEN             [ dword ]
    FRAGTYPE            [ dword ]
    FRAGNAME            [ dword ]
    FRAGDATA            [ bytes, length = FRAGLEN -4 ]
    
FRAGMENTREFERENCE    
    FRAGINDEX           [ dword, points into the wld fragments table ]
    
'''


import struct, array

Version1WLD = 0x00015500
Version2WLD = 0x1000C800
MagicWLD =  0x54503D02

from fragment import *

        
class WLDFile():
    
    def __init__(self, name):
        self.name = name
        self.filename = name+'.wld'
                
        # xor codes for the simple hash encoder
        self.codes = [0x95, 0x3A, 0xC5, 0x2A, 0x95, 0x7A, 0x95, 0x6A]
        
        self.names = None   # decoded namehash
        self.fragment_decoders = { 
            0x36 : self.decode0x36, 0x03 : self.decode0x03, 0x31 : self.decode0x31,
            0x30 : self.decode0x30, 0x05 : self.decode0x05, 0x04 : self.decode0x04
            }
            
        self.fragment_type_counts = {}
        self.fragments = {}
        
    # this simple hash encoder/decoder is used for the contents of the names string table 
    # (hence its designation as "namehash") and for several other types of data inside the wld
    def decodeBytes(self, bytes):
        for i in range(0, len(bytes)):
            bytes[i] = bytes[i] ^ self.codes[i & 7] 
            
        return bytes
            
    def countFragmentType(self, type):
        if (self.fragment_type_counts.has_key(type)):
            self.fragment_type_counts[type] += 1
        else:
            self.fragment_type_counts[type] = 1
          
    # return a name string from the namehash bytearray
    # nameidx is the position pointer to the start of the name, it's end is marked
    # with a C style 0 byte
    def getName(self, nameidx):
        position = -nameidx
        if position == 0:
            return ''
            
        name = self.names[position:]
        # find the position of 0 byte terminator
        i = 0
        end = 0
        for c in name:
            if c == 0:
                end = i
                break;
            i += 1
         
        name = name[0:end]        
        return str(name)
        
    # -------------------------------------------------------------------------
    # FRAGMENT decoders    
    # we pass in the fragment type and nameRef already decoded in the main fragment reading loop
    # additionaly the original file offset of the fragment is used as fragment ID which 
    # is useful for easy handling of fragment references
    
    def decode0x36(self, id, type, nameRef, buf, offset):
        f = Fragment36(id, type, nameRef, self)
        self.fragments[f.id] = f
        f.decode(buf, offset)
        # f.dump()
    def decode0x31(self, id, type, nameRef, buf, offset):
        f = Fragment31(id, type, nameRef, self)
        self.fragments[f.id] = f
        f.decode(buf, offset)
        # f.dump()
    def decode0x30(self, id, type, nameRef, buf, offset):
        f = Fragment30(id, type, nameRef, self)
        self.fragments[f.id] = f
        f.decode(buf, offset)
        # f.dump()
    def decode0x05(self, id, type, nameRef, buf, offset):
        f = Fragment05(id, type, nameRef, self)
        self.fragments[f.id] = f
        f.decode(buf, offset)
        # f.dump()
    def decode0x04(self, id, type, nameRef, buf, offset):
        f = Fragment04(id, type, nameRef, self)
        self.fragments[f.id] = f
        f.decode(buf, offset)
        # f.dump()
    def decode0x03(self, id, type, nameRef, buf, offset):
        f = Fragment03(id, type, nameRef, self)
        self.fragments[f.id] = f
        f.decode(buf, offset)
        # f.dump()


    # -------------------------------------------------------------------------
    # main loader driver
    def load(self, s3d):
        print 'WLDFile loading ', self.filename, ' from S3D container'
        
        s3dfile =  s3d.getFile(self.filename)
        wld = s3dfile.data
        # print 'total length:', s3dfile.size
        
        # process WLD header
        offset = 0
        (magic, version, max_fragment, dummy1, dummy2, name_hash_len) = struct.unpack('<iiiiii', wld[offset:offset+24])
        offset += 28    # header length = 7 * u32
        
        version &= 0xffffffffe
        if (magic != MagicWLD):
            print 'invalid file magic number, aborting load'
            return
            
        # print 'WLD magic=0x%x version=0x%x max_fragment=%i' % (magic, version, max_fragment)
        if (version == Version1WLD):
            print 'processing version 1 WLD file'
        elif (version == Version2WLD):
            print 'processing version 2 WLD file'
        else:
            return
        
        self.version = version
        
        # process NAMEHASH
        # print 'name_hash length:', name_hash_len
        format = '<'+str(name_hash_len)+'s'
        (name_hash,) = struct.unpack(format, wld[offset:offset+name_hash_len])
        offset += name_hash_len
        
        self.names = self.decodeBytes(bytearray(name_hash))
        # self.names = str(self.names).split('\0')
        # print self.names
        
        # load the FRAGMENTS
        sum_len = 0
        frag_id = 0
        for i in range(0, max_fragment):
            # fragment header
            (fragment_len, fragment_type, fragment_name) = struct.unpack('<iii', wld[offset:offset+12])
            
            # fnam = self.getName(fragment_name)
            # print fnam, len(fnam)
            # print 'fragment len: %i type: 0x%x name:%s' % (fragment_len, fragment_type, fnam )
            
            self.countFragmentType(fragment_type)       # keep some statistics on fragment type counts

            if self.fragment_decoders.has_key(fragment_type):
                func = self.fragment_decoders[fragment_type]
                func(frag_id, fragment_type, fragment_name, wld, offset)
                    
            # fragment data
            sum_len += fragment_len + 8 # add the len and type fields (but not the name field, see below)
            offset += 12                # skip header
            offset += fragment_len-4    # for now simply skip, the fragment length seems to include the name field
                                        # thus we need to subtract 4 
            frag_id += 1                # fragment id is simply its position in the file
        
        # print 'sum of all fragment lengths:', sum_len
        '''
        for k in self.fragment_type_counts.keys():
            print 'fragment type:0x%x count:%i' % (k, self.fragment_type_counts[k])
        '''
        print 'WLDFile load complete.'
        print 'name0:', self.getName(-1)
    
    def getFragment(self, idx_plus_1):
        # Note on fragment references
        # references > 0 are a straight index into our fragments table 
        # references <= 0 are a lot more involved: these have to be converted into
        # namehash references like this: name_idx = (-frag_ref) - 1
        # with this namehash ref we can then lookup the fragment name 
        # finally we need to look through all our fragments to find one with matches the name
        # whoever invented this nonsense should be bitch slapped silly
        if idx_plus_1 > 0:
            return self.fragments[idx_plus_1 - 1]
        
        nameRef = (idx_plus_1)-1
        name = self.getName(nameRef)   # getName() expects a negated index, so we can pass as is
        # print 'named frag reference:', name
        for frag in self.fragments.values():
            if frag.nameRef == nameRef:
                return frag
        
        return None