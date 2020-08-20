_web_members = {
    "QtWebKitWidgets": [
        "QWebView",
        "QWebPage",
    ],
    "QtWebEngineWidgets": [
        "QWebEngineView",
        "QWebEnginePage",
        "QWebEngineSettings",
    ],  
        "QtWebChannel": [
        "QWebChannel",
    ],   
}

def update_members(common_members):
    common_members.update(_web_members)
    common_members["QtWidgets"].append("qApp")