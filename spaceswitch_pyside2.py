"""

Put this file in your scripts directory:
"%USERPROFILE%\Documents\maya\####\scripts"
or
"%USERPROFILE%\Documents\maya\scripts"


Run with:

import spaceswitch_pyside2 as space
space.UI.show_dialog()


"""

from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui, maya.OpenMaya as om, maya.cmds as cmds, maya.mel as mel, base64


def MayaWindow():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(long(pointer), QtWidgets.QMainWindow)


class UI(QtWidgets.QDialog):

    SCRIPT = "spaceswitch"
    TITLE = "SpaceSwitch"
    VERSION = "0.0.6"
    """
    Messages:
    """
    NO_INTERNET = "Could not establish a connection to the server."
    WORKING_ON_IT = "Still working on this feature!"
    NO_WRITE_PERMISSION = "Insufficient write permissions."

    dlg_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = UI()
        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
            cls.dlg_instance.refresh()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()
            cls.dlg_instance.refresh()

    def __init__(self, parent=MayaWindow()):
        super(UI, self).__init__(parent=parent)
        self.namespaces = True
        self.setWindowTitle(("{} {}").format(UI.TITLE, UI.VERSION))
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setFixedWidth(220)
        self.setMaximumHeight(self.height())
        self.create_layouts()
        self.create_widgets()
        self.create_connections()

        self.check_for_updates(warning=False)

    def create_layouts(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # Menu bar
        menu_bar = QtWidgets.QMenuBar()
        settings_menu = menu_bar.addMenu("Settings")
        self.toggle_namespaces = settings_menu.addAction("Hide namespaces")
        self.toggle_namespaces.setCheckable(True)
        self.toggle_namespaces.setChecked(self.namespaces)
        settings_menu.addSeparator()
        self.all_frames = settings_menu.addAction("Apply to all frames")
        self.all_frames.setCheckable(True)

        menu_extra = menu_bar.addMenu("Extra")
        self.updates = menu_extra.addAction("Check for updates")
        menu_extra.addSeparator()
        self.credits = menu_extra.addAction("Credits")

        self.main_layout.setMenuBar(menu_bar)

        self.selection_layout = QtWidgets.QHBoxLayout()
        self.button_layout = QtWidgets.QHBoxLayout()
        self.target_layout = QtWidgets.QVBoxLayout()
        self.selected_target_layout = QtWidgets.QHBoxLayout()
        self.selected_target_layout.setSpacing(0)
        self.main_layout.addLayout(self.selection_layout)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addLayout(self.target_layout)

    def create_widgets(self):
        button_background = "QPushButton {background-color: #555555;border: transparent;} QPushButton:hover {background-color: #666666;} QPushButton:pressed {background-color: #333333;}"
        label_background = "QLabel {background-color: #333333;border-radius: 3px;}"
        self.selection = QtWidgets.QLabel()
        self.selection.setStyleSheet(label_background)
        self.selection.setFixedWidth(110)
        self.combobox = QtWidgets.QComboBox()
        self.selection_layout.addWidget(self.selection)
        self.selection_layout.addWidget(self.combobox)
        self.attribute_btn = QtWidgets.QPushButton("Set Attribute")
        self.apply_btn = QtWidgets.QPushButton("Apply")
        self.target_fold = QtWidgets.QPushButton()
        self.target_fold.setFixedSize(18, 18)
        self.target_fold.setIcon(QtGui.QIcon(":arrowDown.png"))
        self.target_fold.setStyleSheet(button_background)
        self.target_fold.setToolTip("Set a different target object.")
        self.button_layout.addWidget(self.attribute_btn)
        self.button_layout.addWidget(self.apply_btn)
        self.button_layout.addWidget(self.target_fold)
        self.separator_target = QtWidgets.QFrame(frameShape=QtWidgets.QFrame.HLine)
        self.title_target = QtWidgets.QLabel(
            "Shift + Select a different target object."
        )
        self.selected_target = QtWidgets.QLabel()
        self.selected_target.setFixedHeight(18)
        self.selected_target.setStyleSheet(label_background)
        self.target_layout.addWidget(self.separator_target)
        self.target_layout.addWidget(self.title_target)
        self.target_layout.addWidget(self.selected_target)
        self.attribute_btn.hide()
        self.separator_target.hide()
        self.title_target.hide()
        self.selected_target.hide()

    def create_connections(self):
        self.toggle_namespaces.triggered.connect(self.set_namespaces)
        self.target_fold.clicked.connect(
            lambda: self.show_hide_target(button_triggered=True)
        )
        self.attribute_btn.clicked.connect(self.select_attr)
        self.apply_btn.clicked.connect(self.apply_changes)
        self.updates.triggered.connect(self.check_for_updates)
        self.credits.triggered.connect(self.coffee)

    def showEvent(self, event):
        self.idx = om.MEventMessage.addEventCallback("SelectionChanged", self.refresh)

    def set_namespaces(self):
        self.namespaces = self.toggle_namespaces.isChecked()
        self.refresh()

    def getSelectedObj(self):
        return cmds.ls(selection=True)

    def refresh(self, *args):
        self.enum_attr = ""
        sel = self.getSelectedObj()
        no_selection = "No selection."
        no_target = "No target object selected."
        if len(sel) > 0:
            if self.namespaces:
                name = "...:%s" % sel[0].split(":")[1]
                self.selection.setText(name)
                self.selection.setAlignment(
                    QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
                )
            else:
                self.selection.setText(sel[0])
                self.selection.setAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            self.attribute_btn.hide()
            if len(self.getEnum()) > 0:
                self.apply_btn.setEnabled(True)
                self.combobox.setEnabled(True)
                self.combobox.clear()
                if len(self.getEnum()) == 1:
                    self.set_combobox(sel[0], self.getEnum()[0])
                elif len(self.getEnum()) > 1:
                    self.attribute_btn.show()
            else:
                self.apply_btn.setEnabled(False)
                self.combobox.setEnabled(False)
                self.combobox.clear()
            if len(sel) == 1:
                self.selected_target.setText(no_target)
                self.selected_target.setAlignment(
                    QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
                )
            else:
                self.show_hide_target()
                if not self.namespaces:
                    self.selected_target.setAlignment(
                        QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                    )
                else:
                    self.selected_target.setAlignment(
                        QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
                    )
                if self.namespaces:
                    name = "...:%s" % sel[1].split(":")[1]
                    self.selected_target.setText(name)
                else:
                    self.selected_target.setText(sel[1])
        else:
            self.attribute_btn.hide()
            self.selection.setText(no_selection)
            self.selected_target.setText(no_target)
            self.selection.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.selected_target.setAlignment(
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
            )
            self.apply_btn.setEnabled(False)
            self.combobox.clear()
            self.combobox.setEnabled(False)

    def getEnum(self):
        sel = self.getSelectedObj()[0]
        enum_attributes = []
        allAttrs = cmds.listAttr(sel)
        cbAttrs = cmds.listAnimatable(sel)
        if allAttrs and cbAttrs:
            orderedAttrs = [
                attr for attr in allAttrs for cb in cbAttrs if cb.endswith(attr)
            ]
            for i in orderedAttrs:
                attrType = cmds.attributeQuery(i, node=sel, attributeType=True)
                if attrType == "enum":
                    enum_values = cmds.attributeQuery(i, node=sel, listEnum=True)[
                        0
                    ].split(":")
                    attrs = ["xyz", "xzy", "yxz", "yzx", "zxy", "zyx"]
                    if not any(x in enum_values for x in attrs):
                        enum_attributes.append(i)

            if enum_attributes:
                self.apply_btn.setEnabled(True)
            else:
                self.apply_btn.setEnabled(False)
            return enum_attributes

    def select_attr(self):
        sel = self.getSelectedObj()[0]
        selected_channelbox = cmds.channelBox("mainChannelBox", q=True, sma=True)
        attrType = cmds.attributeQuery(
            selected_channelbox, node=sel, attributeType=True
        )
        if selected_channelbox:
            if not attrType == "enum":
                cmds.warning("Ensure that the selected attribute is an enum type.")
                return
            self.set_combobox(sel, selected_channelbox[0])
            self.attribute_btn.hide()
        else:
            self.attribute_btn.show()
            cmds.warning(
                "More than one attribute detected. Please select it manually and hit the 'Set Attribute' button."
            )

    def set_combobox(self, sel, enum_attr):
        self.enum_attr = enum_attr
        enumOptions = cmds.attributeQuery(enum_attr, node=sel, listEnum=True)[0].split(
            ":"
        )
        currentValue = cmds.getAttr(("{}.{}").format(sel, enum_attr))
        self.combobox.clear()
        for i, op in enumerate(enumOptions):
            self.combobox.addItem(op)
            if i == currentValue:
                self.combobox.setCurrentIndex(i)

    def show_hide_target(self, button_triggered=False):
        sel = self.getSelectedObj()
        self.open_icon = False
        for widget in (
            self.target_layout.itemAt(i) for i in range(self.target_layout.count())
        ):
            widget = widget.widget()

            def show_hide_widgets(condition_met):
                if condition_met:
                    widget.show()
                    self.open_icon = True
                else:
                    widget.hide()
                    self.adjustSize()
                    self.open_icon = False

            if not button_triggered:
                show_hide_widgets(len(sel) > 1)
            if button_triggered:
                show_hide_widgets(widget.isHidden())

        if self.open_icon:
            self.target_fold.setIcon(QtGui.QIcon(":arrowUp.png"))
        else:
            self.target_fold.setIcon(QtGui.QIcon(":arrowDown.png"))

    def apply_changes(self):
        sel = self.getSelectedObj()
        too_many_objects = "Too many objects selected!"

        def do_xform(target, all_xform=False):
            if all_xform:
                xform = all_xform
            else:
                xform = cmds.xform(target, q=True, ws=True, matrix=True)
            index = self.combobox.currentIndex()
            cmds.setAttr(("{}.{}").format(sel[0], self.enum_attr), index)
            cmds.xform(target, ws=True, matrix=xform)

        def multiple_frames(keyframes):
            cmds.undoInfo(openChunk=True)
            try:
                cmds.refresh(suspend=True)
                max_bar_value = len(keyframes) * 2
                bar_value = 1
                gMainProgressBar = mel.eval("$tmp = $gMainProgressBar")
                cmds.progressBar(
                    gMainProgressBar,
                    edit=True,
                    beginProgress=True,
                    maxValue=max_bar_value,
                )
                list_xform = []
                current_time = cmds.currentTime(q=True)
                for frame in keyframes:
                    cmds.currentTime(frame)
                    list_xform.append(cmds.xform(target, q=True, ws=True, matrix=True))
                    cmds.progressBar(
                        gMainProgressBar,
                        edit=True,
                        status="Saving Positions (%s/%s)..."
                        % (bar_value, max_bar_value),
                        step=1,
                    )
                    bar_value += 1

                for i, frame in enumerate(keyframes):
                    cmds.currentTime(frame)
                    do_xform(target, list_xform[i])
                    cmds.progressBar(
                        gMainProgressBar,
                        edit=True,
                        status="Applying Positions (%s/%s)..."
                        % (bar_value, max_bar_value),
                        step=1,
                    )
                    bar_value += 1

                cmds.currentTime(current_time)
                cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
            finally:
                cmds.refresh(suspend=False)
                cmds.undoInfo(closeChunk=True)

        # Check selection length to determinate the target.
        if len(sel) == 2:
            target = sel[1]
        elif len(sel) == 1:
            target = sel[0]
        elif len(sel) > 2:
            cmds.warning(too_many_objects)
            return

        try:
            keyframes = sorted(set(cmds.keyframe(target, query=True)))
        except:
            keyframes = None
        # Check if there is a timeline selection.
        timeline = cmds.timeControl("timeControl1", q=1, ra=1)

        if keyframes:
            if cmds.timeControl("timeControl1", rv=1, q=True):
                keyframes = sorted(
                    frame for frame in keyframes if timeline[0] <= frame <= timeline[1]
                )
                if len(keyframes) < 2:
                    cmds.currentTime(keyframes[0])
                    do_xform(target)
                else:
                    multiple_frames(keyframes)

            elif not self.all_frames.isChecked():
                do_xform(target)
            else:
                if len(keyframes) == 1:
                    do_xform(target)
                else:
                    multiple_frames(keyframes)
        else:
            do_xform(target)

    # Check for Updates
    def check_for_updates(self, warning=True, *args):
        import json, urllib2

        script_name = UI.TITLE.lower()

        url = "https://raw.githubusercontent.com/Alehaaaa/mayascripts/main/version.json"

        try:
            response = urllib2.urlopen(url, timeout=1)
        except:
            if warning:
                om.MGlobal.displayWarning(UI.NO_INTERNET)
            return
        content = response.read()

        if content:
            data = json.loads(content)
            script = data[script_name]

            version = str(script["version"])
            changelog = str("\n".join(script["changelog"]))

        if version > UI.VERSION:
            update_available = cmds.confirmDialog(
                title="New update for {0}!".format(UI.TITLE),
                message="Version {0} available, you are using {1}\n\nChangelog:\n{2}".format(
                    version, UI.VERSION, changelog
                ),
                messageAlign="center",
                button=["Install", "Close"],
                defaultButton="Install",
                cancelButton="Close",
                dismissString="Close",
            )
            if update_available == "Install":
                try:
                    repo_url = "https://raw.githubusercontent.com/Alehaaaa/mayascripts/main/aleha_tools/updater.py"

                    exec(
                        "import urllib2;exec(urllib2.urlopen('{}').read());Updater().install('{}');".format(
                            repo_url, script_name
                        )
                    )
                    self.deleteLater()

                    cmds.evalDeferred(
                        "import aleha_tools.{} as spaceswitch;spaceswitch.UI.show_dialog();".format(
                            script_name
                        )
                    )
                except:
                    cmds.warning("Could not update the script!")
                    cmds.evalDeferred(
                        "import spaceswitch_pyside2 as spaceswitch;spaceswitch.UI.show_dialog();"
                    )
                    return

        else:
            if warning:
                om.MGlobal.displayWarning("All up-to-date.")

    def coffee(self):
        aleha_credits = QtWidgets.QMessageBox()
        base64Data = "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"
        image_64_decode = base64.decodestring(base64Data)
        image = QtGui.QImage()
        image.loadFromData(image_64_decode, "JPG")
        pixmap = QtGui.QPixmap(image).scaledToHeight(56, QtCore.Qt.SmoothTransformation)
        aleha_credits.setIconPixmap(pixmap)
        aleha_credits.setWindowTitle("Buy me a coffee!")
        aleha_credits.setText(
            'Created by @Aleha - <a href=https://www.instagram.com/alejandro_anim><font color="white">Instagram</a><br><br>If you liked this set of tools,<br>you can send me some love!'
        )
        aleha_credits.setFixedSize(400, 300)
        aleha_credits.exec_()

    def closeEvent(self, event):
        try:
            om.MMessage.removeCallback(self.idx)
        except:
            pass


if __name__ == "__main__":
    try:
        ui.close()
        ui.deleteLater()
    except:
        pass

    ui = UI()
    ui.show()
