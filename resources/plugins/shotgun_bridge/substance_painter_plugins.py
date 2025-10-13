import importlib 
import substance_painter_plugins 
 
# Get the list of available Plugin names: 
all_plugins_names = substance_painter_plugins.plugin_module_names() 
for name in all_plugins_names: 
    print(name) 
 
# Load the "hello world" Plugin: 
plugin = importlib.import_module("hello_plugin") 
 
# Start the Plugin if it wasn't already: 
if not substance_painter_plugins.is_plugin_started(plugin): 
    substance_painter_plugins.start_plugin(plugin) 