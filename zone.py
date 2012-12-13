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
from panda3d.core import Vec4, BitMask32 
from panda3d.core import CollisionNode, CollisionSolid

from s3dfile import S3DFile
from wldfile import WLDFile, WLDContainer
from ddsfile import DDSFile
from polygroup import PolyGroup
from mesh import Mesh
from sprite import Sprite



    
class Zone():

    def __init__(self, world, name, basedir):
        self.world = world
        self.name = name
        self.basedir = basedir
        
        self.world.consoleOut('zone initializing: '+self.name)
        
        self.textures = {}      # dictionary of panda3d Texure() objects, indexed by texture name
        self.nulltex = Texture()  # create dummy exture object for use in non textured polys

        self.meshes = []
        self.wld_containers = {}
        
        self.rootNode = NodePath(PandaNode("zone_root"))
        self.rootNode.reparentTo(render)
        
        self.delta_t = 0
        
    # This currently only updates the direct zone sprites
    def update(self):
        # print 'update delta_t:', globalClock.getDt()
        self.delta_t += globalClock.getDt()
        if self.delta_t > 0.2:
            self.delta_t = 0
            for sprite in self.zone_wld_container.sprites.values():
                # if anim_delay > 0 this sprite is an animated texture
                if sprite.anim_delay > 0:
                    sprite.update()     # drive all sprite animation updates    
        
        
    # build the main zone geometry mesh
    def prepareZoneMesh(self):
        wld_container = self.wld_containers['zone']
        wld_obj = wld_container.wld_file_obj
        
        # load the 0x36 bsp region fragments (sub meshes): all these meshes together
        # make up the main zone geometry
        for f in wld_obj.fragments.values():
            if f.type == 0x36:
                # print 'adding fragment_36 to main zone mesh'
                # f.dump()
                m = Mesh(self.name)
                m.buildFromFragment(f, wld_container)
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
    # Note that we currently still store all textures (from all containers) into 
    # a single zone wide dictionary. Need to watch closely if texture names are really unique
    # and if not switch everything over to a store by container (or key more elaborately)
    def loadTexture(self, texname, container):
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
            s3dentry = container.s3d_file_obj.getFile(texname)            
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
            name = self.prepTextureName(texname)
            if not self.textures.has_key(name):
                self.textures[name] = t  # and finally store
            else:
                print 'Not storing duplicate texture:', name
            
        
    def prepTextureName(self, name):
        n = name.lower()
        i = name.find('.')
        if i != -1:
            n = n[0:i]
            
        return n
        
    # Params
    # wld_container is a WldContainer object
    def preloadWldTextures(self, wld_container):
        print 'preloading textures for container:', wld_container.name
        wld = wld_container.wld_file_obj  # the in memory wld file
        # loop over all 0x03 fragments and load all referenced texture files from the s3d
        f31 = None
        for f in wld.fragments.values():
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
            
                    self.loadTexture(name.lower(), wld_container)
                    
                    
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
            f30 = wld.getFragment(ref30)
            # f30.dump()

            material_name = wld.getName(f30.nameRef)
            
            # Note on TRANSPARENCY: as far as I can tell so far, bit 2 in the params1 field of f30
            # is the "semi-transparent" indicator used for all types of water surfaces for the old
            # zones (pre POP? Seems to not work like this in zones like POV for example anymore)
            # lets go by this theory anyway for now
            '''
            if f30.params1 & 0x00000004:
                print 'SEMI TRANSPARENT MATERIAL:'
                f30.dump()
            '''    
            # print 'looking up 0x05 fragment with id_plus_1:', f30.frag05Ref
            
            # Note that there are frag05Refs inside some 0x30 fragments with value <=0 
            # these named references seem to point directly to 0x03 texture fragments
            # instead of the usual indirection chain  0x05->0x04->0x03
            # in some instances these point nowhere meaningful at all though. Need to catch all these
            frag = wld.getFragment(f30.frag05Ref)
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
                    f04 = wld.getFragment(f05.frag04Ref)
                    # f04.dump()

                    name = wld.getName(f04.nameRef)
                    sprite = Sprite(name, idx, f30.params1)
                    sprite.setAnimDelay(f04.params2)
                    
                    for f03ref in  f04.frag03Refs:
                        f03 = wld.getFragment(f03ref)
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
                wld_container.sprites[idx] = sprite
                
            idx += 1    # need to increment regardless of whether we stored or not
                        # so that the index lookup using the refs in the 0x36's works
    
        print 'wld_container defines %i sprites' % (len(wld_container.sprites))
        
    # preload the textures/sprites for all loaded containers
    def preloadTextures(self):
        # self.preloadWldTextures(self.zone_wld_container)
        for wld_obj in self.wld_containers.values():
            self.preloadWldTextures(wld_obj)
    
            
    # We let Panda3D "flatten" the plethora of GEOMs we created from the original bsp tree
    # ==> this process creates a complete new NodePath->GeomNode tree from our original
    # In order to implement texture animation and transparency we need to map the new Geom's textures
    # back to our Sprites so we can change texture assignments and transparency on a Geom level in 
    # the new structure
    
    # Remap the Textures in use for the main Zone Geometry
    def remapTextures(self):
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
                    sprite = self.zone_wld_container.findSpriteUsing(tex)
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
        
        
        
    # load up everything related to this zone
    def load(self):
        # ---- ZONE GEOMETRY ----
        # load main zone s3d
        s3dfile_name = self.name+'.s3d'
        self.world.consoleOut('zone loading zone s3dfile: ' + s3dfile_name)
        
        s3d = S3DFile(self.basedir+self.name)
        if s3d.load() != 0:
            self.world.consoleOut( 'ERROR loading s3dfile:' + self.basedir+s3dfile_name)
            return -1
            
        # s3d.dumpListing()
        
        # load main zone wld
        wldZone = WLDFile(self.name)
        wldZone.load(s3d)
        self.zone_wld_container = WLDContainer(self, wldZone, s3d)
        self.wld_containers['zone'] = self.zone_wld_container

        # ---- PLACEABLES ----
        '''
        s3dfile_name = self.name+'_obj.s3d'
        self.world.consoleOut('zone loading placeable objects s3dfile: ' + s3dfile_name)
        
        self.s3d_obj1 = S3DFile(self.basedir+self.name+'_obj')
        if self.s3d_obj1.load() != 0:
            self.world.consoleOut( 'ERROR loading s3dfile:' + self.basedir+s3dfile_name)
            return -1
        self.s3d_obj1.dumpListing()
        self.wldObj1 = WLDFile(self.name+'_obj')
        self.wldObj1.load(self.s3d_obj1)
        self.wld_containers['obj1'] = self.wldObj1
        '''
        
        # --- TEXTURES ----
        self.world.consoleOut('preloading textures')
        self.preloadTextures()
        self.world.consoleOut( 'preparing zone mesh')
        self.prepareZoneMesh()

        # let Panda3D attempt to flatten the zone geometry (reduce the excessive
        # Geom count resulting from the layout of the .wld zone data as a huge
        # bunch of tiny bsp regions)
        self.world.consoleOut('flattening zone mesh geom tree')        
        self.rootNode.flattenStrong()    
        
        # texture->sprite remapping after the flatten above
        self.remapTextures()
                    
        # COLLISION:
        # The following makes the complete zone base geometry eligible for collisions
        # this is of course extremely inefficient. TODO
        self.rootNode.setCollideMask(BitMask32.bit(0)) 

        return 0
