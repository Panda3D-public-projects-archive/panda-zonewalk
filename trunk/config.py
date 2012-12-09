'''
config.py

Zonewalk configuration support
gsk dec 2012


LICENSE:

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

import os

from filedialog import FileDialog

class Configurator():
    
    def __init__(self, world):
        self.world = world
        self.cfg_file = None
        self.config = {}
        self.frmDialog = None
        
        try:
            self.cfg_file = open('zonewalk.cfg')
        except IOError as e:
            pass
            
        if self.cfg_file == None:
            print 'no config'
            self.frmDialog = FileDialog(
                "Please enter the full path to the EverQuest directory:", 
                "No configuration found.",
                self.confPathCallback) 
            self.frmDialog.activate()
            self.frmDialog.run()
        else:
            cfg = self.cfg_file.readlines()
            for line in cfg:
                # print line
                tokens = line.split('=')
                key = tokens[0].strip()
                value = tokens[1].strip()
                
                self.config[key] = value
                self.world.consoleOut('config: %s = %s' % (key, value))
    
    def saveConfig(self):
        try:
            self.cfg_file = open('zonewalk.cfg', 'w')
        except IOError as e:
            print 'ERROR: cannot write configuration file'
            return
        
        for key in self.config.keys():
            line = key + ' = ' + self.config[key] + '\n' 
            self.cfg_file.write(line)
    
        self.cfg_file.close()
        
    def confPathCallback(self, path):
        if not os.path.exists(path):
            self.frmDialog.setStatus('Error, path invalid: '+path)
            return 0

        # self.statusLabel['text'] = 'Loading default zone from path : '+textEntered
        # self.result = textEntered
        # self.done = 1

        # user entered path exists: store it into config
        self.config['basepath'] = path
        
        # set a few defaults
        self.config['xres'] = '1024'
        self.config['yres'] = '768'
        self.config['default_zone'] = 'blackburrow'

        # write config
        self.saveConfig()
        
        return 1    # let the dialog know it can exit
                
