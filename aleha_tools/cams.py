"""

Put this file in your scripts directory:
"%USERPROFILE%\Documents\maya\## VERSION ##\scripts"


Run with:

import aleha_tools.cams as cams
cams.UI().show(dockable=True)



"""

import random, os

from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import maya.OpenMayaUI as omui
import maya.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel


def get_maya_win():
    win_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(win_ptr), QtWidgets.QMainWindow)


def delete_workspace_control(control):
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.workspaceControl(control, e=True, close=True)
        cmds.deleteUI(control, control=True)


class UI(MayaQWidgetDockableMixin, QtWidgets.QDialog):

    TITLE = "Cams"
    VERSION = "0.0.93"
    """
    Messages:
    """
    NO_INTERNET = "Could not establish a connection to the server."
    WORKING_ON_IT = "Still working on this feature!"
    NO_WRITE_PERMISSION = "Insufficient write permissions."

    def __init__(self, parent=None):
        delete_workspace_control(self.TITLE + "WorkspaceControl")

        super(self.__class__, self).__init__(parent=parent)
        self.mayaMainWindow = get_maya_win()

        self.__height__ = 25
        self.__width__ = 75
        self.__margin__ = 6

        self.setObjectName(self.__class__.TITLE)

        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle("{} {}".format(self.TITLE, self.VERSION))
        self.setMaximumHeight(50)

        self.get_prefs()
        self.process_prefs()

        self.create_layouts()
        self.create_widgets()
        self.create_buttons()
        self.create_connections()

        self.settings_window = None
        self.options = None

        if not self.skip_update:
            self.check_for_updates(warning=False)

    def create_layouts(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)

        # Menu bar layout
        menu_bar = QtWidgets.QMenuBar()

        menu_general = menu_bar.addMenu("General")
        self.reload_btn = menu_general.addAction("Reload UI")
        self.settings_btn = menu_general.addAction("Camera Defaults")

        menu_tools = menu_bar.addMenu("Tools")
        self.multicams = menu_tools.addAction("MultiCams")
        self.add_hud = menu_tools.addAction("HUD Editor")

        self.menu_presets = QtWidgets.QMenu("HUD", self)
        self.menu_presets.aboutToShow.connect(lambda: self.add_presets())
        menu_bar.addMenu(self.menu_presets)

        self.add_presets()

        menu_extra = menu_bar.addMenu("Extra")
        self.updates = menu_extra.addAction("Check for updates")
        menu_extra.addSeparator()
        self.reset_cams_data = menu_extra.addAction("Reset Default Data")
        menu_extra.addSeparator()
        self.credits = menu_extra.addAction("Credits")

        self.main_layout.setMenuBar(menu_bar)

        # Cameras layout
        self.default_cam_layout = QtWidgets.QHBoxLayout()
        self.cameras_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(self.default_cam_layout)
        self.main_layout.setMargin(self.__margin__)

    def add_presets(self):
        self.get_prefs()
        self.menu_presets.clear()

        hud_presets = self.user_prefs.get("hud", [])
        for i in hud_presets:
            preset = self.menu_presets.addAction(i)
            preset.triggered.connect(
                lambda preset=hud_presets[i]: self.apply_selection(preset)
            )

        self.menu_presets.addSeparator()
        self.HUD_checkbox = self.menu_presets.addAction("HUD Display")
        self.HUD_checkbox.setCheckable(True)
        HUD_checkbox_state = self.HUD_display_cam()
        self.HUD_checkbox.setChecked(HUD_checkbox_state)
        self.HUD_checkbox.triggered.connect(lambda: self.HUD_display_cam(change=True))
        clear = self.menu_presets.addAction("Clear HUD")
        clear.triggered.connect(lambda: self.clear_hud())

    def create_widgets(self):

        self.default_cam_btn = self.create_icon_button(self.default_cam[0])
        self.default_cam_layout.addWidget(self.default_cam_btn)

        # Right-click menu for the default camera button
        self.default_cam_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.default_cam_btn.customContextMenuRequested.connect(
            lambda pos: self.show_context_menu(
                pos, self.default_cam[0], self.default_cam_btn
            )
        )

        self.line = QtWidgets.QFrame()
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setLineWidth(1)
        self.default_cam_layout.addWidget(self.line)
        if self.get_cameras():
            self.line.show()
        else:
            self.line.hide()

        self.default_cam_layout.addLayout(self.cameras_layout)
        self.default_cam_layout.addStretch()

    def create_buttons(self):

        for c in self.get_cameras():
            layout = QtWidgets.QHBoxLayout()

            layout.setSpacing(1)
            button = self.create_icon_button(["...%s" % c[-6:] if len(c) > 8 else c][0])
            layout.addWidget(button)
            # layout.addWidget(delete)
            self.cameras_layout.addLayout(layout)

            # Right-click menu for button
            button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(
                lambda pos, c=c, button=button: self.show_context_menu(pos, c, button)
            )

            # Connections for buttons
            button.clicked.connect(lambda c=c: self.look_thru(c))
            # delete.clicked.connect(lambda button=button: self.delete_cam(button.text()))

    def create_connections(self):

        self.default_cam_btn.clicked.connect(
            lambda: self.look_thru(self.default_cam[0])
        )

        self.settings_btn.triggered.connect(lambda: self.settings())
        self.reload_btn.triggered.connect(self.reload)
        self.multicams.triggered.connect(lambda: self.run_tools("multicams", py=False))
        self.add_hud.triggered.connect(lambda: self.run_tools("HUDWindow"))

        self.reset_cams_data.triggered.connect(lambda: self.process_prefs(reset=True))
        self.updates.triggered.connect(self.check_for_updates)
        self.credits.triggered.connect(self.coffee)

    def show_context_menu(self, pos, cam, button):

        menu = QtWidgets.QMenu()

        select_action = menu.addAction("Select")
        select_action.triggered.connect(lambda cam=cam: self.select_cam(cam))

        duplicate_action = menu.addAction("Duplicate")
        duplicate_action.triggered.connect(lambda cam=cam: self.duplicate_cam(cam))

        if cam != self.default_cam[0]:
            rename_action = menu.addAction("Rename")
            rename_action.triggered.connect(lambda cam=cam: self.rename_cam(cam))

        menu.addSeparator()

        self.resolution_checkbox = menu.addAction("Display Gate")
        self.resolution_checkbox.setCheckable(True)
        self.resolution_checkbox.setChecked(
            cmds.getAttr("{}.displayResolution".format(cam))
        )
        self.resolution_checkbox.triggered.connect(
            lambda cam=cam: self.resolution_cam(cam)
        )

        options_action = menu.addAction("Options")
        options_action.triggered.connect(lambda cam=cam: Options.show_dialog(cam))

        menu.addSeparator()
        tear_off_copy = menu.addAction("Tear Off Copy")
        tear_off_copy.triggered.connect(lambda cam=cam: self.tear_off_cam(cam))
        apply_camera_default = menu.addAction("Apply Camera Defaults")
        apply_camera_default.triggered.connect(
            lambda cam=cam: self.apply_camera_default(cam)
        )

        if cam != self.default_cam[0]:
            menu.addSeparator()
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(lambda cam=cam: self.delete_cam(cam))

        menu.exec_(button.mapToGlobal(pos))

    def apply_selection(self, settings):

        # Command for displaying the current frame number (HUD Section 4)
        def HUD_current_frame():
            # Get current frame and total frame count
            Current = cmds.currentTime(query=True)
            Total = cmds.playbackOptions(query=True, maxTime=True)
            result = "{}/{}".format(int(Current), int(Total))
            return result

        # Command for displaying the number of total frames
        def HUD_total_frames():
            result = cmds.playbackOptions(query=True, maxTime=True)
            return result

        # Command for displaying the number of total frames
        def HUD_framerate():
            fps_map = {
                "game": 15,
                "film": 24,
                "pal": 25,
                "ntsc": 30,
                "show": 48,
                "palf": 50,
                "ntscf": 60,
            }
            fps = cmds.currentUnit(q=True, t=True)
            if not isinstance(fps, float):
                fps = fps_map.get(fps, "None")
            return str(fps) + "fps"

        def HUD_camera_focal_length():
            # Get the camera attached to the active model panel
            try:
                ModelPane = cmds.getPanel(withFocus=True)
                Camera = cmds.modelPanel(ModelPane, query=True, camera=True)
                Attr = ".focalLength"
                result = cmds.getAttr(Camera + Attr)
            except:
                result = "None"
            return result

        # Command for displaying the scene name (HUD Section 7)
        def HUD_get_scene_name():
            result = cmds.file(query=True, sceneName=True)
            if not result:
                result = "UNTITLED Scene"
            else:
                result = cmds.file(query=True, sceneName=True, shortName=True)
            return result

        # Command for displaying the current user name (HUD Section 9)
        def HUD_get_username():
            username = os.getenv("USER")
            result = username if username else "UNKNOWN"
            return result

        # Command for displaying the date and hour (HUD Section 9)
        def HUD_get_date():
            import datetime

            result = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            return result

        # Show HUD Display
        FontSize = "large"  # "small" or "large"

        # Remove HUD sections if they already exist
        for pos in [0, 2, 4, 5, 7, 9]:
            cmds.headsUpDisplay(removePosition=[pos, 0])

        headsup_positions = {
            "tlc": ["top_left", 0],
            "tmc": ["top_center", 2],
            "trc": ["top_right", 4],
            "blc": ["bottom_left", 5],
            "bmc": ["bottom_center", 7],
            "brc": ["bottom_right", 9],
        }

        for key, item in headsup_positions.items():
            selected_command = settings[key]
            if selected_command != "None":
                align = item[0].split("_")[-1]

                command = None
                preset = None
                if selected_command == "Current Frame":
                    label = "Frame:"
                    command = HUD_current_frame
                elif selected_command == "Total Frames":
                    label = "Total:"
                    command = HUD_total_frames
                elif selected_command == "Framerate":
                    label = ""
                    command = HUD_framerate
                elif selected_command == "Username":
                    label = "User:"
                    command = HUD_get_username
                elif selected_command == "Scene Name":
                    label = ""
                    command = HUD_get_scene_name
                elif selected_command == "Focal Length":
                    label = "Focal Length:"
                    command = HUD_camera_focal_length
                elif selected_command == "Date":
                    label = ""
                    command = HUD_get_date
                elif selected_command == "Camera Name":
                    preset = "cameraNames"
                elif selected_command == "View Axis":
                    preset = "viewAxis"
                else:
                    continue

                if command:
                    cmds.headsUpDisplay(
                        item[0],
                        section=item[1],
                        block=0,
                        bs=FontSize,
                        label=label,
                        dfs=FontSize,
                        lfs=FontSize,
                        command=command,
                        blockAlignment=align,
                        attachToRefresh=True,
                    )
                if preset:
                    cmds.headsUpDisplay(
                        item[0],
                        section=item[1],
                        block=0,
                        bs=FontSize,
                        dfs=FontSize,
                        lfs=FontSize,
                        preset=preset,
                        blockAlignment=align,
                    )

        # Set HUD display color to Maya default
        cmds.displayColor("headsUpDisplayLabels", 16, dormant=True)
        cmds.displayColor("headsUpDisplayValues", 16, dormant=True)

    def clear_hud(self):
        for pos in [0, 2, 4, 5, 7, 9]:
            cmds.headsUpDisplay(removePosition=[pos, 0])

    def settings(self):
        self.process_prefs(save=False)

        if self.settings_window is not None:
            self.settings_window.close()
            self.settings_window.deleteLater()

        self.settings_window = QtWidgets.QDialog(parent=get_maya_win())
        self.settings_window.setWindowFlags(
            self.settings_window.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint
        )
        self.settings_window.setWindowTitle("Cams Default settings")
        self.settings_window.setFixedSize(320, 230)

        def get_float(value):
            return "{:.3f}".format(value / 1000.0)

        def update_button_color():
            rgb = self.default_gate_mask_color[0]
            qcolor = QtGui.QColor(*[int(q * 255) for q in rgb])
            h, s, v, _ = qcolor.getHsv()
            qcolor.setHsv(h, s, v)
            gate_mask_color_picker.setStyleSheet(
                "background-color: {}".format(qcolor.name())
            )
            gate_mask_color_slider.setValue(v)

        onlyFloat = QtGui.QRegExpValidator(QtCore.QRegExp(r"[0-9].+"))

        main_layout = QtWidgets.QFormLayout()
        self.settings_window.setLayout(main_layout)

        camera_select = QtWidgets.QComboBox()
        camera_select.addItems(["persp", "top", "front", "side"])
        camera_select.setCurrentText(self.default_cam[0])
        camera_select.setEnabled(self.default_cam[1])

        near_clip_plane = QtWidgets.QLineEdit()
        far_clip_plane = QtWidgets.QLineEdit()
        near_clip_plane.setText(str(self.default_near_clip_plane[0]))
        far_clip_plane.setText(str(self.default_far_clip_plane[0]))

        near_clip_plane.setEnabled(self.default_near_clip_plane[1])
        far_clip_plane.setEnabled(self.default_far_clip_plane[1])

        overscan_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        overscan_value = QtWidgets.QLineEdit()
        overscan_slider.setRange(1000, 2000)
        overscan_slider.setValue((float(self.default_overscan[0]) * 1000))
        overscan_value.setText(str(get_float(overscan_slider.value())))

        overscan_slider.setEnabled(self.default_overscan[1])
        overscan_value.setEnabled(self.default_overscan[1])

        gate_mask_opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        gate_mask_opacity_slider.setRange(0, 1000)
        gate_mask_opacity_slider.setValue(
            int(float(self.default_gate_mask_opacity[0]) * 1000)
        )

        gate_mask_opacity_value = QtWidgets.QLineEdit()
        gate_mask_opacity_value.setText(
            str(get_float(gate_mask_opacity_slider.value()))
        )

        gate_mask_opacity_slider.setEnabled(self.default_gate_mask_opacity[1])
        gate_mask_opacity_value.setEnabled(self.default_gate_mask_opacity[1])

        overscan_container = QtWidgets.QHBoxLayout()
        overscan_container.addWidget(overscan_value)
        overscan_container.addWidget(overscan_slider)

        gate_mask_opacity_container = QtWidgets.QHBoxLayout()
        gate_mask_opacity_container.addWidget(gate_mask_opacity_value)
        gate_mask_opacity_container.addWidget(gate_mask_opacity_slider)

        color_slider_and_picker = QtWidgets.QHBoxLayout()
        gate_mask_color_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        gate_mask_color_slider.setRange(0, 255)
        gate_mask_color_slider.setValue(128)
        gate_mask_color_picker = QtWidgets.QPushButton()
        gate_mask_color_picker.setFixedWidth(80)
        gate_mask_color_picker.setFixedHeight(17)

        gate_mask_color_picker.setEnabled(self.default_gate_mask_color[1])
        gate_mask_color_slider.setEnabled(self.default_gate_mask_color[1])

        update_button_color()

        color_slider_and_picker.addWidget(gate_mask_color_picker)
        color_slider_and_picker.addWidget(gate_mask_color_slider)

        near_clip_plane.setValidator(onlyFloat)
        far_clip_plane.setValidator(onlyFloat)
        overscan_value.setValidator(onlyFloat)
        gate_mask_opacity_value.setValidator(onlyFloat)

        near_clip_plane.setFixedWidth(80)
        far_clip_plane.setFixedWidth(80)
        overscan_value.setFixedWidth(80)
        gate_mask_opacity_value.setFixedWidth(80)

        ok_close_layout = QtWidgets.QHBoxLayout()
        ok_btn = QtWidgets.QPushButton("OK")
        close_btn = QtWidgets.QPushButton("Close")
        ok_close_layout.addWidget(ok_btn)
        ok_close_layout.addWidget(close_btn)

        from collections import OrderedDict

        layout_dict = OrderedDict(
            [
                ("Main camera", camera_select),
                ("Near Clip Plane", near_clip_plane),
                ("Far Clip Plane", far_clip_plane),
                ("Overscan", overscan_container),
                ("Gate Mask Opacity", gate_mask_opacity_container),
                ("Gate Mask Color", color_slider_and_picker),
            ]
        )

        # Loop through each key-value pair in the dictionary and add it to the layout with a checkbox
        for index, (key, value) in enumerate(layout_dict.items()):
            if index == 1 or index == 3:
                main_layout.addRow(QtWidgets.QFrame(frameShape=QtWidgets.QFrame.HLine))

            widget_container = QtWidgets.QHBoxLayout()
            checkbox = QtWidgets.QCheckBox()
            checkbox.setFixedWidth(15)
            widget_container.addWidget(checkbox)
            label = QtWidgets.QLabel(key)
            label.setFixedWidth(100)
            widget_container.addWidget(label)
            if isinstance(value, QtWidgets.QLayout):
                for i in range(value.count()):
                    widget = value.itemAt(i).widget()
                    if isinstance(widget, QtWidgets.QWidget):
                        checkbox.setChecked(widget.isEnabled())
                        checkbox.toggled.connect(
                            lambda checked=checkbox.isChecked(), v=widget: v.setEnabled(
                                checked
                            )
                        )
                widget_container.addLayout(value)
            if isinstance(value, QtWidgets.QWidget):
                checkbox.setChecked(value.isEnabled())
                checkbox.toggled.connect(
                    lambda checked=checkbox.isChecked(), v=value: v.setEnabled(checked)
                )
                widget_container.addWidget(value)
            main_layout.addRow(widget_container)

            if index == 5:
                main_layout.addRow(ok_close_layout)

        overscan_slider.valueChanged.connect(
            lambda: overscan_value.setText(str(get_float(overscan_slider.value())))
        )

        gate_mask_opacity_slider.valueChanged.connect(
            lambda: gate_mask_opacity_value.setText(
                get_float(gate_mask_opacity_slider.value())
            )
        )

        gate_mask_color_picker.clicked.connect(
            lambda: show_color_selector(gate_mask_color_picker)
        )

        gate_mask_color_slider.valueChanged.connect(
            lambda: update_button_value(gate_mask_color_slider.value())
        )

        all_widgets = [
            near_clip_plane,
            far_clip_plane,
            overscan_value,
            gate_mask_opacity_value,
        ]

        for widget in all_widgets:
            widget.returnPressed.connect(lambda: apply_settings())

        ok_btn.clicked.connect(lambda: apply_settings())
        close_btn.clicked.connect(lambda: self.settings_window.close())

        def update_button_value(value):
            color = gate_mask_color_picker.palette().color(QtGui.QPalette.Button)
            h, s, v, _ = color.getHsv()
            color.setHsv(h, s, value)
            gate_mask_color_picker.setStyleSheet(
                "background-color: {}".format(color.name())
            )

        def show_color_selector(button):
            initial_color = button.palette().color(QtGui.QPalette.Base)
            color = QtWidgets.QColorDialog.getColor(initial=initial_color)
            if color.isValid():
                button.setStyleSheet("background-color: {}".format(color.name()))
                h, s, v, _ = color.getHsv()
                gate_mask_color_slider.setValue(v)

        def apply_settings():

            cam = camera_select.currentText(), camera_select.isEnabled()
            near = float(near_clip_plane.text()), near_clip_plane.isEnabled()
            far = float(far_clip_plane.text()), far_clip_plane.isEnabled()
            overscan = float(overscan_value.text()), overscan_value.isEnabled()
            mask_op = (
                float(gate_mask_opacity_value.text()),
                gate_mask_opacity_value.isEnabled(),
            )
            r, g, b, _ = (
                gate_mask_color_picker.palette().color(QtGui.QPalette.Button).getRgb()
            )
            mask_color = [
                round(x / 255.0, 3) for x in [r, g, b]
            ], gate_mask_color_picker.isEnabled()

            self.process_prefs(cam, near, far, overscan, mask_op, mask_color)
            if self.default_cam[1]:
                self.default_cam_btn.setText(self.default_cam[0])
            self.settings_window.close()

        self.settings_window.show()

    """
    Create functions
    """

    def get_prefs(self):
        # Default settings

        prefs_dir = os.path.join(
            os.environ["MAYA_APP_DIR"], cmds.about(v=True), "prefs", "aleha_tools"
        )
        if not os.path.exists(prefs_dir):
            os.makedirs(prefs_dir)

        self.prefs_path = os.path.join(prefs_dir, "camsPrefs.aleha")

        if os.path.exists(self.prefs_path):
            with open(self.prefs_path, "r") as prefs_file:
                self.user_prefs = eval(prefs_file.read())
                self.cams_prefs = self.user_prefs.get("default_settings", None)
                if not self.cams_prefs:
                    self.save_prefs()

        else:
            self.user_prefs = {}
            self.save_prefs()

    def save_prefs(self, cam_prefs=None):
        if not cam_prefs:
            cam_prefs = self.initial_settings

        if not self.user_prefs.get("hud", None):
            default_hud = {
                "bmc": "Camera Name",
                "trc": "None",
                "tlc": "None",
                "tmc": "None",
                "brc": "None",
                "blc": "Axis View",
            }
            self.user_prefs["hud"] = {"Default": default_hud}

        with open(self.prefs_path, "w") as prefs_file:
            self.cams_prefs = self.user_prefs["default_settings"] = cam_prefs
            prefs_file.write(str(self.user_prefs))

    def process_prefs(
        self,
        cam=False,
        near=False,
        far=False,
        overscan=False,
        mask_op=False,
        mask_color=False,
        skip_update=False,
        reset=False,
        save=True,
    ):

        self.old_Node = "Cams_StoreNode"
        self.initial_settings = {
            "camera": ("persp", True),
            "overscan": (1.0, True),
            "near_clip": (1.0, True),
            "far_clip": (10000.0, True),
            "display_resolution": (1, True),
            "mask_opacity": (1.0, True),
            "mask_color": ([0.0, 0.0, 0.0], True),
            "skip_update": False,
        }

        if cmds.objExists(self.old_Node):
            old_Value = cmds.getAttr(self.old_Node + ".data")
            settings = eval(old_Value)
            # Convert old transformNode
            for i in self.initial_settings:
                if i == "skip_update":
                    continue
                value = settings[i]
                if type(value) != tuple:
                    settings[i] = (value, True)
                else:
                    break

            self.save_prefs(cam_prefs=settings)

            cmds.delete(self.old_Node)

        # Set the value of the attribute to a dictionary of multiple variable values
        if cam:
            self.cams_prefs["camera"] = cam
        if near:
            self.cams_prefs["near_clip"] = near
        if far:
            self.cams_prefs["far_clip"] = far
        if overscan:
            self.cams_prefs["overscan"] = overscan
        if mask_op:
            self.cams_prefs["mask_opacity"] = mask_op
        if mask_color:
            self.cams_prefs["mask_color"] = mask_color
        if skip_update:
            self.cams_prefs["skip_update"] = skip_update

        self.default_cam = self.cams_prefs["camera"]
        self.default_overscan = self.cams_prefs["overscan"]
        self.default_near_clip_plane = self.cams_prefs["near_clip"]
        self.default_far_clip_plane = self.cams_prefs["far_clip"]
        self.default_resolution = self.cams_prefs["display_resolution"]
        self.default_gate_mask_opacity = self.cams_prefs["mask_opacity"]
        self.default_gate_mask_color = self.cams_prefs["mask_color"]
        self.skip_update = self.cams_prefs["skip_update"]

        if save:

            if not reset:
                self.save_prefs(cam_prefs=self.cams_prefs)
            else:
                self.save_prefs()

    def look_thru(self, cam):
        cmds.lookThru(cmds.getPanel(wf=True), cam)

    def select_cam(self, cam):
        cmds.select(cam)

    def rename_cam(self, cam):
        self.rename_window = QtWidgets.QInputDialog()
        self.rename_window.setWindowTitle("Rename {}".format(cam))
        self.rename_window.setLabelText("New name:")
        self.rename_window.setTextValue(cam)

        self.rename_window.setWindowFlags(
            self.rename_window.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint
        )

        result = self.rename_window.exec_()

        if result == QtWidgets.QDialog.Accepted:
            input = self.rename_window.textValue()
            cmds.rename(cam, input)
            self.reload()

    def tear_off_cam(self, cam):
        def getPanelFromCamera(cameraName):
            for panelName in cmds.getPanel(type="modelPanel"):
                if cmds.modelPanel(panelName, query=True, camera=True) == cameraName:
                    return panelName

        mel.eval("tearOffCopyItemCmd modelPanel " + getPanelFromCamera(cam))

    def apply_camera_default(self, cam):
        parameters = {
            "overscan": self.default_overscan,
            "ncp": self.default_near_clip_plane,
            "fcp": self.default_far_clip_plane,
            "displayResolution": self.default_resolution,
            "displayGateMaskOpacity": self.default_gate_mask_opacity,
            "displayGateMaskColor": self.default_gate_mask_color,
        }

        for i, v in parameters.items():
            try:
                if i == "displayResolution":
                    if v[1]:
                        cmds.setAttr("{}.{}".format(cam, i), v[0])
                        cmds.setAttr("{}.displayGateMask".format(cam), v[0])
                elif i == "displayGateMaskColor":
                    if v[1]:
                        r, g, b = v[0]
                        cmds.setAttr("{}.{}".format(cam, i), r, g, b, type="double3")
                else:
                    if v[1]:
                        cmds.setAttr("{}.{}".format(cam, i), v[0])
            except:
                pass

    def resolution_cam(self, cam):
        cmds.setAttr(
            "{}.displayResolution".format(cam), self.resolution_checkbox.isChecked()
        )
        cmds.setAttr(
            "{}.displayGateMask".format(cam), self.resolution_checkbox.isChecked()
        )

    def HUD_display_cam(self, change=False):
        heads = [
            "top_left",
            "top_center",
            "top_right",
            "bottom_left",
            "bottom_center",
            "bottom_right",
        ]
        true_false = True
        for i in heads:
            try:
                state = cmds.headsUpDisplay(i, q=True, visible=True)
                true_false = state
                break
            except:
                true_false = False
                pass
        if change:
            for i in heads:
                try:
                    cmds.headsUpDisplay(i, e=True, visible=not true_false)
                except:
                    pass

            true_false = not true_false
        return true_false

    def duplicate_cam(self, cam):
        cmds.duplicate(cam)
        self.reload()

    def delete_cam(self, cam):
        delete = QtWidgets.QMessageBox()
        response = delete.question(
            None,
            "Delete {}".format(cam),
            "Are you sure you want to delete {}?".format(cam),
            delete.Yes | delete.No,
            delete.No,
        )

        if response == delete.Yes:
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

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif isinstance(item, QtWidgets.QLayout):
                    self.clearLayout(item)
                    del item

        try:
            if not self.get_cameras():
                self.line.hide()
            else:
                self.line.show()
        except:
            pass

        self.resize(80, self.height())
        self.adjustSize()

    def reload(self):
        self.clearLayout(self.cameras_layout)
        self.create_buttons()
        if self.get_cameras():
            self.line.show()
        else:
            self.line.hide()

    def get_cameras(self):
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
        return self.non_startup_cameras

    def create_icon_button(self, text):
        button = QtWidgets.QPushButton(text)
        button.setIcon(QtGui.QIcon(":Camera.png"))
        button.setStyleSheet(
            "color: rgb(0, 0, 0);background-color: rgb({})".format(
                ",".join(self.getcolor())
            )
        )
        button.setFixedSize(self.__width__, self.__height__)
        return button

    def getcolor(self):
        return [str(int(random.uniform(200 * 0.7, 200 * 0.9))) for i in range(3)]

    # Open Tools
    def run_tools(self, tool, py=True):
        if not py:
            extra = "reload(tool);tool.{}();".format(tool)
        else:
            extra = "reload(tool);tool.{}.show_dialog()".format(tool)

        exec("import aleha_tools.cams_tools.{} as tool;{}".format(tool, extra))

    """
    Extra Functionality
    """

    # Check for Updates
    def check_for_updates(self, warning=True, *args):
        import json, urllib2

        script_name = self.TITLE.lower()

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
            changelog = script["changelog"]

        def convert_list_to_string():
            result, sublst = [], []
            for item in changelog:
                if item:
                    sublst.append(str(item))
                else:
                    if sublst:
                        result.append(sublst)
                        sublst = []
            if sublst:
                result.append(sublst)
            result = result[:4]
            result.append(["== And more =="])
            return "\n\n".join(["\n".join(x) for x in result])

        if version > self.VERSION:
            update_available = cmds.confirmDialog(
                title="New update for {0}!".format(self.TITLE),
                message="Version {0} available, you are using {1}\n\nChangelog:\n{2}".format(
                    version, self.VERSION, convert_list_to_string()
                ),
                messageAlign="center",
                button=["Install", "Skip", "Close"],
                defaultButton="Install",
                cancelButton="Close",
            )
            if update_available == "Install":

                import aleha_tools.updater as updater

                reload(updater)

                updater.Updater().install(script_name)
                try:
                    currentShelf = cmds.tabLayout(
                        mel.eval("$nul=$gShelfTopLevel"), q=1, st=1
                    )
                    buttons = cmds.shelfLayout(currentShelf, q=True, ca=True)
                    for b in buttons:
                        if (
                            cmds.shelfButton(b, exists=True)
                            and cmds.shelfButton(b, q=True, l=True) == "cams"
                        ):
                            cmds.shelfButton(
                                b,
                                edit=True,
                                command="import aleha_tools.cams as cams;cams.UI().show(dockable=True)",
                            )
                except:
                    pass

                self.deleteLater()
                cmds.evalDeferred(
                    "import aleha_tools.{} as cams;reload(cams);cams.UI().show(dockable=True);".format(
                        script_name
                    )
                )

            elif update_available == "Skip":
                self.process_prefs(skip_update=1)
        else:
            if warning:
                om.MGlobal.displayWarning("All up-to-date.")

    def coffee(self):

        import base64

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
            # cmds.scriptJob(kill=self.script_job_id)
            for no_py in ["MultiCams"]:
                cmds.deleteUI(no_py)
        except:
            pass
        event.accept()

    def contextMenuEvent(self, event):
        event.ignore()


"""
Options
"""


class Options(QtWidgets.QDialog):

    dlg_instance = None

    @classmethod
    def show_dialog(cls, cams):
        try:
            cls.dlg_instance.close()
            cls.dlg_instance.deleteLater()
        except:
            pass

        cls.dlg_instance = Options(cams)
        cls.dlg_instance.show()

    def __init__(self, cam, parent=None):
        super(Options, self).__init__(get_maya_win())

        self.cam = cam

        self.setWindowTitle("Options: {}".format(self.cam))
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setFixedSize(300, 227)

        # First section: Attributes
        self.onlyFloat = QtGui.QRegExpValidator(QtCore.QRegExp(r"[0-9].+"))

        self.create_layouts()
        self.create_widgets()
        self.create_connections()

        # self.script_job_id = cmds.scriptJob(event=["Undo", self.reload])

    def create_layouts(self):

        self.form_layout = QtWidgets.QFormLayout(self)
        self.focal_length_container = QtWidgets.QHBoxLayout()
        self.overscan_container = QtWidgets.QHBoxLayout()
        self.opacity_self = QtWidgets.QHBoxLayout()
        self.color_slider_and_picker = QtWidgets.QHBoxLayout()
        self.apply_buttons = QtWidgets.QHBoxLayout()

    def create_widgets(self):

        self.focal_length_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.focal_length_slider.setRange(2500, 500000)
        self.focal_length_slider.setValue(
            int(round(cmds.getAttr("{}.fl".format(self.cam)) * 1000))
        )

        self.focal_length_value = QtWidgets.QLineEdit()
        self.focal_length_value.setText(
            str(self.get_float(self.focal_length_slider.value()))
        )
        self.focal_length_value.setFixedWidth(80)

        self.overscan_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.overscan_slider.setRange(1000, 2000)
        self.overscan_slider.setValue(
            int(cmds.getAttr("{}.overscan".format(self.cam)) * 1000)
        )

        self.overscan_value = QtWidgets.QLineEdit()
        self.overscan_value.setText(str(self.get_float(self.overscan_slider.value())))
        self.overscan_value.setFixedWidth(80)

        self.near_clip_plane = QtWidgets.QLineEdit()
        self.far_clip_plane = QtWidgets.QLineEdit()
        self.near_clip_plane.setFixedWidth(80)
        self.far_clip_plane.setFixedWidth(80)

        self.focal_length_value.setValidator(self.onlyFloat)
        self.overscan_value.setValidator(self.onlyFloat)
        self.near_clip_plane.setValidator(self.onlyFloat)
        self.far_clip_plane.setValidator(self.onlyFloat)

        self.near_clip_plane.setText(str(cmds.getAttr("{}.ncp".format(self.cam))))
        self.far_clip_plane.setText(str(cmds.getAttr("{}.fcp".format(self.cam))))

        self.focal_length_container.addWidget(self.focal_length_value)
        self.focal_length_container.addWidget(self.focal_length_slider)

        self.overscan_container.addWidget(self.overscan_value)
        self.overscan_container.addWidget(self.overscan_slider)

        # Second section: Display Options
        self.gate_mask_opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.gate_mask_opacity_slider.setRange(0, 1000)
        self.gate_mask_opacity_slider.setValue(
            int(
                round(cmds.getAttr("{}.displayGateMaskOpacity".format(self.cam)) * 1000)
            )
        )
        self.gate_mask_opacity_value = QtWidgets.QLineEdit()
        self.gate_mask_opacity_value.setText(
            str(self.get_float(self.gate_mask_opacity_slider.value()))
        )
        self.gate_mask_opacity_value.setFixedWidth(80)
        self.opacity_self.addWidget(self.gate_mask_opacity_value)
        self.opacity_self.addWidget(self.gate_mask_opacity_slider)

        self.gate_mask_color_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.gate_mask_color_slider.setRange(0, 255)
        self.gate_mask_color_slider.setValue(128)
        self.gate_mask_color_picker = QtWidgets.QPushButton()
        self.gate_mask_color_picker.setFixedWidth(80)
        self.gate_mask_color_picker.setFixedHeight(17)

        self.update_button_color(self.cam)

        self.color_slider_and_picker.addWidget(self.gate_mask_color_picker)
        self.color_slider_and_picker.addWidget(self.gate_mask_color_slider)

        self.ok_btn = QtWidgets.QPushButton("OK")
        self.apply_btn = QtWidgets.QPushButton("Apply")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")

        self.apply_buttons.addWidget(self.ok_btn)
        self.apply_buttons.addWidget(self.apply_btn)
        self.apply_buttons.addWidget(self.cancel_btn)

        self.form_layout.addRow("Focal Length:", self.focal_length_container)
        self.form_layout.addRow(QtWidgets.QFrame(frameShape=QtWidgets.QFrame.HLine))
        self.form_layout.addRow("Near Clip Plane:", self.near_clip_plane)
        self.form_layout.addRow("Far Clip Plane:", self.far_clip_plane)
        self.form_layout.addRow(QtWidgets.QFrame(frameShape=QtWidgets.QFrame.HLine))
        self.form_layout.addRow("Overscan:", self.overscan_container)
        self.form_layout.addRow("Gate Mask Opacity:", self.opacity_self)
        self.form_layout.addRow("Gate Mask Color:", self.color_slider_and_picker)

        self.form_layout.addRow(self.apply_buttons)

    def create_connections(self):

        all_widgets = [
            self.focal_length_value,
            self.overscan_value,
            self.near_clip_plane,
            self.far_clip_plane,
            self.gate_mask_opacity_value,
        ]

        for widget in all_widgets:
            widget.returnPressed.connect(
                lambda cam=self.cam: self.apply_modifications(cam, close=True)
            )

        self.ok_btn.clicked.connect(
            lambda cam=self.cam: self.apply_modifications(cam, close=True)
        )
        self.apply_btn.clicked.connect(
            lambda cam=self.cam: self.apply_modifications(cam)
        )
        self.cancel_btn.clicked.connect(self.close)

        self.focal_length_slider.valueChanged.connect(
            lambda: self.focal_length_value.setText(
                str(self.get_float(self.focal_length_slider.value()))
            )
        )

        self.overscan_slider.valueChanged.connect(
            lambda: self.overscan_value.setText(
                str(self.get_float(self.overscan_slider.value()))
            )
        )

        self.gate_mask_opacity_slider.valueChanged.connect(
            lambda: self.gate_mask_opacity_value.setText(
                self.get_float(self.gate_mask_opacity_slider.value())
            )
        )

        self.gate_mask_color_picker.clicked.connect(
            lambda: self.show_color_selector(self.gate_mask_color_picker)
        )

        self.gate_mask_color_slider.valueChanged.connect(
            lambda: self.update_button_value(self.gate_mask_color_slider.value())
        )

    """
    Create functions
    """

    def apply_modifications(self, cam, close=False):
        self.get_picker_color()
        parameters = {
            "fl": self.focal_length_value.text(),
            "overscan": self.overscan_value.text(),
            "ncp": self.near_clip_plane.text(),
            "fcp": self.far_clip_plane.text(),
            "displayGateMaskOpacity": self.gate_mask_opacity_value.text(),
            "displayGateMaskColor": "rgbf",
        }

        for i, v in parameters.items():
            try:
                if v != "rgbf":
                    cmds.setAttr("{}.{}".format(cam, i), float(v))
                else:
                    r, g, b = self.gate_mask_color_rgbf
                    cmds.setAttr("{}.{}".format(cam, i), r, g, b, type="double3")
            except:
                pass

        if close:
            self.close()

    def get_float(self, value):
        return "{:.3f}".format(value / 1000.0)

    def get_picker_color(self):
        style_sheet = self.gate_mask_color_picker.styleSheet()
        bg_color = style_sheet[style_sheet.find(":") + 1 :].strip()
        qcolor = QtGui.QColor(bg_color)
        r, g, b, _ = qcolor.getRgbF()
        self.gate_mask_color_rgbf = [r, g, b]

    def update_button_color(self, cam):
        rgb = cmds.getAttr(cam + ".displayGateMaskColor")[0]
        qcolor = QtGui.QColor(*[int(q * 255) for q in rgb])
        h, s, v, _ = qcolor.getHsv()
        qcolor.setHsv(h, s, v)
        self.gate_mask_color_picker.setStyleSheet(
            "background-color: {}".format(qcolor.name())
        )
        self.gate_mask_color_slider.setValue(v)

    def update_button_value(self, value):
        color = self.gate_mask_color_picker.palette().color(QtGui.QPalette.Button)
        h, s, v, _ = color.getHsv()
        color.setHsv(h, s, value)
        self.gate_mask_color_picker.setStyleSheet(
            "background-color: {}".format(color.name())
        )

    def show_color_selector(self, button):
        initial_color = button.palette().color(QtGui.QPalette.Base)
        color = QtWidgets.QColorDialog.getColor(initial=initial_color)
        if color.isValid():
            button.setStyleSheet("background-color: {}".format(color.name()))
            h, s, v, _ = color.getHsv()
            self.gate_mask_color_slider.setValue(v)
