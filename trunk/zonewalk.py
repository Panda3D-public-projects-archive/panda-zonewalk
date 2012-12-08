'''
zonewalk
gsk December 2012

'''

import os
import sys, copy, struct
from math import pi, sin, cos



from direct.gui.OnscreenText import OnscreenText 


import direct.directbase.DirectStart

from panda3d.core import TextNode, PandaNode, NodePath

from panda3d.core import Filename,AmbientLight,DirectionalLight, PointLight
from panda3d.core import Vec3, Vec4, Point3, VBase4
from panda3d.core import PStatClient

from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import WindowProperties



from zone import Zone
from config import Configurator
from filedialog import FileDialog

VERSION = '0.0.2'

# Function to put instructions on the screen.
def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1,1,1,1),
                        pos=(-1.3, pos), align=TextNode.ALeft, scale = .04)

# Function to put title on the screen.
def addTitle(text):
    return OnscreenText(text=text, style=1, fg=(1,1,1,1),
                        pos=(1.3,-0.95), align=TextNode.ARight, scale = .03)
        
class World(DirectObject):

    def __init__(self):
        
        self.zone = None
        self.zone_reload_name = None
        
        self.winprops = WindowProperties( )

        # Configuration
        self.configurator = Configurator()
        cfg = self.configurator.config
        self.xres = int(cfg['xres'])
        self.yres = int(cfg['yres'])

        self.eyeHeight = 1.5
        self.rSpeed = 80
        self.flyMode = 1

        # application window setup
        base.win.setClearColor(Vec4(0,0,0,1))
        self.winprops.setTitle( 'zonewalk')
        self.winprops.setSize(self.xres, self.yres) 
        
        base.win.requestProperties( self.winprops ) 
        base.disableMouse()
        
        # console output
        self.consoleNode = NodePath(PandaNode("console_root"))
        self.consoleNode.reparentTo(aspect2d)

        self.console_num_lines = 24
        self.console_cur_line = -1
        self.console_lines = []
        for i in range(0, self.console_num_lines):
            self.console_lines.append(OnscreenText(text='', style=1, fg=(1,1,1,1),
                        pos=(-1.3, .4-i*.05), align=TextNode.ALeft, scale = .035, parent = self.consoleNode))
                        
        # Post the instructions
        self.title = addTitle('zonewalk v.' + VERSION)
        self.inst0 = addInstructions(0.95, "[FLYMODE]")
        self.inst1 = addInstructions(-0.95, "F-key toggles flymode on/off. Camera control with WSAD/mouselook, L-key to load a zone, ESC to exit.")
        self.inst2 = addInstructions(0.9,  "Loc:")
        self.inst3 = addInstructions(0.85, "Hdg:")
        self.error_inst = addInstructions(0, '')
        
        self.campos = Point3(155.6, 41.2, 4.93)
        base.camera.setPos(self.campos)
        
        # Accept the application control keys: currently just esc to exit navgen       
        self.accept("escape", self.exitGame)
        
        # Create some lighting
        ambient_level = .7
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor(Vec4(ambient_level, ambient_level, ambient_level, 1.0))
        render.setLight(render.attachNewNode(ambientLight))


        direct_level = 1.0
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(Vec3(0.0, 0.0, -1.0))
        directionalLight.setColor(Vec4(direct_level, direct_level, direct_level, 1))
        directionalLight.setSpecularColor(Vec4(1, 1, 1, 1))
        render.setLight(render.attachNewNode(directionalLight))
        
        # create a point light that will follow our view point (the camera for now)
        # this basically works like additional ambient lights, softening the contrasts
        self.plight = PointLight('plight')
        self.plight.setColor(VBase4(.2, .2, .2, 1))
        # self.plight.setAttenuation(Point3(0, 0, .5))
        
        self.plnp = render.attachNewNode(self.plight)
        self.plnp.setPos(0, 0, self.eyeHeight)
        render.setLight(self.plnp)
        
        self.keyMap = {"left":0, "right":0, "forward":0, "backward":0, "cam-left":0, \
            "cam-right":0, "mouse3":0, "flymode":1 }

        # camera control
        self.campos = Point3(0, 0, 0)
        self.camHeading = 0.0
        self.camPitch = 0.0
        base.camLens.setFov(65.0)
                
        # Add the spinCameraTask procedure to the task manager.
        # taskMgr.add(self.spinCameraTask, "SpinCameraTask")
        taskMgr.add(self.camTask, "camTask")
        
        self.toggleControls(1)

        # need to step the task manager once to make our fake console work
        taskMgr.step()

    # CONSOLE ---------------------------------------------------------------------
    def consoleScroll(self):
        for i in range(0, self.console_num_lines-1):
            self.console_lines[i].setText(self.console_lines[i+1].getText())
            
    def consoleOut(self, text):
        print text  # output to stdout/log too

        if self.console_cur_line == self.console_num_lines-1:
            self.consoleScroll()
        elif self.console_cur_line < self.console_num_lines-1:
            self.console_cur_line += 1

        self.console_lines[self.console_cur_line].setText(text)

        taskMgr.step()
    
    def consoleOn(self):
        self.consoleNode.show()
        
    def consoleOff(self):
        self.consoleNode.hide()
        
    def toggleControls(self, on):
        if on == 1:
            self.accept("escape", self.exitGame)

            self.accept("f", self.toggleFlymode)
            self.accept("l", self.reloadZone)
            self.accept("a", self.setKey, ["cam-left",1])
            self.accept("d", self.setKey, ["cam-right",1])
            self.accept("w", self.setKey, ["forward",1])
            self.accept("mouse1", self.setKey, ["forward",1])
            self.accept("mouse3", self.setKey, ["mouse3",1])
            self.accept("s", self.setKey, ["backward",1])
        
            self.accept("a-up", self.setKey, ["cam-left",0])
            self.accept("d-up", self.setKey, ["cam-right",0])
            self.accept("w-up", self.setKey, ["forward",0])
            self.accept("mouse1-up", self.setKey, ["forward",0])
            self.accept("mouse3-up", self.setKey, ["mouse3",0])
            self.accept("s-up", self.setKey, ["backward",0])
        else:
            messenger.clear()
            
    def toggleFlymode(self):
        zname = ''
        if self.zone:
            zname = self.zone.name
            
        if self.flyMode == 1:
            self.flyMode = 0
            self.inst0.setText("[WALKMODE] "+zname)
        else:
            self.flyMode = 1
            self.inst0.setText("[FLYMODE] "+zname)

    # Define a procedure to move the camera.
    def spinCameraTask(self, task):
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (pi / 180.0)
        base.camera.setPos(20 * sin(angleRadians), -20.0 * cos(angleRadians), 3)
        base.camera.setHpr(angleDegrees, 0, 0)
        return task.cont
        

    def camTask(self, task):
        # query the mouse
        mouse_dx = 0
        mouse_dy = 0

        # if we have a mouse and the right button is depressed
        if base.mouseWatcherNode.hasMouse() and self.keyMap["mouse3"] != 0:
            # determine movement since last frame
            mouse_dx=base.mouseWatcherNode.getMouseX()
            mouse_dy=base.mouseWatcherNode.getMouseY()
            # print 'mousex:%i mousey:%i' % (mouse_x, mouse_y)           
            # reset mouse position to screen center
            base.win.movePointer(0, self.xres / 2 , self.yres / 2)
            
        if (self.keyMap["cam-left"]!=0 or mouse_dx < 0):
            if self.rSpeed < 160:
                self.rSpeed += 80 * globalClock.getDt()

            self.camHeading += self.rSpeed * globalClock.getDt()
            if self.camHeading > 360.0:
                self.camHeading = self.camHeading - 360.0
        elif (self.keyMap["cam-right"]!=0 or mouse_dx > 0):
            if self.rSpeed < 160:
                self.rSpeed += 80 * globalClock.getDt()

            self.camHeading -= self.rSpeed * globalClock.getDt()
            if self.camHeading < 0.0:
                self.camHeading = self.camHeading + 360.0
        else:
            self.rSpeed = 80

        if mouse_dy > 0:
            self.camPitch += self.rSpeed * globalClock.getDt()
        elif mouse_dy < 0:
            self.camPitch -= self.rSpeed * globalClock.getDt()
            
        # set camera heading and pitch
        base.camera.setHpr(self.camHeading, self.camPitch, 0)

        # viewer position (camera) movement control
        v = render.getRelativeVector(base.camera, Vec3.forward())
        if not self.flyMode:
            v.setZ(0.0)
            
        if self.keyMap["forward"] == 1:
            self.campos += v * 40.0 * globalClock.getDt()
        if self.keyMap["backward"] == 1:
            self.campos -= v * 40.0 * globalClock.getDt()
            
        base.camera.setPos(self.campos)
        self.plnp.setPos(self.campos)      # move the point light with the viewer position

        # update loc and hpr display
        pos = base.camera.getPos()
        hpr = base.camera.getHpr()
        self.inst2.setText('Loc: %.2f, %.2f, %.2f' % (pos.getX(), pos.getY(), pos.getZ()))
        self.inst3.setText('Hdg: %.2f, %.2f, %.2f' % (hpr.getX(), hpr.getY(), hpr.getZ()))
        return task.cont

        
    def exitGame(self):           
        sys.exit(0)
                
    #Records the state of the arrow keys
    # this is used for camera control
    def setKey(self, key, value):
        self.keyMap[key] = value

    def update(self):

        if self.zone_reload_name != None:
            self.doReload(self.zone_reload_name)
            self.zone_reload_name = None

        if self.zone != None:
            self.zone.update()
            
        taskMgr.step()
        
    def loadZone(self, name, path):
        if path[len(path)-1] != '/':
            path += '/'

        if self.zone:
            self.zone.rootNode.removeNode()
            
        self.zone = Zone(self, name, path)
        error = self.zone.load()
        if error == 0:
            self.consoleOff()
            if self.flyMode == 1:
                self.inst0.setText('[FLYMODE] ' + name)
            else:
                self.inst0.setText('[WALKMODE] ' + name)
                
    def load(self):
        self.consoleOut('zonewalk v.%s loading configuration' % VERSION)
        
        cfg = self.configurator.config
        
        zone_name = cfg['default_zone']
        basepath = cfg['basepath']
        self.loadZone(zone_name, basepath)
        basepath = cfg['basepath']

    # zone reload user interface
    def doReload(self, name):
        cfg = self.configurator.config
        basepath = cfg['basepath']
        self.loadZone(name, basepath)
        
        
    def reloadZoneDialogCB(self, name):
        self.frmDialog.end()
        self.zone_reload_name = name
        self.toggleControls(1)

    def reloadZone(self):
        self.toggleControls(0)
        self.consoleOn()
        self.frmDialog = FileDialog(
            "Please enter the shortname of the zone you wish to load:", 
            "Examples: qrg, blackburrow, freportn, ecommons etc.",
            self.reloadZoneDialogCB) 
        
        self.frmDialog.activate()


# ------------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------------

print 'starting zonewalk v' + VERSION

# PStatClient.connect()

world = World()
world.load()

# this position is near the qeynos side zone in of Blackburrow
world.campos = Point3(-155.6, 41.2, 4.9 + world.eyeHeight)
world.camHeading = 270.0
base.camera.setPos(world.campos)

while True:
    world.update();
    
    
    

