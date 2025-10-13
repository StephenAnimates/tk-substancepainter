# Copyright (c) 2023 Autodesk Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk Inc.

"""
App Launch Hook for the tk-substancepainter engine.

This hook overrides the default launch behavior to handle the specific
requirements of launching Substance 3D Painter on macOS.
"""

import sgtk
import subprocess

class AppLaunch(sgtk.Hook):
    """
    Hook to run an application.
    """

    def execute(
        self, app_path, app_args, version, engine_name, software_entity=None, **kwargs
    ):
        """
        The execute function of the hook will be called to start the required application.

        For macOS, this hook launches the internal executable directly to ensure
        that environment variables are correctly passed to the application.
        """

        if sgtk.util.is_macos() and app_path.endswith(".app"):
            # On macOS, to ensure environment variables are correctly passed to a GUI
            # application, we must use the 'open' command-line utility. This is the
            # standard and most reliable way to launch .app bundles with a specific
            # environment.
            self.parent.log_debug("Using 'open' command for robust macOS launch.")
 
            # The 'env' kwarg provided by the launch process contains the fully
            # prepared environment, including SGTK_PYTHONPATH and the crucial
            # DYLD_LIBRARY_PATH. We use this directly.
            launch_env = kwargs.get("env")

            # Build the command list for subprocess.Popen.
            # -n: Open a new instance of the application.
            # -a: Specify the application to open.
            cmd = ["open", "-n", "-a", app_path]

            # If there are arguments, add them after the '--args' flag.
            if app_args:
                cmd.append("--args")
                cmd.append(app_args)

            self.parent.log_debug(f"Constructed launch command: {cmd}")

            # Launch the 'open' command with the prepared environment.
            # This correctly passes the environment to the new application instance.
            subprocess.Popen(cmd, env=launch_env)

        else:
            # For other platforms (Windows, Linux), fall back to the default launch behavior.
            self.parent.log_debug("Using default launch logic.")
            base_hook = self.parent.get_hook_baseclass()
            return base_hook.execute(
                self,
                app_path=app_path,
                app_args=app_args,
                version=version,
                engine_name=engine_name,
                software_entity=software_entity,
                **kwargs,
            )