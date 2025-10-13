// Substance Painter plugin to communicate with it's related Shotgun engine.
// The idea is to communicate with the engine through websockets since
// the engine is written in python.

// Original code by: Diego Garcia Huerta
// Updated by: Stephen Studyvin

// Updated:
// September 2025, to support current Adobe Substance 3D Painter version.

import QtQuick 2.2
import Painter 1.0
import Qt.labs.platform 1.0
import QtQuick.Dialogs 1.2
import QtQuick.Window 2.2
import "."

/**
 * main.qml
 *
 * This is the main entry point for the Flow Production Tracking (FlowPTR) integration
 * plugin within Adobe Substance 3D Painter.
 *
 * It performs the following key functions:
 * - Creates and manages the WebSocket server to communicate with the Python engine.
 * - Bootstraps the external Python engine process.
 * - Adds a button to the main toolbar to open the FlowPTR menu.
 * - Exposes Substance 3D Painter's project and application APIs to the Python engine
 *   through registered commands.
 */
Item
{
  id: root

  PainterPlugin {
    id: painterPlugin
  }

  /**
   * Helper function to extract a message string from a data object.
   * @param {any} data - The input data, which can be a string or an object with a 'message' property.
   * @returns {string}
   */
  function _getLogMessage(data) {
    if (typeof data === 'object' && data !== null && data.hasOwnProperty("message")) {
        return data.message.toString();
    }
    return data.toString();
  }

  function log_info(data) {
    alg.log.info("FlowPTR engine | " + _getLogMessage(data));
  }

  function log_warning(data) {
    alg.log.warning("FlowPTR engine | " + _getLogMessage(data));
  }

  function log_debug(data) {
    if (root.debug) {
      alg.log.info("(DEBUG) FlowPTR engine | " + _getLogMessage(data));
    }
  }

  function log_error(data) {
    alg.log.error("FlowPTR engine | " + _getLogMessage(data));
  }

  function log_exception(data) {
    alg.log.exception("FlowPTR engine | " + _getLogMessage(data));
  }

  Component.onCompleted:
  {
    // This block is executed once when the plugin is first loaded.
    // It handles the initial setup of the bridge.
    console.log("FlowPTR Bridge: Component.onCompleted started.");

    painterPlugin.log_debug("Initializing FlowPTR Bridge Plugin.");

    // get the port we have been assigned from sthe startup software launcher
    var args = Qt.application.arguments[1];
    var query = getQueryParams(args);

    if (typeof(query.SGTK_SUBSTANCEPAINTER_ENGINE_PORT) === "undefined" ||
        typeof(query.SGTK_SUBSTANCEPAINTER_ENGINE_STARTUP) === "undefined" ||
        typeof(query.SGTK_SUBSTANCEPAINTER_ENGINE_PYTHON) === "undefined")
    {
      // If the required environment variables are not present, it means
      // Substance 3D Painter was not launched through the FlowPTR launcher.
      // we are not in a shotgun toolkit environment, so we bail out as soon as
      // possible
      painterPlugin.log_warning("Not in a Flow Production Tracking environment so the engine won't be run. Have you launched Substance 3D Painter through the FlowPTR Desktop application?");
      return;
    }

    var sgtk_substancepainter_engine_port = query.SGTK_SUBSTANCEPAINTER_ENGINE_PORT;
    
    server.port = parseInt(sgtk_substancepainter_engine_port);
    painterPlugin.log_debug("Engine port:" + server.port);
    server.listen = true;

    var openMenuButton = alg.ui.addWidgetToPluginToolBar("menu.qml");

    openMenuButton.clicked.connect(displayMenu);
    openMenuButton.enabled = Qt.binding(function() { return server.isEngineLoaded; });

    // We initialize here the engine instead of when the app has finished 
    // loading because the user can always reload the plugin from the Plugins
    // menu and that event does not get called in that case.
    if (!isEngineLoaded)
    {
      bootstrapEngine();
    }
  }

  Connections {
    target: alg.project
    onNewProjectCreated:
  {
    // This signal is emitted by Substance 3D Painter when a new project is created.
    // We check if a mesh was imported and, if so, send its path to the engine
    // so it can potentially change the Toolkit context.

    // Called when a new project is created, before the onProjectOpened callback

    // no chance this project is saved, but if a mesh that is known by
    // toolkit is loaded, we can change the context of teh engine
    var mesh_url = alg.project.lastImportedMeshUrl();
    if (mesh_url)
    {
      var mesh_path = alg.fileIO.urlToLocalFile(mesh_url);
      server.sendCommand("NEW_PROJECT_CREATED", {path:mesh_path});
    }
  }
  }

  Connections {
    target: alg.project
    onProjectOpened:
  {
    // This signal is emitted by Substance 3D Painter when a project is fully loaded.
    // We send the project path to the engine so it can synchronize its context.

    // Called when the project is fully loaded
    server.sendCommand("PROJECT_OPENED", {path:currentProjectPath()});
  }
  }

  function getQueryParams(qs)
  {
    /**
     * Parses a URL query string into a key-value parameter object.
     */
    // This takes care of parsing the parameters passed in the command line
    // to substance painter
    var params = {};

    try
    {
      qs = qs.split('+').join(' ');

      var tokens,
          re = /[?&]?([^=]+)=([^&]*)/g;

      while (tokens = re.exec(qs))
      {
          params[decodeURIComponent(tokens[1])] = decodeURIComponent(tokens[2]);
      }
    }
    catch (err) 
    {
    }

    return params;
  }


  function onProcessEndedCallback(result)
  {
    /**
     * Callback executed when the external Python engine process terminates.
     * If the process crashed, it attempts to restart it to maintain the connection.
     */
    // We try to keep the engine alive by restarting it if something went wrong.
    painterPlugin.log_warning("FlowPTR Engine connection was lost. Restarting engine...");
    if (result.crashed)
    {
      bootstrapEngine();
    }
  }

  function bootstrapEngine()
  {
    /**
     * Starts the external Python engine process.
     * It retrieves the path to the Python executable and the bootstrap script
     * from the command-line arguments and launches it as a subprocess.
     */
    // Initializes the toolkit engine by reading the argument passed by the
    // startup module in the command line. The argument is in the form of an
    // url parameters and contains the location to python, the location to the
    // bootstrap engine and the port to use for the server<->client connection.
    var args = Qt.application.arguments[1];
    const query = getQueryParams(args);

    const sgtk_substancepainter_engine_startup = '"' + query.SGTK_SUBSTANCEPAINTER_ENGINE_STARTUP+ '"'
    const sgtk_substancepainter_engine_python = '"' + query.SGTK_SUBSTANCEPAINTER_ENGINE_PYTHON + '"'
    
    painterPlugin.log_debug("Starting tk-substancepainter engine with params: " + sgtk_substancepainter_engine_python + " " + sgtk_substancepainter_engine_startup)
    alg.subprocess.start(sgtk_substancepainter_engine_python + " " + sgtk_substancepainter_engine_startup, onProcessEndedCallback)
  }

  function displayMenu(data) 
  {
    /**
     * Sends a command to the Python engine to display the main FlowPTR menu.
     * It includes the position where the user clicked the toolbar button.
     */
    // tells the engine to show the menu
    server.sendCommand("DISPLAY_MENU", {clickedPosition: openMenuButton.clickedPosition});
  }

 function sendProjectInfo() 
 {
    // Sends information about the current project to the client.
    try
    {
        server.sendCommand("OPENED_PROJECT_INFO", {
          projectUrl: alg.project.url()
        });
    }
    catch(err) {}
  }

  function disconnect() 
  {
    /**
     * Called when the WebSocket connection is lost. It attempts to restart the engine.
     */
    server.isEngineLoaded = false;

    painterPlugin.log_warning("FlowPTR Engine connection was lost. Reconnecting ...");
    bootstrapEngine();
  }

  function getVersion(data) 
  {
    /**
     * Callback to get the version of Substance 3D Painter and its API.
     */
    return {
             painter: alg.version.painter,
             api: alg.version.api
           };
  }
  
  function engineReady(data) 
  {
    /**
     * Callback executed when the Python engine signals that it is fully initialized.
     * This enables the UI and synchronizes the project context.
     */
    painterPlugin.log_info("Engine is ready.")
    server.isEngineLoaded = true;
    
    // update the engine context accoding to the current project loaded
    server.sendCommand("PROJECT_OPENED", {path:currentProjectPath()});
  }

  function cleanUrl(url) 
  {
    /**
     * Normalizes a file URL to a consistent format for comparison.
     */
    return alg.fileIO.localFileToUrl(alg.fileIO.urlToLocalFile(url));
  }

  function openProject(data) 
  {
    /**
     * Callback to open a Substance 3D Painter project from a given file path.
     * It handles checking for unsaved changes in the current project.
     */
    var projectOpened = alg.project.isOpen();
    var isAlreadyOpen = false;

    var url = alg.fileIO.localFileToUrl(data.path);

    try 
    {
      isAlreadyOpen = cleanUrl(alg.project.url()) == cleanUrl(url);
    }
    catch (err) 
    {
      alg.log.exception(err);
    }

    // If the project is already opened, keep it
    try
    {
      if (!isAlreadyOpen)
      {
        if (projectOpened && alg.project.needSaving())
        {
          // Ask the user if they want to save their current opened project
          saveChangesDialog.open();
          // The dialog will handle closing and opening the new project.
          // Store the URL to open in a property on the dialog.
          saveChangesDialog.nextProjectUrl = url;
          return true; // Stop execution here, dialog will continue.
        }
        else if (projectOpened)
        {
            // Project is open but has no changes, so just close it.
            alg.project.close();
        }
        alg.project.open(url);
      }
    }
    catch (err) 
    {
      alg.log.exception(err)
      return false;
    }

    return true;
  }

  function currentProjectPath(data)
  {
    /**
     * Callback to get the file path of the currently open project.
     */
    try 
    {
      var projectOpened = alg.project.isOpen();
      if (projectOpened)
      {
        var path = alg.fileIO.urlToLocalFile(alg.project.url());
        return path
      }
      else
      {
        return "Untitled.spp"
      }    
    }
    catch (err)
    {
      return "Untitled.spp"
    }
  }

  function currentProjectMesh(data)
  {
    /**
     * Callback to get the file path of the mesh used in the current project.
     */
    try
    {
      var projectOpened = alg.project.isOpen();
      if (projectOpened)
      {
        var path = alg.fileIO.urlToLocalFile(alg.project.lastImportedMeshUrl());
        return path
      }
      else
      {
        return null;
      }    
    }
    catch (err)
    {
      return null;
    }
  }

  
  function saveProjectAs(data)
  {
    /**
     * Callback to save the current project to a new file path.
     */
    try
    {
      var url = alg.fileIO.localFileToUrl(data.path);
      alg.project.save(url, alg.project.SaveMode.Full);
    }
    catch (err)
    {
      alg.log.exception(err)
      return false;
    }

    return true;
  }


  function saveProject(data)
  {
    /**
     * Callback to save the current project.
     */
    try
    {
      alg.project.save("", alg.project.SaveMode.Full);
    }
    catch (err)
    {
      alg.log.exception(err)
      return false;
    }
    
    return true;
  }

  function needsSavingProject(data)
  {
    /**
     * Callback to check if the current project has unsaved changes.
     */
    try
    {
      return alg.project.needSaving();
    }
    catch (err)
    {
      alg.log.exception(err)
      return false;
    }
    
    return false;
  }

  function closeProject(data)
  {
    /**
     * Callback to close the current project.
     */
    try
    {
      var projectOpened = alg.project.isOpen();
      if (projectOpened)
        return alg.project.close();
    }
    catch (err)
    {
      alg.log.exception(err)
      return false;
    }
    return false;
  }

  function executeStatement(data)
  {
    /**
     * Callback to execute an arbitrary JavaScript statement.
     */
    try
    {
      return eval(data.statement);
    }
    catch (err)
    {
      alg.log.exception(err)
      return false;
    }
    
    return false;
  }

  function importProjectResource(data)
  {
    /**
     * Callback to import a file as a project resource (e.g., a texture).
     * It also stores metadata in the project settings to track that this
     * resource was loaded via the Toolkit Loader.
     */
    try
    {
      var result = alg.resources.importProjectResource(data.path, [data.usage], data.destination);
      
      // we store the info as a project settings as it will be reused later 
      // when tk-multi-breakdown2 tries to figure out what resources are
      // up to date and which are not.

      var settings = alg.project.settings.value("tk-multi-loader2", {});    
      settings[result] = data.path;

      alg.project.settings.setValue("tk-multi-loader2", settings);

      return result;
    }
    catch (err)
    {
      alg.log.exception(err)
    }
    
    return null;
  }

  function getProjectSettings(data)
  {
    /**
     * Callback to retrieve a value from the project's metadata settings.
     */
    return alg.project.settings.value(data.key, {});
  }

  function getResourceInfo(data)
  {
    /**
     * Callback to get information about a specific project resource,
     * identified by its URL.
     */
    try
    {
      return alg.resources.getResourceInfo(data.url);
    }
    catch (err)
    {
      alg.log.exception(err)
    }

    return null;
  }

  function getProjectExportPath(data)
  {
    /**
     * Callback to get the default export path for the current project.
     */
    return alg.mapexport.exportPath();
  }

  function saveProjectAsAction(data)
  {
    /**
     * Callback to trigger the native 'Save As' dialog.
     */
    return saveSessionDialog.open();
  }

  function getMapExportInformation(data)
  {
    /**
     * Callback to get a list of maps that would be exported with the current settings.
     */
    var export_preset = alg.mapexport.getProjectExportPreset();
    var export_options = alg.mapexport.getProjectExportOptions();
    var export_path = alg.mapexport.exportPath();
    return alg.mapexport.getPathsExportDocumentMaps(export_preset, export_path, export_options.fileFormat)
  }

  function exportDocumentMaps(data)
  {
    /**
     * Callback to start the texture export process. This is an asynchronous
     * operation, so it sends events back to the engine when it starts and finishes.
     */
    var export_preset = alg.mapexport.getProjectExportPreset();
    var export_options = alg.mapexport.getProjectExportOptions();
    var export_path = data.destination;
    server.sendCommand("EXPORT_STARTED", {});
    var result = alg.mapexport.exportDocumentMaps(export_preset, export_path, export_options.fileFormat)
    server.sendCommand("EXPORT_FINISHED", {map_infos:result});
    return true;
  }

  function updateDocumentResources(data)
  {
    /**
     * Callback to replace all usages of one resource with another.
     * Used by the Breakdown app.
     */
    return alg.resources.updateDocumentResources(data.old_url, data.new_url);
  }

  function documentResources(data)
  {
    /**
     * Callback to get a list of all resources currently in use in the project.
     */
    return alg.resources.documentResources();
  }

  function toggleDebugLogging(data)
  {
    /**
     * Callback to enable or disable debug logging for this plugin.
     */
    alg.log.debug("Debug Logging is : " + data.enabled);
    painterPlugin.debug = data.enabled;
    server.debug = data.enabled;
  }

  CommandServer
  {
    // This is the WebSocket server instance.
    id: server
    Component.onCompleted:
    {
      registerCallback("LOG_INFO", painterPlugin.log_info);
      registerCallback("LOG_WARNING", painterPlugin.log_warning);
      registerCallback("LOG_DEBUG", painterPlugin.log_debug);
      registerCallback("LOG_ERROR", painterPlugin.log_error);
      registerCallback("LOG_EXCEPTION", painterPlugin.log_exception);

      registerCallback("SEND_PROJECT_INFO", sendProjectInfo);
      registerCallback("GET_VERSION", getVersion);
      registerCallback("ENGINE_READY", engineReady);
      registerCallback("OPEN_PROJECT", openProject);
      registerCallback("GET_CURRENT_PROJECT_PATH", currentProjectPath);
      registerCallback("SAVE_PROJECT", saveProject);
      registerCallback("SAVE_PROJECT_AS", saveProjectAs);
      registerCallback("SAVE_PROJECT_AS_ACTION", saveProjectAsAction);
      registerCallback("NEEDS_SAVING", needsSavingProject);
      registerCallback("CLOSE_PROJECT", closeProject);
      registerCallback("EXECUTE_STATEMENT", executeStatement);
      registerCallback("IMPORT_PROJECT_RESOURCE", importProjectResource);
      registerCallback("GET_PROJECT_SETTINGS", getProjectSettings);
      registerCallback("GET_RESOURCE_INFO", getResourceInfo);
      registerCallback("GET_PROJECT_EXPORT_PATH", getProjectExportPath);
      registerCallback("GET_MAP_EXPORT_INFORMATION", getMapExportInformation);
      registerCallback("EXPORT_DOCUMENT_MAPS", exportDocumentMaps);
      registerCallback("UPDATE_DOCUMENT_RESOURCES", updateDocumentResources);
      registerCallback("DOCUMENT_RESOURCES", documentResources);
      registerCallback("TOGGLE_DEBUG_LOGGING", toggleDebugLogging);
      //checkConnectionTimer.start();
    }

    onConnectedChanged: 
    {
      // If the client disconnects, trigger the reconnect logic.
      if (!connected)
      {
        disconnect();
      }
    }
  }

  FileDialog
  {
    // A standard file dialog used for the 'Save As' action.
    id: saveSessionDialog
    title: "Save Project"
    selectExisting : false
    nameFilters: [ "Substance Painter files (*.spp)" ]

    onAccepted:
    {
      var url = fileUrl.toString();
      alg.project.save(url, alg.project.SaveMode.Full);
      return true;
    }
    onRejected:
    {
      return false;
    }
  }

  MessageDialog {
      // A standard message dialog used to ask the user to save changes
      // before opening a new project, preventing data loss.
      id: saveChangesDialog
      title: "Save Changes?"
      text: "The current project has unsaved changes. Do you want to save them before opening the new project?"
      icon: StandardIcon.Question
      standardButtons: StandardButton.Save | StandardButton.Discard | StandardButton.Cancel
      property var nextProjectUrl: ""

      onButtonClicked: (button) => {
          if (button === StandardButton.Save) {
              alg.project.save();
              alg.project.close();
              alg.project.open(nextProjectUrl);
          } else if (button === StandardButton.Discard) {
              alg.project.close();
              alg.project.open(nextProjectUrl);
          }
          // If 'Cancel', do nothing.
      }

      onVisibleChanged: {
          if (!visible) nextProjectUrl = ""; // Clear the URL when dialog is closed
      }
  }
}
