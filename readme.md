# Portal.blender
![GitHub Release](https://img.shields.io/github/v/release/sean1832/portal.blender)
![Static Badge](https://img.shields.io/badge/blender-4.2.0%2B-blue)
![GitHub License](https://img.shields.io/github/license/sean1832/portal.blender)

Portal.blender is a Blender add-on that allows you to communicate data between Blender and other applications using IPC. It is the Blender adaptor of the [Portal](https://github.com/sean1832/portal) project.

![image](/doc/images/portal-server-panel.png)

## Installation
- Download the latest release from the [releases page](https://github.com/sean1832/Portal.blender/releases/latest).
- Drag and drop the zip file into Blender to install.

### Dependencies
If this is your first time installing the Portal add-on, you will need to install the dependencies. To do this, follow these steps:
> [!IMPORTANT]
> You must start blender as an administrator to install the dependencies. After the dependencies are installed, you can run Blender as a regular user. See [issue](https://github.com/sean1832/Portal.blender/issues/1).
1. Open the preferences (Edit > Preferences > Add-ons).
2. Search for the 'Portal' add-on.
3. Open the details section of the add-on.
4. Click on the 'Install dependencies' button.
5. Restart Blender.

![image](/doc/images/dependencies-installation.png)

## Usage
- Locate the `Portal Server` panel in the `3D View` sidebar. (Shortcut: `N`)
- Select `Connection Type` from the dropdown menu.
- Click `Start Server` to start the server.


## Documentation
For more information, visit the [Portal](https://github.com/sean1832/portal).
