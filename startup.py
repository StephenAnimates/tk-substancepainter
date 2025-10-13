# Copyright (c) 2017 Shotgun Software Inc.
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

# https://help.autodesk.com/view/SGDEV/ENU/?guid=SGD_pg_developer_pg_sgtk_developer_app_html

import os
import sys
import socket
from contextlib import closing
import subprocess
import shutil
import sgtk

from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation

class SubstancePainterLauncher(SoftwareLauncher):
    """
    Handles the launching of Adobe Substance 3D Painter. Contains the logic for
    scanning for installed versions of the software and
    how to correctly set up a launch environment for the tk-substancepainter
    engine. This is part of the Toolkit platform's startup framework.

    For more on the SoftwareLauncher, see:
    https://help.autodesk.com/view/SGDEV/ENU/?guid=SG_Pipeline_Toolkit_Core_API_tk_core_platform_launch
    """

    print("starting the Substance Painter SoftwareLauncher")

    # Named regex strings to insert into the executable template paths when
    # matching against supplied versions and products. Similar to the glob
    # strings, these allow us to alter the regex matching for any of the
    # variable components of the path in one place.
    COMPONENT_REGEX_LOOKUP = {
        "version": "[\d.]+",
        "version_back": "[\d.]+",  # backreference to ensure same version
    }

    # This dictionary defines a list of executable template strings for each
    # of the supported operating systems. The templates are used for discovery
    # of installed versions.
    EXECUTABLE_MATCH_TEMPLATES = [
        {
            # Modern Adobe-branded path
            "darwin": "/Applications/Adobe Substance 3D Painter/Adobe Substance 3D Painter.app",
            "win32": "C:/Program Files/Adobe/Adobe Substance 3D Painter/Adobe Substance 3D Painter.exe",
            "linux": "/opt/Adobe/Adobe_Substance_3D_Painter/Adobe_Substance_3D_Painter",
        },
        {
            # Legacy Allegorithmic-branded path
            "darwin": "/Applications/Allegorithmic/Substance Painter/Substance Painter.app",
            "win32": "C:/Program Files/Allegorithmic/Substance Painter/Substance Painter.exe",
            "linux": "/opt/Allegorithmic/Substance_Painter/Substance_Painter",
        },
    ]

    SUPPORTED_PLATFORMS = ["darwin", "win32", "linux"]

    @property
    def minimum_supported_version(self):
        """
        The minimum software version that is supported by the launcher.
        """
        return "2018.3.0"

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch Substance 3D Painter so that it will automatically
        load Toolkit after startup.

        :param str exec_path: Path to executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on launch.
        :returns: :class:`LaunchInformation` instance
        """

        # Before launching, ensure the Python plugin is installed.
        self._install_plugin()

        # Initialize an empty environment. We will only pass the variables
        # that need to be added or modified to the launch environment.
        required_env = {}

        # The exec_path is the path stored on the Software entity in Flow.
        # If it's not set, we'll try to find the executable locally as a fallback.
        launch_path = exec_path

        if not launch_path or not os.path.exists(launch_path):
            self.logger.warning(
                "Executable path not found in Flow or is invalid. "
                "Scanning for a local installation..."
            )
            for match_template_set in self.EXECUTABLE_MATCH_TEMPLATES:
                template_path = match_template_set.get(sys.platform)
                if template_path and os.path.exists(template_path):
                    launch_path = template_path
                    self.logger.debug("Found local executable at: %s", launch_path)
                    break

        # --- Version Check ---
        # Per your research, the only reliable way to get the version is via the
        # command line. We will do this before launching the app.
        try:
            version_check_path = launch_path
            if sys.platform == "darwin" and launch_path.endswith(".app"):
                app_name = os.path.splitext(os.path.basename(launch_path))[0]
                version_check_path = os.path.join(launch_path, "Contents", "MacOS", app_name)

            self.logger.debug("Checking version with command: '%s -v'", version_check_path)
            output = subprocess.check_output([version_check_path, "-v"], stderr=subprocess.STDOUT, text=True)
            # The output is typically "Adobe Substance 3D Painter, version X.Y.Z"
            version_str = output.split("version")[-1].strip()
            self.logger.info("Detected Substance 3D Painter version: %s", version_str)

            # You can add a compatibility check here if needed in the future.

        except Exception as e:
            self.logger.warning("Could not determine Substance 3D Painter version. "
                                "Proceeding without version check. Error: %s", e)

        self.logger.info("Startup install_plugin - Launching executable: %s", launch_path)

        # Set the environment variables required by the pure Python plugin's
        # bootstrap process. The start_plugin() function will read these
        # to initialize the Toolkit engine.
        required_env["SGTK_ENGINE"] = self.engine_name
        required_env["SGTK_CONTEXT"] = sgtk.context.serialize(self.context)
        required_env["SGTK_PYTHONPATH"] = os.pathsep.join(sys.path)

        # self.logger.debug("Prepared launch environment: %s", required_env)

        # On macOS, the app bundle's Contents/MacOS folder needs to be on the
        # PATH for the process to be able to find its libraries.
        if sys.platform == "darwin":
            # To solve the 'libssl.3.dylib' loading error, we must add the Flow Desktop
            # app's Python library path to the dynamic library search path.
            # The python executable running this script is inside the app bundle, so we
            # can derive the correct path from its location.
            sg_python_lib_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "..", "Python3", "lib"))
            if os.path.exists(sg_python_lib_path):
                self.logger.debug("Prepending FlowPTR Python lib path to DYLD_LIBRARY_PATH: %s", sg_python_lib_path)
                dyld_path = os.environ.get("DYLD_LIBRARY_PATH", "")
                required_env["DYLD_LIBRARY_PATH"] = sg_python_lib_path + os.pathsep + dyld_path
            else:
                self.logger.warning("Could not find FlowPTR Python lib path '%s' to set DYLD_LIBRARY_PATH. SSL errors may occur.", sg_python_lib_path)

        # If args are empty, pass an empty string. The app_launch hook will handle it.
        # An empty string is safer than a single dash or other placeholder.
        launch_args = args if args else ""

        if file_to_open:
            required_env["SGTK_FILE_TO_OPEN"] = file_to_open

        # The launch_path, args, and environment are passed to the app_launch hook.
        to_launch = {"/npath": launch_path, "/nargs": launch_args, "/nenv": required_env}
        self.logger.info("Launching executable:/n%s", to_launch)
        return LaunchInformation(launch_path, launch_args, required_env)

    def scan_software(self):
        """
        Scan the filesystem for Substance 3D Painter executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """

        self.logger.debug("Scanning for Substance 3D Painter executables...")

        # use the bundled icon
        icon_path = os.path.join(self.disk_location, "icon_256.png")
        self.logger.debug("Using icon path: %s" % (icon_path,))

        if sys.platform not in self.SUPPORTED_PLATFORMS:
            self.logger.debug("Substance 3D Painter not supported on this platform.")
            return []

        all_sw_versions = []

        # Since Substance 3D Painter uses static installation paths without version
        # numbers, we don't need the complex glob and regex matching. We can
        # simply iterate through our known templates and check if they exist.
        for match_template_set in self.EXECUTABLE_MATCH_TEMPLATES:
            executable_path = match_template_set.get(sys.platform)
            if not executable_path:
                continue

            if os.path.exists(executable_path):
                self.logger.debug("Found executable: %s", executable_path)
                all_sw_versions.append(
                    SoftwareVersion(
                        "Unknown", "Substance 3D Painter", executable_path, icon_path
                    )
                )

        return all_sw_versions

    def _is_supported(self, sw_version):
        """
        Overrides the base implementation to prevent it from corrupting the path on macOS.
        The actual version check is handled at launch time by the engine.

        :param sw_version: The :class:`SoftwareVersion` to check.
        :returns: A tuple of (bool, str) indicating if the version is supported and a reason.
        """
        return (True, "")

    def _find_free_port(self):
        """
        Finds and returns a free port on the local machine.
        This is a self-contained implementation to ensure compatibility with older
        versions of the tk-core API that may not have this utility.
        """
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    def _install_plugin(self):
        """
        Copies the Python plugin from the engine's bundle to the user's
        Substance 3D Painter plugin directory.

        For more on plugin installation paths, see:
        https://substance3d.adobe.com/documentation/pt/python-api/introduction-189549348.html#Pythonplugins-Loadingplugins
        """
        self.logger.info("Installing FlowPTR plugin...")

        """

        # Determine the user's Documents directory in a cross-platform, robust way.
        if sys.platform == "win32":
            try:
                # On Windows, query the registry to correctly find the Documents folder,
                # even if it has been relocated or is on a non-English system.
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
                documents_dir = winreg.QueryValueEx(key, "Personal")[0]
                winreg.CloseKey(key)
            except (ImportError, FileNotFoundError):
                # Fallback for older Python or unusual Windows setups.
                documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
        else:
            # On macOS and Linux, '~/Documents' is a reliable convention.
            documents_dir = os.path.join(os.path.expanduser("~"), "Documents")

        # Construct the path to the Substance 3D Painter plugins directory.
        plugin_dir = os.path.join(documents_dir, "Adobe", "Adobe Substance 3D Painter", "python", "plugins")

        # The source of our plugin is inside the engine bundle.
        plugin_src_dir = os.path.join(self.disk_location, "resources", "plugins", "FlowPTR_Plugin")

        # The destination for our plugin package will be a folder named 'FlowPTR_Plugin'
        # inside the Adobe Substance 3D Painter/python/plugins directory.
        plugin_dest_dir = os.path.join(plugin_dir, "FlowPTR_Plugin")

        self.logger.debug("Plugin source directory: %s", plugin_src_dir)
        self.logger.debug("Plugin destination directory: %s", plugin_dest_dir)

        # Ensure the parent plugins directory exists.
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)

        # If the destination plugin folder already exists, remove it to ensure a clean installation.
        if os.path.exists(plugin_dest_dir):
            self.logger.debug("Removing existing plugin folder: %s", plugin_dest_dir)
            shutil.rmtree(plugin_dest_dir)

        # Copy the entire plugin folder to create the package structure.
        # shutil.copytree will create the 'FlowPTR_Plugin' destination folder
        # and copy the contents of the source into it.
        shutil.copytree(plugin_src_dir, plugin_dest_dir)

        self.logger.info("FlowPTR Plugin installed and configured successfully.")
        """
