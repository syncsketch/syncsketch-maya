import logging

logger = logging.getLogger('syncsketchGUI_install')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s]',
                              "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)
