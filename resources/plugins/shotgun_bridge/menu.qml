// Substance Painter menu in the toolbar.
// We track is the engine has been loaded and enable/diable the Shotgun icon
// accordingly.

// Original code by: Diego Garcia Huerta
// Updated by: Stephen Studyvin

// Updated:
// September 2025, to support current Adobe Substance 3D Painter version.

import AlgWidgets.Style 1.0
import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

Button {
  // This is the main button control that will be added to the toolbar.
  id: control
  antialiasing: true
  height: 32
  width: 32
  tooltip: "Open Flow Production Tracking Menu"

  // Custom properties for this button.
  // 'clickedPosition' stores the global screen coordinates of a click.
  property var clickedPosition: null
  // 'isEngineLoaded' is a flag that tracks the status of the Python engine.
  property bool isEngineLoaded: false

  // The button is only enabled when the Python engine has finished loading.
  enabled: control.isEngineLoaded

  // Custom styling for the button's appearance.
  style: ButtonStyle {
    background: Rectangle {
        // The background is transparent by default and turns dark grey on hover.
        color: control.hovered ?
          "#262626" :
          "transparent"
    }
  }

  // The main icon for the button.
  Image {
    id: controlImage
    anchors.fill: parent
    antialiasing: true
    anchors.margins: 8
    fillMode:Image.PreserveAspectFit
    source: control.hovered ? "icons/sg_hover.png" : "icons/sg_idle.png"
    mipmap: true
    // The icon is faded out when the button is disabled.
    opacity: control.enabled ?
      1.0:
      0.3
    sourceSize.width: control.width
    sourceSize.height: control.height
  }

  // This handler is executed when the button is clicked.
  onClicked: (mouse) => {
    if (control.isEngineLoaded)
    {
      // If the engine is ready, calculate the global position of the click
      // and store it. This is used by the Python engine to show the menu
      // at the correct location.
      // mapToGlobal requires a QQuickItem, so we pass the button itself.
      control.clickedPosition = control.mapToGlobal(mouse.x, mouse.y);
      // The 'clicked' signal is implicitly emitted by the Button control.
    }
    else{
      // If the engine is still loading, log a warning to the console.
      alg.log.warn("FlowPTR Engine is being loaded. Please wait...");
    }
  }

  // This rectangle acts as a status indicator for the "loading" state.
  Rectangle {
    id: statusIndicator
    height: 5
    width: height
    x: 2
    y: 2
    radius: width

    visible: !control.isEngineLoaded
    color: "#FFC700" // Yellow for "loading"

    // Add a pulsing animation while the engine is loading to give feedback.
    SequentialAnimation on opacity {
        running: !control.isEngineLoaded
        loops: Animation.Infinite
        NumberAnimation { to: 0.5; duration: 750; easing.type: Easing.InOutQuad }
        NumberAnimation { to: 1.0; duration: 750; easing.type: Easing.InOutQuad }
    }
  }

  // This rectangle acts as a status indicator for the "loaded" state.
  Rectangle {
      height: 5; width: height; x: 2; y: 2
      radius: width
      visible: control.isEngineLoaded
      color: "#00A859" // Green for "loaded"
  }
}
