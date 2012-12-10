'''
fragment

zonewalk wld file fragment processing
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



import struct, array

import wldfile as WLD

class Fragment():
    def __init__(self, id, type, nameRef, wld):
        self.id = id
        self.type = type
        self.nameRef = nameRef
        self.wld = wld
   
    def dump(self):
        f = self
        print 'FRAGMENT id:%i type:0x%x name:%s' % (f.id, f.type, f.wld.getName(self.nameRef))
        
# Mesh Fragment
class Fragment36(Fragment):
    def __init__(self, id, type, nameRef, wld):
        Fragment.__init__(self, id, type, nameRef, wld)
        
    def decode(self, buf, offset):
        f = self
        # print 'DECODING FRAGMENT id:%i type:0x%x name:%s' % (offset, self.type, f.wld.getName(self.nameRef))
        
        # read header data
        offset += 12    # skip over generic fragment header first
        (f.flags, f.fragment1, f.fragment2, f.fragment3, f.fragment4) = struct.unpack('<iiiii',buf[offset:offset+20])
        offset += 20
        (f.centerX, f.centerY, f.centerZ) = struct.unpack('<fff', buf[offset:offset+12])
        offset += 12
        (f.params2_0, f.params2_1, f.params2_2) = struct.unpack('<iii', buf[offset:offset+12])
        offset += 12
        (f.maxDist, f.minX, f.minY, f.minZ, f.maxX, f.maxY, f.maxZ,) = struct.unpack('<fffffff', buf[offset:offset+28])
        offset += 28
        (f.vertexCount, f.texCoordsCount, f.normalsCount, f.colorCount, f.polyCount) = struct.unpack('<hhhhh', buf[offset:offset+10])
        offset += 10
        (f.size6, f.polyTexCount, f.vertexTexCount, f.size9, scale) = struct.unpack('<hhhhh', buf[offset:offset+10])
        offset += 10
    
        f.scale = 1.0/(1<<scale)
    
        # read vertex data
        f.vertexList = []
        for i in range(0, f.vertexCount):
            vdata = struct.unpack('<hhh', buf[offset:offset+6])
            offset += 6
            vertex = array.array('f', (vdata[0]*f.scale, vdata[1]*f.scale, vdata[2]*f.scale) )
            f.vertexList.append(vertex)

        # read texture u,v coordinates: careful, these differ between version 1 and 2 wld file
        self.uvList = []
        recip_255 = 1.0 / 256.0
        if self.wld.version == WLD.Version1WLD:
            for i in range(0, f.texCoordsCount):    
                vdata = struct.unpack('<hh', buf[offset:offset+4])
                offset += 4
                uvdata = array.array('f', (vdata[0]*recip_255, vdata[1]*recip_255))
                self.uvList.append(uvdata)
        if self.wld.version == WLD.Version2WLD:
            for i in range(0, f.texCoordsCount):    
                vdata = struct.unpack('<ff', buf[offset:offset+8])
                offset += 8
                # print vdata[0], vdata[1]
                uvdata = array.array('f', (vdata[0], 0.0-vdata[1]))
                self.uvList.append(uvdata)
        
        # Vertex normals
        f.vertexNormalsList = []
        recip_127 = 1.0 / 127.0
        for i in range(0, f.normalsCount):
            vdata = struct.unpack('<bbb', buf[offset:offset+3])
            offset += 3
            vnormal = array.array('f', (vdata[0]*recip_127, vdata[1]*recip_127, vdata[2]*recip_127) )
            f.vertexNormalsList.append(vnormal)

        # Vertex colors: 32bit rgba
        f.vertexColorsList = []
        for i in range(0, f.colorCount):
            (rgba,) = struct.unpack('<i', buf[offset:offset+4])
            offset += 4
            f.vertexColorsList.append(rgba)
        
        # read polygon data (actually this is a misnomer as the fixed length structure in the wld for these 
        # does only allow triangles; I've kept the naming in order to stay in line with the available documentation)
        f.polyList = []
        for i in range(0, f.polyCount):
            (pflag,) = struct.unpack('<H', buf[offset:offset+2])
            offset += 2
            pverts = struct.unpack('<HHH', buf[offset:offset+6])
            offset += 6
            f.polyList.append(pverts)   # NOTE: we do not store the flags currently!
            
        # skip size6 * 4 bytes (unknown)
        offset += f.size6 *4
        
        # read polygon texture assignments
        # each entry in polyTexList is a tuple: (pcount, texidx)
        # denoting the number of consecutive polygons using texture texidx
        # texidx is the index into the 0x31 texture list fragment 
        f.polyTexList = []
        for i in range(0, f.polyTexCount):
            # pcount is the number of consecutive polygons that use the same texture
            # texidx references the entry in the 0x31 texture list fragment that this mesh uses
            # polygons are grouped by the texture they use and the list here is in the same order
            # therefore assignment is straight forward
            (pcount, texidx) = struct.unpack('<hh', buf[offset:offset+4])
            offset += 4
            f.polyTexList.append((pcount,texidx))
                
    def dump(self):
        Fragment.dump(self)
        f = self
        print 'flags:0x%x frag1:%i frag2:%i frag3:%i frag4:%i' % (f.flags, f.fragment1, f.fragment2, f.fragment3, f.fragment4)
        print 'centerX:%f centerY:%f centerZ:%f ' % (f.centerX, f.centerY, f.centerZ)
        print 'maxDist:%f minX:%f minY:%f minZ:%f maxX:%f maxY:%f maxZ:%f' % (f.maxDist, f.minX, f.minY, f.minZ, f.maxX, f.maxY, f.maxZ)
        print 'vertexCount:%i texCoordsCount:%i normalsCount:%i colorCount:%i polyCount:%i' % (f.vertexCount, f.texCoordsCount, f.normalsCount, f.colorCount, f.polyCount)
        print 'size6:%i polyTexCount:%i vertexTexCount:%i size9:%i scale:%f' % (f.size6, f.polyTexCount, f.vertexTexCount, f.size9, f.scale)


# Texture List
class Fragment31(Fragment):
    def __init__(self, id, type, nameRef, wld):
        Fragment.__init__(self, id, type, nameRef, wld)
        
    def decode(self, buf, offset):        
        offset += 12    # skip over generic fragment header first
        f = self
        (f.flags, f.numNameRefs) = struct.unpack('<ii',  buf[offset:offset+8])
        offset += 8
        self.nameRefs = []
        for i in range(0, f.numNameRefs):
            (nameRef,) = struct.unpack('<I',  buf[offset:offset+4])
            offset += 4
            self.nameRefs.append(nameRef)
            
    def dump(self):
        Fragment.dump(self)
        f = self
        print 'numF30Refs:%i' % (f.numNameRefs)
        for nameRef in f.nameRefs:
            print 'f30Ref:%i' % (nameRef)
        
# Texture Reference
class Fragment30(Fragment):
    def __init__(self, id, type, nameRef, wld):
        Fragment.__init__(self, id, type, nameRef, wld)
        
    def decode(self, buf, offset):        
        offset += 12    # skip over generic fragment header first
        f = self
        (f.flags, f.params1, f.params2, f.params3_1, f.params3_2, f.frag05Ref ) = struct.unpack('<iiiffI',  buf[offset:offset+24])
        offset += 24
        # note that we do not read&store the "datapair" that can follow here if Bit 1 of flags is set.
        # Its purpose is unknown anyway currently 
        
    def dump(self):
        Fragment.dump(self)
        f = self
        print 'frag05Ref:%i flags:0x%x params1:0x%x params2:0x%x params3_1:%f params3_2:%f' % \
        (f.frag05Ref, f.flags, f.params1, f.params2, f.params3_1, f.params3_2)

# Texture Bitmap Info Reference
class Fragment05(Fragment):
    def __init__(self, id, type, nameRef, wld):
        Fragment.__init__(self, id, type, nameRef, wld)
        
    def decode(self, buf, offset):        
        offset += 12    # skip over generic fragment header first
        f = self
        (f.frag04Ref, f.flags  ) = struct.unpack('<Ii',  buf[offset:offset+8])
        offset += 8
        
    def dump(self):
        Fragment.dump(self)
        f = self
        print 'frag04Ref:%i flags:0x%x' % (f.frag04Ref, f.flags)
        
# Texture Bitmap Info
class Fragment04(Fragment):
    def __init__(self, id, type, nameRef, wld):
        Fragment.__init__(self, id, type, nameRef, wld)
        
    def decode(self, buf, offset):        
        offset += 12    # skip over generic fragment header first
        f = self
        (f.flags, f.numRefs ) = struct.unpack('<ii',  buf[offset:offset+8])
        offset += 8
        
        # skip unused params fields if they exist (as indicated by flags)
        if f.flags & (1 << 2):
            offset += 4
        if f.flags & (1 << 3):
            offset += 4

        f.frag03Refs = []
        for i in range(0, f.numRefs):
            (ref,) = struct.unpack('<I',  buf[offset:offset+4])
            offset += 4
            f.frag03Refs.append(ref)
        
    def dump(self):
        Fragment.dump(self)
        f = self
        print 'flags:0x%x numRefs:%i' % (f.flags, f.numRefs)
        for ref in f.frag03Refs:
            print ref

# Texture Bitmap Names        
class Fragment03(Fragment):
    def __init__(self, id, type, nameRef, wld):
        Fragment.__init__(self, id, type, nameRef, wld)
        
    def decode(self, buf, offset):        
        offset += 12    # skip over generic fragment header first
        f = self
        (f.numNames,) = struct.unpack('<i',  buf[offset:offset+4])
        offset += 4
        if f.numNames == 0:
            f.numNames = 1
            
        # print f.numNames
        f.names = []
        for i in range(0, f.numNames):
            (namelen,) = struct.unpack('<H',  buf[offset:offset+2])
            offset += 2
            
            if namelen > 0:
                format = '<'+str(namelen)+'s'
                # print namelen
                # print format
                (namehash,) = struct.unpack(format, buf[offset:offset+namelen])
                offset += namelen
            
                name = f.wld.decodeBytes(bytearray(namehash))             
                
                # strip the C style 0 byte terminator
                j = 0
                end = 0
                for c in name:
                    if c == 0:
                        end = j
                        break;
                    j += 1
                name = str(name[0:end])
                f.names.append(name)
            
    def dump(self):
        Fragment.dump(self)
        f = self
        print 'numNames:%i' % (f.numNames)
        for name in f.names:
            print name

