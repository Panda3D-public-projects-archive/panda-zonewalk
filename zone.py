'''
zone

zone management 
(c) gsk 2012


Copyright (c) <2012>, <gsk>
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


import struct
import zlib

from panda3d.core import Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles, GeomNode, CullFaceAttrib
from panda3d.core import PNMImage, Texture, StringStream
from panda3d.core import PandaNode, NodePath

from s3dfile import S3DFile
from wldfile import WLDFile
from ddsfile import DDSFile


# The PolyGroup defines a submesh in which all polygons use the same texture
# Each PolyGroup is mapped directly to a Panda3D NodePath which gets the texture assigned
class PolyGroup():
    
    # vdata is the Panda3D vertex data object created by the main Mesh
    def __init__(self, vdata):
        self.vdata = vdata      # vertex data, passed in from parent mesh
        
        self.name = 'blah'
        self.geom = Geom(self.vdata)
        self.primitives = GeomTriangles(Geom.UHStatic)
        self.geom.addPrimitive(self.primitives)
        
        
    def build(self, zone, f, start_index, n_polys, tex_idx):
        polyList = f.polyList
        poly_idx = start_index
        for poly in range(0, n_polys):
            p = polyList[poly_idx]
            poly_idx += 1
            self.primitives.addVertices(p[0], p[1], p[2])

        self.node = GeomNode(self.name)
        self.node.addGeom(self.geom)
        # attach all our nodes under the zone's geometry root node
        self.nodePath = zone.rootNode.attachNewNode(self.node)
        
        # self.nodePath.setRenderModeWireframe()
        # Texture setup
        # self.nodePath.setRenderModeFilled()
        # self.nodePath.showBounds()
        
        self.nodePath.setPos(f.centerX, f.centerY,f.centerZ)    # translate to correct world position
        self.nodePath.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))

        # Texture setup
        sprite = zone.getSprite(tex_idx)
        if sprite != None:
            # sprite.dump()
            t = sprite.textures[0]
            self.nodePath.setTexture(t)
        else:
            pass
            # print 'Error: texture (idx=%i) not found. PolyGroup will be rendered untextured' % (tex_idx)
        
         
     
        
class Mesh():

    def __init__(self, name):
        self.name = name
        self.poly_groups = []
        
        # GeomVertexFormats
        #
        # GeomVertexFormat.getV3cpt2()  - vertex, color, uv
        # GeomVertexFormat.getV3t2()    - vertex, uv
        # GeomVertexFormat.getV3c4()    - vertex, color
        # GeomVertexFormat.getV3n3t2()  - vertex, normal, uv
        # GeomVertexFormat.getV3n3cpt2()- vertex, normal, rgba, uv
        
        self.vdata = GeomVertexData(name,GeomVertexFormat.getV3n3cpt2(), Geom.UHStatic)
        
        self.vertex = GeomVertexWriter(self.vdata, 'vertex')
        self.vnormal = GeomVertexWriter(self.vdata, 'normal')
        self.color = GeomVertexWriter(self.vdata, 'color')
        self.texcoord = GeomVertexWriter(self.vdata, 'texcoord')
        
        
    # f is a 0x36 mesh fragment (see fragment.py for reference)
    def buildFromFragment(self, f, zone):
        # write vertex coordinates
        for v in f.vertexList:
            self.vertex.addData3f(v[0], v[1], v[2])

        # write vertex colors
        for rgba in f.vertexColorsList:
            self.color.addData1f(rgba)

        # write vertex normals
        for v in f.vertexNormalsList:
            self.vnormal.addData3f(v[0], v[1], v[2])
            
        # write texture uv
        for uv in f.uvList:
            self.texcoord.addData2f(uv[0], uv[1])
            
        # Build PolyGroups
        # each polyTexList is a tuple containing a polygon count and the texture index for those polys        
        # we create a PolyGroup for each of these
        # the PolyGroup creates all Polygons sharing a texture and adds them under a NodePath
        poly_idx = 0
        for pt in f.polyTexList:
            pg = PolyGroup(self.vdata)
            self.poly_groups.append(pg)
            
            n_polys = pt[0]
            tex_idx = pt[1]
            
            # pass fragment so that it can access the SPRITES
            pg.build(zone, f, poly_idx, n_polys, tex_idx)
            poly_idx += n_polys            
        
        if poly_idx != f.polyCount or poly_idx != len(f.polyList):
            print 'ERROR: polycount mismatch'
            
        
class Sprite():
    
    def __init__(self, name, idx):
        self.name = name
        self.index = idx
        self.numtex = 0
        
        self.current_texture = 0
        
        self.texnames = []
        self.textures = []
        
    def addTexture(self, texname, texture):
        self.texnames.append(texname)
        self.textures.append(texture)
        self.numtex += 1
        
    def dump(self):
        print 'SPITE: %s index:%i numtex:%i' % (self.name, self.index, self.numtex)
        for name in self.texnames:
            print name

    
class Zone():

    def __init__(self, world, name, basedir):
        self.world = world
        self.name = name
        self.basedir = basedir
        
        self.world.consoleOut('zone initializing: '+self.name)
        
        self.textures = {}      # dictionary of panda3d Texure() objects, indexed by texture name
        self.sprites = {}       # SPRITE objects (1-n multitexture groups), indexed by 0x31 fragment index number
                                # as referenced in our meshes
        self.meshes = []
        
        self.rootNode = NodePath(PandaNode("zone_root"))
        self.rootNode.reparentTo(render)
        
    def update(self):
        pass
        
    def getSprite(self, index):
        if self.sprites.has_key(index):
            return self.sprites[index]
        
        return None
            
    def prepareZoneMesh(self):
        
        # load the 0x36 bsp region fragments (sub meshes): all these meshes together
        # make up the main zone geometry
        for f in self.wldZone.fragments.values():
            if f.type == 0x36:
                # print 'adding fragment_36 to main zone mesh'
                # f.dump()
                m = Mesh(self.name)
                m.buildFromFragment(f, self)
                self.meshes.append(m)
                    
    # dump .bmp file header info
    def dumpBMPInfo(self, bm):
        (magic, size, dummy, offset) = struct.unpack('<2siii', bm[0:14])
        print 'bmp magic:%s size:%i offset:%i' % (magic, size, offset)
        
        (biSize, biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage, dummy1, dummy2, biClrUsed, biClrImportant) = \
        struct.unpack('<iIIhhiiIIii', bm[14:14+40])
        print 'biSize:%i biWidth:%i biHeight:%i biPlanes:%i biBitcount:%i biCompression:%i biSizeImage:%i biClrUsed:%i biClrImportant:%i' % \
        (biSize, biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage, biClrUsed, biClrImportant)
        
    # Panda3D's PNImage loader cant deal with bmp files that have limited size palettes
    # it only can process full size palletes (1024 bytes)
    # Here we patch up the Bitmap header of a bmp from a s3d file to prepare it for extending the palette
    # to the full size.
    # NOTE that we dont touch the data in the bitmap info header (biSizeImage and biClrUsed in particular)
    # so in effect the headers we produce here are corrupt
    # The PNImage loader accepts the files though (more proof that it doesnt even correctly evaluate the header
    # but simply assumes a std 1024 bytes pallete (and thus the std. 14+40+1024 = 1078 bytes offset)

    def patchBmHeader(self, bm, new_offset):
        (magic, size, dummy, offset) = struct.unpack('<2siii', bm[0:14])       
        (biSize, biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage, dummy1, dummy2, biClrUsed, biClrImportant) = \
        struct.unpack('<iIIhhiiIIii', bm[14:14+40])

        size_diff = offset - new_offset
        new_size = size + size_diff

        bm_hdr = struct.pack('<2siii', magic, new_size, dummy, new_offset)       
        bm_info_hdr = struct.pack('<iIIhhiiIIii', biSize, biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage, dummy1, dummy2, biClrUsed, biClrImportant)
        new_bm_hdr = bm_hdr + bm_info_hdr
        self.dumpBMPInfo(new_bm_hdr)
        return new_bm_hdr
        
    # some of the ancient texture files in the old s3d archives even use short color tables
    # (not the standard 256*4 = 1024 bytes). Panda3D's PNImage loader barfs on these. 
    # Patch them up here
    def checkBmp(self, bm, name):
        (magic, size, dummy, offset) = struct.unpack('<2siii', bm[0:14])
        if offset != 1078:  # the "normal" offset for a palletized 8 bit image (1024 palette+54 header)
            print 'Patching up Panda3D incompatible .bmp texture:', name
    
            color_table = bm[54:offset]     # extract original color table
            image_data = bm[offset:size]    # extract original image data
            
            hdr = self.patchBmHeader(bm, 1078)  # fix up the bitmap header
            new_bm = hdr + color_table + str(bytearray(1078-offset)) + image_data # assemble new bmp
        else:
            new_bm = bm     # leave it as is
            
        return new_bm
        
    # Parameter f is a 0x03 type texture file definition fragment
    def loadTexture(self, f):
        # Note that we reference the texture files by name. The loader here
        # loads textures only if they are not already in the dictionary. 
        
        # this currently only supports the .bmp files I found in the old (pre GOD?) s3d zone files
        texname = self.wldZone.getName(f.nameRef)
        
        # In typical windows style we'll encounter all types of mixed case names, even spelled
        # differently in various fragments within the same file: Once again we simply enforce all lower case
        # before using the name as a key
        # This works by the assumption that texture names are unique 
        # (and also case insensitive as s3d.getFile() enforces lower case on all names)
        texname = texname.lower()
        
        if not self.textures.has_key(texname):
            # print 'loading texture:', texname
            s3dentry = self.s3d.getFile(texname+'.bmp')
            if s3dentry == None:
                s3dentry = self.s3d.getFile(texname+'.dds')
                
            if s3dentry != None:
                texfile = s3dentry.data
                (magic,) = struct.unpack('<2s', texfile[0:2])
                if magic == 'BM':
                    # Generic BMP file
                    # self.dumpBMPInfo(texfile)
                    texfile = self.checkBmp(texfile, texname)
                    if texfile == None:
                        return
                    
                    ts = StringStream(texfile)  # turn into an istream
                    ti = PNMImage()             # create panda3d general purpose image object
                    ti.read(ts)                 # load from istream
                    
                    t = Texture()               # create texture object
                    t.load(ti)                  # load texture from pnmimage
                    self.textures[texname] = t  # and finally store
                elif magic == 'DD':
                    # DDS file
                    dds = DDSFile(texfile)
                    dds.patchHeader()
                    # dds.dumpHeader()
                    # dds.uncompressToBmp()
                    # dds.save(texname+'.dds')
                    
                    ts = StringStream(dds.buf)  # turn into an istream                   
                    t = Texture()               # create texture object
                    t.readDds(ts)               # load texture from dds ram image
                    self.textures[texname] = t  # and finally store
                else:
                    print 'Error unsupported texture: %s magic:%s referenced in fragment: %i' % (texname, magic, f.id)
            else:
                print 'Error: texture %s not found in s3d archive' % (texname)
            
        
    def prepTextureName(self, name):
        n = name.lower()
        i = name.find('.')
        if i != -1:
            n = n[0:i]
            
        return n
        
    def preloadTextures(self):
        # loop over all 0x03 fragments and load all referenced texture files from the s3d
        f31 = None
        for f in self.wldZone.fragments.values():
            if f.type == 0x03:
                self.loadTexture(f)
            if f.type == 0x31:
                f31 = f         # we'll need this one below 
                
        # create the SPRITE objects: these can reference a single texture or
        # a list of them (for animated textures like water, lava etc.)
        # we need to step through all entries of the 0x31 list fragment for the zone
        # We store the SPRITEs using their index within the 0x31 fragments list as the key
        # because this is exactly how the meshes (0x36 fragments) reference them
        idx = 0
        for ref30 in f31.nameRefs:
            sprite_error = 0
            sprite = None
            # print ref30
            f30 = self.wldZone.getFragment(ref30)
            material_name = self.wldZone.getName(f30.nameRef)
            
            # f30.dump()
            # print 'looking up 0x05 fragment with id_plus_1:', f30.frag05Ref
            
            # Note that there are frag05Refs inside some 0x30 fragments with value <=0 
            # these named references seem to point directly to 0x03 texture fragments
            # instead of the usual indirection chain  0x05->0x04->0x03
            # in some instances these point nowhere meaningful at all though. Need to catch all these
            frag = self.wldZone.getFragment(f30.frag05Ref)
            if frag != None:
                if frag.type == 0x03:    # this is a direct 0x03 ref (see note above)
                    f03 = frag
                    texfile_name = self.prepTextureName(f03.names[0])
                    # print texfile_name
                    if self.textures.has_key(texfile_name):
                        # we dont have a sprite def (0x04) for these, so we use the material (0x30) name
                        sprite = Sprite(material_name, idx)
                        sprite.addTexture(texfile_name, self.textures[texfile_name]) 
                    else:
                        sprite_error = 1
                        print 'Error in Sprite:', material_name, 'Texure not found:', texfile_name                        
                elif frag.type == 0x05:
                    f05 = frag
                    # f05.dump()
                    f04 = self.wldZone.getFragment(f05.frag04Ref)
                    # f04.dump()

                    name = self.wldZone.getName(f04.nameRef)
                    sprite = Sprite(name, idx)
                    for f03ref in  f04.frag03Refs:
                        f03 = self.wldZone.getFragment(f03ref)
                        # f03.dump()
                        # NOTE that this assumes the zone 0x03 fragments only ever reference one single texture
                        texfile_name = self.prepTextureName(f03.names[0])
                        # print texfile_name
                        if self.textures.has_key(texfile_name):
                            sprite.addTexture(texfile_name, self.textures[texfile_name]) 
                        else:
                            sprite_error = 1
                            print 'Error in Sprite:', name, 'Texure not found:', texfile_name
                else:
                    sprite_error = 1
                    print 'Error in Material:%s. Texture ref in 0x30 frag is not type 0x5 or 0x3 but 0x%x' % (material_name, frag.type)
                    print 'F30 DUMP:'
                    f30.dump()
                    print 'Referenced Fragment DUMP:'
                    frag.dump()
                    
            else:
                sprite_error = 1
                print 'Error in Sprite: could not resolve frag05ref:%i in 0x30 fragment:%i' % (f30.frag05Ref, f30.id)

            if sprite_error != 1:   # only add error free sprites
                # sprite.dump()
                self.sprites[idx] = sprite
                
            idx += 1    # need to increment regardless of whether we stored or not
                        # so that the index lookup using the refs in the 0x36's works
                
                
    def load(self):
        s3dfile_name = self.name+'.s3d'
        self.world.consoleOut('zone loading zone s3dfile: ' + s3dfile_name)
        
        self.s3d = S3DFile(self.basedir+self.name)
        if self.s3d.load() != 0:
            self.world.consoleOut( 'ERROR loading s3dfile:' + self.basedir+s3dfile_name)
            return -1
            
        # self.s3d.dumpListing()
        
        self.wldZone = WLDFile(self.name)
        self.wldZone.load(self.s3d)

        self.world.consoleOut('zone preloading textures')
        self.preloadTextures()
        self.world.consoleOut( 'zone preparing zone mesh')
        self.prepareZoneMesh()

        # let Panda3D attempt to flatten the zone geometry (reduce the excessive
        # Geom count resulting from the layout of the .wld zone data as a huge
        # bunch of tiny bsp regions)
        self.world.consoleOut('flattening zone mesh geom tree')
        self.rootNode.flattenStrong()    
        
        return 0
