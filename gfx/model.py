'''
model.py, implements ModelManager and Model classes


The model class is used to implement mobs, players and placeables
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

from panda3d.core import PandaNode, NodePath, CullFaceAttrib, TransparencyAttrib
from panda3d.core import Vec3

from file.wldfile import WLDContainer
from mesh import Mesh


class ModelManager():
    
    # Params
    # need to pass in the directory of all loaded wld containers for the zone
    def __init__(self, zone):
        self.zone = zone
        self.models = {}
        self.container_directory = zone.wld_containers
        self.placeables_fragments = []
       
    # Params
    # wld_file_obj is expected to be the "objects.wld" wld file found in the zone s3d files
    # that lists all placeables
    def loadPlaceables(self, wld_file_obj):
        # We need to a.) find all distinct models referenced here and 
        # b.) store the reference data so that we can actually spawn the placeables later on
        for f in wld_file_obj.fragments.values():
            if f.type == 0x15:
                # f.dump()
                self.placeables_fragments.append(f)     # store the f15 ref
                name = f.refName
                if not self.models.has_key(name):
                    m = Model(self, name)
                    self.models[name] = m
        
        # load all referenced models
        for model in self.models.values():
            model.load()
            
        # spawn placeables
        for f in self.placeables_fragments:
            model_name = f.refName
            # print 'spawning placeable:', model_name+str(f.id)
            model = self.models[model_name]
            if model.loaded > 0:
                p_node = PandaNode(model_name+str(f.id))
            
                # for now we attach a new parent node for every placeable directly under the zone root
                np = self.zone.rootNode.attachNewNode(p_node)
                np.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullClockwise))
            
                # setting up texture alpha transparency for all models this way currently
                # seems to work well with our "masked" textures at leaser
                np.setTransparency(TransparencyAttrib.MAlpha)
            
                np.setPos(f.xpos, f.ypos, f.zpos )
                np.setHpr(f.xrot / 512.0 * 360.0, f.yrot / 512.0 * 360.0, f.zrot / 512.0 * 360.0 )
            
                # NOTE on placeables scale: from what I've seen so far for placeables this seems to always
                # be x=0.0 y=1.0 z=1.0
                # No idea if this is a bug or intentional. For now we assume a unified scale for x/y being
                # stored in yscale and one for z in zscale
                # print 'scalex:%f scaley:%i scalez:%f' % (f.xscale, f.yscale, f.zscale )
                np.setScale(f.yscale, f.yscale, f.zscale )
            
                # attach an instance of the model under the placeable's NodePath
                model.mesh.root.instanceTo(np)
        
class Model():
    
    def __init__(self, mgr, name):
        self.mm = mgr
        self.name = name
        self.wld_container = None   # the container we were loaded from
        self.mesh = None
        self.loaded = 0
        
    # wld_containers : directory of wld container objects
    def load(self):
        # print 'loading model:', self.name
        
        # find our 0x14 fragment in any of the "object" wld files in the container directory
        f14 = None
        for c in self.mm.container_directory.values():
            if c.type == 'obj':
                f14 = c.wld_file_obj.getFragmentByName(self.name)
                if f14 != None:
                    self.wld_container = c  # ok , this is "our" wld container
                    break;
        
        if f14 == None:
            print 'ERROR during model load. Base 0x14 fragment not found. Model:', self.name
            return
        
        wld_file_obj = self.wld_container.wld_file_obj
        
        # note that this will need to be changed when we support animated mob models
        # for those f14.fragRefs does not point to a 0x2d frag but rather to a 0x11 anim track ref
        f2d = wld_file_obj.getFragment(f14.fragRefs3[0])
        if f2d == None:
            return  # for now we need to abort here because we dont support animated models yet!
            
        # f2d.dump()
                    
        f36 = wld_file_obj.getFragment(f2d.fragRef)
        # f36.dump()
        
        m = Mesh(self.name+'_mesh')
        m.buildFromFragment(f36, self.wld_container,False)
        self.mesh = m
        self.loaded = 1
        