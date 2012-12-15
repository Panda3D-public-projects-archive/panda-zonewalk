'''
sprite.py

Sprite class for managing multitextures and texture animation
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

from panda3d.core import TextureAttrib



         
class Sprite():
    
    def __init__(self, name, idx, params1, textureManager):
        self.name = name
        self.index = idx
        self.params1 = params1
        self.tm = textureManager
        
        self.transparent = 0
        self.masked = 0
        self.alpha = 1.0 

        # bit 2 set - semi transparent textures (water et al)
        if self.params1 & 0x00000004:
            self.transparent = 1
            self.alpha = 0.4      # default transparency alpha applied to semi transparent textures
        else:
            self.transparent = 0

        # bit 1 set - masked textures (trees etc) 
        # seen several kinds with different params1 masks, common is always bit 1 set
        # examples. Unsure what bits 2-4 mean
        # bit    543210
        # 0x13  - 10011
        # 0xb   - 01011
        # 0x17  - 10111
        if self.params1 & 0x00000002:
            print 'masked texture sprite:%s params:0x%x' % (name, self.params1)
            self.masked = 1
            
        # fully transparent (zone boundaries)
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
        # special case handling: if we are "masked" (old style bmp texture transparency for leaves etc)
        if self.masked == 1:
            # see if the texture manager has a "masked" version (with added alpha channel)
            texname = 'masked-'+texname
            texture = self.tm.getMaskedTexture(texname)
            
        self.texnames.append(texname)
        self.textures.append(texture)
        self.numtex += 1
        
    def setAnimDelay(self, delay):
        self.anim_delay = delay
        
    def dump(self):
        print 'SPRITE: %s index:%i numtex:%i anim_delay:%i' % (self.name, self.index, self.numtex, self.anim_delay)
        for name in self.texnames:
            print name

