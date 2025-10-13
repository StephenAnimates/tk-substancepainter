** Configuration for custom "Scene Actions" in the tk-substancepainter engine**


This will add a cutom configuration to handle panels in the asset step and project configurations. So rather than looking for the standard config the tk-multi-shotgunpanel settings will be in the **tk-multi-shotgunpanel/basic/scene_actions.py** file

1. Update the configuration in substancepainter asset_step.yml

In the project, this will be in the tk-substancepainter/config/env/includes/substancepainter/ folder
Change the line for the location the tk-multi-shotgunpanel from:
```yaml
tk-multi-shotgunpanel: '@common.apps.tk-multi-shotgunpanel.location'
```
And change it to:
```yaml
tk-multi-shotgunpanel: '@substancepainter.apps.tk-multi-shotgunpanel.location'
```
This redirects the asset_step configuration to look for the substancepainter location in the apps.yml file, rather than the default (standard) settings location.

2. Update the configuration in project.yml

In the same location, there is a project.yml file.
Change the line for the location the tk-multi-shotgunpanel from:
```yaml
tk-multi-shotgunpanel: '@common.apps.tk-multi-shotgunpanel'
```
And change it to:
```yaml
tk-multi-shotgunpanel: '@substancepainter.apps.tk-multi-shotgunpanel'
```
Similarly to the asset_step configuration, this redirects the project configuration to look for the substancepainter location in the apps.yml file, rather than the default (standard) settings location.

2. Update the configuration in apps.yml
As before, in the same location, there is a apps.yml file.
Add a line for the hook to the scene_actions.py file in the "tk-multi-shotgunpanel/basic" folder. This will allow both the "asset_step.yml" and the "project.yml" files to look in the substancepainter location first, which will set up the hook operations file, then pass the location to the "common.apps.tk-multi-breakdown2.location"
```yaml
substancepainter.apps.tk-multi-shotgunpanel:
    actions_hook: "{engine}/tk-multi-shotgunpanel/basic/scene_actions.py"
    location: '@common.apps.tk-multi-breakdown2.location'