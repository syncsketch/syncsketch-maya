import logging
logger = logging.getLogger("syncsketchGUI")


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
    

