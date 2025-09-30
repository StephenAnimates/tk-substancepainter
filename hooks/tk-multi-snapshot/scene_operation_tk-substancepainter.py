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

HookClass = sgtk.get_hook_baseclass()

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"

class SceneOperation(HookClass):
    """
    Hook called to perform scene operations in Substance 3D Painter for the
    tk-multi-snapshot app.

    This hook implements the logic for getting the current scene path,
    opening a snapshot, and saving a snapshot.
    """

    def execute(self, operation, file_path, context, **kwargs):
        """
        Main hook entry point

        :param str operation:       Scene operation to perform (e.g., "current_path",
                                    "open", "save", "save_as").

        :param str file_path:       File path to use if the operation
                                    requires it (e.g., "open", "save_as").

        :param context:             The context the file operation is being
                                    performed in.

        :returns:   Depends on operation:
                    'current_path' - Return the current scene
                                     file path as a String
                    all others     - None
        """
        engine = sgtk.platform.current_engine()

        # ---- Get the current scene path
        if operation == "current_path":
            # This is called by the Snapshot app to find out the path of the
            # current open project, which is the source for the snapshot.
            return engine.app.get_current_project_path()

        # ---- Open a file
        elif operation == "open":
            # This is called when a user double-clicks a snapshot in the UI
            # to restore it.
            engine.app.open_project(file_path)

        # ---- Save the current file
        elif operation == "save":
            # This is called when a user is working on a snapshot and saves it.
            engine.app.save_project()

        # ---- Save the current file as a new file
        elif operation == "save_as":
            # This is the most important operation for this hook. It's called
            # when the user clicks the "Create Snapshot" button. The app provides
            # the path where the new snapshot file should be saved.
            engine.app.save_project_as(file_path)
