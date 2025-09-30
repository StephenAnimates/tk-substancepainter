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

"""

import os
import sys
import time
import inspect
import logging
import traceback
from functools import wraps

import tank
from tank.log import LogManager
from tank.platform import Engine
from tank.platform.constants import SHOTGUN_ENGINE_NAME
from tank.platform.constants import TANK_ENGINE_INIT_HOOK_NAME

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"

# env variable that control if to show the compatibility warning dialog
# when Substance Painter software version is above the tested one.
SHOW_COMP_DLG = "SGTK_COMPATIBILITY_DIALOG_SHOWN"

MINIMUM_SUPPORTED_VERSION = "2018.3"


# logging functionality
def display_error(msg):
    t = time.asctime(time.localtime())
    print("%s - FlowPTR Error | Substance 3D Painter engine | %s " % (t, msg))


def display_warning(msg):
    t = time.asctime(time.localtime())
    print("%s - FlowPTR Warning | Substance 3D Painter engine | %s " % (t, msg))


def display_info(msg):
    t = time.asctime(time.localtime())
    print("%s - FlowPTR Info | Substance 3D Painter engine | %s " % (t, msg))


def display_debug(msg):
    if os.environ.get("TK_DEBUG") == "1":
        t = time.asctime(time.localtime())
        print("%s - FlowPTR Debug | Substance 3D Painter engine | %s " % (t, msg))

# methods to support the state when the engine cannot start up
# for example if a non-tank file is loaded in Substance Painter we load the
# project context if exists, so we give a chance to the user to at least
# do the basics operations.

def refresh_engine(scene_name, prev_context):
    """
    Refresh the current engine
    """

    engine = tank.platform.current_engine()

    if not engine:
        # If we don't have an engine for some reason then we don't have
        # anything to do.
        sys.stdout.write("refresh_engine | no engine!\n")
        return

    # This is a File->New call, so we just leave the engine in the current
    # context and move on.
    if scene_name in ("", "Untitled.spp"):
        if prev_context and prev_context != engine.context:
            engine.change_context(prev_context)

        # FlowPTR menu may have been removed, so add it back in if its not
        # already there.
        engine.create_shotgun_menu()
        return

    # determine the tk instance and ctx to use:
    tk = engine.sgtk

    # loading a scene file
    new_path = os.path.abspath(scene_name)

    # this file could be in another project altogether, so create a new
    # API instance.
    try:
        # and construct the new context for this path:
        tk = tank.tank_from_path(new_path)
        ctx = tk.context_from_path(new_path, prev_context)
    except tank.TankError:
        try:
            # could not detect context from path, will use the project context
            # for menus if it exists
            ctx = engine.sgtk.context_from_entity_dictionary(engine.context.project)
            message = (
                "Flow Production Tracking could not detect a context from the project path.\n"
                "from the project loaded. FlowPTR menus will be reset\n"
                "to the project '%s' context.\n"
                % engine.context.project.get("name")
            )
            engine.show_warning(message)

        except tank.TankError:
            (exc_type, exc_value, exc_traceback) = sys.exc_info()
            message = ""
            message += "Flow Production Tracking engine cannot be started.\n"
            message += "Please contact support\n\n"
            message += "Exception: %s - %s\n" % (exc_type, exc_value)
            message += "Traceback (most recent call last):\n"
            message += "\n".join(traceback.format_tb(exc_traceback))

            # disabled menu, could not get project context
            engine.create_shotgun_menu(disabled=True)
            engine.show_error(message)
            return

    if ctx != engine.context:
        engine.change_context(ctx)

    # FlowPTR menu may have been removed,
    # so add it back in if its not already there.
    engine.create_shotgun_menu()


class SubstancePainterEngine(Engine):
    """
    The Flow Production Tracking Toolkit engine for Adobe Substance 3D Painter.

    This engine is responsible for managing the communication with Substance 3D Painter,
    bootstrapping the Toolkit environment, handling context changes, and displaying
    Toolkit app UIs.
    """

    def __init__(self, *args, **kwargs):
        """
        Engine Constructor
        """
        self._qt_app = None
        self._dcc_app = None
        self._menu_generator = None
        self._event_callbacks = {}

        Engine.__init__(self, *args, **kwargs)

    @property
    def app(self):
        """
        A client object that provides an API for interacting with Substance 3D Painter.
        """
        return self._dcc_app

    def show_message(self, msg, level="info"):
        """
        Displays a dialog with the message according to  the severity level
        specified.
        """
        if self._qt_app_central_widget:
            from sgtk.platform.qt5 import QtWidgets, QtGui, QtCore

            level_icon = {
                "info": QtWidgets.QMessageBox.Information,
                "error": QtWidgets.QMessageBox.Critical,
                "warning": QtWidgets.QMessageBox.Warning,
            }

            dlg = QtWidgets.QMessageBox(self._qt_app_central_widget)
            dlg.setIcon(level_icon[level])
            dlg.setText(msg)
            dlg.setWindowTitle("FlowPTR Substance 3D Painter engine")
            dlg.setWindowFlags(dlg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            dlg.show()
            dlg.exec_()

    def show_error(self, msg):
        """
        Displays an error dialog message
        """
        self.show_message(msg, level="error")

    def show_warning(self, msg):
        """
        Displays a warning dialog message
        """
        self.show_message(msg, level="warning")

    def show_info(self, msg):
        """
        Displays an informative dialog message
        """
        self.show_message(msg, level="info")

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
        self.logger.debug(
            "calling Substance 3D Painter with debug: %s" % LogManager().global_debug
        )

        # flip debug logging
        LogManager().global_debug = not LogManager().global_debug
        if self.app:
            self.app.toggle_debug_logging(LogManager().global_debug)

    def __open_log_folder(self):
        """
        Opens the file system folder where log files are being stored.
        """
        self.log_info("Log folder is located in '%s'" % LogManager().log_folder)

        if self.has_ui:
            # only import QT if we have a UI
            from sgtk.platform.qt import QtGui, QtCore

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
            painter_version = self._dcc_app.get_application_version()
            host_info["version"] = painter_version
        except Exception:
            pass
        return host_info

    def process_request(self, method, **kwargs):
        """
        This method is the primary entry point for commands sent from the
        QML plugin running inside Substance 3D Painter. It acts as a dispatcher,
        routing requests to the appropriate engine methods.

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
                refresh_engine(path, self.context)
            else:
                self.logger.info(
                    "change_context_on_new_project is off so context won't be changed."
                )

        if method == "PROJECT_OPENED":
            path = kwargs.get("path")
            refresh_engine(path, self.context)

        if method == "QUIT":
            if self._qt_app:
                self.destroy_engine()
                self._qt_app.quit()

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
        This is called before any apps are initialized.
        """

        self.logger.debug("%s: Initializing...", self)

        self.tk_substancepainter = self.import_module("tk_substancepainter")
        self.utils = self.tk_substancepainter.utils

        self.init_qt_app()

        port = os.environ["SGTK_SUBSTANCEPAINTER_ENGINE_PORT"]
        url = "ws://localhost:%s" % port

        engine_client_class = self.tk_substancepainter.application.EngineClient
        self._dcc_app = engine_client_class(self, parent=self._qt_app, url=url)

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

        painter_version_str = self._dcc_app.get_application_version()

        # Normalize the version strings for reliable comparison.
        # This handles different versioning schemes used by Substance 3D Painter over the years.
        painter_version = self.utils.to_normalized_version(painter_version_str)
        painter_min_supported_version = self.utils.to_normalized_version(MINIMUM_SUPPORTED_VERSION)

        if painter_version < painter_min_supported_version:
            msg = (
                "FlowPTR integration is not compatible with Substance 3D Painter versions"
                " older than %s" % MINIMUM_SUPPORTED_VERSION
            )
            raise tank.TankError(msg)

        if painter_version > painter_min_supported_version:
            # show a warning that this version of Substance 3D Painter isn't yet fully tested
            # with Flow Production Tracking:
            msg = (
                "The FlowPTR Pipeline Toolkit has not yet been fully "
                "tested with Substance 3D Painter %s.  "
                "You can continue to use Toolkit but you may experience "
                "bugs or instability."
                "\n\n" % (painter_version)
            )

            # determine if we should show the compatibility warning dialog:
            show_warning_dlg = self.has_ui and SHOW_COMP_DLG not in os.environ

            if show_warning_dlg:
                # make sure we only show it once per session
                os.environ[SHOW_COMP_DLG] = "1"

                # check against the compatibility_dialog_min_version
                # setting
                min_version_str = self.get_setting("compatibility_dialog_min_version")

                min_version = self.utils.to_normalized_version(min_version_str)
                if painter_version < min_version:
                    show_warning_dlg = False

            if show_warning_dlg:
                # Note, title is padded to try to ensure dialog isn't insanely
                # narrow!
                self.show_warning(msg)

            # always log the warning to the script editor:
            self.logger.warning(msg)

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

    def create_shotgun_menu(self, disabled=False):
        """
        Creates the main Flow Production Tracking menu.
        Note that this only creates the menu, not the child actions
        :return: bool
        """

        # only create the FlowPTR menu if not in batch mode and menu doesn't
        # already exist
        if self.has_ui:
            # create our menu handler
            self._menu_generator = self.tk_substancepainter.MenuGenerator(
                self, self._menu_name
            )

            self._qt_app.setActiveWindow(self._menu_generator.menu_handle)
            self._menu_generator.create_menu(disabled=disabled)
            return True

        return False

    def display_menu(self, pos=None):
        """
        Shows the engine's main menu at the given screen position.
        """
        if self._menu_generator:
            self._menu_generator.show(pos)

    def init_qt_app(self):
        """
        Initializes if not done already the QT Application for the engine.

        This method ensures that a QApplication instance exists, which is required
        for displaying any Qt-based UIs from Toolkit apps. It also sets up a
        main window to act as a parent for dialogs.
        """
        from sgtk.platform.qt5 import QtWidgets, QtGui

        if not QtWidgets.QApplication.instance():
            self._qt_app = QtWidgets.QApplication(sys.argv)
            self._qt_app.setWindowIcon(QtGui.QIcon(self.icon_256))

            self._qt_app_main_window = QtWidgets.QMainWindow()
            self._qt_app_central_widget = QtWidgets.QWidget()
            self._qt_app_main_window.setCentralWidget(self._qt_app_central_widget)
            self._qt_app.setQuitOnLastWindowClosed(False)

            # Make the QApplication use the dark theme. Must be called after the QApplication is instantiated
            self._initialize_dark_look_and_feel()

        else:
            self._qt_app = QtWidgets.QApplication.instance()

    def post_app_init(self):
        """
        Called after all apps have been initialized.
        This is where we create the main menu, run startup apps, and start the
        main Qt event loop.
        """

        # for some reason this engine command get's lost so we add it back
        self.__register_reload_command()

        # Run a series of app instance commands at startup.
        self._run_app_instance_commands()

        # Create the FlowPTR menu
        self.create_shotgun_menu()

        # Let the app know we are ready for action!
        self._dcc_app.broadcast_event("ENGINE_READY")

        # make sure we setup this engine as the current engine for the platform
        tank.platform.engine.set_current_engine(self)

        # emit an engine started event
        self.sgtk.execute_core_hook(TANK_ENGINE_INIT_HOOK_NAME, engine=self)

        # initalize qt loop
        self._qt_app.exec_()

    def post_context_change(self, old_context, new_context):
        """
        Runs after a context change. The Substance 3D Painter event watching will
        be stopped and new callbacks registered containing the new context
        information.

        :param old_context: The context being changed away from.
        :param new_context: The new context being changed to.
        """

        # restore the open log folder, it get's removed whenever the first time
        # a context is changed
        self.__register_open_log_folder_command()
        self.__register_reload_command()

        if self.get_setting("automatic_context_switch", True):
            # finally create the menu with the new context if needed
            if old_context != new_context:
                self.create_shotgun_menu()

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
                        self.logger.debug(msg)

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
                        self.logger.debug(msg)

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

    def destroy_engine(self):
        """
        Called when the engine is being destroyed.
        """
        self.logger.debug("%s: Destroying...", self)

    def _get_dialog_parent(self):
        """
        Get the QWidget parent for all dialogs created through
        show_dialog & show_modal.
        """
        return self._qt_app_main_window

    @property
    def has_ui(self):
        """
        Detect and return if Substance 3D Painter is running in batch mode
        """
        return True

    def _emit_log_message(self, handler, record):
        """
        Called by the engine to log messages.
        All log messages from the toolkit logging namespace will be passed to
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

        # Select Substance 3D Painter display function to use according to the logging
        # record level.
        if record.levelno >= logging.ERROR:
            fct = display_error
        elif record.levelno >= logging.WARNING:
            fct = display_warning
        elif record.levelno >= logging.INFO:
            fct = display_info
        else:
            fct = display_debug

        # Display the message in Substance 3D Painter script editor in a thread safe manner.
        self.async_execute_in_main_thread(fct, msg)

    def close_windows(self):
        """
        Closes the various windows (dialogs, panels, etc.) opened by the
        engine.
        """

        # Make a copy of the list of Tank dialogs that have been created by the
        # engine and are still opened since the original list will be updated
        # when each dialog is closed.
        opened_dialog_list = self.created_qt_dialogs[:]

        # Loop through the list of opened Tank dialogs.
        for dialog in opened_dialog_list:
            dialog_window_title = dialog.windowTitle()
            try:
                # Close the dialog and let its close callback remove it from
                # the original dialog list.
                self.logger.debug("Closing dialog %s.", dialog_window_title)
                dialog.close()
            except Exception as exception:
                traceback.print_exc()
                self.logger.error(
                    "Cannot close dialog %s: %s", dialog_window_title, exception
                )
