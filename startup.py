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
import sys
import shutil
import hashlib
import socket

##############

import sgtk
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation

# Since this file is loaded by the Toolkit bootstrap process, we can't directly
# import from the engine's python folder. We add it to the path temporarily.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
from tk_substancepainter import utils
sys.path.pop(0)

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"

logger = sgtk.LogManager.get_logger(__name__)

# We use this to indicate that we could not retrieve the version for the
# binary/executable, so we allow the engine to run with it
UNKNOWN_VERSION = "UNKNOWN_VERSION"

# note that this is the same in engine.py
MINIMUM_SUPPORTED_VERSION = "2018.3"

# adapted from:
# https://stackoverflow.com/questions/2270345/finding-the-version-of-an-application-from-python
if sys.platform == "win32":
    def get_file_info(filename, info):
        """
        Extracts a specific information string from a Windows executable's
        version info resource.

        :param str filename: The path to the executable.
        :param str info: The name of the info field to extract (e.g., "FileVersion").
        :return: The value of the info field, or an empty string if not found.
        """
        from ctypes import windll, create_unicode_buffer, c_uint, byref, cast, POINTER

        # Get the size of the version info block.
        size = windll.version.GetFileVersionInfoSizeW(filename, None)
        if not size:
            return ""

        # Create a buffer and load the version info into it.
        res = create_unicode_buffer(size)
        if not windll.version.GetFileVersionInfoW(filename, None, size, res):
            return ""

        # Find the language and codepage of the version info.
        r = c_uint()
        l = c_uint()
        if not windll.version.VerQueryValueW(res, u"\\VarFileInfo\\Translation", byref(r), byref(l)):
            return ""
        if not l.value:
            return ""

        # Codepages are returned as a pointer to an array of words.
        codepages = cast(r, POINTER(c_uint)).contents
        codepage = (codepages.value & 0xFFFF, codepages.value >> 16)

        # Construct the query string and extract the requested information.
        query = u"\\StringFileInfo\\%04x%04x\\%s" % (codepage[0], codepage[1], info)
        if not windll.version.VerQueryValueW(res, query, byref(r), byref(l)):
            return ""

        return cast(r, POINTER(c_uint * l.value)).contents.value


def md5(fname):
    """
    Calculates the MD5 checksum of a file.
    Used to reliably check if two files are identical.
    """
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def samefile(file1, file2):
    """Checks if two files are identical by comparing their MD5 hashes."""
    return md5(file1) == md5(file2)


# based on:
# https://stackoverflow.com/questions/38876945/copying-and-merging-directories-excluding-certain-extensions
def copytree_multi(src, dst, symlinks=False, ignore=None):
    """
    Recursively copies a directory tree, similar to shutil.copytree, but with
    a key difference: it overwrites files in the destination only if they are
    different from the source file (checked via MD5 hash).
    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.isdir(dst):
        os.makedirs(dst)

    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)

        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree_multi(srcname, dstname, symlinks, ignore)
            else:
                if os.path.exists(dstname):
                    if not samefile(srcname, dstname):
                        os.unlink(dstname)
                        shutil.copy2(srcname, dstname)
                        logger.info("File copied: %s" % dstname)
                    else:
                        # same file, so ignore the copy
                        logger.info("Same file, skipping: %s" % dstname)
                        pass
                else:
                    shutil.copy2(srcname, dstname)
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        except shutil.Error as err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except OSError:
        pass
    except OSError as why:
        errors.extend((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)

def ensure_scripts_up_to_date(engine_scripts_path, scripts_folder):
    """
    Ensures that the QML plugin scripts in the user's Substance 3D Painter
    plugins directory are up-to-date with the ones bundled in the engine.
    """
    logger.info("Updating scripts...: %s" % engine_scripts_path)
    logger.info("                     scripts_folder: %s" % scripts_folder)

    copytree_multi(engine_scripts_path, scripts_folder)

    return True

def get_free_port():
    """Finds and returns an available TCP port on the local machine."""
    # Ask the OS to allocate a port.
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def _get_python_executable(app_path):
    """
    Returns the path to the Python executable that ships with Substance 3D Painter.

    :param str app_path: The path to the main application.
    :return: The path to the python executable.
    """
    python_exe_path = None

    if sys.platform == "win32":
        # e.g. C:/Program Files/Adobe/Adobe Substance 3D Painter/python/python.exe
        python_exe_path = os.path.join(os.path.dirname(app_path), "python", "python.exe")
    elif sys.platform == "darwin":
        # e.g. /Applications/Adobe Substance 3D Painter/Adobe Substance 3D Painter.app/Contents/MacOS/python/bin/python3
        python_exe_path = os.path.join(app_path, "Contents", "MacOS", "python", "bin", "python3")
    elif sys.platform.startswith("linux"):
        # e.g. /opt/Adobe/Adobe_Substance_3D_Painter/python/bin/python3
        python_exe_path = os.path.join(os.path.dirname(app_path), "python", "bin", "python3")

    return python_exe_path

class SubstancePainterLauncher(SoftwareLauncher):
    """
    Handles launching SubstancePainter executables. Automatically starts up
    a tk-substancepainter engine with the current context in the new session
    of SubstancePainter.
    """

    # Named regex strings to insert into the executable template paths when
    # matching against supplied versions and products. Similar to the glob
    # strings, these allow us to alter the regex matching for any of the
    # variable components of the path in one place.

    # It seems that Substance 3D Painter does not use any version number in the
    # installation folders.
    COMPONENT_REGEX_LOOKUP = {}

    # This dictionary defines a list of executable template strings for each
    # of the supported operating systems. The templates are used for both
    # globbing and regex matches by replacing the named format placeholders.
    # with an appropriate glob or regex string.

    EXECUTABLE_TEMPLATES = {
        "darwin": ["/Applications/Adobe Substance 3D Painter/Adobe Substance 3D Painter.app", "/Applications/Allegorithmic/Substance Painter.app"],
        "win32": ["C:/Program Files/Adobe/Adobe Substance 3D Painter/Adobe Substance 3D Painter.exe", "C:/Program Files/Allegorithmic/Substance Painter/Substance Painter.exe"],
        "linux": [
            "/opt/Adobe/Adobe_Substance_3D_Painter/Adobe_Substance_3D_Painter",
            "/usr/Allegorithmic/Substance Painter",
            "/usr/Allegorithmic/Substance_Painter/Substance Painter",
            "/opt/Allegorithmic/Substance_Painter/Substance Painter",
        ],
    }

    @property
    def minimum_supported_version(self):
        """
        The minimum software version that is supported by the launcher.
        """
        return MINIMUM_SUPPORTED_VERSION

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch Substance 3D Painter in that will automatically
        load Toolkit and the tk-substancepainter engine when Substance 3D Painter starts.

        :param str exec_path: Path to Substance 3D Painter executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on
                                            launch.
        :returns: :class:`LaunchInformation` instance
        """
        required_env = {}

        resources_plugins_path = os.path.join(self.disk_location, "resources", "plugins")
        startup_path = os.path.join(self.disk_location, "startup", "bootstrap.py")

        # The classic bootstrap approach involves setting environment variables
        # that the QML plugin will use to launch the Python engine process.
        # Prepare the launch environment with variables required by the
        # classic bootstrap approach.
        self.logger.debug(
            "Preparing SubstancePainter Launch via Toolkit Classic methodology ..."
        )

        required_env["SGTK_SUBSTANCEPAINTER_ENGINE_STARTUP"] = startup_path.replace("\\", "/")

        # Use the Python executable that is bundled with Substance 3D Painter.
        # This ensures access to its PySide2 and native API without needing
        # an external framework.
        python_path = _get_python_executable(exec_path)
        self.logger.info("Using Substance 3D Painter's Python: %s" % python_path)
        required_env["SGTK_SUBSTANCEPAINTER_ENGINE_PYTHON"] = python_path.replace("\\", "/")

        required_env["SGTK_SUBSTANCEPAINTER_SGTK_MODULE_PATH"] = sgtk.get_sgtk_module_path()

        required_env["SGTK_SUBSTANCEPAINTER_ENGINE_PORT"] = str(get_free_port())

        # Pass the file to open to the engine via an environment variable.
        if file_to_open:
            required_env["SGTK_FILE_TO_OPEN"] = file_to_open

        # No special command-line arguments are needed for Substance 3D Painter.
        # All bootstrap information is passed via environment variables.
        args = ""

        required_env["SGTK_ENGINE"] = self.engine_name
        required_env["SGTK_CONTEXT"] = sgtk.context.serialize(self.context)

        # Ensure the QML plugin scripts are copied to the correct user directory.
        user_scripts_path = self._get_user_plugin_path()
        ensure_scripts_up_to_date(resources_plugins_path, user_scripts_path)

        return LaunchInformation(exec_path, args, required_env)

    def _get_icon(self, exec_path):
        """
        Find the icon for the application.

        :param str exec_path: Path to the executable.
        :returns: Full path to application icon as a string or None.
        """
        icon_path = None

        if sys.platform == "darwin":
            # The user-provided path for the icon on macOS.
            # The executable path is the .app bundle itself.
            icon_path = os.path.join(exec_path, "Contents", "Resources", "painter.icns")

        elif sys.platform == "win32":
            # On Windows, the icon is typically embedded in the executable.
            # We can just return the path to the executable and the OS will handle it.
            icon_path = exec_path

        elif sys.platform.startswith("linux"):
            # On Linux, the icon is often a PNG file in a resources or icons folder
            # near the executable.
            icon_path = os.path.join(os.path.dirname(exec_path), "resources", "icon.png")

        if icon_path and os.path.exists(icon_path):
            self.logger.debug("Found application icon at: %s", icon_path)
            return icon_path

        # the engine icon
        self.logger.debug("Using fallback engine icon.")
        engine_icon = os.path.join(self.disk_location, "icon_256.png")
        return engine_icon

    def _get_user_plugin_path(self):
        """
        Returns the platform-specific path to the user's Substance 3D Painter
        plugins directory. It checks for both modern (Adobe) and legacy
        (Allegorithmic) paths.

        :return: Path to the user plugins directory.
        """
        if sys.platform == "win32":
            import ctypes.wintypes

            CSIDL_PERSONAL = 5  # My Documents
            SHGFP_TYPE_CURRENT = 0  # Get current My Documents folder

            path_buffer = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(
                None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, path_buffer
            )
            documents_path = path_buffer.value
            
            # Check for new and old plugin paths
            adobe_path = os.path.join(documents_path, "Adobe", "Adobe Substance 3D Painter", "plugins")
            allegorithmic_path = os.path.join(documents_path, "Allegorithmic", "Substance Painter", "plugins")
            return adobe_path if os.path.exists(os.path.dirname(adobe_path)) else allegorithmic_path
        else: # macOS and Linux
            adobe_path = os.path.expanduser(r"~/Documents/Adobe/Adobe Substance 3D Painter/plugins")
            allegorithmic_path = os.path.expanduser(r"~/Documents/Allegorithmic/Substance Painter/plugins")
            return adobe_path if os.path.exists(os.path.dirname(adobe_path)) else allegorithmic_path

    def _is_supported(self, sw_version):
        """
        Inspects the supplied :class:`SoftwareVersion` object to see if it
        aligns with this launcher's known product and version limitations. Will
        check the :meth:`~minimum_supported_version` as well as the list of
        product and version filters.
        :param sw_version: :class:`SoftwareVersion` object to test against the
            launcher's product and version limitations.
        :returns: A tuple of the form: ``(bool, str)`` where the first item
            is a boolean indicating whether the supplied :class:`SoftwareVersion` is
            supported or not. The second argument is ``""`` if supported, but if
            not supported will be a string representing the reason the support
            check failed.
        This helper method can be used by subclasses in the :meth:`scan_software`
        method.

        To check if the version is supported:
        
        First we make an exception for cases were we cannot retrieve the 
        version number, we accept the software as valid.

        Second, checks against the minimum supported version. If the
        supplied version is greater it then checks to ensure that it is in the
        launcher's ``versions`` constraint. If there are no constraints on the
        versions, we will accept the software version.

        :param str version: A string representing the version to check against.
        :return: Boolean indicating if the supplied version string is supported.
        """

        # we support cases were we could not extract the version number
        # from the binary/executable
        if sw_version.version == UNKNOWN_VERSION:
            return (True, "")

        # normalize the version string for comparison
        version = utils.to_normalized_version(sw_version.version)

        # second, compare against the minimum version
        if self.minimum_supported_version:
            min_version = utils.to_normalized_version(self.minimum_supported_version)

            if version < min_version:
                # the version is older than the minimum supported version
                return (
                    False,
                    "Executable '%s' didn't meet the version requirements, "
                    "%s is older than the minimum supported %s"
                    % (sw_version.path, sw_version.version, self.minimum_supported_version),
                )

        # third if the version is new enough, we check if we have any
        # version restrictions
        if not self.versions:
            # No version restriction. All versions supported
            return (True, "")

        # if so, check versions list
        supported = sw_version.version in self.versions
        if not supported:
            return (
                False,
                "Executable '%s' didn't meet the version requirements"
                "(%s not in %s)" % (sw_version.path, sw_version.version, self.versions),
            )

        # passed all checks. must be supported!
        return (True, "")

    def scan_software(self):
        """
        Scan the filesystem for Substance 3D Painter executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """
        self.logger.debug("Scanning for Substance 3D Painter executables...")

        supported_sw_versions = []
        for sw_version in self._find_software():
            (supported, reason) = self._is_supported(sw_version)

            if supported:
                supported_sw_versions.append(sw_version)
            else:
                self.logger.debug(
                    "SoftwareVersion %s is not supported: %s" % (sw_version, reason)
                )

        return supported_sw_versions

    def _get_mac_version(self, bundle_path):
        """
        Get the version number from the app bundle's Info.plist file.

        :param str bundle_path: Path to the .app bundle.
        :return: The version string or UNKNOWN_VERSION.
        """
        try:
            # The plistlib module is standard in Python 3.
            import plistlib

            plist_path = os.path.join(bundle_path, "Contents", "Info.plist")
            with open(plist_path, "rb") as fp:
                plist_data = plistlib.load(fp)
            return plist_data.get("CFBundleShortVersionString", UNKNOWN_VERSION)
        except Exception as e:
            self.logger.warning("Could not read version from %s: %s", plist_path, e)
            return UNKNOWN_VERSION

    def _find_software(self):
        """
        Find executables in the default install locations.
        """

        # all the executable templates for the current OS
        platform = "linux" if sys.platform.startswith("linux") else sys.platform
        executable_templates = self.EXECUTABLE_TEMPLATES.get(platform, [])

        # all the discovered executables
        sw_versions = []

        for executable_template in executable_templates:

            self.logger.debug("Processing template %s.", executable_template)

            executable_matches = self._glob_and_match(
                executable_template, self.COMPONENT_REGEX_LOOKUP
            )

            # Extract all products from that executable.
            for (executable_path, key_dict) in executable_matches:

                # extract the matched keys form the key_dict (default to None
                # if not included)
                if sys.platform == "win32":
                    executable_version = get_file_info(executable_path, "FileVersion")
                    # make sure we remove those pesky \x00 characters
                    executable_version = executable_version.strip("\x00")
                elif sys.platform == "darwin":
                    executable_version = self._get_mac_version(executable_path)
                else:
                    executable_version = key_dict.get("version", UNKNOWN_VERSION)

                self.logger.debug(
                    "Software found: %s | %s.", executable_version, executable_template
                )
                sw_versions.append(
                    SoftwareVersion(
                        executable_version,
                        "Adobe Substance 3D Painter",
                        executable_path,
                        self._get_icon(executable_path),
                    )
                )

        return sw_versions
