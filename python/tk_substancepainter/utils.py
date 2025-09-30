# Copyright (c) 2023 Autodesk Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using,copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk Inc.

import os
import sgtk
from packaging.version import parse as LooseVersion
from sgtk.util.filesystem import ensure_folder_exists


def to_normalized_version(version):
    """
    Converts a version string into a new style version.

    - Old versions (e.g., "2.6.2") are left as is.
    - Year-based versions (e.g., "2018.3.1") are converted to a major
      version number by subtracting 2014. For example, "2018.3.1" becomes "4.3.1".
      This was the scheme introduced in 2017.1 (which became 3.1).
    - Modern semantic versions (e.g., "6.1.0", "11.0.3") are left as is.

    :param version: Version string to normalize.
    :returns: A `packaging.version.Version` object.
    """
    version_obj = LooseVersion(str(version))
    if version_obj.major >= 2017:
        return LooseVersion("%s.%s.%s" % (version_obj.major - 2014, version_obj.minor, version_obj.micro))
    return version_obj


def get_session_path():
    """
    Return the path to the current Substance 3D Painter session.
    :return: The path to the current project file, or None.
    """
    engine = sgtk.platform.current_engine()
    path = engine.app.get_current_project_path()
    return path


def save_session(path):
    """
    Save the current session to the supplied path.
    This will create the destination folder if it does not exist.
    :param str path: The path to save the session to.
    """
    folder = os.path.dirname(path)
    ensure_folder_exists(folder)
    engine = sgtk.platform.current_engine()
    engine.app.save_project_as(path)


def get_save_as_action():
    """
    Returns a dictionary suitable for use as a log action button for saving the session.
    It will try to use the tk-multi-workfiles2 app's save dialog if available,
    otherwise it will fall back to the native Substance 3D Painter 'Save As' dialog.
    :return: A dictionary for use in `logger.error(extra=...)`.
    """
    # Get the current engine instance.
    engine = sgtk.platform.current_engine()

    # By default, the callback for the "Save As..." button will be the engine's
    # wrapper around the native Substance 3D Painter save dialog.
    callback = engine.app.save_project_as_action

    # For a more integrated experience, we check if the Workfiles2 app is
    # available in the current environment.
    if "tk-multi-workfiles2" in engine.apps:
        app = engine.apps["tk-multi-workfiles2"]
        # If Workfiles2 is present, we prefer to use its "Save As" dialog,
        # as it provides a consistent, Toolkit-aware file browser.
        if hasattr(app, "show_file_save_dlg"):
            callback = app.show_file_save_dlg

    # Construct the dictionary that the Toolkit logging system uses to create
    # an action button in the log output.
    return {
        "action_button": {
            "label": "Save As...",
            "tooltip": "Save the current session to a new file.",
            "callback": callback,
        }
    }