# Autodesk Flow Production Tracking (FlowPTR) formerly known as ShotGrid/Shotgun, toolkit engine for Adobe Substance 3D Painter

[Key features of Flow Production Tracking (Formerly ShotGrid)](https://www.autodesk.com/products/flow-production-tracking/features)

![tk-substancepainter_04](https://raw.githubusercontent.com/StephenAnimates/tk-substancepainter/master/config/images/tk-substancepainter_04.PNG)

## Overview

This is an mplementation of a **Flow Production Tracking (ShotGrid/Shotgun)** engine for [**Adobe Substance 3D Painter**](https://www.adobe.com/products/substance3d.html). It supports the bootstrap startup methods and integrates the Toolkit Pipeline in the a new Substance Painter menu.

**Note for developers:** The communication between the Python-based engine and Adobe Substance 3D Painter is handled via QtWebsockets. The engine leverages the native Python environment and PySide6 library bundled with Substance 3D Painter.

Uses a project configuration with the following:
Toolkit Basic Configuration v1.7.6 (containing qt6)

App v2.1.0
Python 3.11.9
Startup v2.4.5
Engine v2.8.0
Core v0.23.1


**This engine has been developed and tested on Windows and macOS and should be compatible with modern versions of Adobe Substance 3D Painter on all supported platforms (Windows, macOS, and Linux).**

For detailed information on integrations, see the [Flow Production Tracking Developer Help Center](https://help.autodesk.com/view/SGDEV/ENU/?guid=SG_Supervisor_Artist_sa_integrations_sa_integrations_user_guide_html)

## Engine Installation

This guide provides instructions for setting up the engine with a modern, `tk-config-default2` based Toolkit configuration.


### 1. Configure the Software in Flow Production Tracking

In order for Adobe Substance 3D Painter to show up in the FlowPTR launcher, we need to add it to the list of software for the FlowPTR site that is valid for this project.

1. Open the FlowPTR site, sucah as: `example.shotgrid.autodesk.com`.
2. Clink the FlowPTR Settings menu at the top right of the webpage (your profile photo).
  * Click in the **Software** menu
![select_a_project_configuration](config/images/select_a_project_configuration.png)
3. Create a new entry for Adobe Substance 3D Painter by clicking the **Add Software** button
4. In the **Create a new Software** form, add the relevant information, such as:
  * In the **Software Name** field, enter **Subs Painter** - while you can enter any name you wish, keep it short as this will be the name displayed in the Desktop app, and longer names will not display well in the app.
  * In the **Description** field, enter "Adobe Substance 3D Painter" and any additinal description you wish.
  * In the **Engine** field, enter "tk-substancepainter".
You can enter information in the other fields as you need, but the fields listed above are necessary.

![create_new_software](config/images/create_new_software.png)

* Note that you can restrict this application to certain projects by adding the project names in the projects field. If no projects are specified this application will show up for all the projects that have this engine in their configuration files. It's recommended to initially assign software to a test project to make sure it's working before rolling it out to any other live project.

If you want more information on how to configure software, here is the detailed documentation from the documentation [Configuring software in FlowPTR](https://help.autodesk.com/view/SGDEV/ENU/?guid=SGD_pg_integrations_admin_guides_integrations_admin_guide_html#configuring-software-launches)


### 2. Configuring Adobe Substance 3D Painter in the FlowPTR software launcher

If you have not already downloaded the FlowPTR deskop software (usually named "Shotgun"), download it while still logged into the FlowPTR site.

1. Click on **Apps** > **Desktop App** and follow the instructions (alternatively, click on your profile photo in the top right of the page and select **Manage Apps** then follow the link to Desktop app).

[Flow Production Tracking (ShotGrid/Shotgun) Desktop Download Instructions](https://help.autodesk.com/view/SGDEV/ENU/?guid=SG_Supervisor_Artist_sa_integrations_sa_integrations_user_guide_html#getting-started-with-flow-production-tracking-desktop)
[Direct Download to Current MacOS Installer](https://sg-software.ems.autodesk.com/deploy/desktop/FlowProductionTrackingInstaller_Current.dmg)
[Direct Download to Current Linux Installer](https://sg-software.ems.autodesk.com/deploy/desktop/flow_production_tracking-current-1.x86_64.rpm)
[Direct Download to Current Windows Installer](https://sg-software.ems.autodesk.com/deploy/desktop/FlowProductionTrackingInstaller_Current.exe)

2. Start up the Shotgun app. While the application is still named **Shotgun**, you will see the splash screen indicating that it's called Flow Production Tracking.
3. The desktop app may be minimized when it first starts. You can locate it in the System tray when using Windows, or in the top right in the menu bar on macOS. Click the FlowPTR icon to open the window.

The window will show the thumbnails and titles of the projects you are assigned (or have visibility with).

Click on a project you want to configure to use Adobe Substance 3D Painter.

## 3. Configuring your project for Flow Production Tracking (ShotGrid/Shotgun) Toolkit

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

(I think the following is outdated:)
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




#### Method 1: Using ShotGrid Desktop (Recommended)
The safest way to ensure the file structure is created correctly and dependencies are handled.

1. Open **ShotGrid Desktop**: Launch the ShotGrid Desktop application and select the project you want to modify.
2. Access the **Project Setup Wizard**: There are two primary places to find the **Advanced project setup** option:
  A. **Project Area Contextual Menu**: Right-click in the main area of the window where the software is shown.
  B. **User Profile Menu:** Click on your User Profile Picture (icon) in the bottom-right corner of the application window.
3. Select the "Advanced project setup..." option.
4. Choose **New Configuration**: The wizard will prompt you to select a configuration to install.
5. Select **tk-config-default2**: Choose the option that points to the tk-config-default2 repository (often listed as the "Default Configuration").
6. Complete the **Wizard**: Follow the prompts to finish the setup. This process updates the **Pipeline Configuration Entity** on the Flow Production Tracking site and downloads the new tk-config-default2 structure locally.

Once complete, the next time you launch any application from ShotGrid Desktop for that project, it will use the tk-config-default2 structure.
If you see the message that *You are trying to set up a project which has already been set up*, as it indicates, you can either:
1. Use the tank command to forece the project setup using `tank setup_project --force`
2. Alternatively, log into your Flow Production Tracking site and clear the Project.tank_name field
and delete all pipeline configurations for your project.

#### Method 2: Manual Update via the ShotGrid Site
If you cannot access the **Advanced Setup** wizard, you can directly change the configuration source on the Flow Production Tracking website.
1. Navigate to **Pipeline Configurations**: Log into your **Flow Production Tracking** site and click on your profile picture to show the menu, then in the **Admin** section, locate the **Defulat Layouts** > **Pipeline Configuration** > **Pipeline Configuration List**.
2. Locate the **Primary Config**: Find the primary configuration for your project.
  - If there is not a basic configuration for your particular project, create a new one.
  - Click the **Add Pipeline Configuration** button.
  - In the **Name** field, enter *Primary*
  - In the **Description** field, enter something that will indicate the use of the configuration, such as *A new primary configuration using the tk-config-default2*
  - In the **Plugin Ids** field, enter `basic.*`
  - In the **Descriptor** field, enter `sgtk:descriptor:app_store?name=tk-config-default2` (You can add `&version=vX.X.X` to specify a version, where X.X.X ist the version number).
  - In the **Project** field, enter a project that you want to specifiy for this configuration.
3. If you already have a configuration you want to use, update the **Descriptor** field to replace the descriptor that may show tk-config-basic with one that points to tk-config-default2.
Example Old Descriptor (if any): `sgtk:descriptor:app_store?name=tk-config-basic&version=v1.7.6`
New Descriptor: `sgtk:descriptor:app_store?name=tk-config-default2&version=v1.8.x` (Use the latest version)
4. **Clear Local Cache**: On your machine, delete the contents of the old tk-config-basic configuration folder (or delete the entire folder associated with the project's config).
5. Restart **ShotGrid Desktop**, and click your project icon to open it. You may see a message that the storage roots cannot be mapped.
6. Open the roots.yml file (from the path shown in the message).

This forces the Toolkit to download the new tk-config-default2 code corresponding to the updated descriptor.




![select_deployment](config/images/select_deployment.png)

### Follow the directions to install for your configuration

See the installation.md file:

### 7. Cache the Configuration

One last step is to cache the engine and apps from the configuration files into disk. FlowPTR provides a tank command for this. 
[Tank Advanced Commands](https://support.shotgunsoftware.com/hc/en-us/articles/219033178-Administering-Toolkit#Advanced%20tank%20commands

1. Open the **FlowPTR Desktop** (if it's not already open).
2. From the Projects screen, right-click in the **FlowPTR Desktop** app and choose **Refresh Projects**. (if you are in a project, I suggest you go back to the main projects page to refresh the projects by clicking the < arrow top left)
3. Open a **Windows Command Prompt** or a **macOS Terminal** window.
4. Run the `tank cache_apps` , and press the **Enter/Return** key. (if the Tank command is not an environment var you will need to add the path to the specific project configuration where the tank command is located)
Example: `~/Library/Caches/Shotgun/djcad/p{project id}.basic.desktop/cfg/tank cache_apps`

FlowPTR Toolkit will start revising the changes we have done to the configuration yml files and downloading what is requires. If it's successsful, you will see:
```
Cache apps completed!
```
![tank_cache_apps](config/images/tank_cache_apps.png)

## Adobe Substance 3D Painter engine should be ready to use

Go back to the FlowPTR Desktop app and open the project with the configuration, Adobe Substance 3D Painter or "Subs Painter" if you following the guidenace, as an application to launch. Click the icon to lanuch Adobe Substance 3D Painter.

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