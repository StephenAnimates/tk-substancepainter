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

import os
import sgtk
from sgtk.platform.qt5 import QtWidgets

HookClass = sgtk.get_hook_baseclass()

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"

class SceneOperation(HookClass):
    """
    Hook called to perform scene operations in Substance 3D Painter.

    This hook implements the logic for the open, save, save as, and new file
    actions in the Workfiles2 app.
    """

    # A class-level variable to temporarily store the path to the mesh selected
    # by the user during the "New File" operation.
    _new_scene_mesh_path = None

    def execute(
        self,
        operation,
        file_path,
        context,
        parent_action,
        file_version,
        read_only,
        **kwargs
    ):
        """
        Main hook entry point
        This method is called by the Workfiles2 app to perform an action
        on the current scene.

        :param str operation:       String
                                Scene operation to perform

        :param file_path:       String
                                File path to use if the operation
                                requires it (e.g. open)

        :param context:         Context
                                The context the file operation is being
                                performed in.

        :param parent_action:   This is the action that this scene operation is
                                being executed for.  This can be one of:
                                - open_file
                                - new_file
                                - save_file_as
                                - version_up

        :param file_version:    The version/revision of the file to be opened.  If this is 'None'
                                then the latest version should be opened.

        :param read_only:       Specifies if the file should be opened read-only or not

        :returns:               Depends on operation:
                                'current_path' - Return the current scene
                                                 file path as a String
                                'reset'        - True if scene was reset to an empty
                                                 state, otherwise False
                                all others     - None
        """
        app = self.parent
        engine = sgtk.platform.current_engine()

        # ---- Get the current scene path
        if operation == "current_path":
            # This is called by Workfiles to find out the path of the current
            # open project.
            return engine.app.get_current_project_path()

        # ---- Open a file
        elif operation == "open":
            # This is called when a user clicks "Open" in the Workfiles UI.
            # It opens the specified project file.
            engine.app.open_project(file_path)

        # ---- Save the current file
        elif operation == "save":
            # This is called when a user clicks "Save" in the Workfiles UI.
            # It saves the current project.
            engine.app.save_project()

        # ---- Save the current file as a new file
        elif operation == "save_as":
            # This is called when a user clicks "Save As" in the Workfiles UI.
            # It saves the current project to the specified path.
            engine.app.save_project_as(file_path)

        # ---- Reset the scene to an empty state for a new file
        elif operation == "reset":
            # This is called as part of the "New File" workflow.
            # For Substance 3D Painter, creating a new project requires a mesh.
            # We use the mesh path that was captured in the 'prepare_new' step.
            if self._new_scene_mesh_path:
                self.parent.log_info(
                    "Creating new project with mesh: %s" % self._new_scene_mesh_path
                )
                # Create a new project using the selected mesh.
                # The project is created in a temporary state and will be saved
                # to its final work file path by a subsequent 'save_as' call
                # from the Workfiles app.
                engine.app.new_project(self._new_scene_mesh_path)
                # Reset the stored path.
                self._new_scene_mesh_path = None
                return True
            else:
                # If no mesh path was stored, it means 'prepare_new' was not
                # successful or was cancelled. We can just close the project.
                self.parent.log_warning(
                    "No mesh selected for new scene. Closing current project."
                )
                engine.app.close_project()
                return True

        # ---- Prepare for a new file operation
        elif operation == "prepare_new":
            # This is called before the 'reset' operation when "New File" is
            # initiated. It's our chance to gather any information needed to
            # create a new scene. For Substance 3D Painter, we must ask the
            # user to select a mesh file.

            # Reset any previously stored path.
            self._new_scene_mesh_path = None

            # Use a Qt file dialog to ask the user for a mesh file.
            file_dialog = QtWidgets.QFileDialog(
                parent=engine.get_dialog_parent(),
                caption="Select a mesh for the new project",
                filter="Mesh Files (*.fbx *.obj *.abc)",
            )
            file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
            if file_dialog.exec_():
                # If the user selects a file, store its path.
                self._new_scene_mesh_path = file_dialog.selectedFiles()[0]
