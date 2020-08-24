import logging
logger = logging.getLogger("syncsketchGUI")


try:
    from webLoginWidgetEngine import LoginView, logout_view
except ImportError:
    logger.info("Import Deprecated LoginView")
    from webLoginWidget import WebLoginWindow as LoginView
    from webLoginWidget import logout_view
else:
    logger.info("Import Latest LoginView")


try:
    from webPlayerWidgetEngine import OpenPlayerView as OpenPlayerView
except ImportError:
    logger.info("Import Deprecated PlayerView")
    from webPlayerWidget import OpenPlayer as OpenPlayerView
else:
    logger.info("Import Latest PlayerView")

