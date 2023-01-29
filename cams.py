'''

Put this file in your scripts directory:
"%USERPROFILE%\Documents\maya\####\scripts"
or
"%USERPROFILE%\Documents\maya\scripts"


Run with:

import cams
reload(cams)
cams.UI()

'''


import maya.cmds as cmds
import random

class UI:

    TITLE = "Cams"    
    VERSION = '0.0.3'


    """
    Error Messages:
    """
    NO_INTERNET = "Could not establish a connection to the server."


    def __init__(self):
        self.__height__ = 25
        self.__width__ = 75
        self.__margin__ = 6

        self.layouts = {}

        # Create window
        if cmds.window(UI.TITLE, exists=True):
            cmds.deleteUI(UI.TITLE)
        try:
            self.window = cmds.window(UI.TITLE, title="Change Camera", menuBar=True, rtf=True, tlb=True, sizeable = False)
        except:
            self.window = cmds.window(UI.TITLE, title="Change Camera", menuBar=True, rtf=True, sizeable = False)

        #Menu bar
        cmds.menu( label='Tools')
        cmds.menuItem( label='Reload', command = self.reload )
        cmds.menuItem( divider=True )
        cmds.menuItem( label='MultiCams', command = "multicams()" )
        cmds.menu( label='About', helpMenu=True )
        cmds.menuItem( label='Check for updates', command = self.check_for_updates )
        cmds.menuItem( divider=True )
        cmds.menuItem( label='Credits', c=lambda *args: self.coffee() )

        #Cameras Layout
        cmds.columnLayout()
        self.main = cmds.rowLayout(numberOfColumns = 4)
        cmds.separator(w = self.__margin__/2, style="none")
        cmds.iconTextButton( style='iconAndTextHorizontal', bgc = self.getcolor(), image1='Camera.xpm', label='persp', w = self.__width__, h = self.__height__, command="cmds.lookThru( cmds.getPanel(wf=True), 'persp')")
        cmds.separator(w = self.__margin__*1.5, height = self.__height__, style="single")

        self.create_layouts()

        cmds.setParent( '..' )
        cmds.setParent( '..' )
        cmds.separator(h = self.__margin__/2, style="none")
        cmds.showWindow( self.window )


    def create_layouts(self):

        # Get all custom cameras in scene
        cameras = [camera for camera in cmds.ls(type=('camera'), l=True)]
        startup_cameras = [camera.split("|")[-2] for camera in cameras if cmds.camera(cmds.listRelatives(camera, parent=True)[0], startupCamera=True, q=True)]
        self.non_startup_cameras = list(set([camera.split("|")[-2] for camera in cameras]) - set(startup_cameras))
        self.non_startup_cameras.sort()

        self.row_layout = cmds.rowLayout(parent = self.main, numberOfColumns = len(self.non_startup_cameras)*2 + 4 )
        for index,c in enumerate(self.non_startup_cameras):
            self.layouts[index] = "button_layout%s" % (index)
            cmds.rowLayout( self.layouts[index], parent = self.row_layout, numberOfColumns = 20 )
            cmds.iconTextButton(
                style='iconAndTextHorizontal',
                w = self.__width__, h = self.__height__,
                bgc = self.getcolor(),
                image='Camera.xpm',
                label=["...%s" % c[-6:] if len(c) > 8 else c][0],
                command= lambda index=index: cmds.lookThru( cmds.getPanel(wf=True), self.non_startup_cameras[index]))

            cmds.iconTextButton(
                style='iconOnly',
                image='closeTabButton.png',
                command = lambda c=c : self.delete_cam(c))

            cmds.separator(w = self.__margin__/5, style="none")
            cmds.setParent("..")

        cmds.window(UI.TITLE, edit=True, width=100, rtf=True)


    def delete_cam(self,cam):
        result = cmds.confirmDialog( title='Confirm Delete', message='Are you sure you want to delete this camera?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No')
        if result == 'Yes':
            multicams_nodes = [node for node in cmds.ls() if "multicam_%s_" % cam in node]
            for i in multicams_nodes:
                try:
                    cmds.delete(i)
                except:
                    pass

            #Delete cam from self.non_startup_cameras
            button_index = [i for i, c in enumerate(self.non_startup_cameras) if cam in c][0]
            self.non_startup_cameras.pop(button_index)

            #Delete cam
            cmds.delete(cam)
            self.reload()


    def reload(self, *args):
        try:
            cmds.deleteUI(self.row_layout)
        except:
            pass
        self.layouts = {}
        self.create_layouts()


    def check_for_updates(self, *args):
        import json, urllib2
        import maya.OpenMaya as om

        url = 'https://raw.githubusercontent.com/Alehaaaa/mayascripts/main/version.json'

        try:
            response = urllib2.urlopen(url)
        except:
            om.MGlobal.displayWarning(UI.NO_INTERNET)
            return
        content = response.read()

        if content:
            data = json.loads(content)
            script = data[UI.TITLE.lower()]

            version = str(script['version'])
            changelog = str('\n'.join(script['changelog']))

        if version > UI.VERSION:
            update_available = cmds.confirmDialog(
                title="New update for {0}!".format(UI.TITLE),
                message="Version {0} available, you are using {1}\n\nChangelog:\n{2}".format(version,UI.VERSION,changelog),
                messageAlign = 'center',
                button=['Install','Close'],
                defaultButton='Install',
                cancelButton='Close',
                dismissString='Close'
            )
            if update_available == 'Install':
                self.install()

    def install(self, *args):
        import os, urllib2
        import maya.OpenMaya as om
        
        url = 'https://raw.githubusercontent.com/Alehaaaa/mayascripts/main/{0}.json'.format(UI.TITLE)

        try:
            response = urllib2.urlopen(url)
        except:
            om.MGlobal.displayWarning(UI.NO_INTERNET)
            return
        content = response.read()

        if not content:
            om.MGlobal.displayWarning(UI.NO_INTERNET)
            return

        scriptPath = os.environ['MAYA_SCRIPT_PATH']
        path = []

        for i in scriptPath.split(';'):
            if os.path.isfile('{0}/{1}.py'.format(i,UI.TITLE.lower())):
                path.append(i)
        
        for p in path:
            with open(p, "w") as f:
                f.write(content)
        
        om.MGlobal.displayWarning("Re-open the script {0}.".format(UI.TITLE))

    def coffee(self):
        coffee = cmds.confirmDialog(
            title="Buy me a coffee!",
            message="Created by @Aleha\nIf you liked it, you can tell send me some love:",
            messageAlign = 'center',
            bgc = self.getcolor(),
            button=['Instagram','Close'],
            defaultButton='Instagram',
            cancelButton='Close',
            dismissString='Close')
        if coffee == 'Instagram':
            cmds.showHelp('https://www.instagram.com/alejandro_anim/', absolute=True)


    def getcolor(self):
        return [round(random.uniform(0.525, 0.750), 3) for i in range(3)]


class multicams:
    
    TITLE = "MultiCams"

    def __init__(self):
        
        self.__margin__ = 3
        self.__width__ = 90

        # Create window
        if cmds.window(multicams.TITLE, exists=True):
            cmds.deleteUI(multicams.TITLE)
        try:
            window = cmds.window(multicams.TITLE, menuBar=True, rtf=True, tlb=True, s=False)
        except:
            window = cmds.window(multicams.TITLE, menuBar=True, rtf=True, s=False)

        cmds.columnLayout()
        cmds.separator(h=self.__margin__, st="none")

        cmds.rowLayout(numberOfColumns = 5)
        cmds.separator(w=self.__margin__, st="none")
        cmds.rowColumnLayout(numberOfColumns = 3)
        cmds.columnLayout()
        self.textScrollList_layout = cmds.columnLayout()
        self.cameras = cmds.textScrollList(w=self.__width__, h=self.__width__/1.2)
        cmds.setParent("..")
        cmds.separator(h=5, st="none")
        cmds.button("select_cameras", label="Select Cameras", w=self.__width__, h=25, bgc=self.getcolor(), command=lambda *args: self.get_cameras())
        cmds.setParent("..")
        cmds.setParent("..")
        cmds.separator(w=15, h=80, st="single")
        cmds.columnLayout()
        cmds.text(label = "Select cameras\nand create", w=self.__width__)
        cmds.separator(h=8, st="none")
        cmds.button(label="Create!", w=self.__width__, h=35, bgc=self.getcolor(), command=lambda *args: self.create_multi())
        cmds.separator(h=8, st="none")
        self.camera_name = cmds.textField( w=self.__width__)
        cmds.setParent("..")
        cmds.separator(w=self.__margin__, st="none")
        cmds.setParent("..")
        cmds.separator(h=self.__margin__, st="none")

        cmds.showWindow(window)


    def getcolor(self):
        return [round(random.uniform(0.525, 0.750), 3) for i in range(3)]


    def get_cameras(self):
        __selection__ = cmds.ls(selection = True)
        self.selected_cameras = [c for c in __selection__ if c in [x.split("|")[-2] for x in cmds.ls(type=('camera'), l=True)]]
        self.selected_cameras.sort()
        
        cmds.deleteUI(self.cameras)
        self.cameras = cmds.textScrollList(parent=self.textScrollList_layout, w=self.__width__, h=self.__width__/1.2, append = self.selected_cameras)


    def create_multi(self):
        if not self.selected_cameras:
            return

        input_name = cmds.textField(self.camera_name, q=True, text=True)
        cam_name = input_name if input_name else "camview"
        new_cam = cmds.rename(cmds.camera()[0],cam_name)

        #Parent new camera to selected ones
        constraint = "multicam_" + new_cam + "_parentConstraint"
        for obj in self.selected_cameras:
            cmds.parentConstraint( obj, new_cam, n = constraint)

        #Lock and Hide attributes
        attributes = [str(c).split("|")[-1] for c in cmds.listAnimatable(new_cam) if "%s." % (new_cam) in str(c)]
        for a in attributes:
            cmds.setAttr (a, keyable = False, cb = False, lock = True)
        
        #Get camera names for enum attribute, shorten them id too long
        enum_names = []
        for s in self.selected_cameras:
            enum_names.append(s)
        
        #Add enum attribute with shortened names of selected cameras
        cmds.addAttr(new_cam, niceName='------', longName='selectedCamera', attributeType='enum', keyable=True, enumName = ":".join(enum_names))

        parent_attributes = []
        for attribute in cmds.listAnimatable(constraint):
            if attribute[-2] == "W" or attribute[-3] == "W":
                parent_attributes.append(attribute.split(".")[-1])

        for i, parent_attribute in enumerate(parent_attributes):
            for j in range(len(parent_attributes)):
                cmds.setDrivenKeyframe(constraint, at=parent_attribute, cd="{}.selectedCamera".format(new_cam), dv=j, v=i == j)
            cmds.setAttr("{}.{}".format(constraint,parent_attribute))
        

        #cam_name = cmds.camera(new_cam, q = True, name = True)
        plusMinusAverage = 'multicam_%s_plusMinusAverage' % (new_cam)

        if not cmds.objExists('multicam_%s_plusMinusAverage' % (new_cam)):
            cmds.shadingNode('plusMinusAverage', asUtility=True, name=plusMinusAverage)

        for i, c in enumerate(self.selected_cameras):
            
            md_name = 'multicam_%s_%s_multiplyDivide' % (new_cam,c)
            
            if not cmds.objExists(md_name):
                cmds.shadingNode('multiplyDivide', asUtility=True, name=md_name)
            
            cmds.connectAttr('%s.fl' % (c), '%s.input1X' % (md_name), f = True)
            
            cmds.connectAttr("%s.%s" % (constraint,parent_attributes[i]), '%s.input2X' % (md_name), f = True)

            cmds.connectAttr('%s.outputX' % (md_name),'%s.input1D[%s]' % (plusMinusAverage,i), f = True)

            
        cmds.connectAttr('%s.output1D' % (plusMinusAverage), '%s.fl' % (cmds.listRelatives(new_cam, shapes=True)[0]), f = True)
        UI().reload()

UI()