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

   
class WLDContainer():
    
    # type can be 'zone_obj', 'zone', 'obj' or 'chr'
    def __init__(self, type, zone, wld, s3d):
        self.type = type
        self.name = wld.name
        self.zone = zone
        self.wld_file_obj = wld # the in memory WLDFile object
        self.s3d_file_obj = s3d # the in memory S3DFile object that the wld_file_object was loaded from
        
        self.sprite_list = {}
        self.animated_sprites = []  # Lists those sprites that are animated
        
    # SPRITE LISTS represent the original structure of the 0x31 lists in a wld 
    def getSprite(self, sprite_index, list_index):
        if self.sprite_list.has_key(list_index):
            sprite_list = self.sprite_list[list_index]
            if sprite_list.has_key(sprite_index):
                sprite_list = self.sprite_list[list_index]
                return sprite_list[sprite_index]
        else:
            print 'ERROR invalid sprite list index:%i for sprite:%i in container:%s' % \
                (list_index, sprite_index, self.name)
            
        #if self.sprites.has_key(index):
        #    return self.sprites[index]
        
        return None

    # find the sprite using the texture passed in as a parameter
    def findSpriteUsing(self, t):
        # print 'SEARCHING texture:', t, ' in container:', self.name, ' num lists:', str(len(self.sprite_list))
        for slist in self.sprite_list.values():
            for sprite in slist.values():
                for texture in sprite.textures:
                    # print 'looking at sprite texture:', texture
                    if texture == t:
                        # print 'M A T C H'
                        return sprite
                    
        return None
        
        
class WLDFile():
    
    def __init__(self, name):
        self.name = name
        self.filename = name+'.wld'
                
        # xor codes for the simple hash encoder
        self.codes = [0x95, 0x3A, 0xC5, 0x2A, 0x95, 0x7A, 0x95, 0x6A]
        
        self.names = None   # decoded namehash
        
        self.known_fragments = [ 0x36, 0x31, 0x30, 0x2d, 0x15, 0x14, 0x13, 0x12, 0x11, 0x10, 0x5, 0x4, 0x3 ] 
        self.fragment_type_counts = {}
        self.fragments = {}
        
        self.dump_list = []     # list of fragment types to dump while loading
        
    def setDumpList(self, list):
        self.dump_list = list
        
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
    
    def decodeFragment(self, id, type, nameRef, buf, offset):
        # print type
        fragment = None
        if type == 0x36:
            fragment = Fragment36(id, type, nameRef, self)
        elif type == 0x31:
            fragment = Fragment31(id, type, nameRef, self)
        elif type == 0x30:
            fragment = Fragment30(id, type, nameRef, self)
        elif type == 0x2D:
            fragment = Fragment2D(id, type, nameRef, self)
        elif type == 0x15:
            fragment = Fragment15(id, type, nameRef, self)
        elif type == 0x14:
            fragment = Fragment14(id, type, nameRef, self)
        elif type == 0x13:
            fragment = Fragment13(id, type, nameRef, self)
        elif type == 0x12:
            fragment = Fragment12(id, type, nameRef, self)
        elif type == 0x11:
            fragment = Fragment11(id, type, nameRef, self)
        elif type == 0x10:
            fragment = Fragment10(id, type, nameRef, self)
        elif type == 0x05:
            fragment = Fragment05(id, type, nameRef, self)
        elif type == 0x04:
            fragment = Fragment04(id, type, nameRef, self)
        elif type == 0x03:
            fragment = Fragment03(id, type, nameRef, self)

        fragment.decode(buf, offset)
        self.fragments[fragment.id] = fragment
        if type in self.dump_list:
            fragment.dump()
        

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
            
            if fragment_type in self.known_fragments:
                self.decodeFragment(frag_id, fragment_type, fragment_name, wld, offset)
                
            # fragment data
            sum_len += fragment_len + 8 # add the len and type fields (but not the name field, see below)
            offset += 12                # skip header
            offset += fragment_len-4    # skip to next fragment, the fragment length seems to include the name field
                                        # thus we need to subtract 4 
            frag_id += 1                # fragment id is simply its position in the file
        
        # print 'sum of all fragment lengths:', sum_len
        '''
        for k in self.fragment_type_counts.keys():
            print 'fragment type:0x%x count:%i' % (k, self.fragment_type_counts[k])
        '''
        print 'WLDFile load complete.'
        # print 'name0:', self.getName(-1)
    
    def getFragment(self, idx_plus_1):
        # Note on fragment references
        # references > 0 are a straight index into our fragments table 
        # references <= 0 are more involved: these have to be converted into
        # namehash references like this: name_idx = (-frag_ref) - 1
        # with this namehash ref we can then lookup the fragment name 
        # finally we need to look through all our fragments to find one with matches the name
        # whoever invented this nonsense should be bitch slapped silly
        if idx_plus_1 > 0:
            try:
                return self.fragments[idx_plus_1 - 1]
            except:
                return None
        
        nameRef = (idx_plus_1)-1
        name = self.getName(nameRef)   # getName() expects a negated index, so we can pass as is
        # print 'named frag reference:', name
        for frag in self.fragments.values():
            if frag.nameRef == nameRef:
                return frag
        
        return None
        
    # find a fragment by its name
    # we need to iterate over all our fragments: should this turn out to be too slow
    # we need to implement a name directory that gets filled with data when we decode 
    # our fragments initially
    def getFragmentByName(self, name):
        for f in self.fragments.values():
            if f.name == name:
                return f
                
        return None
        