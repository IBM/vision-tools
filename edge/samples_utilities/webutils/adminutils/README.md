# MVI Edge Adminutils

This web sample demonstrates the use of the Controller REST API for a number of functions that are not exposed in the UI.

The `Login/Logout` button will create and end sessions with the controller.
> The default userid and password are hard-coded but can be over-ridden

## Status

Displays all of the Status Server-Sent Events (SSE) that the controller sends to SSE subscribers. Many of these are not displayed in the product UI.

> the `ping` message type, used to keep a subscription from timing out, is not displayed but can be seen in the network tab of a browser's debugger.

The text area displays a `+` for each ping received and the content of each SSE received

> Note SSEs are also displayed as color-coded flash messages. Flash message with the Info and Success severities (blue and green) will automatically be removed after 5 seconds. Messages with Warning or Error severities (orange and red) will remaind displayed until they are clicked.

The Engine Status button retrieves the state of all running inspections on the vision-edge-cme and displays this in the text area

## Backup/Restore

Backup or Restore the entire system configuration. This does not backup or restore metadata, images files, etc.

## Purge Data

Purge various levels of configuration and metadata. This can be useful for people doing demos who wish to return a system to a pre-demo state.

>NOTE Purging Configurations and Metadata is system-wide. All of the indicated content for all inspections is Purged

### All
Returns the system to a post-installation state

### Settings
Clears the System Settings

### Configuration
Clears all Configuration and Metadata but leaves System Settings intact. 

### Metadata
Clears all metadata but leaves System Settings and Configurations intact. 
>This is probably the most useful purge level for returning a system to a pre-demo state.

## Users

Provides for adding and deleting users, changing user passwords and emails.
>Note while emails can be stored for users, they cannot be entered or retrieved by the product UI and are not used by the product in any way. Handling user emails would require GDPR compliance.

## Folder Device Management

### File Upload
Provides for uploading image or video files to folder type input sources (devices). 
> Only files that match the type of folder device can be uploaded. IE image files to image folders and video files to video folders.

### Processed / Unprocessed File Management
Files in folder-type devices are handled as follows:
- When an inspection using a folder-type device is enabled, the unprocessed files in the folder are moved to a processed state once they are processed. 
- Processed files will not be processed again if the inspection is disabled and re-enabled. 
- While an inspection is running, files added to the folder will be processed as soon as they are added.
- When an inspection is enabled, all files in the folder in the unprocessed state will be processed

Folder Device Management provides:

- The number of processed and unprocessed files for each device.
  - This is a snapshot of the file states when the Folder Device Management is opened.
  - The state can be refreshed using the `Refresh Stats` button
- Allows the files for a device to be moved from the processed to the unprocessed state using the `Restore Processed Files` button
  - For running inspections, the files will immediately be processed again
  - For disabled inspections, the files will remain in the unprocessed state until the inspection is enabled
