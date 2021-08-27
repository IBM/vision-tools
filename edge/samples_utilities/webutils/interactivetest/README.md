# MVI Edge Interactive Test

This web sample demonstrates the use of the Controller REST API to interact with an inspection in `interactive` mode, which is the mode used by the `Review inspection` page in the product UI. 

In this mode:
- triggers are sent to an inspection to process images.
- metadata is returned to the UI but is not stored in the system and is not sent to external entities such as the MVI Training server, or MQTT topics.
- files in folder type devices are not moved from the unprocessed to the processed state.

## Using the sample
- The `Login/Logout` button will create and end sessions with the controller.
- The `Inspection UUID` must be provided for the inspection that should be run in interactive mode. This can be discovered using the Swagger doc when the controller is started in Development Mode (See the inception document under installation for details). It can also be discovered using a browser debugger and checking the HTTP Response of the ~synopsis call when an inspection is selected in the product UI.
- The `Start` and `Stop` buttons will start and stop the inspection in interacctive mode. While started, the inspection remains enabled and waits for triggers to indicate that it should process an image
- The `Trigger` button processes and image. The processed image is displayed with annottions and the Metadata returned is displayed in the text area.
- The `Trigger w/ Rules` button causes the Rules for the inspection to be reloaded by the running inspection. This allows for Rules to be modified and tested without stopping and re-starting the inspection.
- The `Trigger Interval` field determines the interval in milliseconds to pause between triggers when the `Loop Trigger` button is clicked
- The `Loop Trigger` will send triggers to the inspection at the interval specified in the `Trigger Interval` field.
  >NOTE if the interval is too low and the inference engine respond quickly enough, this may cause the Looping to fall behind and no updates to be displayed. The loop  must be stopped if this happens.
- The `Stop Loop` button stops the trigger loop.



