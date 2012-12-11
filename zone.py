'''
zone

zone management 
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


import struct
import zlib

from panda3d.core import Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles, GeomNode, CullFaceAttrib
from panda3d.core import PNMImage, Texture, StringStream
from panda3d.core import PandaNode, NodePath, TextureAttrib, TransparencyAttrib, ColorAttrib
from panda3d.core import Vec4 

from s3dfile import S3DFile
from wldfile import WLDFile
from ddsfile import DDSFile


# The PolyGroup defines a submesh in which all polygons use the same texture
# Each PolyGroup is mapped directly to a Panda3D NodePath which gets the texture assigned
class PolyGroup():
    
    # vdata is the Panda3D vertex data object created by the main Mesh
    def __init__(self, vdata, tex_idx):
        self.vdata = vdata      # vertex data, passed in from parent mesh
        
        self.name = 'PolyGroup_'+str(tex_idx)
        self.geom = Geom(self.vdata)
        self.primitives = GeomTriangles(Geom.UHStatic)
        self.geom.addPrimitive(self.primitives)
        
    # called by the sprite animation code to let us know we need to change our texture image
    def animFrameChange(self, t):
        return 
        # print 'POLYGROUP ANIMATION UPDATE'
        self.nodePath.setTexture(t, 1)
            
                
    def build(self, zone, f, start_index, n_polys, tex_idx):

        sprite = zone.getSprite(tex_idx)
            
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
        # self.nodePath.setRenderModeFilled()
        # self.nodePath.showBounds()
        
        self.nodePath.setPos(f.centerX, f.centerY,f.centerZ)    # translate to correct world position
        
        self.nodePath.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
        # self.nodePath.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullClockwise))

        # Texture setup
        if sprite != None:
            # sprite.dump()
            if sprite.numtex > 0:   
                t = sprite.textures[0]
                self.nodePath.setTexture(t)
        else:
            print 'Error: texture (idx=%i) not found. PolyGroup will be rendered untextured' % (tex_idx)

        return 1
        
              
        
class Mesh():

    def __init__(self, name):
        self.name = name
        self.poly_groups = []
        
        # GeomVertexFormats
        #
        # GeomVertexFormat.getV3cpt2()  - vertex, color, uv
        # GeomVertexFormat.getV3t2()    - vertex, uv
        # GeomVertexFormat.getV3cp()    - vertex, color
        # GeomVertexFormat.getV3n3t2()  - vertex, normal, uv
        # GeomVertexFormat.getV3n3cpt2()- vertex, normal, rgba, uv
        
        # textured
        self.vdata = GeomVertexData(name, GeomVertexFormat.getV3n3cpt2(), Geom.UHStatic)
        
        # plain color filled polys
        # self.vdata = GeomVertexData(name, GeomVertexFormat.getV3cp(), Geom.UHStatic)
        
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
            '''
            r = (rgba & 0xff000000) >> 24
            g = (rgba & 0x00ff0000) >> 16
            b = (rgba & 0x0000ff00) >> 8
            a = (rgba & 0x000000ff)
            if a != 0:
                print 'vertex color has alpha component, r:0x%x g:0x%x b:0x%x a:0x%x ' % (r, g, b, a)
            '''    
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
            n_polys = pt[0]
            tex_idx = pt[1]

            pg = PolyGroup(self.vdata, tex_idx)
                        
            # pass fragment so that it can access the SPRITES
            if pg.build(zone, f, poly_idx, n_polys, tex_idx) == 1:
                self.poly_groups.append(pg)

            poly_idx += n_polys            
        
        if poly_idx != f.polyCount or poly_idx != len(f.polyList):
            print 'ERROR: polycount mismatch'
            
        
class Sprite():
    
    def __init__(self, name, idx, params1):
        self.name = name
        self.index = idx
        self.params1 = params1
        
        self.alpha = 0.4      # default transparency alpha applied to semi transparent textures

        if self.params1 & 0x00000004:
            self.transparent = 1
        else:
            self.transparent = 0

        if not self.params1 & 0x80000000:
            self.transparent = 1
            self.alpha = 0.0         # these are completely transparent (=invisible)
        
        self.numtex = 0             # number of texture images (for multi textures or animated textures)
        self.anim_delay = 0         # delay (in ms) between animation frame switches
        self.current_texture = 0    # current animation frame
        
        self.texnames = []
        self.textures = []
        
        self.anim_render_states = [] # animated textures: render states of geoms (after flattening)referencing us
                            
                            
    def update(self):
        # print 'SPRITE ANIMATION UPDATE'
        # update frame
        self.current_texture += 1
        if self.current_texture == self.numtex:
            self.current_texture = 0
            
        t = self.textures[self.current_texture]
        
        # gnr is a tuple (see addAnimGeomRenderState() below)
        for gnr in self.anim_render_states:
            geom_node = gnr[0]
            geom_number = gnr[1]
            render_state = gnr[2]

            # geom_render_state = geom_node.getGeomState(geom_number)              
            # print geom_render_state
            # attr = geom_render_state.getAttrib(26)  # attrib 26 is the texture attribute (hope this is static)
            # print attr
            # tex = attr.getTexture()

            # do the texture switch on the geom level by setting the TextureAttrib on its RenderState
            ta = TextureAttrib.make(t)
            new_state = render_state.setAttrib(ta, 1) # potentialy needs passing "int override" (=1?) as second param          
            geom_node.setGeomState(geom_number, new_state)
            
    # store render states passed in here for use in the texture animation frame update loop
    # input is a tuple of (geom_node, geom_number, render_states)
    def addAnimGeomRenderState(self, g):
        self.anim_render_states.append(g)
        
    def addTexture(self, texname, texture):
        self.texnames.append(texname)
        self.textures.append(texture)
        self.numtex += 1
        
    def setAnimDelay(self, delay):
        self.anim_delay = delay
        
    def dump(self):
        print 'SPRITE: %s index:%i numtex:%i anim_delay:%i' % (self.name, self.index, self.numtex, self.anim_delay)
        for name in self.texnames:
            print name

    
class Zone():

    def __init__(self, world, name, basedir):
        self.world = world
        self.name = name
        self.basedir = basedir
        
        self.world.consoleOut('zone initializing: '+self.name)
        
        self.textures = {}      # dictionary of panda3d Texure() objects, indexed by texture name
        self.nulltex = Texture()  # create dummy exture object for use in non textured polys

        self.sprites = {}       # SPRITE objects (1-n multitexture groups), indexed by 0x31 fragment index number
                                # as referenced in our meshes
        self.meshes = []
        
        self.rootNode = NodePath(PandaNode("zone_root"))
        self.rootNode.reparentTo(render)
        
        self.delta_t = 0
        
    def update(self):
        # print 'update delta_t:', globalClock.getDt()
        self.delta_t += globalClock.getDt()
        if self.delta_t > 0.2:
            self.delta_t = 0
            for sprite in self.sprites.values():
                # if anim_delay > 0 this sprite is an animated texture
                if sprite.anim_delay > 0:
                    sprite.update()     # drive all sprite animation updates    
        
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
    def dumpBMPInfo(self, bm, name=''):
        (magic, size, dummy, offset) = struct.unpack('<2siii', bm[0:14])
        print 'bmp %s magic:%s size:%i offset:%i' % (name, magic, size, offset)
        
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
            
        # file = open(name, 'wb')
        # file.write(new_bm)
        # file.close()
        
        return new_bm
        
    # Parameter f is a 0x03 type texture file definition fragment
    def loadTexture(self, texname):
        # Note that we reference the texture files by name. The loader here
        # loads textures only if they are not already in the dictionary. 
        
        # this currently only supports the .bmp files I found in the old (pre GOD?) s3d zone files
        # texname = self.wldZone.getName(f.nameRef)
        
        # In typical windows style we'll encounter all types of mixed case names, even spelled
        # differently in various fragments within the same file: Once again we simply enforce all lower case
        # before using the name as a key
        # This works by the assumption that texture names are unique 
        # (and also case insensitive as s3d.getFile() enforces lower case on all names)
        # texname = texname.lower()
        
        if not self.textures.has_key(texname):
            # print 'loading texture:', texname
            s3dentry = self.s3d.getFile(texname)            
            if s3dentry != None:
                texfile = s3dentry.data
                (magic,) = struct.unpack('<2s', texfile[0:2])
                if magic == 'BM':
                    # Generic BMP file
                    texfile = self.checkBmp(texfile, texname)
                    if texfile == None:
                        return

                    # self.dumpBMPInfo(texfile, texname)
                    
                    ts = StringStream(texfile)  # turn into an istream
                    ti = PNMImage()             # create panda3d general purpose image object
                    ti.read(ts)                 # load from istream
                    
                    t = Texture()               # create texture object
                    t.load(ti)                  # load texture from pnmimage
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
                else:
                    print 'Error unsupported texture: %s magic:%s referenced in fragment: %i' % (texname, magic, f.id)
                    return
            else:
                print 'Error: texture %s not found in s3d archive' % (texname)
                return
            
            # t.setWrapU(Texture.WMClamp)
            # t.setWrapV(Texture.WMClamp)
            
            # need to strip the extension (or do we? rather go back to storing with it? Need to 
            # check how the PolyGroup code handles texture references once again)
            self.textures[self.prepTextureName(texname)] = t  # and finally store
            
        
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
                # f.dump()
                
                # NOTE
                # in VERSION 2 WLD zones (ex. povalor, postorms) I've found texture names
                # that have three parameters prepended like this for example: 1, 4, 0, POVSNOWDET01.DDS
                # no idea yet as to what these mean but in order to be able to load the texture from 
                # the s3d container we need to strip this stuff
                for name in f.names:
                    i = name.rfind(',')
                    if i != -1:
                        # See NOTE above
                        print 'parametrized texture name found:%s wld version:0x%x' % (name, self.wldZone.version)
                        name = name[i+1:].strip()
            
                    self.loadTexture(name.lower())
                    
                    
            if f.type == 0x31:
                f31 = f         # we'll need this one below 
                # f31.dump()
                
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
            # f30.dump()

            material_name = self.wldZone.getName(f30.nameRef)
            
            # Note on TRANSPARENCY: as far as I can tell so far, bit 2 in the params1 field of f30
            # is the "semi-transparent" indicator used for all types of water surfaces for the old
            # zones (pre POP? Seems to not work like this in zones like POV for example anymore)
            # lets go by this theory anyway for now
            if f30.params1 & 0x00000004:
                print 'SEMI TRANSPARENT MATERIAL:'
                f30.dump()
                
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
                        sprite = Sprite(material_name, idx, f30.params1)
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
                    sprite = Sprite(name, idx, f30.params1)
                    sprite.setAnimDelay(f04.params2)
                    
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
                    # This is the "does point nowhere meaningful at all" case
                    # infact the reference points back to the same fragment (circular)
                    # This type of 0x30 fragment seem  to only have been used for zone boundary polygons
                    # in the original EQ classic zones 
                    # Note that we create a sprite with just a dummy texture in it for these
                    
                    # sprite_error = 1
                    print 'Warning : Non standard material:%s. Texture ref in 0x30 frag is not type 0x5 or 0x3 but 0x%x' % (material_name, frag.type)
                    # print 'F30 DUMP:'
                    # f30.dump()
                    # print 'Referenced Fragment DUMP:'
                    # frag.dump()
                    
                    # this will be a sprite with just the dummy nulltex textures
                    # we need this so that transparent zonewalls in the very old classic zones work
                    # newer zones have actually textured ("collide.dds") zone walls
                    sprite = Sprite(name, idx, f30.params1)
                    sprite.addTexture('nulltexture', self.nulltex)
            else:
                sprite_error = 1
                print 'Error in Sprite: could not resolve frag05ref:%i in 0x30 fragment:%i' % (f30.frag05Ref, f30.id)

            if sprite_error != 1:   # only add error free sprites
                # sprite.dump()
                self.sprites[idx] = sprite
                
            idx += 1    # need to increment regardless of whether we stored or not
                        # so that the index lookup using the refs in the 0x36's works
    
        print 'zone has %i sprites' % (len(self.sprites))
        
    # find the sprite using the texture passed in            
    def findSpriteUsing(self, t):
        # print 'SEARCHING texture:', t
        for sprite in self.sprites.values():
            for texture in sprite.textures:
                # print 'looking at sprite texture:', texture
                if texture == t:
                    # print 'M A T C H'
                    return sprite
                    
        return None
            
        
    # load up everything related to this zone
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
        
        
        # -------------------------------------------------------------------------------------
        # ANIMATED TEXTURE SETUP AND TRANSPARENCY
        # trying to evaluate the scene graph structure under our root node here
        # since flattenStrong() totally changes the structure of our scene from how we 
        # originally created it, we need to find a way to:
        #   - get a the geoms that the flatten process has produced
        #   - find their textures
        #   - map those back to our sprites
        #   - and finally set up the update process for texture animations based on the above
        # 
        # NOTE this code will fail if there is more than one sprite useing a single texture!
        # Not encountered this yet though.
        # self.rootNode.ls()
    
        
        self.world.consoleOut('setting up animated textures')        
        for child in self.rootNode.getChildren():
            # print child
            geom_node = child.node()
            for geom_number in range(0, geom_node.getNumGeoms()):
                geom_render_state = geom_node.getGeomState(geom_number)              
                attr = geom_render_state.getAttrib(26)  # attrib 26 is the texture attribute (hope this is static)
                if attr != None:
                    # print attr
                    tex = attr.getTexture()
                    # print tex       # BINGO! now we have the texture for this GEOM, lets find the sprite
                    sprite = self.findSpriteUsing(tex)
                    if sprite != None:
                        # print sprite
                        
                        if sprite.transparent == 1:
                            # EXPERIMENTAL TRANSPARENCY SUPPORT ###############
                            ta = TransparencyAttrib.make(TransparencyAttrib.MAlpha)
                            geom_render_state = geom_render_state.setAttrib(ta, 1)  # potentialy needs passing "int override" (=1?) as second param
                            ca = ColorAttrib.makeFlat(Vec4(1, 1, 1, sprite.alpha))
                            geom_render_state = geom_render_state.setAttrib(ca, 1)  # potentialy needs passing "int override" (=1?) as second param
                            geom_node.setGeomState(geom_number, geom_render_state)
                            # #####################################################

                        if sprite.anim_delay > 0:
                            # ANIMATED SPRITE
                            # sprite.addAnimGeomRenderState((geom_node, geom_number, geom_render_state))
                            sprite.addAnimGeomRenderState((geom_node, geom_number, geom_render_state))

                    else:
                        print 'could not find sprite for geom node, node texture cant be animated'
                    

        
        return 0
