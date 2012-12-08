'''
configuration support
'''

import os

from filedialog import FileDialog

class Configurator():
    
    def __init__(self):
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
                print 'config: %s = %s' % (key, value)
    
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
            print 'Error: invalid path'
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
                
