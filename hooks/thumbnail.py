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
import tempfile
import uuid

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class ThumbnailHook(HookBaseClass):
    """
    Hook that can be used to generate a thumbnail for the current session.
    It is used by apps like the Publisher to create a thumbnail for a publish.
    """

    def execute(self, **kwargs):
        """
        Main hook entry point

        :returns:       String
                        Hook should return a file path pointing to the location
                        of a thumbnail file on disk that will be used.
                        If the hook returns None then the screenshot
                        functionality will be enabled in the UI.
        """
        # get the engine name from the parent object (app/engine/etc.)
        engine = sgtk.platform.current_engine()

        # depending on engine:
        if engine and engine.name == "tk-substancepainter":
            return self._extract_substancepainter_thumbnail()

        # For any other engine, fall back to the default behavior.
        return None

    def _extract_substancepainter_thumbnail(self):
        """
        Generates and saves a thumbnail from the current Substance 3D Painter viewport.

        This method uses the engine's built-in `extract_thumbnail` function, which
        sends a request to the QML plugin to capture the viewport via the native API.
        This is more reliable than a generic screen grab.

        :returns:   The path to the thumbnail on disk
        """
        engine = sgtk.platform.current_engine()

        # Define a temporary path to save the thumbnail to.
        temp_dir = tempfile.gettempdir()
        temp_filename = "sgtk_thumb_%s.jpg" % uuid.uuid4().hex
        thumb_path = os.path.join(temp_dir, temp_filename)

        # Ask the engine to save the thumbnail to the specified path.
        if engine.app.extract_thumbnail(thumb_path):
            self.parent.log_debug("Successfully generated thumbnail: %s" % thumb_path)
            return thumb_path
        else:
            self.parent.log_error("Thumbnail generation failed.")
            return None
