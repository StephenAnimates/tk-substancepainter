# This is the main entry point for the pure Python FlowPTR plugin.
# It is responsible for bootstrapping and starting the Toolkit engine.

# For more on creating Python plugins for Substance 3D Painter, see:
# https://substance3d.adobe.com/documentation/pt/python-api/api/substance_painter/

import os
import sys
import time
import traceback

# Substance 3D Painter modules
import substance_painter
import sgtk

# import the QT module from sgtk to build custom UI
from PySide6 import QtCore, QtGui, QtWidgets

# GLOBAL REFERENCES for the menu and its actions. (Must be defined globally/in class scope)
FLOWPTR_TOP_LEVEL_ACTION = None
_ENGINE_INSTANCE = None
_PLUGIN_INSTANCE = None

plugin_widgets = []

# ------------------------------------------------------------------
# SUBSTANCE PAINTER ENTRY POINTS (The Proxy Functions)
# ------------------------------------------------------------------

def start_plugin():
    """
    Substance Painter calls this function. It instantiates the Toolkit class.

    This function handles the core bootstrapping of the Toolkit engine within
    Substance 3D Painter.

    For more on starting Toolkit engines, see:
    https://help.autodesk.com/view/SGDEV/ENU/?guid=SG_Pipeline_Toolkit_Core_API_tk_core_platform_html#sgtk.platform.start_engine
    """
    global _ENGINE_INSTANCE

    # If the SGTK_ENGINE environment variable is not set, it means that
    # Substance Painter was not launched from the Flow Desktop launcher.
    # In this case, we should not proceed with initializing the engine.
    if "SGTK_ENGINE" not in os.environ:
        substance_painter.logging.log(substance_painter.logging.DBG_INFO, "FlowPTR", "Not a Toolkit launch. The Flow Production Tracking plugin will not be loaded.")
        return

    _setup_sgtk_environment()
    substance_painter.logging.log(substance_painter.logging.INFO, "FlowPTR", "Starting Flow Production Tracking integration...")

    try:
        if sgtk.platform.current_engine():
            _ENGINE_INSTANCE = sgtk.platform.current_engine()
            substance_painter.logging.log(
                    substance_painter.logging.INFO,
                    "FlowPTR",
                    "An engine is already running. Re-using the existing instance."
                )
        else:
            # Manually start the engine using the context passed by the launcher.
            # This is the correct and most robust method for this integration.
            engine_name = os.environ.get("SGTK_ENGINE")
            context_str = os.environ.get("SGTK_CONTEXT")

            context = sgtk.context.deserialize(context_str)
            # Start the engine with the deserialized context.
            _ENGINE_INSTANCE = sgtk.platform.start_engine(engine_name, context.sgtk, context)

            try:
                

                substance_painter.logging.log(
                    substance_painter.logging.INFO,
                    "FlowPTR",
                    f"Starting engine '{engine_name}' with context: {context}"
                )
            except Exception as e:
                raise Exception(f"Failed to deserialize context or start engine: {e}")

        if not _ENGINE_INSTANCE:
            raise Exception("Failed to bootstrap the Toolkit engine.")

        substance_painter.logging.log(
            substance_painter.logging.INFO,
            "FlowPTR",
            f"Engine '{_ENGINE_INSTANCE.name}' started successfully."
        )

    except Exception as e:
        etype, value, tb = sys.exc_info()
        error_msg = f"Failed to initialize the Flow Production Tracking integration: {e}\n"
        error_msg += "".join(traceback.format_exception(etype, value, tb))
        substance_painter.logging.log(substance_painter.logging.ERROR, "FlowPTR", error_msg)

def close_plugin():
    """
    Substance Painter calls this function to shut down.
    """
    global _ENGINE_INSTANCE, FLOWPTR_TOP_LEVEL_ACTION

    substance_painter.logging.log(substance_painter.logging.INFO, "FlowPTR", "Closing plugin and cleaning up UI...")

    """

    # First, destroy the engine. This will trigger the shutdown of all apps
    # and UI elements in the correct order.
    if _ENGINE_INSTANCE:
        _ENGINE_INSTANCE.destroy()
        _ENGINE_INSTANCE = None
        substance_painter.logging.log(substance_painter.logging.INFO, "FlowPTR", "Toolkit engine destroyed.")

    # After the engine is destroyed, clean up the main menu action.
    if FLOWPTR_TOP_LEVEL_ACTION:
        substance_painter.ui.delete_ui_element(FLOWPTR_TOP_LEVEL_ACTION)
        FLOWPTR_TOP_LEVEL_ACTION = None
        substance_painter.logging.log(substance_painter.logging.INFO, "FlowPTR", "Main menu action removed.")

    """

# --- Helper function to set up the Toolkit environment ---
def _setup_sgtk_environment():
    """
    Adds the Toolkit core API to the Python path so it can be imported.
    This relies on the SGTK_PYTHONPATH environment variable set by the launcher.
    """
    sgtk_pythonpath = os.environ.get("SGTK_PYTHONPATH")
    if sgtk_pythonpath:
        for path in sgtk_pythonpath.split(os.pathsep):
            if path and path not in sys.path:
                sys.path.insert(0, path)
