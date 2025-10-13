import os

# Substance 3D Painter modules
import substance_painter.ui
import substance_painter.export
import substance_painter.project
import substance_painter.textureset

# PySide module to build custom UI
from PySide6 import QtWidgets, QtGui

plugin_widgets = []

print("Custom Export plugin is starting...")

def export_textures():
    # Verify if a project is open before trying to export something
    if not substance_painter.project.is_open():
        return

    # Get the currently active layer stack (paintable)
    stack = substance_painter.textureset.get_active_stack()

    # Get the parent Texture Set of this layer stack
    material = stack.material()

    # Build Export Preset resource URL
    # - Context: name of the library where the resource is located
    # - Name: name of the resource (filename without extension or Substance graph path)
    export_preset = substance_painter.resource.ResourceID(
        context="starter_assets",
        name="PBR Metallic Roughness")

    print("Preset:")
    print(export_preset.url())

    # Setup the export settings
    resolution = material.get_resolution()

    # Setup the export path, in this case the textures
    # will be put next to the spp project file on the disk
    project_filepath = substance_painter.project.file_path()
    export_path = os.path.dirname(project_filepath)

    # Build the configuration
    config = {
        "exportShaderParams": False,
        "exportPath": export_path,
        "exportList": [{"rootPath": str(stack)}],
        "exportPresets": [{"name": "default", "maps": []}],
        "defaultExportPreset": export_preset.url(),
        "exportParameters": [
            {
                "parameters": {"paddingAlgorithm": "infinite"}
            }
        ]
    }

    try:
        # Run the export process.
        substance_painter.export.export_project_textures(config)

        # Show a success message to the user.
        QtWidgets.QMessageBox.information(
            substance_painter.ui.get_main_window(),
            "Export Complete",
            f"Textures exported successfully to:\n{export_path}"
        )
    except Exception as e:
        # If an error occurs, show it to the user in a message box.
        substance_painter.ui.show_error_message(f"Texture export failed: {e}")

def start_plugin():
    # Create a text widget for a menu
    Action = QtGui.QAction("Custom Export", triggered=export_textures)

    # Add this widget to the existing File menu of the application
    substance_painter.ui.add_action(substance_painter.ui.ApplicationMenu.File,Action)

    # Store the widget for proper cleanup later when stopping the plugin
    plugin_widgets.append(Action)

def close_plugin():
    # Remove all widgets that have been added to the UI
    for widget in plugin_widgets:
        substance_painter.ui.delete_ui_element(widget)

    plugin_widgets.clear()

if __name__ == "__main__":
    start_plugin()