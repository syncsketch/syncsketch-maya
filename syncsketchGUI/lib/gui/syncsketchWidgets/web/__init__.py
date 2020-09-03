import logging
logger = logging.getLogger("syncsketchGUI")

'''
The Pyside2 version used in Maya2017 doesnt support the new QWebEngineView yet. 
The Pyside2 version used in Maya2020 dropped the support of the old QWebView widget. 
In order to support both Maya versions this module switches between two widget implementations. 
Unfortunately Maya2019 seems to have a bug with the QWebEngineView widget, since it displays only a grey window.
Therefore the old widget is used as default. With this implementation only >=Maya2020 uses the new widgets. 
'''
try: 
    from webLoginWidget import WebLoginWindow as LoginView
    from webLoginWidget import logout_view
except ImportError:
    logger.debug("Import Latest LoginView")
    from webLoginWidgetEngine import LoginView, logout_view
else:
    logger.debug("Import Deprecated LoginView")


try:
    from webPlayerWidget import OpenPlayer as OpenPlayerView
except ImportError:
    logger.debug("Import Latest PlayerView")
    from webPlayerWidgetEngine import OpenPlayerView as OpenPlayerView
else:
    logger.debug("Import Deprecated PlayerView")
    

