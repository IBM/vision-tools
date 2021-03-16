# IBM_PROLOG_BEGIN_TAG
#
# Copyright 2020 IBM International Business Machines Corp.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#           http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
#  implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  IBM_PROLOG_END_TAG

from __future__ import print_function

import argparse
import csv
import json
import logging
import sys
from datetime import datetime

import requests

cfg = {}
csvResult = {}
fnset = set()



## IMPORTANT: Note that this script will automatically filter certain items from results if no command line flags
## are specified that require those items to be included. "Training" data that does NOT include a
## Maximo Visual Inspection Mobile Inference result and any data set that ends with "_test" (case insensitive) will
## be omitted. See below for the "--showall" flag which explains more.
TEST_DATASET_NAME_EYECATCHER = "_test" #any data set that ends in this string will be considered a test data set



# ------------------------------------
# Eases printing to STDERR
def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)


# ------------------------------------
# Checks if result from Vision API succeeded
# (Current API returns failure indication in the JSON body)
def rspOk(rsp):
  logging.debug("status_code: {}, OK={}.".format(rsp.status_code, rsp.ok))
  
  if rsp.ok:
    try:
      jsonBody = rsp.json()
      if ("result" in jsonBody) and (jsonBody["result"] == "fail"):
        result = False
        logging.info(json.dumps(jsonBody, indent=2))
      else:
        result = True
    except ValueError:
      result = True
      logging.info("good status_code, but no data")
  else:
    result = False
  
  return result


# ------------------------------------
# local post function to hide common parameters
#
def post(url, **kwargs):
  headers = {}
  headers['X-Auth-Token'] = u'%s' % cfg['token']

  return requests.post(url, headers=headers, verify=False, **kwargs)


def get(url, **kwargs):
  headers = {}
  headers['X-Auth-Token'] = u'%s' % cfg['token']
  
  return requests.get(url, headers=headers, verify=False, **kwargs)


# -------------------------------------
# sets up the API access
#
def setupAPIAccess(url, user, passwd):
  global cfg
  cfg["url"] = url
  # Disable warning messages about SSL certs
  requests.packages.urllib3.disable_warnings()
  
  if user is not None and passwd is not None:
    auth = {
      "grant_type": "password",
      "username": user,
      "password": passwd
    }
    logging.info("Setting up auth token")
    resp = requests.post(url + "/api/tokens", verify=False, json=auth)
    respdata = resp.json()
    cfg['token'] = respdata['token']


# -------------------------------------
# parse commandline options -- using argparse
#
# argparse "results" class is returned
#
# Note: If '--category' or '--objlabel' arguments are specified, the script will look for false negatives.
# A false negative image is one that is either that has a category value that matches the "--category" value
# OR if the image has an object tag that matches the "--objlabel" value.  If either of these command line
# arguments is specified, the output csv file will only contain those images that were deemed to be
# a false negative.
#
# Without the use of either "--category" or "--objlabel", the script will not try to determine if
# an image is a false negative.  With a 60K image dataset, the script completed in about 30 seconds.
# If either "--category" or "--objlabel" is specified, the script will look for false negatives,
# causing the script to run longer.  With a 60K image dataset, the script completed in about 60 seconds.
#
def getInputs():
  parser = argparse.ArgumentParser(description="Tool to classify all images in a directory")
  parser.add_argument('--dsid', action="store", dest="dsid", required=False,
                      help="(Optional) UUID of a target dataset")
  parser.add_argument('--category', action="store", dest="categoryname", required=False,
                      help="(Optional) Name of the category to determine if image is a false negative.  If specified, output csv file will only contain false negative image entries.")
  parser.add_argument('--objlabel', action="store", dest="objlabel", required=False,
                      help="(Optional) Name of the object label to determine if image is a false negative.  If specified, output csv file will only contain false negative image entries.")
  parser.add_argument('--url', action="store", dest="url", required=True,
                      help="Vision URL eg https://ip/powerai-vision WITHOUT trailing slash or /api")
  parser.add_argument('--user', action="store", dest="user", required=True,
                      help="Username")
  parser.add_argument('--passwd', action="store", dest="passwd", required=True,
                      help="Password")
  parser.add_argument('--showall', action="store_true", dest="showall", required=False,
                      help="(Optional) Show all image data. By default, this tool filters training data, and any data set that ends in \"" + TEST_DATASET_NAME_EYECATCHER + "\" (case insensitive) which indicates test data, not production data.")
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('--output', action="store", dest="output",
                      help="Output file name eg output.csv")
  group.add_argument('--migrate-metadata', action="store_true", dest="migrate",
                      help="Migrate Visual Inspector 1.0 metadata to 1.1 formats. Does not create CSV output. Requires IBM Visual Insights or Maximo Visual Inspection 1.2.0.1 or greater")
  parser.add_argument('--debug', action="store_true", dest="debug", required=False,
                      help="Set Debug logging level")
  parser.add_argument('--newerthan', action="store", dest="newerthan", required=False, default=0,
                      help="(Optional) Output only records newer than this timestamp in YYYYMMDDHHmmss format eg \"20200622134840\" is \"2020 June 22, 13:48:40\"")



  
  try:
    results = parser.parse_args()
  
  except argparse.ArgumentTypeError as e:
    logging.error(e.args)
    parser.print_help(sys.stderr)
    results = None
  
  return results

def getDatasets(qparm=None):
  result = None
  url = cfg["url"] + "/api/datasets"
  logging.debug("getDatasets: URL = {}".format(url))
  rsp = get(url)
  
  if rspOk(rsp):
    result = rsp.json()
  return result

def getFileList(dsId, qparm=None):
  result = None
  
  url = cfg["url"] + "/api/datasets/" + dsId + "/files"
  if qparm:
    url += "?" + qparm
  logging.debug("getFileList: URL= {}".format(url))
  rsp = get(url)
  if rspOk(rsp):
    result = rsp.json()
  return result

def postUserMetadata(dsId, fileId, jsonBody):
  result = None
  success = False
  url = cfg["url"] + "/api/datasets/" + dsId + "/files/" + fileId + "/user-metadata"
  logging.debug("postUserMetadata: URL= {}".format(url))
  resp = post(url, json=jsonBody)

  if rspOk(resp):
    result = resp.json()
    logging.debug("postUserMetadata: result json= {}".format(result))
    success = True
  return success


# return an array of files with extra data attached like the datasetid, URL, and owner that are not available via the API response directly
def enumeratefiles(dsid=None, url="http://ip/instance-name"):
  # get list of all datasets
  logging.info("Retrieving global dataset list...")
  datasets = getDatasets()
  if dsid:
    # filter down to just the dataset we care about
    datasets = [dataset for dataset in datasets if dataset['_id'] == dsid]
  logging.info("Successfully retrieved %d datasets" % len(datasets))
  
  # holding spot accumulator for all files system-wide
  files = []
  # iterate across all datasets, one-by-one
  for dataset in datasets:
    # get files for this specific dataset
    dsfiles = getFileList(dataset['_id'])
    logging.info("Fetched %7d items in Dataset %s = %s" % (len(dsfiles), dataset['_id'], dataset['name']))
    # create a unique URL and some other book keeping items for this file
    for file in dsfiles:
      # note these strings must match the CSV header capitalization and spelling to allow for an easy construction of the final row from a header field list
      file['datasetid'] = dataset.get('_id', "")
      file['datasetname'] = dataset.get('name', "")
      file['owner'] = dataset.get('owner', "")
      file['url'] = url + "/" + "#/datasets/" + dataset['_id'] + "/label?imageId=" + file['_id']
    # append this into the master list for csv processing...
    files.extend(dsfiles)
  
  return files

# -------------------------------------
# Parse and save file metadata
#
def saveMetadata(dsid=None, url="http://ip/instance-name"):
  
  # get the list of affected files that we're potentially acting upon
  # note that filters or other rules might mean that we may not actually touch ALL of these
  dsFiles = enumeratefiles(dsid=args.dsid, url=args.url)
  
  # save metadata through visual inspection's user-metadata API
  logging.info("Beginning migration for %d files..." % len(dsFiles))
  successcount = 0
  for dsFile in dsFiles:
    if "___" in dsFile['original_file_name']:
      filejson = {}
      visinspectdata = dsFile['original_file_name'].split('___')

      # default keys common to both Object Detection and Image Classification
      keys = ['InspectionType', 'Timestamp', 'TriggerID', 'Reference', 'TriggerString', 'InspectionName', 'InspectionLocation', 'InspectionDevice']
      # add additional metadata keys based on the parsing of the original file name (INSPECTION vs TRAINING)
      if visinspectdata[0] == "INSPECTION":
        keys.insert(6, 'InspectionResult')
        keys.extend(['InspectionModelType', 'InspectionLabels', 'InspectionScores', 'InspectionThresholds'])
        # add additional metadata keys if the file is from object detection model
        if visinspectdata[9] == "ObjectDetection":
          keys.extend(['InspectionExpectedCounts', 'InspectionBoundingBoxes', 'InspectionAboveBelow', 'InspectionPassFail', 'InspectionAndOr', 'InspectionLevel', 'FailedLabels'])

      # remove the .jpeg or .png appended by Inspector on the very end...
      if '.jpeg' in visinspectdata:
        visinspectdata.remove('.jpeg')
      if '.png' in visinspectdata:
        visinspectdata.remove('.png')

      # further parse metadata values into lists
      for count, data in enumerate(visinspectdata):
        if "__" in data:
          listItem = data.split("__")
          visinspectdata[count] = listItem
      logging.debug("visinspectdata split into an array of length %d" % len(visinspectdata))
      if visinspectdata[0] == "INSPECTION" and visinspectdata[9] == "ObjectDetection":
        #this field may or may not exist depending on the version of the original app
        #note that we check that the LENGTH is greater than 19 (ie there's at least a foo[19] in the zero-indexed array
        if (len(visinspectdata) > 19) and (visinspectdata[19] == ""):
          # no failed labels were found; replace with an empty array
          visinspectdata[19] = []
        # reformat the list of bounding boxes
        bbBoxesList = []
        for x, box in enumerate(visinspectdata[14]):
          if "_" in box:
            points = box.split("_")
            bboxesDict = {"xmax": points[0], "xmin": points[1], "ymax": points[2], "ymin": points[3]}
            bbBoxesList.append(bboxesDict)
        visinspectdata[14] = bbBoxesList

      # merge the metadata keys and values to send as the json body
      filejson = dict(zip(keys, visinspectdata))
      logging.debug(filejson)
      #TODO: re-save bounding boxes as inferred label type
      logging.info("Migrating dataset %s, file %s" % (dsFile['datasetid'], dsFile['_id']))
      success = postUserMetadata(dsFile['datasetid'], dsFile['_id'], filejson)
      if success:
        successcount += 1

  logging.info("Migration complete. Migrated %d records" % (successcount))
  if successcount != len(dsFiles):
    logging.warning("We failed to migrate data for %d files." % (len(dsFiles) - successcount))
  return successcount

def getUserMetadata(dsId):
  result = []
  url = cfg["url"] + "/api/datasets/" + dsId + "/files/user-metadata" + "?" + "format=pipe"
  # if newerthan > 0:
  #   url += "&query=user_metadata.Timestamp%20%3E%20%2220200622113447%22"
  logging.debug("getUserMetadata: URL = {}".format(url))
  rsp = get(url)
  if rspOk(rsp):
    csvstring = rsp.content.decode('utf-8')
    reader = csv.DictReader(csvstring.splitlines(), delimiter='|')
    for row in reader:
      result.append(row)
  return result

def getFalseNegativeSet(dsid=None, categoryname=None, objlabel=None):
  global fnset
  #falseset = set()
  if categoryname or objlabel:
    dsfiles = getFileList(dsid)
    for dsfile in dsfiles:
      if dsfile.get('category_name', "") == categoryname:
        #logging.debug("Added %s based on category" % (dsfile['_id']))
        #falseset.add(dsfile['_id'])
        fnset.add(dsfile['_id'])
      else:
        if objlabel and 'tag_list' in dsfile.keys():
          tagobject = [tagobject for tagobject in dsfile['tag_list'] if tagobject['tag_name'] == objlabel]
          if tagobject:
            #falseset.add(dsfile['_id'])
            fnset.add(dsfile['_id'])
  logging.debug("Size of falseset is %d" % len(fnset))
  return

# return an array of files with extra data attached like the datasetid, URL, and owner that are not available via the API response directly
def fetchCSV(dsid=None, categoryname=None, objlabel=None, url="http://ip/instance-name", showall=False):
  # get list of all datasets
  logging.info("Retrieving global dataset list...")
  global fnset
  datasets = getDatasets()
  if dsid:
    # filter down to just the dataset we care about
    datasets = [dataset for dataset in datasets if dataset['_id'] == dsid]
  logging.info("Successfully retrieved %d datasets" % len(datasets))
  
  # holding spot accumulator for all files system-wide
  rows = []
  #iterate across all datasets, one-by-one
  for dataset in datasets:
    logging.info("Fetching " + dataset['name'])
    if (not showall) and dataset['name'].lower().endswith(TEST_DATASET_NAME_EYECATCHER):
      logging.info("Skipping retrieval of data from dataset " + dataset['name'] + " since its name matches " + TEST_DATASET_NAME_EYECATCHER + " (case insensitive).")
      continue
    #get files for this specific dataset
    dscsvdata = getUserMetadata(dataset['_id'])
    getFalseNegativeSet(dataset['_id'], categoryname, objlabel)
    logging.info("Fetched %7d items in Dataset %s = %s" % (len(dscsvdata), dataset['_id'], dataset['name']))
    # create a unique URL and some other book keeping items for this file
    for file in dscsvdata:
      # note these strings must match the CSV header capitalization and spelling to allow for an easy construction of the final row from a header field list
      file['DataSetID'] = dataset.get('_id', "")
      file['DataSetName'] = dataset.get('name', "")
      file['Owner'] = dataset.get('owner', "")
      file['URL'] = url + "/" + "#/datasets/" + dataset['_id'] + "/label?imageId=" + file['#file_id']
      # The 'FalseNegative' field is used to denote if a image has been 'tagged' that the
      # InspectionPassed is not correct after manual visual inspection has been done.
      # By default we set the value to 'False'  and only if either the image has the
      # 'category_name' or an object label of objlabel, set it to 'True'
      #if file['#file_id'] in falseset:
      if file['#file_id'] in fnset:
        #logging.info("setting InspectionPassed to TRUE on %s" % (file['#file_id']))
        file['InspectionPassed'] = 'true'
  # append this into the master list for csv processing...
    rows.extend(dscsvdata)
  
  return rows


# -------------------------------------
# Generate CSV from dictionary
#
def generateCSV(dsid=None, categoryname=None, objlabel=None, url="http://ip/instance-name", filename="output.csv", showall=False, newerthan=0):
  numrows = 0
  global fnset

  rows = fetchCSV(dsid=dsid, categoryname=categoryname, objlabel=objlabel, url=url, showall=showall)
  
  # Generate minimal info CSV
  with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    headers = ['DataSetID', 'DataSetName', 'Owner', 'URL', 'InspectionType', 'FormattedDate', 'Timestamp', 'Reference',
               'TriggerString', 'InspectionName', 'InspectionPassed',
               'InspectionLocation', 'InspectionDevice', 'InspectionModelType', 'InspectionLabels', 'FailedLabels']
    # headers.extend(['Metadata%d' % i for i in range(25)])
    writer.writerow(headers)
    # writer.writeheader()
    logging.debug("Parsing data for dataset %s" % rows[0]['DataSetID'])
    for row in rows:
      #logging.debug("Parsing row = %s" % (row))
      #note that we check to see if there's an InspectionType key, and THEN see if there's a valid VALUE. If so, then
      #we parse this as an Inspector row.
      if categoryname or objlabel:
        if "#file_id" in row.keys() and row['#file_id'] not in fnset:
          continue
      if "InspectionType" in row.keys() and len(row["InspectionType"]) != 0:
        # reformat time to something excel can parse
        fmtedtime = ""
        try:
          dt = datetime.strptime(row['Timestamp'], "%Y%m%d%H%M%S")
          fmtedtime = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
          fmtedtime = ""
        row['FormattedDate'] = fmtedtime
        if (not showall) and (row['InspectionType'] == "Collected"):
          # NOTE Special behavior here. We skip this row since we're filtering out training data
          continue
        if (row['Timestamp'] is None):
          logging.debug("WARN: No timestamp for %s" % rows[0]['URL'])
          continue
        if (row['Timestamp'].strip() == ""):
          logging.debug("WARN: No timestamp for %s" % rows[0]['URL'])
          continue
        if int(row['Timestamp']) < newerthan:
          # NOTE Special behavior here. We skip this row since we're filtering out all records older than the "newerthan" arg.
          # However, if the 'FalseNegative' field is set to 'True' we want to include the item irregardless of
          # the Timestamp filter
          # If the user didn't specify newerthan, then we default to 0, which will return -all- timestamps.
          continue
      elif showall:
        # handle cases where we found a user-uploaded image, but only if we're dumping all of the user's data
        # mark this rown as having a type of "Labeled" but fill in no further columns
        row['InspectionType'] = 'UNKNOWN'
      else:
        # if InspectionType is not present, OR we are not showing all records, we need to skip a record, so we "continue"
        # to the next row, skipping the write operation.
        continue
      # actually write the row
      visinspectdata = []
      for header in headers:
        # take what we can get
        if header in row.keys():
          visinspectdata.append(row[header])
        else:
          # append an empty column
          visinspectdata.append('')
      writer.writerow(visinspectdata)
      numrows += 1
      
  if numrows != len(rows):
    logging.info("We filtered out %d items." % (len(rows)-numrows))
    
  return numrows

if __name__ == '__main__':
  args = getInputs()
  loglevel = logging.DEBUG if args.debug else logging.INFO
  logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                      datefmt='%H:%M:%S',
                      level=loglevel)
  
  if args is not None:
  
    # set up the auth token
    setupAPIAccess(url=args.url, user=args.user, passwd=args.passwd)

    if args.migrate:
      logging.debug("Starting migration of down-level inspector data to metadata APIs...")
      numfilesmigrated = saveMetadata(dsid=args.dsid, categoryname=args.categoryname, url=args.url)
      logging.info("Finished migrating data for %d files." % (numfilesmigrated))

    elif args.output:
      logging.debug("Saving CSV metadata to %s" % (args.output))
      rowswritten = generateCSV(dsid=args.dsid, categoryname=args.categoryname, objlabel=args.objlabel, url=args.url, filename=args.output, showall=args.showall, newerthan=int(args.newerthan))
      logging.info("Wrote   %7d rows to %s." % (rowswritten, args.output))
    else:
      logging.error("Did not find a valid command or argument to parse.")
  else:
    exit(1)
