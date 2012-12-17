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


-------------------------------------------------------------------------------
ZONE REFERENCE NOTES
-------------------------------------------------------------------------------

Old Style zones (s3d based)
-------------------------------

Usually consist of 3 s3d files: shortname.s3d shortname_chr.s3d shortname_obj.s3d
For some zones, probably when adding additional placeable model types like the jaggedpine forrest
portal crystal in surefall glade (qrg), an additional shortname_2_obj.s3d file exists

The main (shortname.s3d) s3d file contains a bunch of textures and 3 .wld files
    - shortname.wld : this is the main zone geometry
    - objects.wld : placeable objects placements
    - lights.wld : well, duh, lights
    
    
'''


import struct
import zlib

from panda3d.core import Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles, GeomNode, CullFaceAttrib
from panda3d.core import PNMImage, Texture, StringStream
from panda3d.core import PandaNode, NodePath, TextureAttrib, TransparencyAttrib, ColorAttrib
from panda3d.core import Vec4, BitMask32 
from panda3d.core import CollisionNode, CollisionSolid

from file.s3dfile import S3DFile
from file.wldfile import WLDFile, WLDContainer
from file.ddsfile import DDSFile
from polygroup import PolyGroup
from model import ModelManager, Model
from mesh import Mesh
from texture import TextureManager
from sprite import Sprite



class Zone():

    def __init__(self, world, name, basedir):
        self.world = world
        self.name = name
        self.basedir = basedir
        self.load_complete = 0
        
        self.world.consoleOut('zone initializing: '+self.name)
            
        # store the in memory WLDFile objects that make uo the zone for direct access
        self.wld_containers = {}        # and as a directory
        self.zone_wld_container = None
        self.obj1_wld_container = None
        self.obj2_wld_container = None
        self.chr_wld_container  = None
    
        # init our texture manager
        self.tm = TextureManager()

        # init our model manager
        self.mm = ModelManager(self)
        
        self.nulltex = Texture()  # create dummy exture object for use in non textured polys

        
        self.rootNode = NodePath(PandaNode("zone_root"))
        self.rootNode.reparentTo(render)
        
        self.delta_t = 0
        
    # This currently only updates the direct zone sprites
    def update(self):
        if self.load_complete != 1:
            return
            
        # print 'update delta_t:', globalClock.getDt()
        self.delta_t += globalClock.getDt()
        if self.delta_t > 0.2:
            self.delta_t = 0
            for sprite in self.zone_wld_container.animated_sprites:
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
                m.root.reparentTo(self.rootNode)        # "hang" the mesh under our root node

        
    # ---------------------------------------------------------------------             
    # create the SPRITE objects: these can reference a single texture or
    # a list of them (for animated textures like water, lava etc.)
    # we need to step through all entries of the 0x31 list fragment for the zone
    # We store the SPRITEs using their index within the 0x31 fragments list as the key
    # because this is exactly how the meshes (0x36 fragments) reference them
    # The lists them selves are keyed by the 0x31 fragmemts id (=index in the diskfile)
    def loadSpriteList(self, wld_container, f31):
    
        wld = wld_container.wld_file_obj
        wld_container.sprite_list[f31.id] = {}
        sprite_list = wld_container.sprite_list[f31.id]
        
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
                    texfile_name = f03.names[0]                   
                    tx = self.tm.getTexture(texfile_name)
                    if tx != None:
                        # we dont have a sprite def (0x04) for these, so we use the material (0x30) name
                        sprite = Sprite(material_name, idx, f30.params1, self.tm)
                        sprite.addTexture(texfile_name, tx) 
                    else:
                        sprite_error = 1
                        print 'Error in Sprite:', material_name, 'Texture not found:', texfile_name                        
                elif frag.type == 0x05: # this is the "normal" indirection chain 0x30->0x05->0x04->0x03
                    f05 = frag
                    # f05.dump()
                    f04 = wld.getFragment(f05.frag04Ref)
                    # f04.dump()

                    name = wld.getName(f04.nameRef)
                    sprite = Sprite(name, idx, f30.params1, self.tm)
                    sprite.setAnimDelay(f04.params2)
                    
                    for f03ref in  f04.frag03Refs:
                        f03 = wld.getFragment(f03ref)
                        # f03.dump()
                        # NOTE that this assumes the zone 0x03 fragments only ever reference one single texture
                        texfile_name = f03.names[0]
                        tx = self.tm.getTexture(texfile_name)
                        if tx != None:
                            sprite.addTexture(texfile_name, tx) 
                        else:
                            sprite_error = 1
                            print 'Error in Sprite:', name, 'Texure not found:', texfile_name
                else:
                    # This is the "does point nowhere meaningful at all" case
                    # infact the reference points back to the same fragment (circular)
                    # This type of 0x30 fragment seems  to only have been used for zone boundary polygons
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
                    sprite = Sprite(material_name, idx, f30.params1, self.tm)
                    sprite.addTexture('nulltexture', self.nulltex)
            else:
                sprite_error = 1
                print 'Error in Sprite: could not resolve frag05ref:%i in 0x30 fragment:%i' % (f30.frag05Ref, f30.id)

            if sprite_error != 1:   # only add error free sprites
                # sprite.dump()
                # new style sprite list
                sprite_list[idx] = sprite
                if sprite.anim_delay != 0:
                    wld_container.animated_sprites.append(sprite)
                
            idx += 1    # need to increment regardless of whether we stored or not
                        # so that the index lookup using the refs in the 0x36's works
    
        
        
    # preloadWldTextures actually does quite a bit more than just preloading texture files
    # the main task of this code is to generate our SPRITES
    # Params
    # wld_container is a WldContainer object
    def preloadWldTextures(self, wld_container):
        self.world.consoleOut('preloading textures for container: '+ wld_container.name)
        wld = wld_container.wld_file_obj  # the in memory wld file
        
        # loop over all 0x03 fragments and PRELOAD all referenced texture files from the s3d
        f31 = None
        f31_list = []
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
            
                    self.tm.loadTexture(name.lower(), wld_container)
                    
            # need to store the 0x31 texture lists        
            if f.type == 0x31:
                f31_list.append(f)
                
        # not all wld files define sprites
        if len(f31_list) == 0:
            return
        
        for f31 in f31_list:
            self.loadSpriteList(wld_container, f31)
        
        
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
        # ANIMATED TEXTURE SETUP AND TRANSPARENCY FOR ZONE GEOMETRY (NOT PLACEABLES etc!)
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
            
        self.world.consoleOut('setting up animated textures for zone geometry')        
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
                        
                        # set general texture alpha based tansparency for masked textures
                        # if sprite.masked == 1:
                        #     child.setTransparency(TransparencyAttrib.MAlpha)

                        if sprite.transparent == 1 or sprite.masked == 1:
                            # EXPERIMENTAL TRANSPARENCY SUPPORT ###############
                            # This is for semi-transparent polygons (water surfaces etc) 
                            # we implement the transparency via the alpha component of the GEOM's ColorAttrib
                            ta = TransparencyAttrib.make(TransparencyAttrib.MAlpha)
                            geom_render_state = geom_render_state.setAttrib(ta, 1)  # potentialy needs passing "int override" (=1?) as second param
                            
                            if not sprite.masked == 1:
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
        # wldZone.setDumpList([0x14, 0x15])
        wldZone.load(s3d)
        self.zone_wld_container = WLDContainer('zone', self, wldZone, s3d)
        self.wld_containers['zone'] = self.zone_wld_container

        # load the objects.wld file from the same container
        # this basically consists of 0x15 model references for putting all placeables in place
        wldZoneObj = WLDFile('objects')
        # wldZoneObj.setDumpList([0x14, 0x15])
        wldZoneObj.load(s3d)
        self.zone_obj_wld_container = WLDContainer('zone_obj', self, wldZoneObj, s3d)
        self.wld_containers['zone_obj'] = self.zone_obj_wld_container

        # ---- placeables definitions ------------------------------------
        
        s3dfile_name = self.name+'_obj.s3d'
        print '-------------------------------------------------------------------------------------'
        self.world.consoleOut('zone loading placeable objects s3dfile: ' + s3dfile_name)
        
        s3d = S3DFile(self.basedir+self.name+'_obj')
        if s3d.load() == 0:
            # s3d.dumpListing()
            wldObj1 = WLDFile(self.name+'_obj')
            # wldObj1.setDumpList([0x14, 0x15, 0x2D, 0x36])
            wldObj1.load(s3d)
            self.obj1_wld_container = WLDContainer('obj', self, wldObj1, s3d)
            self.wld_containers['obj1'] = self.obj1_wld_container
        else:
            self.world.consoleOut( 'zone object 1 s3dfile does not exist:' + self.basedir+s3dfile_name)
        
        s3dfile_name = self.name+'_2_obj.s3d'
        print '-------------------------------------------------------------------------------------'
        self.world.consoleOut('zone loading placeable objects 2 s3dfile: ' + s3dfile_name)
        
        s3d = S3DFile(self.basedir+self.name+'_2_obj')
        if s3d.load() == 0:
            # s3d.dumpListing()
            wldObj2 = WLDFile(self.name+'_2_obj')
            # wldObj2.setDumpList([0x14, 0x15, 0x2D, 0x36])
            wldObj2.load(s3d)
            self.obj2_wld_container = WLDContainer('obj', self, wldObj2, s3d)
            self.wld_containers['obj2'] = self.obj2_wld_container
        else:
            self.world.consoleOut( 'zone object 2 s3dfile does not exist:' + self.basedir+s3dfile_name)
        
        s3dfile_name = self.name+'_chr.s3d'
        print '-------------------------------------------------------------------------------------'
        self.world.consoleOut('zone loading character s3dfile: ' + s3dfile_name)
        
        s3d = S3DFile(self.basedir+self.name+'_chr')
        if s3d.load() == 0:
            # s3d.dumpListing()
            wldChr = WLDFile(self.name+'_chr')
            # wldChr.setDumpList([0x14, 0x15, 0x2D, 0x36])
            wldChr.load(s3d)
            self.chr_wld_container = WLDContainer('chr', self, wldChr, s3d)
            self.wld_containers['chr'] = self.chr_wld_container
        else:
            self.world.consoleOut( 'zone character s3dfile does not exist:' + self.basedir+s3dfile_name)
        
        # --- TEXTURES ----
        self.world.consoleOut('preloading textures')
        self.preloadTextures()
        
        # ---- Generate main Zone Geometry ----
        self.world.consoleOut( 'preparing zone mesh')
        self.prepareZoneMesh()
        
        # let Panda3D attempt to flatten the zone geometry (reduce the excessive
        # Geom count resulting from the layout of the .wld zone data as a huge
        # bunch of tiny bsp regions)
        self.world.consoleOut('flattening zone mesh geom tree')        
        
        # self.rootNode.ls()
        self.rootNode.flattenStrong()    
        self.rootNode.ls()

        # texture->sprite remapping after the flatten above
        self.remapTextures()
                    
        # COLLISION:
        # The following makes the complete zone base geometry eligible for collisions
        # this is of course extremely inefficient. TODO: at some point we need to use the
        # bsp structures already provided in the wld file to optimize whats in our scene graph
        # and also to build a more intelligent collision system
        self.rootNode.setCollideMask(BitMask32.bit(0)) 

        # ---- load MODELS and spawn placeables -----------------------
        
        # go through all the 0x15 refs and create empty model "shells"
        # for every unique entry
        self.world.consoleOut( 'loading placeables models')
        self.mm.loadPlaceables(wldZoneObj)
        # self.rootNode.ls()
        
            
        print 'zone load complete'
        self.load_complete = 1
        
        return 0
