import maya.cmds as cmds
import urllib2, random

"""
MultiCams Tool
"""


class multicams:

    TITLE = "MultiCams"

    def __init__(self):

        self.__margin__ = 3
        self.__width__ = 90

        # Create window
        if cmds.window(multicams.TITLE, exists=True):
            cmds.deleteUI(multicams.TITLE)
        try:
            window = cmds.window(
                multicams.TITLE, menuBar=True, rtf=True, tlb=True, s=False
            )
        except:
            window = cmds.window(multicams.TITLE, menuBar=True, rtf=True, s=False)

        cmds.columnLayout()
        cmds.separator(h=self.__margin__, st="none")

        cmds.rowLayout(numberOfColumns=5)
        cmds.separator(w=self.__margin__, st="none")
        cmds.rowColumnLayout(numberOfColumns=3)
        cmds.columnLayout()
        self.textScrollList_layout = cmds.columnLayout()
        self.cameras = cmds.textScrollList(w=self.__width__, h=self.__width__ / 1.2)
        cmds.setParent("..")
        cmds.separator(h=5, st="none")
        cmds.button(
            "select_cameras",
            label="Select Cameras",
            w=self.__width__,
            h=25,
            bgc=self.getcolor(),
            command=lambda *args: self.get_cameras(),
        )
        cmds.setParent("..")
        cmds.setParent("..")
        cmds.separator(w=15, h=80, st="single")
        cmds.columnLayout()
        cmds.text(label="Select cameras\nand create", w=self.__width__)
        cmds.separator(h=8, st="none")
        cmds.button(
            label="Create!",
            w=self.__width__,
            h=35,
            bgc=self.getcolor(),
            command=lambda *args: self.create_multi(),
        )
        cmds.separator(h=8, st="none")
        self.camera_name = cmds.textField(w=self.__width__)
        cmds.setParent("..")
        cmds.separator(w=self.__margin__, st="none")
        cmds.setParent("..")
        cmds.separator(h=self.__margin__, st="none")

        cmds.showWindow(window)

    def getcolor(self):
        return [round(random.uniform(0.525, 0.750), 3) for i in range(3)]

    def get_cameras(self):
        __selection__ = cmds.ls(selection=True)
        self.selected_cameras = [
            c
            for c in __selection__
            if c in [x.split("|")[-2] for x in cmds.ls(type=("camera"), l=True)]
        ]
        self.selected_cameras.sort()

        cmds.deleteUI(self.cameras)
        self.cameras = cmds.textScrollList(
            parent=self.textScrollList_layout,
            w=self.__width__,
            h=self.__width__ / 1.2,
            append=self.selected_cameras,
        )

    def create_multi(self):
        if not self.selected_cameras:
            return

        input_name = cmds.textField(self.camera_name, q=True, text=True)
        cam_name = input_name if input_name else "camview"
        new_cam = cmds.rename(cmds.camera()[0], cam_name)

        # Parent new camera to selected ones
        constraint = "multicam_" + new_cam + "_parentConstraint"
        for obj in self.selected_cameras:
            cmds.parentConstraint(obj, new_cam, n=constraint)

        # Lock and Hide attributes
        attributes = [
            str(c).split("|")[-1]
            for c in cmds.listAnimatable(new_cam)
            if "%s." % (new_cam) in str(c)
        ]
        for a in attributes:
            cmds.setAttr(a, keyable=False, cb=False, lock=True)

        # Get camera names for enum attribute, shorten them id too long
        enum_names = []
        for s in self.selected_cameras:
            enum_names.append(s)

        # Add enum attribute with shortened names of selected cameras
        cmds.addAttr(
            new_cam,
            niceName="------",
            longName="selectedCamera",
            attributeType="enum",
            keyable=True,
            enumName=":".join(enum_names),
        )

        parent_attributes = []
        for attribute in cmds.listAnimatable(constraint):
            if attribute[-2] == "W" or attribute[-3] == "W":
                parent_attributes.append(attribute.split(".")[-1])

        for i, parent_attribute in enumerate(parent_attributes):
            for j in range(len(parent_attributes)):
                cmds.setDrivenKeyframe(
                    constraint,
                    at=parent_attribute,
                    cd="{}.selectedCamera".format(new_cam),
                    dv=j,
                    v=i == j,
                )
            cmds.setAttr("{}.{}".format(constraint, parent_attribute))

        # cam_name = cmds.camera(new_cam, q = True, name = True)
        plusMinusAverage = "multicam_%s_plusMinusAverage" % (new_cam)

        if not cmds.objExists("multicam_%s_plusMinusAverage" % (new_cam)):
            cmds.shadingNode("plusMinusAverage", asUtility=True, name=plusMinusAverage)

        for i, c in enumerate(self.selected_cameras):

            md_name = "multicam_%s_%s_multiplyDivide" % (new_cam, c)

            if not cmds.objExists(md_name):
                cmds.shadingNode("multiplyDivide", asUtility=True, name=md_name)

            cmds.connectAttr("%s.fl" % (c), "%s.input1X" % (md_name), f=True)

            cmds.connectAttr(
                "%s.%s" % (constraint, parent_attributes[i]),
                "%s.input2X" % (md_name),
                f=True,
            )

            cmds.connectAttr(
                "%s.outputX" % (md_name),
                "%s.input1D[%s]" % (plusMinusAverage, i),
                f=True,
            )

        cmds.connectAttr(
            "%s.output1D" % (plusMinusAverage),
            "%s.fl" % (cmds.listRelatives(new_cam, shapes=True)[0]),
            f=True,
        )
