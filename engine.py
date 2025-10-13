# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

# Original code by: Diego Garcia Huerta, https://www.linkedin.com/in/diegogh/
# Updated by: Stephen Studyvin

# Updated:
# September 2025, to use Python 3, and support current Adobe Substance 3D Painter version.

# https://help.autodesk.com/view/SGDEV/ENU/

"""
A Substance Painter engine for Flow Production Tracking (ShotGrid)
https://www.adobe.com/products/substance3d.html

Integrations user guide
https://help.autodesk.com/view/SGDEV/ENU/?guid=SG_Supervisor_Artist_sa_integrations_sa_integrations_user_guide_html

"""

import shiboken6
import os
import sys
import time
import inspect
import logging
from functools import wraps


import tank, sgtk
from tank.log import LogManager
from tank.platform import Engine
from tank.platform.constants import SHOTGUN_ENGINE_NAME, TANK_ENGINE_INIT_HOOK_NAME

# https://developers.shotgridsoftware.com/tk-framework-shotgunutils/

# Import PySide6 classes directly
from PySide6 import QtGui, QtCore, QtWidgets

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt

# for the get_all_ui_panels method
from PySide6.QtWidgets import QApplication, QWidget, QDockWidget
from typing import List

class SubstancePainterEngine(Engine):
    """
    The Flow Production Tracking Toolkit engine for Adobe Substance 3D Painter.

    This engine is responsible for managing the communication with Substance 3D Painter,
    bootstrapping the Toolkit environment, handling context changes, and displaying
    Toolkit app UIs.

    For more on Toolkit engines, see:
    https://help.autodesk.com/view/SGDEV/ENU/?guid=SG_Pipeline_Toolkit_Core_API_tk_core_platform_engine_html
    """

    def __init__(self, *args, **kwargs):
        """
        Engine Constructor
        """

        # main application object
        self._qt_app = None
        self._menu_generator = None
        self._dock_widgets = {}
        self._event_callbacks = {}
        self._is_shutting_down = False  # Initialized to False
        self._shotgun_utils = None
        self.overlay_widget = None # Defensive initialization for potential base class access

        # The '_dcc_app' property will now be a simple wrapper around the
        # substance_painter python module for direct API calls.
        # We must import and assign it here in the constructor to ensure it's
        # available for the very first log messages emitted by the base class.
        import substance_painter
        self._dcc_app = substance_painter

        # It is critical to initialize the base Engine class FIRST.
        # This sets up all the core Toolkit functionality, including 'import_framework'.
        Engine.__init__(self, *args, **kwargs)

    def create_widget_from_class(self, widget_class, parent):
        """
        Creates a widget from the given class, parents it to the main application window, and handles its lifetime.

        This is a helper method to ensure that all created widgets are tracked by the engine.

        :param widget_class: The class of the widget to create.
        :param parent: The parent QWidget for the new widget.
        :returns: The created widget instance.
        """
        widget = widget_class(parent)

        # Add to the list of created dialogs for tracking
        self.created_qt_dialogs.append(widget)

        # If the widget is destroyed, remove it from our tracking list
        # To avoid a crash on shutdown, we capture the widget's info now,
        # before it's destroyed. The lambda will then log this safe info
        # instead of the potentially deleted widget object.
        widget_info = "'%s' (%s)" % (widget.windowTitle(), widget.objectName())
        widget.destroyed.connect(
            lambda: self._on_dialog_destroyed(widget, widget_info)
        )

        return widget

    def _on_dialog_destroyed(self, widget, widget_info):
        """
        Callback slot for when a dialog is destroyed.

        Removes the widget from the list of tracked dialogs.

        :param widget: The widget that was destroyed.
        """
        try:
            if widget in self.created_qt_dialogs:
                self.created_qt_dialogs.remove(widget) # Correctly remove the widget
                self.logger.debug("Dialog destroyed and removed from tracking: %s", widget_info)
        except (RuntimeError, ValueError):
            # This can happen if the widget is already gone or list is modified elsewhere.
            self.logger.debug("Dialog was already removed from tracking: %s", widget_info)

    def show_panel(self, panel_id, title, bundle, widget_class, *args, **kwargs):
        """
        Displays a panel as a dockable widget in Substance 3D Painter.

        :param panel_id: Unique identifier for the panel.
        :param title: The title of the panel.
        :param bundle: The app bundle that is requesting the panel.
        :param widget_class: The QWidget class to instantiate for the panel.

        For more on the Substance 3D Painter UI API, see:
        https://substance3d.adobe.com/documentation/pt/python-api/api/substance_painter/ui
        :returns: The created panel widget.
        """
        
        self.logger.info("Showing panel '%s' in a dockable widget...", panel_id)

        # Allow the title to be customized via the app's settings.
        panel_title = bundle.get_setting("panel_title", title)
        self.logger.debug("Resolved panel title to: '%s'", panel_title)

        # Check if a panel with the same ID is already registered and visible.
        if panel_id in self._dock_widgets:
            widget = self._dock_widgets[panel_id]
            if widget:
                widget.show()
                widget.raise_()
                return widget

        try:
            # Create the panel widget
            widget = self.create_widget_from_class(widget_class, self._get_dialog_parent())
            widget.setObjectName(panel_id)
            widget.setWindowTitle(panel_title)

            # Add the widget to the Substance 3D Painter UI as a dockable widget.
            self.app.ui.add_dock_widget(widget)

            # Store a reference to it
            self._dock_widgets[panel_id] = widget

            return widget

        except Exception as e:
            self.logger.exception(
                "Failed to create panel widget for '%s'. Error: %s", panel_id, e
            )
            return None

    @property
    def app(self):
        """
        A client object that provides an API for interacting with Substance 3D Painter.

        In the pure Python plugin model, this is a direct wrapper around the
        `substance_painter` module, allowing for direct API calls.
        """
        return self._dcc_app

    def __get_platform_resource_path(self, filename):
        """
        Returns the full path to the given platform resource file or folder.
        Resources reside in the core/platform/qt folder.
        :return: full path
        """
        tank_platform_folder = os.path.abspath(inspect.getfile(tank.platform))
        return os.path.join(tank_platform_folder, "qt", filename)

    @property
    def register_toggle_debug_command(self):
        """
        Indicates whether the engine should have a toggle debug logging
        command registered during engine initialization.
        :rtype: bool
        """
        return True

    def __toggle_debug_logging(self):
        """
        Toggles global debug logging on and off in the log manager.
        This will affect all logging across all of toolkit.
        """
        self.logger.debug("calling Substance 3D Painter with debug: %s" % LogManager().global_debug)

        # flip debug logging
        LogManager().global_debug = not LogManager().global_debug
        if self.app:
            self.app.toggle_debug_logging(LogManager().global_debug)

    def __open_log_folder(self):
        """
        Opens the file system folder where log files are being stored.
        """
        self.logger.debug("Log folder is located in '%s'" % LogManager().log_folder)

        if self.has_ui:
            # only import QT if we have a UI
            url = QtCore.QUrl.fromLocalFile(LogManager().log_folder)
            status = QtGui.QDesktopServices.openUrl(url)
            if not status:
                self.log_error("Failed to open folder!")

    def __register_open_log_folder_command(self):
        """
        # add a 'open log folder' command to the engine's context menu
        # note: we make an exception for the FlowPTR engine which is a
        # special case.
        """
        if self.name != SHOTGUN_ENGINE_NAME:
            icon_path = self.__get_platform_resource_path("folder_256.png")

            self.register_command(
                "Open Log Folder",
                self.__open_log_folder,
                {
                    "short_name": "open_log_folder",
                    "icon": icon_path,
                    "description": (
                        "Opens the folder where log files are " "being stored."
                    ),
                    "type": "context_menu",
                },
            )

    def __register_reload_command(self):
        """
        Registers a "Reload and Restart" command with the engine if any
        running apps are registered via a dev descriptor.
        """
        from tank.platform import restart

        self.register_command(
            "Reload and Restart",
            restart,
            {
                "short_name": "restart",
                "icon": self.__get_platform_resource_path("reload_256.png"),
                "type": "context_menu",
            },
        )

    @property
    def context_change_allowed(self):
        """
        Whether the engine allows a context change without the need for a
        restart.
        """
        return True

    @property
    def host_info(self):
        """
        :returns: A dictionary with information about the application hosting
                  his engine.

        The returned dictionary is of the following form on success:

            {
                "name": "Substance3DPainter",
                "version": "2018.3.1",
            }

        The returned dictionary is of following form on an error preventing
        the version identification.

            {
                "name": "Substance3DPainter",
                "version: "unknown"
            }
        """

        host_info = {"name": "Substance3DPainter", "version": "unknown"}
        try:
            painter_version = self._dcc_app.project.get_application_version()
            host_info["version"] = painter_version
        except Exception:
            pass
        return host_info

    def process_request(self, method, **kwargs):
        """
        This method is the primary entry point for commands sent from the
        QML plugin running inside Substance 3D Painter. It acts as a dispatcher,
        routing requests to the appropriate engine methods.

        .. note::
            In the pure Python plugin model, this method is no longer actively
            used, as communication happens via direct Python calls.

        :param str method: The name of the command to process.
        :param dict kwargs: A dictionary of parameters for the command.
        """
        self.logger.info("process_request. method: %s | kwargs: %s" % (method, kwargs))

        if method == "DISPLAY_MENU":
            menu_position = None
            clicked_info = kwargs.get("clickedPosition")
            if clicked_info:
                menu_position = [clicked_info["x"], clicked_info["y"]]

            self.display_menu(pos=menu_position)

        if method == "NEW_PROJECT_CREATED":
            path = kwargs.get("path")
            change_context = self.get_setting("change_context_on_new_project", False)
            if change_context:
                self.change_context_from_path(path)
            else:
                self.logger.info(
                    "change_context_on_new_project is off so context won't be changed."
                )

        if method == "PROJECT_OPENED":
            path = kwargs.get("path")
            self.change_context_from_path(path)

        if method in self._event_callbacks:
            self.logger.info("About to run callbacks for %s" % method)
            for fn in self._event_callbacks[method]:
                self.logger.info("  callback: %s" % fn)
                fn(**kwargs)

    def register_event_callback(self, event_type, callback_fn):
        """
        Registers a callback function to be executed when a specific event
        is received from Substance 3D Painter.
        """
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        self._event_callbacks[event_type].append(callback_fn)

    def unregister_event_callback(self, event_type, callback_fn):
        """
        Unregisters a previously registered event callback.
        """
        if event_type not in self._event_callbacks:
            # No callbacks registered for this event type, so nothing to do.
            return

        if callback_fn in self._event_callbacks[event_type]:
            self._event_callbacks[event_type].remove(callback_fn)

    def pre_app_init(self):
        """
        Initializes the Substance 3D Painter engine.

        This is a core Toolkit lifecycle method, called by `start_engine`
        before any apps are loaded. It's the ideal place to set up the
        environment, check for compatibility, and prepare the engine.
        This is called before any apps are initialized.
        """

        self.logger.debug("%s: Initializing...", self)

        # check that we are running an ok version of Substance Painter
        current_os = sys.platform
        if current_os not in ["darwin", "win32", "linux64"]:
            raise tank.TankError(
                "The current platform is not supported!"
                " Supported platforms "
                "are Mac, Linux 64 and Windows 64."
            )

        # default menu name is FlowPTR but this can be overridden
        # in the configuration to be sgtk in case of conflicts
        self._menu_name = "Flow Production Tracking"
        if self.get_setting("use_sgtk_as_menu_name", False):
            self._menu_name = "Sgtk"

            # In the case of Windows, we have the possibility of locking up if
            # we allow the PySide shim to import QtWebEngineWidgets.
            # We can stop that happening here by setting the following
            # environment variable.

            if current_os.startswith("win"):
                self.logger.debug(
                    "Substance 3D Painter on Windows can deadlock if QtWebEngineWidgets "
                    "is imported. Setting "
                    "SHOTGUN_SKIP_QTWEBENGINEWIDGETS_IMPORT=1..."
                )
                os.environ["SHOTGUN_SKIP_QTWEBENGINEWIDGETS_IMPORT"] = "1"

    
    def post_app_init(self):
        """
        Called after all apps have been initialized.

        This is a core Toolkit lifecycle method. It's the perfect place to
        finalize the UI (like creating the menu) and run any startup logic,
        as all app commands are now available.
        This is where we create the main menu and run startup apps.
        """
        self.logger.debug("Engine 'post_app_init' starting...")

        # for some reason this engine command get's lost so we add it back
        self.__register_reload_command()

        # Run a series of app instance commands at startup.
        self._run_app_instance_commands()

        # Create the FlowPTR menu
        self.create_shotgun_menu()

        # make sure we setup this engine as the current engine for the platform
        tank.platform.engine.set_current_engine(self)

        # emit an engine started event
        self.sgtk.execute_core_hook(TANK_ENGINE_INIT_HOOK_NAME, engine=self)
        self.logger.debug("Engine 'post_app_init' finished.")

    def post_context_change(self, old_context, new_context):
        """
        Runs after a context change. The Substance 3D Painter event watching will
        be stopped and new callbacks registered containing the new context
        information. This ensures that all app UIs and actions are updated to
        reflect the new Shot, Asset, or Task that the user is working on.
        information.

        :param old_context: The context being changed away from.
        :param new_context: The new context being changed to.
        """

        # restore the open log folder, it get's removed whenever the first time
        # a context is changed
        self.__register_open_log_folder_command()
        self.__register_reload_command()

        '''
        if self.get_setting("automatic_context_switch", True):
            # finally create the menu with the new context if needed
            if old_context != new_context:
                self.create_shotgun_menu()
        '''

    def _run_app_instance_commands(self):
        """
        Runs the series of app instance commands listed in the
        'run_at_startup' setting of the environment configuration yaml file.
        """

        # Build a dictionary mapping app instance names to dictionaries of
        # commands they registered with the engine.
        app_instance_commands = {}
        for (cmd_name, value) in self.commands.items():
            app_instance = value["properties"].get("app")
            if app_instance:
                # Add entry 'command name: command function' to the command
                # dictionary of this app instance.
                cmd_dict = app_instance_commands.setdefault(
                    app_instance.instance_name, {}
                )
                cmd_dict[cmd_name] = value["callback"]

        # Run the series of app instance commands listed in the
        # 'run_at_startup' setting.
        for app_setting_dict in self.get_setting("run_at_startup", []):
            app_instance_name = app_setting_dict["app_instance"]

            # Menu name of the command to run or '' to run all commands of the
            # given app instance.
            setting_cmd_name = app_setting_dict["name"]

            # Retrieve the command dictionary of the given app instance.
            cmd_dict = app_instance_commands.get(app_instance_name)

            if cmd_dict is None:
                self.logger.warning(
                    "%s configuration setting 'run_at_startup' requests app"
                    " '%s' that is not installed.",
                    self.name,
                    app_instance_name,
                )
            else:
                if not setting_cmd_name:
                    # Run all commands of the given app instance.
                    for (cmd_name, command_function) in cmd_dict.items():
                        msg = (
                            "%s startup running app '%s' command '%s'.",
                            self.name,
                            app_instance_name,
                            cmd_name,
                        )
                        self.logger.debug(*msg)

                        command_function()
                else:
                    # Run the command whose name is listed in the
                    # 'run_at_startup' setting.
                    command_function = cmd_dict.get(setting_cmd_name)
                    if command_function:
                        msg = (
                            "%s startup running app '%s' command '%s'.",
                            self.name,
                            app_instance_name,
                            setting_cmd_name,
                        )
                        self.logger.debug(*msg)
                        command_function()
                    else:
                        known_commands = ", ".join("'%s'" % name for name in cmd_dict)
                        self.logger.warning(
                            "%s configuration setting 'run_at_startup' "
                            "requests app '%s' unknown command '%s'. "
                            "Known commands: %s",
                            self.name,
                            app_instance_name,
                            setting_cmd_name,
                            known_commands,
                        )

    def create_shotgun_menu(self, disabled=False):
        """
        Creates the main Flow Production Tracking menu.

        This method uses the MenuGenerator class to build a QMenu object based
        on the commands registered by all the loaded Toolkit apps.

        :return: bool
        """

        if self.has_ui and self.app.ui:
            self.logger.info("Creating Flow Production Tracking menu...")
            self._menu_generator = self.import_module("tk_substancepainter.menu_generation").MenuGenerator(self, self._menu_name)
            self.logger.info("MenuGenerator instantiated. Building menu...")
            self._menu_generator.create_menu()

            main_window = self._get_dialog_parent()
            menu_bar = main_window.menuBar()

            help_action = None
            for action in menu_bar.actions():
                if action.text().replace("&", "") == "Help":
                    help_action = action
                    break

            if help_action:
                menu_bar.insertMenu(help_action, self._menu_generator.menu_handle)
            else:
                menu_bar.addMenu(self._menu_generator.menu_handle)

            self.logger.info("Flow Production Tracking menu created successfully.")
            return True

        return False

    def destroy_engine(self):
        """
        Called when the engine is being destroyed.
        """

        self.logger.debug("{}: Destroying...".format(self))


        # Set a flag to indicate that shutdown has started. This helps prevent
        # deadlocks in the logging system by switching to synchronous logging.
        self._is_shutting_down = True

        # --- CRITICAL STEP: Find and synchronously stop all data retrievers ---
        # This is the most reliable way to prevent the "QThread destroyed while
        # running" crash. We must find all ShotgunDataRetriever instances and
        # call their stop() method, which is a blocking call that waits for
        # background threads to terminate.
        self.logger.debug("Scanning for active ShotgunDataRetrievers to stop...")
        try:
            
            all_widgets = self.created_qt_dialogs + list(self._dock_widgets.values())
            for widget in all_widgets:
                for child in [widget] + widget.findChildren(QtWidgets.QWidget):
                    model = getattr(child, "_model", None)
                    if model:
                        retriever = getattr(model, "_sg_data_retriever", None)
                        if retriever and hasattr(retriever, "stop"):
                            self.logger.info("Found ShotgunDataRetriever. Stopping it now...")
                            retriever.stop()
                            self.logger.info("ShotgunDataRetriever stopped successfully.")
                            # Assuming one retriever per top-level widget is enough to check
                        break

            # --- Add a delay and process events to ensure threads have time to exit ---
            # After requesting the stop, we need to give the Qt event loop a moment
            # to process the thread's termination signals before we destroy the UI.
            self.logger.debug("Waiting for background threads to terminate...")
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.5) # A short, blocking delay can resolve race conditions.
            QtCore.QCoreApplication.processEvents()
            self.logger.debug("Dackground threads terminated")

        except Exception as e:
            self.logger.exception("An error occurred while stopping data retrievers: %s", e)

        # Now that all background threads are stopped, it is safe to destroy the UI
        self.close_windows()

        try:
            super(SubstancePainterEngine, self).destroy_engine()
            self.logger.debug("tk-substancepainter Engine destroyed.")
        except Exception as e:
            self.logger.error(f"Error during base engine destruction: {e}")

    def _get_dialog_parent(self):
        """
        Get the QWidget parent for all dialogs created through
        show_dialog & show_modal.

        In the pure Python model, this should return the main Substance 3D Painter
        window to ensure that Toolkit dialogs are correctly parented and
        behave as expected within the application.
        """
        return self._dcc_app.ui.get_main_window()

    def close_windows(self):
        """
        Closes the various windows (dialogs, panels, etc.) opened by the
        engine.
        """
        self.logger.debug("Closing all tracked UI windows...")

        # Make a copy of the lists to iterate over, as closing widgets will
        # modify the original lists via the `_on_dialog_destroyed` callback.
        all_widgets = self.created_qt_dialogs[:] + list(self._dock_widgets.values())

        for widget in all_widgets:
            try:
                # For dock widgets, we should also remove them from the main UI
                if isinstance(widget, QDockWidget) and widget.parent():
                    self.logger.debug(f"Removing dock widget from UI: {widget.windowTitle()}")
                    self.app.ui.remove_dock_widget(widget)

                widget.close()
                self.logger.debug(f"Closed widget: {widget.windowTitle()}")
            except Exception as e:
                self.logger.warning(f"Could not close widget '{widget.windowTitle()}'. It may have already been destroyed. Error: {e}")

        self._dock_widgets.clear()



    @property
    def has_ui(self):
        """
        Detect and return if Substance 3D Painter is running in batch mode

        :returns: True if the application has a UI, False otherwise.
        """
        return True

    def _emit_log_message(self, handler, record):
        """
        Called by the engine to log messages.
        All log messages from the toolkit logging namespace will be passed to
        this method. This is the bridge between Toolkit's logging system and
        the host application's output window or console.

        this method.

        :param handler: Log handler that this message was dispatched from.
                        Its default format is "[levelname basename] message".
        :type handler: :class:`~python.logging.LogHandler`
        :param record: Standard python logging record.
        :type record: :class:`~python.logging.LogRecord`
        """
        # Give a standard format to the message:
        #     Shotgun <basename>: <message>
        # where "basename" is the leaf part of the logging record name,
        # for example "tk-multi-shotgunpanel" or "qt_importer".
        if record.levelno < logging.INFO:
            formatter = logging.Formatter("Debug: Flow Production Tracking %(basename)s: %(message)s")
        else:
            formatter = logging.Formatter("Flow Production Tracking %(basename)s: %(message)s")

        msg = formatter.format(record).replace("\n", "\n... ")

        # Determine the correct Substance 3D Painter log function to call based on the record level.
        # We create a lambda to wrap the call, which will be executed on the main thread.
        if record.levelno >= logging.ERROR:
            log_fct = lambda: self._dcc_app.logging.error(msg)
        elif record.levelno >= logging.WARNING:
            log_fct = lambda: self._dcc_app.logging.warning(msg)
        elif record.levelno >= logging.INFO:
            log_fct = lambda: self._dcc_app.logging.info(msg)
        else:
            # For debug messages, we use the generic log() function with the DBG_INFO severity
            # and specify our own channel name, as per the API documentation.
            log_fct = lambda: self._dcc_app.logging.log(
                self._dcc_app.logging.DBG_INFO, "FlowPTR", msg
            )

        # During shutdown, the async handler can cause a deadlock.
        # If the engine is shutting down, bypass the async call and print directly.
        # This is less elegant but ensures the application can exit cleanly.
        if self._is_shutting_down:
            # During shutdown, call the log function directly instead of using
            # the async handler to avoid deadlocks. This is safer than print().
            log_fct()
        else:
            # Display the message in Substance 3D Painter script editor in a thread safe manner.
            self.async_execute_in_main_thread(log_fct)

def get_all_ui_panels() -> List[QWidget]:
    """
    Recursively searches the application's main window for all active QWidgets
    that might represent a custom panel or dockable UI element.
    """
    """
    app = QApplication.instance()
    
    if not app:
        print("Error: QApplication instance not found.")
        return []

    # Get the active window (often the main application window of Substance Painter)
    main_window = app.activeWindow()
    
    if not main_window:
        # Fallback: sometimes the active window is None during certain states
        # The next best parent is often the application instance itself,
        # or the QMainWindow that contains the menubar.
        main_window = app.topLevelWidgets()[0] if app.topLevelWidgets() else None

    if main_window:
        # Use findChildren to recursively search for all QWidget objects.
        # This will find everything—including menus, buttons, and panels—but
        # it is the most comprehensive starting point.
        all_widgets = main_window.findChildren(
            QWidget,
            options=Qt.FindChildrenRecursively
        )
        
        # Filter for top-level panels/docks (widgets with no parent or QMainWindow children)
        # For a practical list of panels, you might filter further:
        
        panels_and_docks = [
            w for w in all_widgets
            if w.windowType() == Qt.WindowType.DockWidget
        ]
        
        return all_widgets  # Returning all widgets for a comprehensive list
    
    return []
    """