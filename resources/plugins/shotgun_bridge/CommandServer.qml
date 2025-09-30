// Based on the dcc-live-link plugin CommandsServer
// The communication is more similar to rpc json than what it was it that
// plugin example.

// Original code by: Diego Garcia Huerta
// Updated by: Stephen Studyvin

// Updated:
// September 2025, to support current Adobe Substance 3D Painter version.

import QtQuick 2.7
import QtWebSockets 1.0

/**
 * CommandServer.qml
 *
 * This QML component creates a WebSocket server within Adobe Substance 3D Painter.
 * It acts as a bridge, allowing an external Python process (the FlowPTR engine)
 * to send commands to and receive results from the application.
 *
 * The communication protocol is based on JSON-RPC 2.0.
 * - The server listens for incoming commands from the Python client.
 * - It executes registered callbacks based on the command's 'method'.
 * - It sends back a 'result' or an 'error' object.
 */
Item {
  id: root

  property alias host : server.host
  property alias listen: server.listen
  property alias port: server.port
  property alias currentWebSocket: server.currentWebSocket
  readonly property bool connected: currentWebSocket !== null
  property bool debug: false;

  signal jsonMessageReceived(var command, var jsonData)

  property var _callbacks: null
  property var m_id: 1

  /**
   * Logs an informational message to Adobe Substance 3D Painter console.
   */
  function log_info(message)
  {
    alg.log.info("FlowPTR bridge: " + message.toString());
  }
 
  /**
   * Logs a warning message to Adobe Substance 3D Painter console.
   */
  function log_warning(message)
  {
    alg.log.warning("FlowPTR bridge: " + message.toString());
  }
 
  /**
   * Logs a debug message to Adobe Substance 3D Painter console, only if debugging is enabled.
   */
  function log_debug(message)
  {
    if (root.debug)
      alg.log.info("(DEBUG) FlowPTR bridge: " + message.toString());
  }
 
  /**
   * Logs an error message to Adobe Substance 3D Painter console.
   */
  function log_error(message)
  {
    alg.log.error("FlowPTR bridge: " + message.toString());
  }
 
  /**
   * Logs an exception message to Adobe Substance 3D Painter console.
   */
  function log_exception(message)
  {
    alg.log.exception("FlowPTR bridge: " + message.toString());
  }

  /**
   * Registers a JavaScript function to be called when a specific command is received.
   * @param {string} command - The name of the command (case-insensitive).
   * @param {function} callback - The function to execute.
   */
  function registerCallback(command, callback) {
    if (_callbacks === null) {
      _callbacks = {};
    }
    _callbacks[command.toUpperCase()] = callback;
  }

  /**
   * Sends a command to the connected client. (Not typically used by the server).
   * @param {string} command - The method name for the JSON-RPC request.
   * @param {object} data - The parameters for the command.
   */
  function sendCommand(command, data) {
    if (!connected) {
      alg.log.warn(qsTr("Can't send \"%1\" command as there is no client connected").arg(command));
      return;
    }
    try {
          m_id +=1;
          var jsonData = {"jsonrpc": "2.0",
                          "method": command,
                          "params": data,
                          "id": m_id};

      log_debug("Sending:" + JSON.stringify(jsonData));
      server.currentWebSocket.sendTextMessage(JSON.stringify(jsonData));
    }
    catch(err) {
      alg.log.error(qsTr("Unexpected error while sending \"%1\" command: %2").arg(command).arg(err.message));
    }
  }

  /**
   * Sends a JSON-RPC 2.0 compliant response back to the client.
   * @param {string} message_id - The ID from the original request.
   * @param {any} result - The data to be sent as the result.
   */
  function sendResult(message_id, result)
  {
    var jsonData;

    if (!connected)
    {
      alg.log.warn(qsTr("Can't send \"%1\" result for message  \"%2\" as there is no client connected").arg(result).arg(message_id));
      return;
    }
    try 
    {
      jsonData = {"jsonrpc": "2.0", "result": result, "id": message_id};
      log_debug("Sending Response:" + JSON.stringify(jsonData));
      server.currentWebSocket.sendTextMessage(JSON.stringify(jsonData));
      log_debug("Sent.");
    }
    catch(err) {
      // Construct a JSON-RPC 2.0 compliant error object.
      var error_obj = {
          code: -32000, // Generic server error
          message: err.message || "An unknown error occurred."
      };
      jsonData = {"jsonrpc": "2.0", "error": error_obj, "id": message_id};
      log_debug("Sending error:" + JSON.stringify(jsonData));
      server.currentWebSocket.sendTextMessage(JSON.stringify(jsonData));
      alg.log.error(qsTr("Unexpected error while sending \"%1\" message id: %2").arg(message_id).arg(err.message));
    }
  }

  WebSocketServer {
    id: server

    listen: false
    port: 12345
    property var currentWebSocket: null
    name: "Adobe Substance 3D Painter Bridge"
    accept: !root.connected // Ensure only one connection at a time

    onClientConnected: {
      // A new client has connected. Store the socket for communication.
      currentWebSocket = webSocket;

      webSocket.statusChanged.connect(function onWSStatusChanged() {
          if (root && root.connected && (
                webSocket.status == WebSocket.Closed ||
                webSocket.status == WebSocket.Error))
          {
            server.currentWebSocket = null;
          }
          if (webSocket.status == WebSocket.Error) {
            alg.log.warn(qsTr("Command server connection error: %1").arg(webSocket.errorString));
          }
      });
      webSocket.onTextMessageReceived.connect(function onWSTxtMessageReceived(message) {
        // A new message has been received from the client.
        // Try to retrieve command and json data
        var command, jsonData, message_id;
        try {
          jsonData = JSON.parse(message);
          message_id = jsonData.id
          command = jsonData.method.toUpperCase(); 
        }
        catch(err) {
          alg.log.warn(qsTr("Command connection received badly formated message starting with: \"%1\"...: %2")
            .arg(message.substring(0, 30))
            .arg(err.message));
          return;
        }
        log_debug("Message received: " + message)

        // Check if a callback is registered for the received command.
        if (root._callbacks && command in root._callbacks) {
          try {
            var result = root._callbacks[command](jsonData.params)
            root.sendResult(jsonData.id, result);
          }
          catch(err) {
            alg.log.warn(err.message);
          }
        }
        else
        {
          log_debug("Message received was ignored: " + message)        
        }
        root.jsonMessageReceived(command, jsonData);
      })
    }

    onErrorStringChanged: {
      alg.log.warn(qsTr("Command server error: %1").arg(errorString));
    }
  }
}
