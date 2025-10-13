# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Menu handling for Adobe Substance 3D Painter

Original code by: Diego Garcia Huerta
Updated by: Stephen Studyvin

Updated:
September 2025, to use Python 3 and PySide6 (sgtk.platform.qt6), and to support current Adobe Substance 3D Painter version.

"""


from collections import defaultdict
import sgtk

__author__ = "Diego Garcia Huerta"
__email__ = "diegogh2000@gmail.com"

# Import from the sgtk qt compatibility layer.
# This ensures the code works with different Qt bindings (PySide2, PySide6).
from sgtk.platform.qt import QtCore, QtGui

try:
    # For modern Qt bindings (PySide2, PySide6), QtWidgets is a separate module.
    from sgtk.platform.qt import QtWidgets
except ImportError:
    # For older Qt bindings (PySide), QtWidgets is part of QtGui.
    QtWidgets = QtGui

class MenuGenerator(object):
    """
    Handles the creation, display, and management of the Flow Production Tracking
    (FlowPTR) menu within Adobe Substance 3D Painter.

    This class builds a QMenu based on the commands registered with the engine,
    including context information, favorites, and commands grouped by app.

    For more on Qt Menus, see:
    https://doc.qt.io/qt-6/qmenu.html
    """

    def __init__(self, engine, menu_name):
        """Initializes the menu generator."""
        self._engine = engine
        self._menu_name = menu_name
        self._dialogs = []
        self._widget = QtWidgets.QWidget()
        self._handle = QtWidgets.QMenu(self._menu_name, self._widget)
        self._ui_cache = []

        

    @property
    def menu_handle(self):
        """The main QMenu object that is being managed."""
        return self._handle

    def hide(self):
        """Hides the menu."""
        self.menu_handle.hide()

    def show(self, pos=None):
        """
        Shows the menu at the given position, or at the current cursor position
        if no position is provided.

        :param pos: A list or tuple [x, y] with the screen coordinates.
        """
        pos = QtGui.QCursor.pos() if pos is None else QtCore.QPoint(pos[0], pos[1])
        qApp = QtWidgets.QApplication.instance()

        # Ensure the menu window is active and on top before showing it.
        self.menu_handle.activateWindow()
        self.menu_handle.raise_()
        # exec_ shows the menu as a modal dialog, waiting for user interaction.
        self.menu_handle.exec_(pos)

    def create_menu(self, disabled=False):
        """
        Renders the entire Flow Production Tracking menu from scratch.

        This method is designed to be called each time the menu is about to be
        shown. By clearing and rebuilding the menu on every call, it ensures
        that all command states (e.g., enabled/disabled based on context) are
        correctly evaluated and displayed to the user.
        """

        self.menu_handle.clear()

        # If the engine is disabled, show a simple message and stop.
        if disabled:
            self.menu_handle.addMenu("Sgtk is disabled.")
            return

        # Add the context-specific sub-menu at the top (e.g., "Shot: D10.010_0020").
        self._context_menu = self._add_context_menu()

        # Add a separator after the context menu.
        self._add_divider(self.menu_handle)

        # now enumerate all items and create menu objects for them
        menu_items = []
        for (cmd_name, cmd_details) in self._engine.commands.items():
            menu_items.append(AppCommand(cmd_name, self, cmd_details))

        # sort list of commands in name order
        menu_items.sort(key=lambda x: x.name)

        # Use the engine's logger for debug messages. This is more informative
        # than a simple print statement and respects Toolkit's logging levels.
        command_names = [item.name for item in menu_items]
        self._engine.logger.debug(f"Found {len(command_names)} commands to build menu: {command_names}")

        # Add any commands marked as "favorites" in the environment config to the top level.
        for fav in self._engine.get_setting("menu_favourites"):
            self._add_favourite(fav, menu_items)

        # Add a separator after the favorites section.
        self._add_divider(self.menu_handle)

        # Add all other app commands, grouped by app, to the main menu.
        self._add_app_menus(menu_items)

        # Add a final "About" item.
        self._add_divider(self.menu_handle)
        self._add_menu_item("About...", self.menu_handle, self._show_about_dialog)

    def _add_favourite(self, fav, menu_items):
        """
        Finds a command specified in the 'menu_favourites' setting and adds it
        directly to the top level of the menu.
        """
        app_instance_name = fav["app_instance"]
        menu_name = fav["name"]

        # Scan through all menu items to find the one matching the favorite definition.
        for cmd in menu_items:
            if (
                cmd.get_app_instance_name() == app_instance_name
                and cmd.name == menu_name
            ):
                # found our match!
                cmd.add_command_to_menu(self.menu_handle)
                # Mark as a favorite so it isn't added again in the app sub-menus.
                cmd.favourite = True

    def _add_app_menus(self, menu_items):
        """
        Organizes all commands by their parent app and adds them to the menu.
        - Commands with a 'context_menu' type are added to the context sub-menu.
        - All other commands are grouped into a dictionary by their app name.
        """
        commands_by_app = defaultdict(list)
        for cmd in menu_items:
            if cmd.get_type() == "context_menu":
                # context menu!
                cmd.add_command_to_menu(self._context_menu)
            else:
                # normal menu
                app_name = cmd.get_app_name()
                if app_name is None:
                    # Group commands that don't belong to a specific app under "Other Items".
                    app_name = "Other Items"
                commands_by_app[app_name].append(cmd)

        self._add_commands_by_app_to_menu(commands_by_app)

    def _add_divider(self, parent_menu):
        """Adds a separator line to a QMenu."""
        divider = QtGui.QAction(parent_menu)
        divider.setSeparator(True)
        parent_menu.addAction(divider)
        return divider

    def _add_sub_menu(self, menu_name, parent_menu):
        """Adds a new sub-menu to a parent QMenu."""
        sub_menu = QtWidgets.QMenu(title=menu_name, parent=parent_menu)
        parent_menu.addMenu(sub_menu)
        return sub_menu

    def _add_menu_item(self, name, parent_menu, callback, properties=None):
        """Adds a single action item to a QMenu."""
        # This is a helper method to create a QAction and connect its `triggered`
        # signal to the provided callback. It also handles setting tooltips and
        # the initial enabled/disabled state based on the command's properties.

        action = QtGui.QAction(name, parent_menu)
        parent_menu.addAction(action)
        action.triggered.connect(callback)

        if properties:
            if "tooltip" in properties:
                action.setTooltip(properties["tooltip"])
                action.setStatustip(properties["tooltip"])
            # The 'enable_callback' is a function provided by the app command
            # that returns True or False, allowing dynamic state changes.
            if "enable_callback" in properties:
                action.setEnabled(properties["enable_callback"]())

        return action

    def _add_context_menu(self):
        """
        Adds the top-level context menu. This menu displays the current Toolkit
        context and provides actions like "Jump to Flow Production Tracking" and
        "Jump to File System".
        """

        ctx = self._engine.context
        ctx_name = str(ctx)

        # create the menu object
        ctx_menu = self._add_sub_menu(ctx_name, self.menu_handle)

        self._add_menu_item("Jump to Flow Production Tracking", ctx_menu, self._jump_to_sg)

        # Add the menu item only when there are some file system locations.
        if ctx.filesystem_locations:
            self._add_menu_item("Jump to File System", ctx_menu, self._jump_to_fs)

        # Add a divider here so that apps can register their own context menu items below it.
        self._add_divider(ctx_menu)

        return ctx_menu

    def _jump_to_sg(self):
        """
        Callback to launch a web browser and navigate to the current context's
        URL in Flow Production Tracking.
        """
        url = self._engine.context.shotgun_url
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def _jump_to_fs(self):
        """
        Callback to open the file system browser to the context's locations on disk.
        """
        # launch one window for each location on disk
        paths = self._engine.context.filesystem_locations
        for path in paths:
            url = QtCore.QUrl.fromLocalFile(path)
            if not QtGui.QDesktopServices.openUrl(url):
                self._engine.log_error(f"Failed to open folder: {path}")

    def _show_about_dialog(self):
        """
        Displays the About dialog box, showing information about the engine.
        """
        engine_name = self._engine.display_name
        engine_version = self._engine.version

        message = (
            f"<b>{engine_name}</b><br>"
            f"Version: {engine_version}<br><br>"
            "This integration connects Adobe Substance 3D Painter with the "
            "Flow Production Tracking toolkit."
        )

        QtWidgets.QMessageBox.about(
            self._widget,  # Parent the dialog to our menu's widget
            f"About {engine_name}",
            message,
        )

    def _add_commands_by_app_to_menu(self, commands_by_app):
        """
        Iterates over the commands grouped by app and adds them to the menu.

        - If an app has multiple commands, a sub-menu is created for it.
        - If an app has only one command, it's added directly to the main menu.
        """
        for app_name in sorted(commands_by_app.keys()):
            cmds = commands_by_app[app_name]
            cmds.sort(key=lambda x: x.name)

            if len(cmds) > 1:
                # If the app has multiple commands, create a sub-menu for it.
                app_menu = self._add_sub_menu(app_name, self.menu_handle)

                for cmd in cmds:
                    cmd.add_command_to_menu(app_menu)
            else:
                # If the app has only one command, add it directly to the main menu
                # to avoid unnecessary sub-menus.
                # todo: Should this be labelled with the name of the app
                # or the name of the menu item? Not sure.
                cmd_obj = cmds[0]
                if not cmd_obj.favourite:
                    # skip favourites since they are already on the menu
                    cmd_obj.add_command_to_menu(self.menu_handle)


class AppCommand(object):
    """
    A wrapper class for a single command dictionary from `engine.commands`.

    This makes it easier to access command properties and provides helper methods
    for interacting with the command's associated app and metadata.
    """

    def __init__(self, name, parent, command_dict):
        self.name = name
        self.parent = parent
        self.properties = command_dict["properties"]
        self.callback = command_dict["callback"]
        self.favourite = False

    def get_app_name(self):
        """
        Returns the display name of the app that this command belongs to.
        """
        if "app" in self.properties:
            return self.properties["app"].display_name
        return None

    def get_app_instance_name(self):
        """
        Returns the name of the app instance, as defined in the environment.
        Returns None if not found.
        """
        if "app" not in self.properties:
            return None

        app_instance = self.properties["app"]
        engine = app_instance.engine

        for (app_instance_name, app_instance_obj) in engine.apps.items():
            if app_instance_obj == app_instance:
                # found our app!
                return app_instance_name

        return None

    def get_documentation_url_str(self):
        """
        Returns the documentation URL for the associated app as a string.
        """
        if "app" in self.properties:
            app = self.properties["app"]
            return app.documentation_url
        return None

    def get_type(self):
        """
        Returns the command type, e.g., 'context_menu' or 'default'.
        """
        return self.properties.get("type", "default")

    def add_command_to_menu(self, menu):
        """
        Adds this app command to the given QMenu.

        It supports creating nested sub-menus if the command name contains '/'.
        """

        # create menu sub-tree if need to:
        # Support menu items seperated by '/'
        parent_menu = menu

        parts = self.name.split("/")
        for item_label in parts[:-1]:
            # see if there is already a sub-menu item
            sub_menu = self._find_sub_menu_item(parent_menu, item_label)
            if sub_menu:
                # already have sub menu
                parent_menu = sub_menu
            else:
                parent_menu = self.parent._add_sub_menu(item_label, parent_menu)

        # Add the final action to the determined parent menu.
        self.parent._add_menu_item(
            parts[-1], parent_menu, self.callback, self.properties
        )

    def _find_sub_menu_item(self, menu, label):
        """
        Helper to find an existing sub-menu QAction within a parent menu by its label.
        """
        for action in menu.actions():
            if action.text() == label:
                return action.menu()
        return None
