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

import os
from collections import OrderedDict
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

class MenuGenerator(object):
    """
    A class to generate a menu from the registered engine commands.
    This is a simplified version, moved directly into the engine to ensure
    it uses the correct PySide6 bindings.
    """


    def __init__(self, engine, menu_name, parent):
        self._engine = engine
        self._menu_name = menu_name
        self._menu = None
        self._parent = parent


    def create_menu(self, disabled=False):
        """
        Creates the main Toolkit menu.
        """

        self._engine.logger.info("Creating the menu from engine.py")
        

        # group commands by app
        app_commands = OrderedDict()
        for (cmd_name, value) in self._engine.commands.items():
            app_name = value["properties"].get("app_name")
            if app_name is None:
                app_name = "Flow Production Tracking"
            if app_name not in app_commands:
                app_commands[app_name] = []
            app_commands[app_name].append((cmd_name, value))

    
        self._engine.logger.info("The menu app_commands: %s", app_commands)

        # sort by name
        for app_name in app_commands:
            app_commands[app_name].sort(key=lambda x: x[0])

        # create the menu
        self._menu = QtWidgets.QMenu(self._menu_name, self._parent)
        self._menu.setTearOffEnabled(True)
        self._menu.setEnabled(not disabled)

        # now add the menu items
        for app_name in app_commands:
            if len(app_commands) > 1:
                # create a sub-menu
                app_menu = QtWidgets.QMenu(app_name, self._menu)
                self._menu.addMenu(app_menu)
            else:
                # there is only one app, so don't create a sub-menu
                app_menu = self._menu

            # add the menu items
            for (cmd_name, value) in app_commands[app_name]:
                # get the icon
                icon = value["properties"].get("icon")
                if icon:
                    icon = QtGui.QIcon(icon)
                else:
                    icon = QtGui.QIcon()

                # get the callback
                callback = value["callback"]

                # create the action
                action = QtGui.QAction(icon, cmd_name, self._menu)
                action.triggered.connect(callback)

                # add the action to the menu
                app_menu.addAction(action)

        # add a separator
        self._menu.addSeparator()

        # add context menu items
        for (cmd_name, value) in self._engine.commands.items():
            if value["properties"].get("type") == "context_menu":
                # get the icon
                icon = value["properties"].get("icon")
                if icon:
                    icon = QtGui.QIcon(icon)
                else:
                    icon = QtGui.QIcon()

                # get the callback
                callback = value["callback"]

                # create the action
                action = QtGui.QAction(icon, cmd_name, self._menu)
                action.triggered.connect(callback)

                # add the action to the menu
                self._menu.addAction(action)

    def show(self, pos=None):
        """
        Shows the menu at the given position.
        """
        if self._menu:
            if pos:
                # The pos is a list [x, y] from the QML side.
                # We need to convert it to a QPoint.
                point = QtCore.QPoint(pos[0], pos[1])
                self._menu.exec_(point)
            else:
                # If no position is given, show at the current cursor position.
                self._menu.exec_(QtGui.QCursor.pos())






# the following was in the engine.py file class SubstancePainterEngine(Engine)

class SubstancePainterEngine(Engine):

    def create_shotgun_menu(self, disabled=False):
        """
        Creates the main Flow Production Tracking menu.

        This method uses the MenuGenerator class to build a QMenu object based
        on the commands registered by all the loaded Toolkit apps.

        Note that this only creates the menu, not the child actions
        :return: bool
        """

        # only create the FlowPTR menu if not in batch mode and menu doesn't
        # already exist
        if self.has_ui and self._dcc_app.ui:
            print("Creating FlowPTR menu...")
            # Create our menu handler. This will build a QMenu object from all
            # the registered app commands using the class now defined in this file.
            parent_widget = self._get_dialog_parent()
            self._menu_generator = MenuGenerator(self, self._menu_name, parent_widget)
            self.logger.info("MenuGenerator instantiated. Building menu...")
            self._menu_generator.create_menu()
            self.logger.info("FlowPTR menu created successfully.")
            return True

        return False
        
    def display_menu(self, pos=None):
        """
        Shows the engine's main menu at the given screen position.

        This method is connected to the 'FlowPTR Plugin' QAction in the main
        Substance 3D Painter UI. When the user clicks the menu item, this
        method is called to display the dynamically generated Toolkit menu.
        """
        if self._menu_generator:
            self.logger.debug("Showing FlowPTR menu...")
            self._menu_generator.show(pos)
        else:
            self.logger.error("Could not show menu because it has not been created.")