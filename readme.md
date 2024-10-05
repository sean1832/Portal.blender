# Portal.blender
![GitHub Release](https://img.shields.io/github/v/release/sean1832/portal.blender)
![Static Badge](https://img.shields.io/badge/blender-4.2.0%2B-blue)
![GitHub License](https://img.shields.io/github/license/sean1832/portal.blender)

Portal.blender is a Blender add-on that allows you to communicate data between Blender and other applications using IPC. It is the Blender adaptor of the [Portal](https://github.com/sean1832/portal) project.

> *⭐️ Like this repo? please consider a star!*

| **Receiver**                                 | **Sender**                                   |
| -------------------------------------------- | -------------------------------------------- |
| ![image](/doc/images/portal-server-recv.png) | ![image](/doc/images/portal-server-send.png) |

## Compatibility
| Portal.blender                                                                       | Portal.Gh                                                                                                                                      |
| ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| [`0.2.3`](https://github.com/sean1832/Portal.blender/releases/tag/0.2.3)             | [`0.5.2`](https://github.com/sean1832/Portal/releases/tag/0.5.2)                                                                               |
| [`0.2.2`](https://github.com/sean1832/Portal.blender/releases/tag/0.2.2)             | [`0.5.1`](https://github.com/sean1832/Portal/releases/tag/0.5.1)                                                                               |
| [`0.2.1`](https://github.com/sean1832/Portal.blender/releases/tag/0.2.1)             | [`0.5.1`](https://github.com/sean1832/Portal/releases/tag/0.5.1)                                                                               |
| [`0.2.0 pre-release`](https://github.com/sean1832/Portal.blender/releases/tag/0.2.0) | [`0.5.0 pre-release`](https://github.com/sean1832/Portal/releases/tag/0.5.0)                                                                   |
| [`0.1.2`](https://github.com/sean1832/Portal.blender/releases/tag/0.1.2)             | [`0.4.0`](https://github.com/sean1832/Portal/releases/tag/0.4.0)                                                                               |
| [`0.1.1`](https://github.com/sean1832/Portal.blender/releases/tag/0.1.1)             | [`0.4.0`](https://github.com/sean1832/Portal/releases/tag/0.4.0)                                                                               |
| [`0.1.0`](https://github.com/sean1832/Portal.blender/releases/tag/0.1.0)             | [`0.4.0`](https://github.com/sean1832/Portal/releases/tag/0.4.0)                                                                               |
| [`0.0.3`](https://github.com/sean1832/Portal.blender/releases/tag/0.0.3)             | [`0.3.1`](https://github.com/sean1832/Portal/releases/tag/0.3.1), [`0.3.0 pre-release`](https://github.com/sean1832/Portal/releases/tag/0.3.0) |
| `0.0.2`                                                                              | `0.2.0`, `0.1.2`, `0.1.1`                                                                                                                      |
| `0.0.1`                                                                              | `0.2.0`, `0.1.2`, `0.1.1`                                                                                                                      |

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

### Custom Handlers
You can create custom handlers to manipulate the data that is received. To do this, follow these steps:
1. Copy and paste the template code into blender's text editor and modify it to suit your needs.
   - [Custom Receiver Handler](/templates/recv_handler.py)
   - [Custom Sender Handler](/templates/send_handler.py)
2. Select `Custom` from the dropdown menu.
3. Attach the handler script to the `Handler` field or click the `folder icon` to locate the script.
4. Click `Start` to start the server.


![alt text](/doc/images/custom-handler.png)

## Roadmap
### v0.3.0
- [ ] Add mouse up / down event for the sender.
- [ ] Implement more material properties.


## Documentation
For more information, visit the [Portal](https://github.com/sean1832/portal).
