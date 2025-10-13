# This was an experiment on how to create a menu in Substance Painter
# just keeping for future reference


import substance_painter

for action in substance_painter.ui.get_main_window().menuBar().actions():
    
    # Each 'action' is a PySide6.QtGui.QAction instance
    action_text = action.text()
    
    # Check if the action is a menu (has a QMenu attached)
    is_menu = action.menu() is not None

    print(f"Action Text: '{action_text}'")
    
    # --- Example: Search for your specific menu item ---
    if action_text == "&Flow Production Tracking":
        print("    --> Found the Flow Production Tracking Menu!")
        # You can now manipulate it (e.g., disable it)
        action.deleteLater()
