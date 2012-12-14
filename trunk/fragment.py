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



==============================================================================
FRAGMENT REFERENCE
based on Windcatcher's post on the EQEMU forums
==============================================================================

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


Misc
----

0x35 - First Fragment - For some reason every .WLD file I've ever encountered begins with one of these. 
I have no idea why or whether this is necessary.

Textures
--------

0x03 - Texture Bitmap Name(s) - Contains the names of one or more bitmaps used in a particular texture. 
When there is more than one bitmap in the fragment it means that the texture is animated (e.g. water).

0x04 - Texture Bitmap Info - Refers to a 0x03 fragment. Also contains flags to tell the client 
information about this particular texture (normal or animated).

0x05 - Texture Bitmap Info Reference - Refers to a 0x04 fragment so 0x04 fragments can be reused.

0x30 - Texture - Refers to a 0x05 fragment. Contains flags to tell the client information about 
this texture (normal, semitransparent, transparent, masked, etc.) Having this fragment separated from the 0x05 fragment means that the zone can have multiple flavors of the same texture bitmap (e.g. one that is normal, one that is semitransparent, etc.)

0x31 - Texture List - Contains references to all of the 0x30 textures used in the zone 
(or, in the case of placeable objects, in that particular object).


Meshes
------

0x36 - Mesh - Contains vertex, normal, color, and polygon information for a mesh. In the case of zones,
the mesh is a subdivision of the zone. In the case of placeable objects, the mesh contains the 
entire information for the object.

Notes on 0x36 fragment:

1. Fragment1 refers to a 0x31 fragment to tell the client what textures are used.
2. Polygons are sorted by texture index. That is, all polygons in the Data5 area that use a 
    particular texture are grouped together.
3. Fragment2 optionally refers to a 0x2F fragment if the mesh is animated (e.g. trees or flags 
    that sway in the breeze).
4. Fragment4 always refers to the first 0x03 fragment in the file (I have no idea why).
5. I don't fully understand this fragment. The Data6 and Data9 areas have something to do 
    with mob models, but I don't know how they work yet.
6. There are new-format and old-format .WLD files. They have different values in the .WLD header 
    and the main difference is in the 0x36 fragment. In new-format files, the texture coordinate values are signed 32-bit values; in old-format files they're signed 16-bit values. At this time OpenZone only exports old-format files but it would be no great effort to switch it to new-format files.

0x37 - Mesh Animated Vertices - For a given 0x36 fragment, this fragment contains a number of animation "frames". For each frame it contains a complete vertex list that supercedes the vertex list in the 0x36 fragment. For instance, if there are three frames and 15 vertices, there will be three sets of 15 vertex values in the 0x37 fragment and they will be used in lieu of the 15 vertex values in the 0x36 fragment.

0x2F - Mesh Animated Vertices Reference - Refers to a 0x37 fragment so it can be reused (e.g. for flags that all have the same shape but have different textures).


Zones
-----

0x21 - BSP Tree - BSP stands for "binary space partition". Basically the zone is broken up 
    into regions so the client can quickly find polygons that are near the player or mobs for 
    purposes of collision avoidance. Normally this is done along a simple grid, but the zone 
    also has to be broken up so that "special" regions (water, lava, PvP, ambient lighting, and others)
    are distinct.

0x22 - BSP Region - For each node in the BSP tree there is a 0x22 fragment that describes the region.
    It contains information on the region's bounds and an optional reference to a 0x36 fragment if 
    there are polygons in that region. Also contains an RLE-encoded array of data that tells the client
    which regions are "nearby". That way, if a player enters one of the "nearby" regions,
    the client knows that objects in the region are visible to the player. 
    The client does this to know when it has to make sure mobs fall to the ground instead of stay 
    at the spawn points, which might be in midair.

0x1B - Light Source - I suspect this defines the ambient light level in a zone 
    (see "Light sources" below for info).

0x08 - Camera - I don't know what the parameters mean yet.

0x1C - Light Source Reference - See "Light sources" below for info.

0x2A - Ambient Light - Refers to a 0x1C fragment. 
    Contains a list of numbers that refer to the 0x22 fragments in the zone 
    (e.g. if there are 100 0x22 fragments then the numbers will be in the range 0-99). 
    This fragment tells the client which regions have the particular light setting. 
    I suspect that you could conceivably have some regions with one ambient light setting, 
    other regions with another ambient light setting, etc. by having multiple 0x1B-0x1C-0x2A sets.

0x09 - Camera Reference - Refers to a 0x08 fragment. I don't know its purpose.

0x14 - Player Info - I don't know its purpose. Its Fragment1 value seems to use a "magic" string:
    "FLYCAMCALLBACK".

0x16 - Zone Unknown - It's used in zone files for some reason...

0x15 - Object Location - In zone files, this might contain the safe point?

0x29 - Region Flag - This is similar to the 0x2A fragment in that it contains a list of numbers,
    where each number refers to a 0x22 region. It tells the client that those regions are "special". 
    The name of the fragment is "magic" in that it determines how the regions are flagged:

"WT_ZONE" .................... Regions are underwater

"LA_ZONE" ................... Regions are lava

"DRP_ZONE" ................... Regions are PvP areas

"DRNTP##########_ZONE" ....... e.g. DRNTP00025-02698-645.6-00020999_ZONE. 
    This seems to tell the client that these regions constitute a zoneline. 
    If the player enters one of these regions the client knows the player is zoning
    and knows the destination. I don't know if the client makes use of this since 
    I don't think every zone has this at all zone points, but it looks interesting. 
    I don't understand the format of the numbered part of the name.


Mob models
----------

0x12 - Mob Track - I don't know what this does, but I suspect it has to do with mob animation.

0x13 - Mob Track Reference - Refers to a 0x12 fragment.

0x2D - Mesh Reference - Refers to a 0x36 fragment. I don't know its purpose.


Light sources
-------------
0x1B - Light Source - Contains information on light color. I don't know what the other parameters in it mean.

0x1C - Light Source Reference - Refers to a 0x1B fragment.

0x28 - Light Info - Refers to a 0x1C fragment. Contains light position and radius. 
    I don't know what the other parameters mean.


Placeable objects
-----------------
0x32 - Vertex Color - For each object that has been placed, there is one of these 
    (put 100 trees in your zone and there are 100 of these fragments). It contains vertex
    shading information for each object. For example, if you have a torch near some trees, 
    those trees should have their polygons shaded based on the light color, angle of incidence, 
    distance, and any intervening polygons. The EQ client does *not* dyamically shade polygons
    in a zone; all polygons must be shaded in this way (including 0x36 fragments in the main zone file).

0x33 - Vertex Color Reference - Refers to a 0x32 fragment.

0x15 - Object Location - Contains object position, rotation, and size. Refers to a 0x33 fragment. 
    When used in the main zone file, this fragment contains information for the whole zone 
    (see frmMainUnit.pas in the OpenZone source).

0x17 - Polygon Animation? - I don't know what this does. 
    I suspect it has something to do with polygon animation.

0x18 - Polygon Animation Reference? - Refers to a 0x17 fragment. I don't know its purpose.

0x2D - Mesh Reference - Refers to the 0x36 fragment.

0x12 - Object Track - I don't know what this does, but I suspect it has to do with object animation.

0x13 - Object Track Reference - Refers to a 0x12 fragment.

0x10 - Track Set - This seems to be optional for placeable objects. 
    My guess is that it allows a placeable object to have more than one animation track. 
    For each track that is used there is a reference to a 0x13 fragment. 
    There might (though not necessarily) also be a reference to a 0x2D fragment for each track.

0x11 - Track Set Reference - Refers to a 0x10 fragment.

0x14 - Placeable Reference - Fragment1 contains a "magic" string: "SPRITECALLBACK". 
    Data2 contains at least one fragment reference that refers to either a 0x2D or 0x11 fragment. 
    I don't understand what all the parameters in this fragment mean.





'''



import struct, array

import wldfile as WLD

class Fragment():
    def __init__(self, id, type, nameRef, wld):
        self.id = id
        self.type = type
        self.nameRef = nameRef
        self.name = wld.getName(nameRef)
        self.wld = wld
   
    def dump(self):
        f = self
        print 'FRAGMENT id:%i    TYPE: 0x%x    name:%s' % (f.id, f.type, f.wld.getName(self.nameRef))
        
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
            (rgba,) = struct.unpack('<I', buf[offset:offset+4])
            offset += 4
            # print 'RGBA 0x%x' % (rgba)
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
        (f.flags, f.params1, f.params2, f.params3_1, f.params3_2, f.frag05Ref ) = struct.unpack('<iIiffI',  buf[offset:offset+24])
        offset += 24
        # note that we do not read&store the "datapair" that can follow here if Bit 1 of flags is set.
        # Its purpose is unknown anyway currently 
        
    def dump(self):
        Fragment.dump(self)
        f = self
        print 'frag05Ref:%i flags:0x%x params1:0x%x params2:0x%x params3_1:%f params3_2:%f' % \
        (f.frag05Ref, f.flags, f.params1, f.params2, f.params3_1, f.params3_2)

# Mesh - Reference
class Fragment2D(Fragment):
    def __init__(self, id, type, nameRef, wld):
        Fragment.__init__(self, id, type, nameRef, wld)
        
    def decode(self, buf, offset):        
        offset += 12    # skip over generic fragment header first
        f = self
        (f.fragRef, f.flags  ) = struct.unpack('<ii',  buf[offset:offset+8])
        offset += 8
        
    def dump(self):
        Fragment.dump(self)
        f = self
        print 'fragRef:%i flags:0x%x' % (f.fragRef, f.flags)


# Object Location - Reference
class Fragment15(Fragment):
    def __init__(self, id, type, nameRef, wld):
        Fragment.__init__(self, id, type, nameRef, wld)
        
    def decode(self, buf, offset):        
        offset += 12    # skip over generic fragment header first
        f = self
        (f.fragRef, f.flags, f.fragRef1 ) = struct.unpack('<iii',  buf[offset:offset+12])
        offset += 12
        
        # for convenience (and performance) reasons we do the name ref lookup here already
        self.refName = self.wld.getName(self.fragRef)
        
        (self.xpos, self.ypos, self.zpos, self.xrot, self.yrot, self.zrot) = \
            struct.unpack('<ffffff', buf[offset:offset+24])
        offset += 24
        (self.xscale, self.yscale, self.zscale) = \
            struct.unpack('<fff', buf[offset:offset+12])
        offset += 12
        (f.fragRef2, ) = struct.unpack('<i',  buf[offset:offset+4])
        offset += 4
        if f.fragRef2 != 0:
            (f.params2, ) = struct.unpack('<i',  buf[offset:offset+4])
            
        
    def dump(self):
        Fragment.dump(self)
        f = self
        print 'flags:0x:%x fragRef1:%i frag1Name:%s fragRef2:%i' % \
            (f.flags, f.fragRef1, self.refName, f.fragRef1 ) 
        print 'xpos:%f ypos:%f zpos:%f xrot:%f yrot:%f zrot:%f xscale:%f yscale:%f zscale:%f ' % \
            (f.xpos, f.ypos, f.zpos, f.xrot, f.yrot, f.zrot, f.xscale, f.yscale, f.zscale)
        
        
# Static or animated Model (Placeable / Mob)
class Fragment14(Fragment):
    def __init__(self, id, type, nameRef, wld):
        Fragment.__init__(self, id, type, nameRef, wld)
        
    def decode(self, buf, offset):        
        offset += 12    # skip over generic fragment header first
        f = self
        (f.flags, f.fragRef1, f.size1, f.size2, f.fragRef2 ) = struct.unpack('<iiiii',  buf[offset:offset+20])
        offset += 20

        if f.flags & (1 << 0):
            offset += 4         # skip params1 for now if its there
        if f.flags & (1 << 1):
            offset += 4         # same for params2

        for i in range(0, f.size1):
            (size, ) = struct.unpack('<i',  buf[offset:offset+4])
            offset += 4
            offset += size*8    # skip size DATAPAIRS (unknown purpose)

        self.fragRefs3 = []
        for i in range(0, f.size2):
            (fragRef3, ) = struct.unpack('<i',  buf[offset:offset+4])
            self.fragRefs3.append(fragRef3)
            offset += 4

        (size, ) = struct.unpack('<i',  buf[offset:offset+4])
        offset += 4
        offset += size

    def dump(self):
        Fragment.dump(self)
        f = self
        print 'flags:0x%x fragRef1:%i fragRef2:%i size1:%i size2:%i' % (f.flags, f.fragRef1, f.fragRef2, f.size1, f.size2 )
        for i in range(0, f.size2):
            print 'frag ref:%i' % (self.fragRefs3[i])

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
        self.params1 = 0
        self.params2 = 0
        
    def decode(self, buf, offset):        
        offset += 12    # skip over generic fragment header first
        f = self
        (f.flags, f.numRefs ) = struct.unpack('<ii',  buf[offset:offset+8])
        offset += 8
        
        # read optional parameters (according to the flags field)
        if f.flags & (1 << 2):
            (f.params1, ) = struct.unpack('<i',  buf[offset:offset+4])
            offset += 4
        if f.flags & (1 << 3):
            # currently assuming  this is the time in ms between animation updates
            (f.params2, ) = struct.unpack('<i',  buf[offset:offset+4])
            offset += 4

        f.frag03Refs = []
        for i in range(0, f.numRefs):
            (ref,) = struct.unpack('<I',  buf[offset:offset+4])
            offset += 4
            f.frag03Refs.append(ref)
        
    def dump(self):
        Fragment.dump(self)
        f = self

        p1 = 0
        p2 = 0
        
        if f.flags & (1 << 2):
            p1 = f.params1
        if f.flags & (1 << 3):
            p2 = f.params2

        print 'flags:0x%x numRefs:%i params1:%i params2:%i' % (f.flags, f.numRefs, p1, p2)
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

