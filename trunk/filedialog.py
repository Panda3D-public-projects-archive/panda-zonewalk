
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectSlider, DirectEntry
from direct.gui.DirectGui import DirectButton, DirectScrolledList, DGG
from direct.showbase.DirectObject import DirectObject

from panda3d.core import TextNode

        
class FileDialog(DirectObject):

    def __init__(self, title, initial_status, callback):
        self.frmLeft = -.7
        self.frmBottom = -.12
        self.frmRight = .7
        self.frmTop = .12
        
        self.frmWidth = self.frmRight - self.frmLeft
        self.frmHeight = self.frmTop - self.frmBottom
        
        self.title = title
        self.initial_status = initial_status
        self.callback = callback
        
        self.result = None
        self.done = 0
            
            
    def activate(self):
        # create main dialog frame
        # Note: frame position references the CENTER of the frame
        self.frm = DirectFrame(
            pos = (0,0,0),
            frameSize = (self.frmLeft, self.frmRight,self.frmBottom, self.frmTop),
            relief = DGG.RIDGE,
            borderWidth = (0.01, 0.01),
            frameColor = (0.6, 0.6, 0.6, 1.0))
        
        self.frm.reparentTo(base.aspect2d)
        
        # Note: wonderfully enough, label position on the other hand
        # references the CENTER of the LEFT border of the label!
        titleLabel = DirectLabel(text = self.title,
            scale = 0.04,
            frameColor = (0.5, 0.5, 0.5, 1),
            relief = DGG.RIDGE,
            borderWidth = (0.01, 0.01),
            text_align = TextNode.ALeft)
            
        titleLabel.setPos(-self.frmWidth/2+.02, 0, self.frmHeight/2-.045)
        titleLabel.reparentTo(self.frm)
        
        sc = .04     
        self.dir_edit_field = DirectEntry(
            text = '',      # prompt text
            scale = sc,
            frameColor = (0.65, 0.65, 0.65, 1),
            command=self.setText,
            width = 32,
            numLines = 1,
            focus = 1,
            focusInCommand=self.efFocusIn,
            )

        self.dir_edit_field.setPos(-self.frmWidth/2+.02, 0, self.frmHeight/2-.13)
        self.dir_edit_field.reparentTo(self.frm)

        self.statusLabel = DirectLabel(text = self.initial_status,
            scale = 0.04,
            frameColor = (0.6, 0.6, 0.6, 1),
            # relief = DGG.RIDGE,
            # borderWidth = (0.01, 0.01),
            text_align = TextNode.ALeft)
            
        self.statusLabel.setPos(-self.frmWidth/2+.02, 0, self.frmHeight/2-.2)
        self.statusLabel.reparentTo(self.frm)

    # call this if you need to run a form before your mainloop starts steppping the taskMgr
    def run(self):
        while self.done != 1:
            taskMgr.step()

        taskMgr.step()          # once more to make the last output from the dialog visible
                                # while we load a zone
        self.frm.removeNode()

    def end(self):
        self.frm.removeNode()
        

    # callback function to set  text: called by the Panda3d taskMgr when the user
    # has entered something into the DirectEntry widget
    def setText(self, textEntered):
        print 'dir_edit_field::setText:', textEntered
        self.done = self.callback(textEntered)
        if self.done != 1:
            self.dir_edit_field['focus'] = 1

                
    #clear the text
    def efFocusIn(self):
        print 'focus in'
        self.dir_edit_field.enterText('')
        
    def setStatus(self, status):
        self.statusLabel['text'] = status
