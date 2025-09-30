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

import os

import sgtk

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"

HookBaseClass = sgtk.get_hook_baseclass()

RESOURCE_IN_USE_COLOR = "#e7a81d"
RESOURCE_NOT_IN_USE_COLOR = "gray"

class SubstancePainterResource(str):
    """
    Helper Class to store metadata per update item.
    
    The tk-multi-breakdown app requires that the 'node' key in each item dictionary
    be a string, as this is what it displays in the UI list.
    
    However, we need to associate more complex data with each item (like the
    resource URL, usage status, etc.) to perform the update correctly.
    
    This class is a workaround for that limitation. It inherits from `str`, so
    it satisfies the breakdown app's requirement. The string value itself is
    formatted with HTML to create a rich text display in the UI. We then attach
    our custom metadata (`resource`, `in_use`, `nice_name`) as attributes directly
    to the object instance.
    
    This allows us to pass complex data through the breakdown process while still
    presenting a user-friendly string in the UI.
    """

    def __new__(cls, resource, in_use, nice_name):
        text = (
            "<span style='color:%s'><b>(%s) - %s</b></span>"
            "<br/><nobr><sub>%s</sub></nobr>"
            % (
                RESOURCE_IN_USE_COLOR if in_use else RESOURCE_NOT_IN_USE_COLOR,
                "Used" if in_use else "Not Used",
                nice_name,
                resource["url"],
            )
        )
        obj = str.__new__(cls, text)
        obj.resource = resource
        obj.in_use = in_use
        obj.nice_name = nice_name
        return obj


class BreakdownSceneOperations(HookBaseClass):
    """
    Breakdown operations for Adobe Substance 3D Painter.

    This implementation handles detection of Adobe Substance 3D Painter resources, 
    that have been loaded with the tk-multi-loader2 toolkit app.
    """

    def _document_resources_by_version(self, engine):
        """
        Scans the current project for all resources that are actively in use
        and returns a dictionary of them, keyed by their unique version ID.
        
        This provides a quick lookup to determine if a resource loaded via the
        Loader is still being used in the project.
        
        :param engine: The current Toolkit engine instance.
        :return: A dictionary of resource info dictionaries.
        """
        resources_in_project = {}

        in_use_resources = engine.app.document_resources()
        for in_use_resource in in_use_resources:
            res_info = engine.app.get_resource_info(in_use_resource)
            if res_info:
                resources_in_project[res_info["version"]] = res_info

        return resources_in_project

    def scan_scene(self):
        """
        The scan scene method is executed once at startup and its purpose is
        to analyze the current scene and return a list of references that are
        to be potentially operated on.

        The return data structure is a list of dictionaries. Each scene 
        reference that is returned should be represented by a dictionary with 
        three keys:

        - "attr": The filename attribute of the 'node' that is to be operated
           on. Most DCCs have a concept of a node, attribute, path or some other
           way to address a particular object in the scene.
        - "type": The object type that this is. This is later passed to the
           update method so that it knows how to handle the object.
        - "path": Path on disk to the referenced object.

        Toolkit will scan the list of items, see if any of the objects matches
        any templates and try to determine if there is a more recent version
        available. Any such versions are then displayed in the UI as out of 
        date.
        """

        refs = []
        engine = sgtk.platform.current_engine()

        # First, get a list of all resources currently being used in the project.
        # We key this by a unique version identifier for fast lookups.
        resources_in_project = self._document_resources_by_version(engine)

        # Next, get the list of all resources that have been imported into this
        # project via the tk-multi-loader2 app. This data is stored in the
        # project's metadata. This gives us a list of what *should* be in the scene.
        resources = engine.app.get_project_settings("tk-multi-loader2") or {}

        # Now, iterate through all the resources that were loaded via the Loader.
        for url in resources.keys():
            res_info = engine.app.get_resource_info(url)

            if res_info:
                # For each loaded resource, check if it's still in our dictionary
                # of actively used resources. This tells us if it's "Used" or "Not Used".
                in_use = res_info["version"] in resources_in_project
                nice_name = res_info["guiName"]

                # The path stored in the project settings is the original publish path.
                # This is what the Breakdown app will use to check for new versions.
                ref_path = resources[url]
                ref_path = ref_path.replace("/", os.path.sep)

                # Create our custom string object to hold all the necessary data.
                # This will be displayed in the UI and passed to the update method.
                refs.append(
                    {
                        "type": "file",
                        "path": ref_path,
                        "node": SubstancePainterResource(res_info, in_use, nice_name),
                    }
                )

        if refs:
            # Sort the list to show "Used" items first, then sort by version.
            # The `not item["node"].in_use` trick sorts boolean False (is in use) before True.
            refs.sort(key=lambda item: (not item["node"].in_use, item["node"].resource["version"]))

        self.parent.log_debug("Scanned scene and found %d references." % len(refs))
        return refs

    def update(self, items):
        """
        Perform replacements given a number of scene items passed from the app.

        Once a selection has been performed in the main UI and the user clicks
        the update button, this method is called.

        The items parameter is a list of dictionaries on the same form as was
        generated by the scan_scene hook above. The path key now holds
        the that each attribute should be updated *to* rather than the current
        path.
        """

        engine = sgtk.platform.current_engine()

        # Get an up-to-date list of resources in the project before we start updating.
        resources_in_project = self._document_resources_by_version(engine)

        for i in items:
            # The 'node' is our custom SubstancePainterResource object.
            node = i["node"]
            node_type = i["type"]
            # The 'path' is the new path to the latest version of the publish.
            new_path = i["path"]

            if node_type == "file":
                # Extract the original resource info from our custom node object.
                res_info = node.resource

                # Double-check that the resource we want to update still exists in the project.
                if res_info["version"] in resources_in_project:
                    res_info = resources_in_project[res_info["version"]]

                # This is the unique URL of the old resource we want to replace.
                url = res_info["url"]

                # A resource can have multiple usages (e.g., basecolor, normal).
                # We need to re-import the new file for each of its original usages.
                for usage in res_info["usages"]:
                    # 1. Import the new file from `new_path` as a new resource.
                    new_url = engine.app.import_project_resource(
                        new_path, usage, "Shotgun"
                    )

                    engine.log_debug("Updating usage: %s" % usage)
                    engine.log_debug("Existing resource url: %s" % url)
                    engine.log_debug("New resource url: %s" % new_url)

                    # 2. Tell Substance 3D Painter to replace all instances of the old resource with the new one.
                    engine.app.update_document_resources(url, new_url)

                    engine.log_debug("Updated usage: %s" % usage)
