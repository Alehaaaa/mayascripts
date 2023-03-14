import datetime, os
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide2 import QtCore, QtGui, QtWidgets
from shiboken2 import wrapInstance


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)


class HUDWindow(QtWidgets.QMainWindow):

    dlg_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = HUDWindow()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()

        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self, parent=maya_main_window()):
        super(HUDWindow, self).__init__(parent)
        self.setWindowTitle("Add HUD Items")
        self.setFixedSize(370, 260)

        """try:"""
        self.get_prefs()
        """except:
            cmds.warning("Error while reading the preferences file at %s"%self.prefs_path)
            return"""

        # Menu bar layout
        menu_bar = QtWidgets.QMenuBar()
        self.menu_presets = menu_bar.addMenu("Presets")
        for i in self.hud_presets:
            self.add_menu_preset(i)

        menu_edit = menu_bar.addMenu("Edit")
        new_btn = menu_edit.addAction("New")
        self.duplicate_btn = menu_edit.addAction("Duplicate")
        menu_edit.addSeparator()
        self.delete_btn = menu_edit.addAction("Delete Current")

        new_btn.triggered.connect(lambda: self.new_preset())
        self.duplicate_btn.triggered.connect(lambda: self.new_preset(duplicate=True))
        self.delete_btn.triggered.connect(lambda: self.delete_preset())

        self.setMenuBar(menu_bar)

        # Create a widget to hold the rectangle and comboboxes
        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)

        # Create a layout for the widget
        layout = QtWidgets.QVBoxLayout(widget)

        # Create the rectangle and add it to the layout
        rectangle = QtWidgets.QFrame()
        rectangle.setFrameShape(QtWidgets.QFrame.StyledPanel)
        width = 350
        rectangle.setFixedSize(width, width / 16 * 9)

        ok_cancel_layout = QtWidgets.QHBoxLayout()
        ok_btn = QtWidgets.QPushButton("Ok")
        cancel_btn = QtWidgets.QPushButton("Cancel")
        ok_cancel_layout.addWidget(ok_btn)
        ok_cancel_layout.addWidget(cancel_btn)

        layout.addWidget(rectangle)
        layout.addLayout(ok_cancel_layout)

        # Create a layout for the comboboxes
        combo_layout = QtWidgets.QGridLayout()

        self.all_combos = {
            "tlc": ["top_left", 0],
            "tmc": ["top_mid", 2],
            "trc": ["top_right", 4],
            "blc": ["bottom_left", 5],
            "bmc": ["bottom_mid", 7],
            "brc": ["bottom_right", 9],
        }
        items = [
            "None",
            "Scene Name",
            "Current Frame",
            "Total Frames",
            "Framerate",
            "Username",
            "Date",
        ]

        # Create the comboboxes and add them to the layout
        self.tlc = QtWidgets.QComboBox()
        self.tlc.addItems(items)
        combo_layout.addWidget(self.tlc, 0, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.tmc = QtWidgets.QComboBox()
        self.tmc.addItems(items)
        combo_layout.addWidget(
            self.tmc, 0, 1, QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter
        )

        self.trc = QtWidgets.QComboBox()
        self.trc.addItems(items)
        combo_layout.addWidget(
            self.trc, 0, 2, QtCore.Qt.AlignTop | QtCore.Qt.AlignRight
        )

        self.blc = QtWidgets.QComboBox()
        self.blc.addItems(items)
        combo_layout.addWidget(
            self.blc, 2, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft
        )

        self.bmc = QtWidgets.QComboBox()
        self.bmc.addItems(items)
        combo_layout.addWidget(
            self.bmc, 2, 1, QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter
        )

        self.brc = QtWidgets.QComboBox()
        self.brc.addItems(items)
        combo_layout.addWidget(
            self.brc, 2, 2, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight
        )

        title_layout = QtWidgets.QVBoxLayout()
        title_layout.setSpacing(4)

        self.preset_title = QtWidgets.QLineEdit()
        self.preset_title.setStyleSheet("font-size: 16px;")
        self.preset_title.setMaxLength(25)
        title_layout.addWidget(QtWidgets.QLabel("Current Preset:"))
        title_layout.addWidget(self.preset_title)
        combo_layout.addLayout(title_layout, 1, 1, QtCore.Qt.AlignCenter)

        self.preset_title.returnPressed.connect(lambda: self.save_prefs())

        # Set the spacing of the combobox layout
        combo_layout.setSpacing(10)

        # Add the combobox layout to the rectangle
        rectangle.setLayout(combo_layout)

        self.refresh_ui()

        ok_btn.clicked.connect(lambda: self.save_changes())
        cancel_btn.clicked.connect(lambda: self.close())

    def add_menu_preset(self, preset_name):
        preset_btn = self.menu_presets.addAction(preset_name)
        preset_btn.triggered.connect(
            lambda preset=preset_name: self.refresh_ui(preset, change=True)
        )

    def save_changes(self):
        self.save_prefs()
        self.close()

    def get_current_preset(self):
        return str(self.preset_title.text())

    def get_prefs(self):

        prefs_dir = os.path.join(
            os.environ["MAYA_APP_DIR"], cmds.about(v=True), "prefs", "aleha_tools"
        )
        if not os.path.exists(prefs_dir):
            os.makedirs(prefs_dir)

        self.prefs_path = os.path.join(prefs_dir, "camsPrefs.aleha")

        self.default_prefs = {
            "bmc": "None",
            "trc": "None",
            "tlc": "None",
            "tmc": "None",
            "brc": "None",
            "blc": "None",
        }
        if not os.path.exists(self.prefs_path):

            with open(self.prefs_path, "w+") as prefs_file:
                # Default HUD settings
                default_hud = {"hud": {"Default": self.default_prefs}}

                prefs_file.write(str(default_hud))

                self.user_prefs = default_hud
                self.hud_presets = self.user_prefs["hud"]

        else:
            with open(self.prefs_path, "r") as prefs_file:
                self.user_prefs = eval(prefs_file.read())
                self.hud_presets = self.user_prefs["hud"]

    def save_prefs(self):
        current_preset = self.get_current_preset()

        try:
            if current_preset != self.displayed_preset:
                self.hud_presets[current_preset] = self.hud_presets.pop(
                    self.displayed_preset
                )
                for action in self.menu_presets.actions():
                    if action.text() == self.displayed_preset:
                        self.menu_presets.removeAction(action)
                self.add_menu_preset(current_preset)
                self.displayed_preset = current_preset

            for combo in self.all_combos:
                current_text = getattr(self, combo).currentText()
                self.hud_presets[current_preset][combo] = str(current_text)
        except:
            self.preset_title.setText("")
            pass
        self.preset_title.clearFocus()

        with open(self.prefs_path, "w") as prefs_file:
            self.user_prefs["hud"] = self.hud_presets
            prefs_file.write(str(self.user_prefs))

    def new_preset(self, duplicate=False):
        def get_new_name(name="New Preset"):
            for r in range(30):
                preset_name = "%s %s" % (name, r) if r else name
                if preset_name not in list(self.hud_presets.keys()):
                    break
            return preset_name

        if duplicate:
            current_preset = self.get_current_preset()
            preset_name = get_new_name(current_preset)
            self.hud_presets[preset_name] = self.hud_presets[current_preset].copy()

            self.add_menu_preset(preset_name)
        else:
            preset_name = get_new_name()
            self.hud_presets[preset_name] = {
                "bmc": "None",
                "trc": "None",
                "tlc": "None",
                "tmc": "None",
                "brc": "None",
                "blc": "None",
            }

            self.add_menu_preset(preset_name)
        self.refresh_ui(preset_name, change=True)
        self.save_prefs()
        self.preset_title.setFocus()

    def delete_preset(self):
        current_preset = self.get_current_preset()

        delete = QtWidgets.QMessageBox()
        response = delete.question(
            None,
            "Delete Preset",
            "Are you sure you want to delete %s?" % current_preset,
            delete.Yes | delete.No,
            delete.No,
        )

        if response == delete.Yes:
            self.hud_presets.pop(current_preset)

            for action in self.menu_presets.actions():
                if action.text() == current_preset:
                    self.menu_presets.removeAction(action)
            self.refresh_ui()
            self.save_prefs()

    def refresh_ui(self, preset=None, change=False):
        current_preset = self.get_current_preset()

        if len(self.hud_presets.keys()) < 1:
            self.delete_btn.setVisible(False)
            self.duplicate_btn.setVisible(False)
            self.menu_presets
            preset = ""
        else:
            self.duplicate_btn.setVisible(True)
            self.delete_btn.setVisible(True)

            if preset != current_preset:
                if change:
                    if self.displayed_preset != "":
                        for combo in self.all_combos:
                            current_text = getattr(self, combo).currentText()
                            if (
                                current_text
                                != self.user_prefs["hud"][self.displayed_preset][combo]
                            ):
                                changes = QtWidgets.QMessageBox()
                                response = changes.question(
                                    None,
                                    "Unsaved changes",
                                    "Do you want to save the changes made to this preset?",
                                    changes.Yes | changes.No,
                                    changes.No,
                                )

                                if response == changes.Yes:
                                    self.save_prefs()
                                break
                    self.preset_title.clearFocus()
                else:
                    preset = self.hud_presets.keys()[0]
                    self.preset_title.clearFocus()

                for combo in self.all_combos:
                    current_selection = self.hud_presets[preset][combo]
                    getattr(self, combo).setCurrentText(
                        current_selection if current_selection else "None"
                    )

            self.preset_title.setText(preset)

        if self.preset_title.text():
            self.preset_title.setEnabled(True)
        else:
            self.preset_title.setEnabled(False)

        self.displayed_preset = preset


if __name__ == "__main__":
    HUDWindow.show_dialog()
