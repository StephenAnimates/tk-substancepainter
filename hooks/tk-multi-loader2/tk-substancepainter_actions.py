# Copyright (c) 2015 Shotgun Software Inc.
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

"""
Hook that defines the available actions for publishes loaded into
Substance 3D Painter.

This hook is responsible for generating the actions that appear in the Loader app
UI. For example, when a user selects a published SBSAR file, this hook will
return actions like "Import as basematerial", "Import as texture", etc.,
allowing the user to choose how to import the file into their project.
"""

import os
import sgtk

__author__ = "Stephen Studyvin"
__contact__ = "https://www.linkedin.com/in/stephenanimates/"

HookBaseClass = sgtk.get_hook_baseclass()

# This dictionary maps a Flow Production Tracking Published File Type to a list
# of valid "usages" within Substance 3D Painter. When a publish of a certain
# type is selected in the Loader, this dictionary is used to generate the
# list of available import actions for the user.
publishedfile_type_to_actions = {
    "Image": ("environment", "colorlut", "alpha", "texture"),
    "Texture": ("environment", "colorlut", "alpha", "texture"),
    "Rendered Image": ("environment", "colorlut", "alpha", "texture"),
    "Substance Material Preset": ["preset"],
    "Sppr File": ["preset"],
    "PopcornFX": ["script"],
    "Pkfx File": ["script"],
    "Shader": ["shader"],
    "Glsl File": ["shader"],
    "Substance Export Preset": ["export"],
    "Spexp File": ["export"],
    "Substance Smart Material": ["smartmaterial"],
    "Spsm File": ["smartmaterial"],
    "Substance File": [
        "basematerial",
        "alpha",
        "texture",
        "filter",
        "procedural",
        "generator",
    ],
    "Sbsar File": [
        "basematerial",
        "alpha",
        "texture",
        "filter",
        "procedural",
        "generator",
    ],
    "Substance Smart Mask": ["smartmask"],
    "Spmsk File": ["smartmask"],
}

class SubstancePainterActions(HookBaseClass):

    def __init__(self, *args, **kwargs):
        """
        Initialize the hook.
        """
        super().__init__(*args, **kwargs)
        self.engine = sgtk.platform.current_engine()

    ###########################################################################
    # public interface - to be overridden by deriving classes

    def generate_actions(self, sg_publish_data, actions, ui_area):
        """
        Returns a list of action instances for a particular publish. This
        method is called each time a user selects a publish in the Loader UI.
        The data returned from this hook will be used to populate the "Actions"
        menu for that publish.
        
        The mapping between Publish types and actions are kept in a different
        place (in the configuration) so at the point when this hook is called,
        the loader app has already established *which* actions are appropriate
        for this object.

        The hook should return at least one action for each item passed in via
        the actions parameter.

        This method needs to return detailed data for those actions, in the form
        of a list of dictionaries. Each dictionary should have 'name', 'params',
        'caption', and 'description' keys.
        
        Because you are operating on a particular publish, you may tailor the
        output  (caption, tooltip etc) to contain custom information suitable
        for this publish.

        The ui_area parameter is a string and indicates where the publish is to
        be shown.
        - If it will be shown in the main browsing area, "main" is passed.
        - If it will be shown in the details area, "details" is passed.
        - If it will be shown in the history area, "history" is passed.

        Please note that it is perfectly possible to create more than one 
        action "instance" for a given action! For example, you could do scene
        introspection, and if the action passed in is "character_attachment",
        you could scan the scene, figure out all the nodes where this object
        can be attached and return a list of action instances: "attach to left
        hand", "attach to right hand" etc. In this case, when more than one
        object is returned for an action, use
        the params key to pass additional data into the run_action hook.

        :param sg_publish_data: Flow Production Tracking data dictionary with all the standard publish fields.
        :param actions: List of action strings which have been defined in the app configuration.
        :param ui_area: String denoting the UI Area (see above).
        :returns List of dictionaries, each with keys name, params, caption 
         and description
        """

        app = self.parent
        app.log_debug(
            "Generate actions called for UI element %s. "
            "Actions: %s. Publish Data: %s" % (ui_area, actions, sg_publish_data)
        )

        published_file_type = sg_publish_data["published_file_type"]["name"]
        app.log_debug("Generating actions for published file type: %s" % published_file_type)

        # Look up the available actions for this published file type
        # in our dictionary.
        available_actions = publishedfile_type_to_actions.get(published_file_type)

        action_instances = []

        if available_actions:
            # If actions are defined for this type, create an action instance
            # for each one.
            for action in available_actions:
                # The 'name' is an internal identifier for the action.
                # The 'caption' is the user-facing text in the menu.
                # The 'params' are passed to the execute_action method.
                action_instances.append(
                    {
                        "name": "Import Project Resource as %s" % action,
                        "params": action,
                        "caption": "Import as %s" % action.capitalize(),
                        "description": (
                            "This will import the %s as a '%s' resource inside the current project."
                            % (published_file_type, action)
                        ),
                    }
                )

        return action_instances

    def execute_multiple_actions(self, actions):
        """
        Executes the specified action on a list of items.

        The default implementation dispatches each item from ``actions`` to
        the ``execute_action`` method.

        The ``actions`` is a list of dictionaries holding all the actions to
        execute.
        Each entry will have the following values:

            name: Name of the action to execute
            sg_publish_data: Publish information coming from Flow Production Tracking
            params: Parameters passed down from the generate_actions hook.

        .. note::
            This is the default entry point for the hook. It reuses the 
            ``execute_action`` method for backward compatibility with hooks
             written for the previous version of the loader.

        .. note::
            The hook will stop applying the actions on the selection if an
            error is raised midway through.

        :param list actions: Action dictionaries.
        """
        app = self.parent
        for single_action in actions:
            app.log_debug("Single Action: %s" % single_action)
            name = single_action["name"]
            sg_publish_data = single_action["sg_publish_data"]
            params = single_action["params"]

            self.execute_action(name, params, sg_publish_data)

    def execute_action(self, name, params, sg_publish_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.
        
        :param name: Action name string representing one of the items returned
                     by generate_actions.
        :param params: Params data, as specified by generate_actions (this will be the 'usage').
        :param sg_publish_data: Flow Production Tracking data dictionary with all the standard
                                publish fields.
        :returns: Does not return a value.
        """
        app = self.parent
        app.log_debug(
            "Execute action called for action %s. "
            "Parameters: %s. Publish Data: %s" % (name, params, sg_publish_data)
        )

        # Get the file path from the publish data.
        path = self.get_publish_path(sg_publish_data).replace(os.path.sep, "/")

        # The 'params' from generate_actions is the 'usage' string we need.
        usage = params

        # Call the engine's import_project_resource method to perform the import.
        # The "Shotgun" destination refers to a shelf inside Substance 3D Painter.
        # This could be configured to be more generic if needed.
        result = self.engine.app.import_project_resource(path, usage, "Shotgun")

        if not result:
            app.log_error(
                "Failed to import resource '%s' as usage '%s'." % (path, usage)
            )
