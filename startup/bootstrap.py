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

"""
This file is loaded automatically by the QML plugin inside Adobe Substance 3D Painter.
It sets up the Toolkit context and prepares the tk-substancepainter engine.
"""

import os
import sys
import traceback

__author__ = "Diego Garcia Huerta"
__email__ = "diegogh2000@gmail.com"

def display_error(logger, msg):
    """Helper to log and print an error message."""
    logger.error("FlowPTR Error | Substance 3D Painter engine | %s " % msg)
    print("FlowPTR Error | Substance 3D Painter engine | %s " % msg)

def display_warning(logger, msg):
    """Helper to log and print a warning message."""
    logger.warning("FlowPTR Warning | Substance 3D Painter engine | %s " % msg)
    print("FlowPTR Warning | Substance 3D Painter engine | %s " % msg)

def display_info(logger, msg):
    """Helper to log and print an info message."""
    logger.info("FlowPTR Info | Substance 3D Painter engine | %s " % msg)
    print("FlowPTR Info | Substance 3D Painter engine | %s " % msg)

def start_toolkit_classic():
    """
    Parses environment variables for an engine name and a serialized Context
    to use for starting up the Toolkit engine.

    This is the "classic" Toolkit bootstrap method, where the host application
    launcher sets environment variables that a startup script (like this one)
    then uses to initialize the engine.
    """
    import sgtk

    logger = sgtk.LogManager.get_logger(__name__)

    logger.debug("Attempting to launch Toolkit in classic mode...")

    # Get the name of the engine to start from the environment.
    # This should be 'tk-substancepainter'.
    env_engine = os.environ.get("SGTK_ENGINE")
    if not env_engine:
        msg = "FlowPTR: Missing required environment variable SGTK_ENGINE."
        display_error(logger, msg)
        return

    # Get the context load from the environment.
    env_context = os.environ.get("SGTK_CONTEXT")
    if not env_context:
        msg = "FlowPTR: Missing required environment variable SGTK_CONTEXT."
        display_error(logger, msg)
        return
    try:
        # The context is passed as a serialized string; deserialize it back into a Context object.
        context = sgtk.context.deserialize(env_context)
    except Exception as e:
        msg = (
            "FlowPTR: Could not create context! Flow Production Tracking Toolkit"
            " will be disabled. Details: %s" % e
        )
        etype, value, tb = sys.exc_info()
        msg += "".join(traceback.format_exception(etype, value, tb))
        display_error(logger, msg)
        return

    try:
        # Start up the Toolkit engine from the environment data.
        # This will find, load, and initialize the tk-substancepainter engine code.
        logger.debug(
            "Launching engine instance '%s' for context %s" % (env_engine, env_context)
        )
        engine = sgtk.platform.start_engine(env_engine, context.sgtk, context)
        logger.debug("Current engine '%s'" % sgtk.platform.current_engine())

    except Exception as e:
        msg = "FlowPTR: Could not start engine. Details: %s" % e
        etype, value, tb = sys.exc_info()
        msg += "".join(traceback.format_exception(etype, value, tb))
        display_error(logger, msg)
        return

def start_toolkit():
    """
    Main bootstrap function. It imports Toolkit, starts the logging,
    and initiates the engine startup process.
    """

    # Verify sgtk can be loaded.
    try:
        import sgtk
    except Exception as e:
        msg = "FlowPTR: Could not import sgtk! Disabling for now: %s" % e
        print(msg)
        return

    # Start up toolkit logging to file.
    sgtk.LogManager().initialize_base_file_handler("tk-substancepainter")

    # Rely on the classic boostrapping method
    start_toolkit_classic()

    # Check if a file was specified to open and open it.
    file_to_open = os.environ.get("SGTK_FILE_TO_OPEN")
    if file_to_open:
        engine = sgtk.platform.current_engine()
        if engine and hasattr(engine.app, "open_project"):
            msg = "FlowPTR: Opening '%s'..." % file_to_open
            display_info(engine.logger, msg)
            engine.app.open_project(file_to_open)
        else:
            msg = "FlowPTR: Engine not available or does not support opening files. Cannot open '%s'." % file_to_open
            # Use a temporary logger since the engine might not exist.
            display_error(sgtk.LogManager.get_logger(__name__), msg)

    # Clean up temporary environment variables set by the launcher.
    del_vars = [
        "SGTK_ENGINE",
        "SGTK_CONTEXT",
        "SGTK_FILE_TO_OPEN",
    ]
    for var in del_vars:
        if var in os.environ:
            del os.environ[var]

def setup_environment():
    """
    Ensures that the path to the Toolkit Core API (`sgtk`) is added to the
    Python path, so that it can be imported by this script.
    """
    SGTK_SUBSTANCEPAINTER_SGTK_MODULE_PATH = os.environ[
        "SGTK_SUBSTANCEPAINTER_SGTK_MODULE_PATH"
    ]

    if (
        SGTK_SUBSTANCEPAINTER_SGTK_MODULE_PATH
        and SGTK_SUBSTANCEPAINTER_SGTK_MODULE_PATH not in sys.path
    ):
        sys.path.insert(0, SGTK_SUBSTANCEPAINTER_SGTK_MODULE_PATH)

if __name__ == "__main__":
    # Set up the environment and fire up Toolkit.
    setup_environment()
    start_toolkit()
