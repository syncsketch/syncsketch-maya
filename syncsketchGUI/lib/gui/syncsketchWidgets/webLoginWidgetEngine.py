from jinja2 import Template
from PySide2 import QtCore, QtWidgets, QtWebEngineWidgets, QtWebChannel
import json
import os
import sys
import sys

import syncsketchGUI.lib.user as user

class Element(QtCore.QObject):
    loaded = QtCore.Signal()

    def __init__(self, name, parent=None):
        print "parent Element : {}".format(parent)
        super(Element, self).__init__(parent)
        self._name = name
        self._is_loaded = False

    @property
    def name(self):
        return self._name

    @property
    def is_loaded(self):
        return self._is_loaded

    @QtCore.Slot()
    def set_loaded(self):
        self._is_loaded = True
        self.loaded.emit()

    def initial_script(self):
        return ""

    def render_script(self, script, **kwargs):
        kwargs["name"] = self.name
        return Template(script).render(**kwargs)


class TestObject(Element):
    def __init__(self, name, parent=None):
        print "parent Element : {}".format(parent)
        super(TestObject, self).__init__(parent)
        #self._name = name
        #self._is_loaded = False

    def initial_script(self):
        _script = r"""
        {{name}}.test('initial');
        """
        return self.render_script(_script)

    @QtCore.Slot(str)
    def test(self, res):
        current_user = user.SyncSketchUser()
        print "parent: {}".format(self.parent)
        jsonData = res
        print(jsonData)
        if not jsonData == "initial":
            print(type(jsonData))
            if isinstance(jsonData, unicode):
                tokenData = json.loads(jsonData)
                print(tokenData)
                #logger.info("tokenData: {0}".format(tokenData))
                current_user.set_name(tokenData["email"])
                current_user.set_token(tokenData["token"])
                current_user.set_api_key(tokenData["token"])
                current_user.auto_login()

                # self.parent.update_login_ui()
                # self.parent.populateTree()
                # self.parent.restore_ui_state()

            #if isinstance(jsonData, untokenData = json.loads(jsonData)
            print(res)


class WebEnginePage(QtWebEngineWidgets.QWebEnginePage):
    def __init__(self, *args, **kwargs):
        super(WebEnginePage, self).__init__(*args, **kwargs)
        self.loadFinished.connect(self.onLoadFinished)
        self._objects = []

    def add_object(self, obj):
        self._objects.append(obj)

    @QtCore.Slot(bool)
    def onLoadFinished(self, ok):
        if ok:
            self.load_qwebchannel()
            self.load_objects()

    def load_qwebchannel(self):
        file = QtCore.QFile(":/qtwebchannel/qwebchannel.js")
        if file.open(QtCore.QIODevice.ReadOnly):
            content = file.readAll()
            file.close()
            self.runJavaScript(content.data().decode("utf8"))
        if self.webChannel() is None:
            channel = QtWebChannel.QWebChannel(self)
            self.setWebChannel(channel)

    def load_objects(self):
        if self.webChannel() is not None:
            self.webChannel().registerObject("qt_page", self)
            objects = {obj.name: obj for obj in self._objects}
            self.webChannel().registerObjects(objects)
            _script = r"""
            var qt_page = null;
            {% for obj in objects %}
            var {{obj}} = null;
            {% endfor %}
            new QWebChannel(qt.webChannelTransport, function (channel) {
                qt_page = channel.objects.qt_page;
                {% for obj in objects %}
                    {{obj}} = channel.objects.{{obj}};
                    qt_page.initial_execute("{{obj}}");
                    {{obj}}.set_loaded()
                {% endfor %}
            });
            """
            self.runJavaScript(
                Template(_script).render(objects=objects.keys()))

    @QtCore.Slot(str)
    def initial_execute(self, name):
        for obj in self._objects:
            if obj.name == name:
                self.runJavaScript(obj.initial_script())


class WebPage(QtWebEngineWidgets.QWebEngineView):
    window_name = 'syncsketchGUI_login_window'
    window_label = 'Login to SyncSketch'

    def __init__(self, parent):
        self.parent = parent
        #super(WebPage).__init__()
        QtWebEngineWidgets.QWebEngineView.__init__(self)
        page = WebEnginePage(self)
        self.setPage(page)

        self.test_object = TestObject("test_object", self)
        self.test_object.loaded.connect(self.test_object_loaded)
        page.add_object(self.test_object)

        self.load(QtCore.QUrl(
            "https://syncsketch.com/login/?next=/users/getToken/&simple=1"))

    @QtCore.Slot()
    def test_object_loaded(self):
        script = self.test_object.render_script(
            r"""
        {{name}}.test(window.getTokenData());
        """
        )
        self.page().runJavaScript(script)
