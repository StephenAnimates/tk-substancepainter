"""
Module that encapsulates access to the actual application

Original code by: Diego Garcia Huerta
Updated by: Stephen Studyvin

Updated:
September 2025, to use Python 3, and support current Adobe Substance 3D Painter version.

"""


import sys
import json
import time
import threading
import uuid
from functools import partial
import sgtk
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)

from sgtk.platform import qt as sgtk_qt

# import the module - note that this is using the special

__author__ = "Diego Garcia Huerta"
__email__ = "diegogh2000@gmail.com"

class Client(sgtk_qt.QtCore.QObject):
    """
    A low-level WebSocket client for communicating with the Adobe Substance 3D Painter
    QML plugin.

    This class handles the connection, message serialization (JSON-RPC 2.0),
    and asynchronous message handling. It uses Qt's WebSocket implementation.

    - Qt WebSockets Documentation: https://doc.qt.io/qt-6/qtwebsockets-index.html
    - JSON-RPC 2.0 Specification: https://www.jsonrpc.org/specification

    """

    requestReceived = sgtk_qt.QtCore.Signal(str, object)

    def __init__(self, engine, parent=None, url="ws://localhost:12345"):
        """
        Initializes the WebSocket client.

        :param engine: The Toolkit engine instance.
        :param parent: The parent QObject.
        :param str url: The WebSocket server URL to connect to.
        """
        super(Client, self).__init__(parent)
        self._sync_response = None
        self.engine = engine
        self.url = url
        self.client = sgtk_qt.QtWebSockets.QWebSocket(
            "", sgtk_qt.QtWebSockets.QWebSocketProtocol.Version13, None
        )

        # Connect Qt signals from the WebSocket to handler methods (slots).
        self.client.connected.connect(self.on_connected)
        self.client.disconnected.connect(self.on_disconnected)
        self.client.error.connect(self.on_error)
        self.client.stateChanged.connect(self.on_state_changed)

        self.client.pong.connect(self.on_pong)
        self.client.textMessageReceived.connect(self.on_text_message_received)

        # Dictionary to store callbacks for asynchronous responses.
        self.callbacks = {}
        self.max_attemps = 5
        self.wait_period = 1

        # borrow the engine logger
        self.log_info = engine.log_info
        self.log_debug = engine.log_debug
        self.log_warning = engine.log_warning
        self.log_error = engine.log_error

        self.log_debug("Client started. - %s " % url)

        # connect to server
        self.connect_to_server()

    def connect_to_server(self):
        """Initiates the connection to the WebSocket server."""
        self.log_debug("Client start connection | %s " % sgtk_qt.QtCore.QUrl(self.url))
        result = self.client.open(sgtk_qt.QtCore.QUrl(self.url))
        self.log_debug("Client start connection | result | %s " % result)

    def ping(self):
        """Sends a ping frame to the server to keep the connection alive."""
        self.log_debug("client: do_ping")
        self.client.ping()

    def on_connected(self):
        """Slot executed when the WebSocket successfully connects."""
        pass
        self.log_debug("client: on_connected")

    def on_disconnected(self):
        """Slot executed when the WebSocket disconnects."""
        self.engine.process_request("QUIT")
        self.log_debug("client: disconnected")

    def on_error(self, error_code):
        """Slot executed when a WebSocket error occurs."""
        self.log_error("client: on_error: {}".format(error_code))
        self.log_error(self.client.errorString())
        self.engine.process_request("QUIT")

    def on_state_changed(self, state):
        """Slot executed when the WebSocket's connection state changes."""
        self.log_debug("client: on_state_changed: %s" % state)
        state = self.client.state()
        if state == sgtk_qt.QtNetwork.QAbstractSocket.SocketState.ConnectingState:
            return

        attempts = 0
        while attempts < self.max_attemps and self.client.state() not in (
            # If disconnected, attempt to reconnect a few times.
            sgtk_qt.QtNetwork.QAbstractSocket.SocketState.ConnectedState,
        ):
            attempts += 1
            self.log_debug("client: attempted to reconnect : %s" % attempts)
            self.connect_to_server()
            time.sleep(self.wait_period)

    def send_and_receive(self, command, **kwargs):
        """
        Sends a command and blocks until a response is received or a timeout occurs.

        This method simulates a synchronous request-response pattern over an
        asynchronous WebSocket. It uses a QEventLoop to pause execution, which
        is then resumed by the response callback or a timeout.

        :param str command: The command method to send.
        :param dict kwargs: The parameters for the command.
        :return: The data from the response, or None on timeout.
        """
        self._sync_response = None
        loop = sgtk_qt.QtCore.QEventLoop()

        def await_for_response(result):
            """Callback executed when a response is received."""
            self._sync_response = result
            loop.quit()

        # Send the message with our one-time callback
        self.send_text_message(command, callback=await_for_response, **kwargs)

        # Set up a timer to exit the loop in case of no response
        timeout_timer = sgtk_qt.QtCore.QTimer(parent=sgtk_qt.QtCore.QCoreApplication.instance())
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(loop.quit)
        timeout_timer.start(5000)  # 5-second timeout

        loop.exec_()

        if timeout_timer.isActive():
            timeout_timer.stop()
        else:
            self.log_warning("Request '%s' timed out.", command)

        return self._sync_response

    def on_text_message_received(self, message):
        """
        Slot executed when a text message is received from the server.
        It parses the JSON-RPC response and triggers the corresponding callback.
        """
        jsonData = json.loads(message)
        message_id = jsonData.get("id")

        # A 'result' key indicates a response to a previous request.
        if "result" in jsonData:
            if message_id in self.callbacks:
                # If a callback was registered for this message ID, execute it.
                result = jsonData.get("result")
                self.callbacks[message_id](result)
                # Remove the one-time callback.
                del self.callbacks[message_id]

    def send_text_message(self, command, message_id=None, callback=None, **kwargs):
        """Constructs and sends a JSON-RPC 2.0 request to the server."""
        if self.client.state() in (
            sgtk_qt.QtNetwork.QAbstractSocket.SocketState.ClosingState,
            sgtk_qt.QtNetwork.QAbstractSocket.SocketState.UnconnectedState,
        ):
            # Don't try to send if we're not connected.
            self.log_warning("Client is not connected. Ignoring message: %s", command)
            return

        # wait until connected
        while self.client.state() == sgtk_qt.QtNetwork.QAbstractSocket.SocketState.ConnectingState:
            sgtk_qt.QtCore.QCoreApplication.processEvents()
            time.sleep(self.wait_period)
            self.log_debug("Waiting for WebSocket to connect...")
            pass

        # Generate a unique ID for this request to track the response.
        if message_id is None:
            message_id = uuid.uuid4().hex

        # Store the callback function to be executed when the response arrives.
        if callback:
            self.callbacks[message_id] = callback

        # Construct the JSON-RPC 2.0 message payload.
        message = json.dumps(
            {"jsonrpc": "2.0", "method": command, "params": kwargs, "id": message_id,}
        )

        self.client.sendTextMessage(message)
        return message_id

    def on_pong(self, elapsedTime, payload):
        """Slot executed when a pong frame is received from the server."""
        pass

    def close(self):
        self.log_debug("client: closed: '%s'", self.client.state())
        self.client.close()


class EngineClient(Client):
    """
    A high-level client that provides a clean API for the engine to interact
    with Adobe Substance 3D Painter.

    Each method in this class corresponds to a function exposed by the QML
    plugin in Adobe Substance 3D Painter and handles the request/response logic.
    """
    def __init__(self, engine, parent=None, url="ws://localhost:12345"):
        super(EngineClient, self).__init__(engine, parent=parent, url=url)

    def get_application_version(self):
        """Retrieves the version of the running Adobe Substance 3D Painter application."""
        version = self.send_and_receive("GET_VERSION")
        self.log_debug("version: %s (%s)" % (version, type(version)))
        painter_version = version["painter"]
        self.log_debug("painter_version: %s" % painter_version)
        return painter_version

    def get_current_project_path(self):
        """Gets the file path of the currently open project."""
        path = self.send_and_receive("GET_CURRENT_PROJECT_PATH")
        self.log_debug("CURRENT_PROJECT_PATH: %s (%s)" % (path, type(path)))
        return path

    def need_saving(self):
        """Checks if the current project has unsaved changes."""
        result = self.send_and_receive("NEEDS_SAVING", path=path)
        return result

    def open_project(self, path):
        """Opens a project from the given file path."""
        path = self.send_and_receive("OPEN_PROJECT", path=path)

    def save_project_as(self, path):
        """Saves the current project to a new file path."""
        success = self.send_and_receive("SAVE_PROJECT_AS", path=path)
        return success

    def save_project_as_action(self):
        """Triggers the native 'Save As' dialog in Adobe Substance 3D Painter."""
        result = self.send_and_receive("SAVE_PROJECT_AS_ACTION")
        return result

    def save_project(self):
        """Saves the current project."""
        success = self.send_and_receive("SAVE_PROJECT")
        return success

    def close_project(self):
        """Closes the current project."""
        success = self.send_and_receive("CLOSE_PROJECT")
        return success

    def broadcast_event(self, event_name):
        """Sends a one-way event notification to the application."""
        self.send_text_message(event_name)

    def execute(self, statement_str):
        """Executes a Python statement inside the Adobe Substance 3D Painter environment."""
        result = self.send_and_receive("EXECUTE_STATEMENT", statement=statement_str)
        return result

    def extract_thumbnail(self, filename):
        """Requests a thumbnail of the current viewport, saving it to `filename`."""
        result = self.send_and_receive("EXTRACT_THUMBNAIL", path=filename)
        return result

    def import_project_resource(self, filename, usage, destination):
        result = self.send_and_receive(
            "IMPORT_PROJECT_RESOURCE",
            path=filename,
            usage=usage,
            destination=destination,
        )
        return result

    def get_project_settings(self, key):
        """Retrieves a value from the project's metadata settings."""
        result = self.send_and_receive("GET_PROJECT_SETTINGS", key=key)
        return result

    def get_resource_info(self, resource_url):
        """Gets information about a specific project resource."""
        result = self.send_and_receive("GET_RESOURCE_INFO", url=resource_url)
        return result

    def get_project_export_path(self):
        """Gets the default export path for the current project."""
        result = self.send_and_receive("GET_PROJECT_EXPORT_PATH")
        return result

    def get_map_export_information(self):
        """Retrieves information about the maps that will be exported."""
        result = self.send_and_receive("GET_MAP_EXPORT_INFORMATION")
        return result

    def export_document_maps(self, destination):
        """
        Triggers the texture export process and waits for it to complete.

        This is a special case that handles an asynchronous operation in Substance
        3D Painter. It works by:
        1. Registering a one-time callback for the 'EXPORT_FINISHED' event.
        2. Sending the 'EXPORT_DOCUMENT_MAPS' command.
        3. Entering a local event loop that waits until the callback is fired.
        """
        self.__export_results = None

        def run_once_finished_exporting_maps(**kwargs):
            """Callback to store the result and break the waiting loop."""
            self.__export_results = kwargs.get("map_infos", {})

        # Register a temporary callback for the completion event from Adobe Substance 3D Painter.
        self.engine.register_event_callback(
            "EXPORT_FINISHED", run_once_finished_exporting_maps
        )

        self.log_debug("Starting map export...")
        result = self.send_and_receive("EXPORT_DOCUMENT_MAPS", destination=destination)

        # Block execution by processing Qt events until the export is finished.
        while self.__export_results is None:
            self.log_debug("Waiting for maps to be exported ...")
            sgtk_qt.QtCore.QCoreApplication.processEvents()
            time.sleep(self.wait_period)

        # Clean up the temporary callback.
        self.engine.unregister_event_callback(
            "EXPORT_FINISHED", run_once_finished_exporting_maps
        )

        result = self.__export_results

        # no need for this variable anymore
        del self.__export_results

        self.log_debug("Map export ended.")
        return result

    def update_document_resources(self, old_url, new_url):
        """Replaces all instances of a resource with a new one."""
        result = self.send_and_receive(
            "UPDATE_DOCUMENT_RESOURCES", old_url=old_url, new_url=new_url
        )
        return result

    def document_resources(self):
        """Gets a list of all resources currently used in the project."""
        result = self.send_and_receive("DOCUMENT_RESOURCES")
        return result

    def log_info(self, message):
        """Sends an info message to be logged in the Adobe Substance 3D Painter console."""
        self.send_text_message("LOG_INFO", message=message)

    def log_debug(self, message):
        """Sends a debug message to be logged in the Adobe Substance 3D Painter console."""
        self.send_text_message("LOG_DEBUG", message=message)

    def log_warning(self, message):
        """Sends a warning message to be logged in the Adobe Substance 3D Painter console."""
        self.send_text_message("LOG_WARNING", message=message)

    def log_error(self, message):
        """Sends an error message to be logged in the Adobe Substance 3D Painter console."""
        self.send_text_message("LOG_ERROR", message=message)

    def log_exception(self, message):
        """Sends an exception message to be logged in the Adobe Substance 3D Painter console."""
        self.send_text_message("LOG_EXCEPTION", message=message)

    def toggle_debug_logging(self, enabled):
        """Toggles the debug logging level in the Adobe Substance 3D Painter plugin."""
        self.send_text_message("TOGGLE_DEBUG_LOGGING", enabled=enabled)


if __name__ == "__main__":
    global client
    app = sgtk_qt.QtCore.QCore_Application(sys.argv)
    # This test block requires a running engine and Substance Painter instance.
    # client = Client(app)
    #
    version = get_application_version(client)
    print("application_version: %s" % version)
    version2 = get_application_version(client)
    print("application_version2: %s" % version2)
    app.exec_()
