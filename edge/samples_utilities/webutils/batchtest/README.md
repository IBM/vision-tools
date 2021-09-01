# MVI Edge BatchTest

This web sample demonstrates the use of the Controller REST API for batch functions. This can be useful for timing batch functions with large sets of images.

The `Login/Logout` button will create and end sessions with the controller.
> The default userid and password are hard-coded but can be over-ridden

All inspections in the system are displayed in a table along with the statistics for the inspections. The statistics are the same ones displayed in the product UI Inspections=>Images tab. The actions available for each inspection are described below

## Refresh

Updates the inspections table

## Clear

Clears the text area

## Inspection Level Actions

### Delete
Deletes all images and their associated metadata for an inspection

### Pass / Fail / Inconclusive
Changes all results for the inspection to the selected result

### Get FilterData
Retreives the data used by the product UI to support filtering and searching. This is provided for timing of the retrieval time. When the data is fetched, a message is displayed in the text area.
