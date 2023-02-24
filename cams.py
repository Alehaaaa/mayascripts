"""

Put this file in your scripts directory:
"%USERPROFILE%\Documents\maya\####\scripts"
or
"%USERPROFILE%\Documents\maya\scripts"


Run with:

import cams
reload(cams)
cams.UI()

"""


import maya.cmds as cmds
import random


class UI:

    TITLE = "Cams"
    VERSION = "0.0.4"

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
            self.window = cmds.window(
                UI.TITLE,
                h=30,
                w=80,
                menuBar=True,
                rtf=True,
                tlb=True,
                sizeable=False,
            )
        except:
            self.window = cmds.window(
                UI.TITLE,
                h=30,
                w=80,
                menuBar=True,
                rtf=True,
                sizeable=False,
            )

        # Menu bar
        cmds.menu(label="Tools")
        cmds.menuItem(label="Reload", command=self.reload)
        cmds.menu(label="About", helpMenu=True)
        cmds.menuItem(label="Check for updates", command=self.check_for_updates)
        cmds.menuItem(divider=True)
        cmds.menuItem(label="Credits", c=lambda *args: self.coffee())

        # Cameras Layout
        cmds.columnLayout()
        self.main = cmds.rowLayout(numberOfColumns=4)
        cmds.separator(w=self.__margin__ / 2, style="none")
        cmds.iconTextButton(
            style="iconAndTextHorizontal",
            bgc=self.getcolor(),
            image1="Camera.xpm",
            label="persp",
            w=self.__width__,
            h=self.__height__,
            command="cmds.lookThru( cmds.getPanel(wf=True), 'persp')",
        )
        self.separator = cmds.separator(
            w=self.__margin__ * 1.5, height=self.__height__, style="single"
        )

        self.create_layouts()
        self.reload()

        cmds.setParent("..")
        cmds.setParent("..")
        cmds.separator(h=self.__margin__ / 2, style="none")
        cmds.showWindow(self.window)

    def create_layouts(self):

        # Get all custom cameras in scene
        cameras = [camera for camera in cmds.ls(type=("camera"), l=True)]
        startup_cameras = [
            camera.split("|")[-2]
            for camera in cameras
            if cmds.camera(
                cmds.listRelatives(camera, parent=True)[0], startupCamera=True, q=True
            )
        ]
        self.non_startup_cameras = list(
            set([camera.split("|")[-2] for camera in cameras]) - set(startup_cameras)
        )
        self.non_startup_cameras.sort()

        self.row_layout = cmds.rowLayout(
            parent=self.main, numberOfColumns=len(self.non_startup_cameras) * 2 + 4
        )
        for index, c in enumerate(self.non_startup_cameras):
            self.layouts[index] = "button_layout%s" % (index)
            cmds.rowLayout(
                self.layouts[index], parent=self.row_layout, numberOfColumns=20
            )
            cmds.iconTextButton(
                style="iconAndTextHorizontal",
                w=self.__width__,
                h=self.__height__,
                bgc=self.getcolor(),
                image="Camera.xpm",
                label=["...%s" % c[-6:] if len(c) > 8 else c][0],
                command=lambda index=index: cmds.lookThru(
                    cmds.getPanel(wf=True), self.non_startup_cameras[index]
                ),
            )

            cmds.iconTextButton(
                style="iconOnly",
                image="closeTabButton.png",
                command=lambda c=c: self.delete_cam(c),
            )

            cmds.separator(w=self.__margin__ / 5, style="none")
            cmds.setParent("..")

        cmds.window(UI.TITLE, edit=True, width=100, rtf=True)

    def delete_cam(self, cam):
        result = cmds.confirmDialog(
            title="Confirm Delete",
            message="Are you sure you want to delete this camera?",
            button=["Yes", "No"],
            defaultButton="Yes",
            cancelButton="No",
            dismissString="No",
        )
        if result == "Yes":
            multicams_nodes = [
                node for node in cmds.ls() if "multicam_%s_" % cam in node
            ]
            for i in multicams_nodes:
                try:
                    cmds.delete(i)
                except:
                    pass

            # Delete cam from self.non_startup_cameras
            button_index = [
                i for i, c in enumerate(self.non_startup_cameras) if cam in c
            ][0]
            self.non_startup_cameras.pop(button_index)

            # Delete cam
            cmds.delete(cam)
            self.reload()

    def reload(self, *args):
        try:
            cmds.deleteUI(self.row_layout)
        except:
            pass
        self.layouts = {}
        self.create_layouts()

        if not self.non_startup_cameras:
            cmds.separator(self.separator, edit=True, style="none")
        else:
            cmds.separator(self.separator, edit=True, style="single")

    def check_for_updates(self, *args):
        import json, urllib2
        import maya.OpenMaya as om

        url = "https://raw.githubusercontent.com/Alehaaaa/mayascripts/main/version.json"

        try:
            response = urllib2.urlopen(url)
        except:
            om.MGlobal.displayWarning(UI.NO_INTERNET)
            return
        content = response.read()

        if content:
            data = json.loads(content)
            script = data[UI.TITLE.lower()]

            version = str(script["version"])
            changelog = str("\n".join(script["changelog"]))

        if version > UI.VERSION:
            update_available = cmds.confirmDialog(
                title="New update for {0}!".format(UI.TITLE),
                message="Version {0} available, you are using {1}\n\nChangelog:\n{2}".format(
                    version, UI.VERSION, changelog
                ),
                messageAlign="center",
                button=["GitHub", "Close"],
                defaultButton="GitHub",
                cancelButton="Close",
                dismissString="Close",
            )
            if update_available == "GitHub":
                cmds.showHelp("https://github.com/Alehaaaa/mayascripts", absolute=True)
        else:
            om.MGlobal.displayWarning("All up-to-date.")

    def coffee(self):
        coffee = cmds.confirmDialog(
            title="Buy me a coffee!",
            message="Created by @Aleha\nIf you liked it, you can send me some love:",
            messageAlign="center",
            bgc=self.getcolor(),
            button=["Instagram", "Close"],
            defaultButton="Instagram",
            cancelButton="Close",
            dismissString="Close",
        )
        if coffee == "Instagram":
            cmds.showHelp("https://www.instagram.com/alejandro_anim/", absolute=True)

    def getcolor(self):
        return [round(random.uniform(0.525, 0.750), 3) for i in range(3)]


UI()
