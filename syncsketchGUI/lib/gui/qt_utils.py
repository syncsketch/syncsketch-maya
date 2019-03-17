from syncsketchGUI.vendor.Qt import QtWidgets, QtCore, QtGui

class suppressedUI():
    def __init__(self, ui):
        self.ui = ui
    def __enter__(self):
        self.ui.blockSignals(True)
        return self.ui
    def __exit__(self, *args):
        self.ui.blockSignals(False)

def enable_interface(ui_to_toggle, isEnabled):
    for ui in ui_to_toggle:
        ui.setEnabled(isEnabled)


def align_to_center(widget, align_object):
    """
    If the UI has a parent, align to it.
    If not, align to the center of the desktop.
    """
    ui_size = widget.geometry()
    if align_object:
        align_object_center = align_object.frameGeometry().center()
        x_coordinate = align_object_center.x() -(ui_size.width() / 2)
        y_coordinate = align_object_center.y() -(ui_size.height() / 2)

    else:
        desktop_screen = QtGui.QDesktopWidget().screenGeometry()
        x_coordinate =(desktop_screen.width() - ui_size.width()) / 2
        y_coordinate =(desktop_screen.height() - ui_size.height()) / 2

    widget.move(x_coordinate, y_coordinate)
    return widget.geometry()