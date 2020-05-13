import pickle
import sys
sys.path.insert(
    0, "D:\\git\\tk-framework-unrealqt\\resources\\pyside2-5.9.0a1\\")


def webengine_hack():
    from PySide2 import QtWidgets
    app = QtWidgets.QApplication.instance()
    if app is not None:
        import sip
        app.quit()
        sip.delete(app)
    import sys
    from PySide2 import QtCore, QtWebEngineWidgets
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QtWidgets.qApp = QtWidgets.QApplication(sys.argv)
    return app


try:
    # just for testing
    from PySide2 import QtWidgets
    app = QtWidgets.QApplication([''])
    from PySide2 import QtWebEngineWidgets
except ImportError as exception:
    print('\nRetrying webengine import...')
    app = webengine_hack()


if __name__ == '__main__':
    import sys
    from PySide2.QtWidgets import QApplication
    from PySide2 import QtGui
    #app = QApplication(sys.argv)
    import syncsketchGUI
    from syncsketchGUI.lib.gui.syncsketchWidgets.mainWidget import MenuWindow

    stylesheet = """
    QHeaderView::section{
        color: #58c491;
        background-color: #5d5d5d;
    }

    QCheckBox::indicator{
        background-color:#292929;

    }
    QCheckBox{
        color:  #c8c8c8;

    }
     QLineEdit {
        border:1px outset;
        border-radius: 2px solid;
        border-color: rgb(83, 83, 83);
        color: #c8c8c8;
        background-color: rgb(255, 255, 255);
    }
        QLineEdit:focus {
        border:4px outset;
        border-radius: 8px;
        border-color: rgb(41, 237, 215);
        color:rgb(0, 0, 0);
        background-color: rgb(255, 150, 150);
    }
    QLabel{
        color: #c8c8c8;
    }
    QGroupBox{
        border:4px outset;
        border-radius: 1px;
        border-color: #494949;
        border-style: solid;
        color: #c8c8c8;
        background-color: #494949;
    }
    QWidget{
        background-color: #444444;
    }

    QPushButton {
        color: blue;
        color:  #c8c8c8;
    }
"""
    app.setStyleSheet(stylesheet)
    menu = MenuWindow(parent=None)
    menu.show()
    app.exec_()
#syncsketchGUI.show_menu_window()
