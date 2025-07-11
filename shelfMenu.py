from maya import cmds
from maya import OpenMayaUI as omui
from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance

def get_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QMainWindow)

def get_meshes_with_visibility():
    visibility_dict = {}
    for lay in [l for l in cmds.ls("layout") if "|geo|" in l]:
        if targets:
            if not any(lay.startswith(x) for x in targets):
                continue
        visibility_dict[lay] = cmds.getAttr(lay + ".v")

    return visibility_dict

class StickyMenu(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super(StickyMenu, self).__init__(parent)

    def mouseReleaseEvent(self, event):
        action = self.actionAt(event.pos())
        if action and action.isCheckable():
            action.setChecked(not action.isChecked())
            event.accept()
        else:
            super(StickyMenu, self).mouseReleaseEvent(event)

    def addCheckableAction(self, label, checked, callback):
        if "|" in label:
            label = label.split("|")[0]
        label = name = ''.join([char for char in label if char.isalpha()])
        action = QtWidgets.QAction(label, self)
        action.setCheckable(True)
        action.setChecked(checked)
        action.toggled.connect(callback)
        self.addAction(action)

def show_mesh_visibility_menu():
    mesh_visibility = get_meshes_with_visibility()
    if not mesh_visibility:
        cmds.warning("No mesh objects found.")
        return

    menu = StickyMenu(get_main_window())

    for mesh, visible in sorted(mesh_visibility.items()):
        def make_callback(mesh_name):
            def toggle(state):
                cmds.setAttr(mesh_name + ".visibility", state)
                
                display_name = mesh_name
                if "|" in display_name:
                    display_name = display_name.split("|")[0]  # Get last part (leaf node)
                display_name = ''.join(c for c in display_name if c.isalpha())
    
                cmds.warning(("Shown" if state else "Hidden") +' layoutRig for '+display_name )
            return toggle
        menu.addCheckableAction(mesh, visible, make_callback(mesh))

    menu.popup(QtGui.QCursor.pos())

if __name__ == "__main__":
    show_mesh_visibility_menu()
