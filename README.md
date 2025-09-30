# Autodesk Flow Production Tracking (FlowPTR) formerly known as ShotGrid/Shotgun, toolkit engine for Adobe Substance 3D Painter

[Key features of Flow Production Tracking (Formerly ShotGrid)](https://www.autodesk.com/products/flow-production-tracking/features)

![tk-substancepainter_04](https://raw.githubusercontent.com/StephenAnimates/tk-substancepainter/master/config/images/tk-substancepainter_04.PNG)

## Overview

This is an mplementation of a Flow Production Tracking (ShotGrid/Shotgun) engine for [**Adobe Substance 3D Painter**](https://www.adobe.com/products/substance3d.html). It supports the bootstrap startup methods and integrates with **Adobe Substance 3D Painter** adding a **Flow Production Tracking** menu in the plugin toolbar. 

* [Engine Installation](#engine-installation)
* [Configuring your project for Flow Production Tracking (ShotGrid/Shotgun) Toolkit](#configuring-your-project-for-shotgun-toolkit)
* [Modifying the toolkit configuration files to add this engine and related apps](#modifying-the-toolkit-configuration-files-to-add-this-engine-and-related-apps)
* [Modifying the Templates](#modifying-the-templates)
* [Configuring Adobe Substance 3D Painter in the software launcher](#configuring-substancepainter-in-the-software-launcher)
* [Caching and downloading the engine into disk](#caching-and-downloading-the-engine-into-disk)

With the engine, hooks for most of the standard tk application are provided:

* [tk-multi-workfiles2](#tk-multi-workfiles2)
* [tk-multi-snapshot](#tk-multi-snapshot)
* [tk-multi-loader2](#tk-multi-loader2)
* [tk-multi-publish2](#tk-multi-publish2)
* [tk-multi-breakdown](#tk-multi-breakdown)

**Note for developers:** The communication between the Python-based engine and **Adobe Substance 3D Painter** is handled via QtWebsockets. The engine leverages the native Python environment and PySide2 library bundled with Substance 3D Painter, removing the need for external Qt frameworks.

**This engine has been developed and tested on Windows and macOS and should be compatible with modern versions of Adobe Substance 3D Painter on all supported platforms (Windows, macOS, and Linux).**

## Engine Installation

This guide provides instructions for setting up this engine with a modern, `tk-config-basic` based Toolkit configuration. The structure of these configurations is more modular and easier to manage than older versions like `tk-config-default2`.

### 1. Download the Engine Code

The first step is to tell your Toolkit project where to find the engine code. In your pipeline configuration, open the `config/core/engine_locations.yml` file and add a block that points to this GitHub repository.

**Make sure to check for the latest version of the engine** here and use the version number in the version section below:
tk-substancepainter releases

```
# config/core/engine_locations.yml

# Adobe Substance 3D Painter
engines.tk-substancepainter.location:
  type: git
  path: https://github.com/StephenAnimates/tk-substancepainter
  version: v2.0.2
```

Or in your environments you should add tk-substancepainter yml file, for example in the asset_step yml file:
``env/asset_step.yml``

Add the include at the beginning of the file, in the 'includes' section:
```
includes/settings/tk-substancepainter.yml
```

Add to project.yml, includes:
```
- ./includes/settings/tk-substancepainter.yml
```
Then to engines:
```
  tk-substancepainter: "@settings.tk-substancepainter.project"
```

``~/Library/Caches/Shotgun/bundle_cache/app_store/tk-config-basic/v1.7.5/env/project.yml``

Now we add a new entry under the engines section, that will include all the information for our Adobe Substance 3D Painter application:
```
yaml
tk-substancepainter: "@settings.tk-substancepainter.asset_step"
```

Finally, do not forget to copy the additional `tk-substancepainter.yml` into your settings folder.

## Modifying the Templates

The additions to `config/core/templates.yml` are provided also under the config directory of this repository, specifically `templates.yml`
This repository's `config` folder contains a self-contained settings file (`config/env/includes/settings/tk-substancepainter.yml`) designed for a modern `tk-config-basic` setup. Follow the steps in the Engine Installation section to integrate it into your project.

## Configuring Adobe Substance 3D Painter in the software launcher

In order for our application to show up in the FlowPTR launcher, we need to add it to our list of software that is valid for this project.

1. Open the FlowPTR site, for example `example.shotgrid.autodesk.com`, after logging in, clink in the **FlowPTR Settings** menu, the arrow at the top right of the page (your user picture). 
2. Click the **Software** option
!select_a_project_configuration
3. Create a new entry for the software, called "Adobe Substance 3D Painter".
!create_new_software
4. Specify the engine this software will use: "tk-substancepainter"
!software_specify_engine

* Note: Restrict the software to certain projects by entering the project in the projects column. If no projects are specified this application will show up for all the projects that have this engine in their configuration files.

If you want more information on how to configure software launches, here is the detailed documentation from FlowPTR.
[Configuring software launches](https://support.shotgunsoftware.com/hc/en-us/articles/115000067493#Configuring%20the%20software%20in%20Shotgun%20Desktop)


## Caching and downloading the engine into disk

One last step is to cache the engine and apps from the configuration files into disk. FlowPTR provides a tank command for this. 
[Tank Advanced Commands](https://help.autodesk.com/view/SGDEV/ENU/?guid=SGD_pg_integrations_admin_guides_advanced_toolkit_administration_html#advanced-tank-commands)

1. Open a **Command** window or **Terminal** and navigate to your pipeline configuration folder, where you will find a `tank` or `tank.bat` file.
(in our case we placed the pipeline configuration under `D:\demo\configs\game_config`)
2. Type `tank cache_apps` , and press the **Enter/Return** key.

FlowPTR Toolkit will start revising the changes we have done to the configuration yml files and downloading what is requires.

![tank_cache_apps](config/images/tank_cache_apps.png)

3. Click on the user icon (bottom right) to show the menu (you can also right click in the main window).
3. Click on **Advanced project setup**

    ![advanced_project_setup](config/images/advanced_project_setup.png)

**Warning:** if you recieve an error message
    [error_project_setup](config/images/error_project_setup.png)

"You are trying to set up a project which has already been set up":

Update the engine

1. Go back to the **Command** or **Terminal** window
2. Navigate to the tank command in the project
```cd ~/Library/Caches/Shotgun/<site>/p<project id>.basic.desktop/cfg/```
```
tank updates [environment_name] [engine_name] [app_name] [--use-legacy-yaml] [--external='/path/to/config']
```
Example:
```
~/Library/Caches/Shotgun/<site>/site.basic.desktop/cfg/
~/Library/Caches/Shotgun/djcad/site.basic.desktop/cfg/tank install_app tk-substancepainter https://github.com/StephenAnimates/tk-substancepainter.git

```

Alternatively, you can update the entire site.
```tank updates```

## Adobe Substance 3D Painter engine should be ready to use

If we now go back and forth from our project in shotgun desktop ( < arrow top left if you are already within a project ), we should be able to see Adobe Substance 3D Painter as an application to launch.

## [tk-multi-workfiles2](https://support.shotgunsoftware.com/hc/en-us/articles/219033088)
This application forms the basis for file management in the Shotgun Pipeline Toolkit. It lets you jump around quickly between your various Shotgun entities and gets you started working quickly. No path needs to be specified as the application manages that behind the scenes. The application helps you manage your working files inside a Work Area and makes it easy to share your work with others.

Basic hooks have been implemented for this tk-app to work. open, save, save_as, reset, and current_path are the scene operations implemented.

The "New File" action has been fully implemented. When a user clicks "New File", they will be prompted to select a mesh, and a new Substance 3D Painter project will be created automatically in the correct context.

## [tk-multi-snapshot](https://support.shotgunsoftware.com/hc/en-us/articles/219033068)
A Shotgun Snapshot is a quick incremental backup that lets you version and manage increments of your work without sharing it with anyone else. Take a Snapshot, add a description and a thumbnail, and you create a point in time to which you can always go back to at a later point and restore. This is useful if you are making big changes and want to make sure you have a backup of previous versions of your scene.

Hooks are provided to be able to use this tk-app, similar to workfiles2.

## [tk-multi-loader2](https://support.shotgunsoftware.com/hc/en-us/articles/219033078)
![tk-substancepainter_01](https://raw.githubusercontent.com/StephenAnimates/tk-substancepainter/master/config/images/tk-substancepainter_01.PNG)

The Shotgun Loader lets you quickly overview and browse the files that you have published to Shotgun. A searchable tree view navigation system makes it easy to quickly get to the task, shot or asset that you are looking for and once there the loader shows a thumbnail based overview of all the publishes for that item. Through configurable hooks you can then easily reference or import a publish into your current scene.

Hook provided support the updating of the following type of files and their related valid usages as resources within Adobe Substance 3D Painter:
- Image: (environment, colorlut, alpha, texture)
- Texture: (environment, colorlut, alpha, texture)
- Rendered Image: (environment, colorlut, alpha, texture)
- Substance Material Preset: (preset)
- Sppr File: (preset)
- PopcornFX: (script)
- Pkfx File: (script)
- Shader: (shader)
- Glsl File: (shader)
- Substance Export Preset: (export)
- Spexp File: (export)
- Substance Smart Material: (smartmaterial)
- Spsm File: (smartmaterial)
- Substance File: (basematerial, alpha, texture, filter, procedural, generator)
- Sbsar File: (basematerial, alpha, texture, filter, procedural, generator)
- Substance Smart Mask: (smartmask)
- Spmsk File: (smartmask)

Note that the Loader always loas the textures within the Project shelf resources folder.

## [tk-multi-publish2](https://support.shotgunsoftware.com/hc/en-us/articles/115000097513)
![tk-substancepainter_03](https://raw.githubusercontent.com/StephenAnimates/tk-substancepainter/master/config/images/tk-substancepainter_03.PNG)

The Publish app allows artists to publish their work so that it can be used by artists downstream. It supports traditional publishing workflows within the artist’s content creation software as well as stand-alone publishing of any file on disk. When working in content creation software and using the basic Shotgun integration, the app will automatically discover and display items for the artist to publish. For more sophisticated production needs, studios can write custom publish plugins to drive artist workflows.

The basic publishing of the current session is provided with this app. In addition to this, two different modes for the exported textures are provided:

In your `config/env/includes/substancepainter/settings.yml` file, under the `tk-multi-publish2` settings, you will find a `collector_settings` section. The `Publish Textures as Folder` setting allows you to choose between publishing textures as a single folder ("Texture Folder" publish type) or as individual files ("Texture" publish type).

```yaml
# config/env/includes/substancepainter/settings.yml

#...
settings.tk-substancepainter.asset_step:
  apps:
    tk-multi-publish2:
      #...
      collector_settings:
          Publish Textures as Folder: true
```


## [tk-multi-breakdown](https://support.shotgunsoftware.com/hc/en-us/articles/219032988)
![tk-substancepainter_02](config/images/tk-substancepainter_02.PNG)

The Scene Breakdown App shows you a list of items you have loaded (referenced) in your scene and tells you which ones are out of date. From this overview, you can select multiple objects and click the update button which will update all your selected items to use the latest published version.

Note that this tool will only update the resources that have been loaded previously trough the Loader toolkit app.

It also displays what textures loaded from the Loader app are in used within the scene and which ones are not. The tidying up of the shelf resources is left for the user.

Credits:
Originally Developed by: [Diego Garcia Huerta](https://www.linkedin.com/in/diegogh/)