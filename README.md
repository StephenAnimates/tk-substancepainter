# Autodesk Flow Production Tracking (FlowPTR) formerly known as ShotGrid/Shotgun, toolkit engine for Adobe Substance 3D Painter

[Key features of Flow Production Tracking (Formerly ShotGrid)](https://www.autodesk.com/products/flow-production-tracking/features)

![tk-substancepainter_04](https://raw.githubusercontent.com/StephenAnimates/tk-substancepainter/master/config/images/tk-substancepainter_04.PNG)

## Overview

This is an mplementation of a Flow Production Tracking (ShotGrid/Shotgun) engine for [**Adobe Substance 3D Painter**](https://www.adobe.com/products/substance3d.html). It supports the bootstrap startup methods and integrates with Adobe Substance 3D Painter adding a **Flow Production Tracking** menu in the plugin toolbar. 

**Note for developers:** The communication between the Python-based engine and Adobe Substance 3D Painter is handled via QtWebsockets. The engine leverages the native Python environment and PySide2 library bundled with Substance 3D Painter, removing the need for external Qt frameworks.

**This engine has been developed and tested on Windows and macOS and should be compatible with modern versions of Adobe Substance 3D Painter on all supported platforms (Windows, macOS, and Linux).**

## Engine Installation

This guide provides instructions for setting up the engine with a modern, `tk-config-basic` based Toolkit configuration.

### 1. Configure the Software in Flow Production Tracking

In order for Adobe Substance 3D Painter to show up in the FlowPTR launcher, we need to add it to our list of software that is valid for this project.

1. Open the FlowPTR site, sucah as: `example.shotgrid.autodesk.com`.
2. Clink the FlowPTR Settings menu at the top right of the webpage (your profile photo).
* Click in the **Software** menu
![select_a_project_configuration](config/images/select_a_project_configuration.png)
3. Create a new entry for Adobe Substance 3D Painter by clicking the **Add Software** button
4. In the **Create a new Software** form, add the relevant information, such as:
    * In the **Software Name** field, enter Subs Painter - whiel you can enter any name you wish, keep it short as this will be the name displayed in the Desktop app, and longer names will not display well.
    * In the **Description** field, enter "Adobe Substance 3D Painter" and any additinal description.
    * In the **Engine** field, enter "tk-substancepainter".
You can enter information in the other fields as you need, but the fields listed above are necessary.

![create_new_software](config/images/create_new_software.png)

* Note that you can restrict this application to certain projects by adding the project names in the projects field. If no projects are specified this application will show up for all the projects that have this engine in their configuration files. It's recommended to initially assign software to a test project to make sure it's working before rolling it out to any other live project.

If you want more information on how to configure software, here is the detailed documentation from the documentation [Configuring software in FlowPTR](https://help.autodesk.com/view/SGDEV/ENU/?guid=SGD_pg_integrations_admin_guides_integrations_admin_guide_html#configuring-software-launches)


### 3. Configuring Adobe Substance 3D Painter in the FlowPTR software launcher

If you have not already downloaded the FlowPTR deskop software (usually named "Shotgun"), download it while still logged into the FlowPTR site.

1. Click on **Apps** > **Desktop App** and follow the instructions (alternatively, click on your profile photo in the top right of the page and select **Manage Apps** then follow the link to Desktop app).

[Flow Production Tracking (ShotGrid/Shotgun) Desktop Download Instructions](https://help.autodesk.com/view/SGDEV/ENU/?guid=SG_Supervisor_Artist_sa_integrations_sa_integrations_user_guide_html#getting-started-with-flow-production-tracking-desktop)
[Direct Download to Current MacOS Installer](https://sg-software.ems.autodesk.com/deploy/desktop/FlowProductionTrackingInstaller_Current.dmg)
[Direct Download to Current Linux Installer](https://sg-software.ems.autodesk.com/deploy/desktop/flow_production_tracking-current-1.x86_64.rpm)
[Direct Download to Current Windows Installer](https://sg-software.ems.autodesk.com/deploy/desktop/FlowProductionTrackingInstaller_Current.exe)

2. Start up the Shotgun app. While the application is still named Shotgun, you will see the splash screen indicating that it's called Flow Production Tracking.
3. The desktop app may be minimized when it first starts. You can locate it in the System tray when using Windows, or in the top right in the menu bar on macOS. Click the FlowPTR icon to open the window.

The window will show the thumbnails and titles of the projects you are assigned (or have visibility with).

Click on a project you want to configure to use Adobe Substance 3D Painter.

## 5. Configuring your project for Flow Production Tracking (ShotGrid/Shotgun) Toolkit

If you haven't done it yet, make sure you have gone through the basic steps to configure your project to use FlowPTR toolkit, this can be done in the desktop app, by clicking on the project icon to open it. If you have previously set up a project and installed the configuration, skip to [Step 6, Caching and downloading the engine into disk].

1. Click on the user icon to show more options (bottom right).
2. Click on **Advanced project setup**

    ![advanced_project_setup](config/images/advanced_project_setup.png)

**Warning:** if you recieve an error message
    [error_project_setup](config/images/error_project_setup.png)

"You are trying to set up a project which has already been set up", this means you can skip this step, and move on to [Step 6, Caching and downloading the engine into disk]

* *Select a configuration*: "Shotgun Default" or pick an existing porject that you have already setup pages and filters for.

![select_a_project_configuration](https://raw.githubusercontent.com/StephenAnimates/tk-substancepainter/master/config/images/select_a_project_configuration.png)

* *Select a FlowPTR Configuration*: select "default" which will download the standard templates from FlowPTR. (this documentation is written assuming you have this configuration)

![select_a_shotgun_configuration](https://raw.githubusercontent.com/StephenAnimates/tk-substancepainter/master/config/images/select_a_shotgun_configuration.png)

* *Define Storages*: Make sure you name your first storage "primary", and a choose a primary folder where all the 'jobs' publishes will be stored, in this case "D:\demo\jobs" for illustrative purposes.
![define_storages](https://raw.githubusercontent.com/StephenAnimates/tk-substancepainter/master/config/images/define_storages.png)

* *Project Folder Name*: This is the name of the project in disk. You might have some sort of naming convention for project that you might follow, or leave as it is. (My advice is that you do not include spaces in the name)
![project_folder_name](https://raw.githubusercontent.com/StephenAnimates/tk-substancepainter/master/config/images/project_folder_name.png)

* *Select Deployment*: Choose "Centralized Setup". This will be the location of the configuration files (that we will be modifying later). For example, you could place the specific configuration for a project (in this example called game_config) within a folder called "configs" at the same level then the jobs folder, something like: 
```shell
├───jobs
└───configs
    └───config
        ├───cache
        ├───config
        │   ├───core
        │   │   ├───hooks
        │   │   └───schema
        │   ├───env
        │   │   └───includes
        │   │       └───settings
        │   ├───hooks
        │   │   └───tk-multi-launchapp
        │   ├───icons
        │   └───tk-metadata
        └───install
            ├───apps
            ├───core
            ├───engines
            └───frameworks
```
**Note**: this might not be suitable for more complex setups, like distributed configurations

![select_deployment](config/images/select_deployment.png)


### 1. Download the Engine Code

The toolkit project configuration needs to be updated with the Adobe Substance 3D Painter engine information. In your pipeline configuration's `config/env/includes/common` directory, open the existing `engines.yml` file. Add the following block to this file, which points the toolkit to this GitHub repository.

**Make sure to check for the latest version of the engine** here and use the version number in the `version` field below:
tk-substancepainter releases

```yaml
# config/env/includes/common/engines.yml

# Adobe Substance 3D Painter
engines.tk-substancepainter.location:
  type: git
  path: https://github.com/StephenAnimates/tk-substancepainter
  version: v2.0.5
```

### 2. Set up the Project Environment

Next, you need to tell Toolkit which apps to run inside Substance 3D Painter. This follows the standard `tk-config-basic` pattern.
 
1.  In your pipeline configuration, create a new folder for the integration: `config/env/includes/substancepainter`.
2.  Copy the contents of this repository's `config/env/includes/substancepainter` folder (which includes `apps.yml`, `asset_step.yml`, `project.yml`, etc.) into your new folder.
 
    *   **Source**: `tk-substancepainter/config/env/includes/substancepainter/*`
    *   **Destination**: `<your-pipeline-config>/config/env/includes/substancepainter/`

3.  Now, open your main `config/env/asset_step.yml` file and add the include for the Substance Painter settings:

```yaml
# config/env/asset_step.yml

includes:
# Add this line
- includes/substancepainter/asset_step.yml

engines:
  # Add this block
  tk-substancepainter: "@substancepainter.asset_step"

# ... rest of the file
```

```yaml
# config/env/project.yml

includes:
# Add this line
- includes/substancepainter/project.yml

engines:
  # Add this block  
  tk-substancepainter: "@substancepainter.project"

# ... rest of the file
```
If the following is not set up in the `apps.yml` file, add it:
```yaml
# config/env/apps.yml

common.apps.tk-multi-workfiles2.location:
  type: app_store
  name: tk-multi-workfiles2
  version: v0.12.1
common.apps.tk-multi-breakdown2.location:
  type: app_store
  name: tk-multi-breakdown2
  version: v0.4.4
common.apps.tk-multi-screeningroom.location:
  type: app_store
  name: tk-multi-screeningroom
  version: v0.4.2

# ... rest of the file
```

Right-click in the Desktop app and choose **Refresh Projects**.

Install the apps from the app store:
```
tank install_app apps tk-multi-workfiles2 tk-substancepainter

tank install_app environment_name tk-multi-breakdown2 app_name

tank install_app environment_name tk-multi-screeningroom app_name

```


### 6. Caching and downloading the engine into disk

One last step is to cache the engine and apps from the configuration files into disk. FlowPTR provides a tank command for this. 
[Tank Advanced Commands](https://support.shotgunsoftware.com/hc/en-us/articles/219033178-Administering-Toolkit#Advanced%20tank%20commands)

1. Open a Windows Command Prompt or a macOS Terminal window
2. Run the `tank cache_apps` , and press the **Enter/Return** key. (if the Tank command is not an environment var you will need to add the path to the specific project configuration where the tank command is located)
Example: `~/Library/Caches/Shotgun/djcad/p{project id}.basic.desktop/cfg/tank cache_apps`

FlowPTR Toolkit will start revising the changes we have done to the configuration yml files and downloading what is requires.

![tank_cache_apps](config/images/tank_cache_apps.png)


## Adobe Substance 3D Painter engine should be ready to use

If we now go back and forth from our project in FlowPTR desktop ( < arrow top left if you are already within a project), we should be able to see Adobe Substance 3D Painter as an application to launch.

## [tk-multi-workfiles2](https://support.shotgunsoftware.com/hc/en-us/articles/219033088)
This application forms the basis for file management in the Shotgun Pipeline Toolkit. It lets you jump around quickly between your various Shotgun entities and gets you started working quickly. No path needs to be specified as the application manages that behind the scenes. The application helps you manage your working files inside a Work Area and makes it easy to share your work with others.

Basic hooks have been implemented for this tk-app to work. open, save, save_as, reset, and current_path are the scene operations implemented.

Note that "New file" does not actually create a new Adobe Substance 3D Painter project, just changes the context. Unfortunately the dialog to create a new project is not accesible through code, so could not be automated without loosing functionality. The user is responsible for creating a new project as normal in Adobe Substance 3D Painter after "New File" is clicked.  

## [tk-multi-loader2](https://support.shotgunsoftware.com/hc/en-us/articles/219033078)
![tk-substancepainter_01](config/images/tk-substancepainter_01.PNG)

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
![tk-substancepainter_03](config/images/tk-substancepainter_03.PNG)

The Publish app allows artists to publish their work so that it can be used by artists downstream. It supports traditional publishing workflows within the artist’s content creation software as well as stand-alone publishing of any file on disk. When working in content creation software and using the basic Shotgun integration, the app will automatically discover and display items for the artist to publish. For more sophisticated production needs, studios can write custom publish plugins to drive artist workflows.

The basic publishing of the current session is provided with this app. In addition to this, two different modes for the exported textures are provided:

In the tk-multi-publish2.yml configuration file, under the collector_settings section, you will find a setting that allows to publish textures as a single folder ("Texture Folder" published file type), or publish the textures individually as textures ("Texture" published file type). By default or if this setting is missing it is configured to publish a a Texture Folder.

```yaml
settings.tk-multi-publish2.substancepainter.asset_step:
  collector: "{self}/collector.py:{engine}/tk-multi-publish2/basic/collector.py"
  collector_settings:
      Work Template: substancepainter_asset_work
      **Publish Textures as Folder: true**
```

## [tk-multi-breakdown2](https://support.shotgunsoftware.com/hc/en-us/articles/219032988)
![tk-substancepainter_02](config/images/tk-substancepainter_02.PNG)

The Scene Breakdown App shows you a list of items you have loaded (referenced) in your scene and tells you which ones are out of date. From this overview, you can select multiple objects and click the update button which will update all your selected items to use the latest published version.

Note that this tool will only update the resources that have been loaded previously trough the Loader toolkit app.

It also displays what textures loaded from the Loader app are in used within the scene and which ones are not. The tidying up of the shelf resources is left for the user.

Credits:
Originally Developed by: [Diego Garcia Huerta](https://www.linkedin.com/in/diegogh/)