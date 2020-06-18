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
def getInputs():
  parser = argparse.ArgumentParser(description="Tool to classify all images in a directory")
  parser.add_argument('--dsid', action="store", dest="dsid", required=False,
                      help="(Optional) UUID of a target dataset")
  parser.add_argument('--url', action="store", dest="url", required=True,
                      help="Vision URL eg https://ip/powerai-vision WITHOUT trailing slash or /api")
  parser.add_argument('--output', action="store", dest="output", required=True,
                      help="Output file name eg output.csv")
  parser.add_argument('--user', action="store", dest="user", required=True,
                      help="Username")
  parser.add_argument('--passwd', action="store", dest="passwd", required=True,
                      help="Password")
  parser.add_argument('--showall', action="store_true", dest="showall", required=False,
                      help="(Optional) Show all image data. By default, this tool filters training data.")
  parser.add_argument('--debug', action="store_true", dest="debug", required=False,
                      help="Set Debug logging level")

  
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
  url = cfg["url"] + "/api/datasets/" + dsId + "/files/" + fileId + "/user-metadata"
  logging.debug("postUserMetadata: URL= {}".format(url))
  resp = post(url, json=jsonBody)

  if rspOk(resp):
    result = resp.json()
    logging.debug("postUserMetadata: result json= {}".format(result))


# -------------------------------------
# Parse and save file metadata
#
def saveMetadata(dsFiles, csvfilename, showall=False):
  # save metadata through visual inspection's user-metadata API
  for dsFile in dsFiles:
    if "___" in dsFile['original_file_name']:
      json = {}
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

      if visinspectdata[0] == "INSPECTION" and visinspectdata[9] == "ObjectDetection":
        if visinspectdata[19] == "":
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
      json = dict(zip(keys, visinspectdata))
      postUserMetadata(dsFile['datasetid'], dsFile['_id'], json)


# -------------------------------------
# Generate CSV from dictionary
#
def generateCSV(filename, rows, showall=False):
  numrows = 0
  # Generate minimal info CSV
  with open(filename, 'w') as csvfile:
    writer = csv.writer(csvfile)
    headers = ['DataSetID', 'DataSetName', 'Owner', 'URL', 'InspectionType', 'FormattedDate', 'RawDate', 'TriggerID', 'Reference', 
               'TriggerString', 'InspectionName', 'InspectionResult', 'InspectionLocation', 'InspectionDevice', 'InspectionModelType', 
               'InspectionLabels', 'InspectionScores', 'InspectionThresholds', 'InspectionExpectedCounts',
               'InspectionBoundingBoxes', 'InspectionAboveBelow', 'InspectionPassFail', 'InspectionAndOr', 'InspectionLevel', 'FailedLabels']
    writer.writerow(headers)

    logging.debug("Parsing data for dataset %s" % rows[0]['datasetid'])
    for row in rows:
      if "___" in row['original_file_name']:
        visinspectdata = row['original_file_name'].split('___')
        # prepend our URL to deep-link to Vision
        visinspectdata[0:0] = [row['datasetid'], row['datasetname'], row['owner'], row['url']]
        # reformat time to something excel can parse
        try:
          dt = datetime.strptime(visinspectdata[5], "%Y%m%d%H%M%S")
          # insert the formatted date in BEFORE the old date
          visinspectdata[5:5] = [dt.strftime("%Y-%m-%d %H:%M:%S")]
        except ValueError:
          visinspectdata[5:5] = [""]
        if (not showall) and (visinspectdata[4] == "TRAINING"):
          #skip this row since we're filtering out training data
          continue
        # remove the .jpeg appended by Inspector on the very end...
        if '.jpeg' in visinspectdata:
          visinspectdata.remove('.jpeg')
        if '.png' in visinspectdata:
          visinspectdata.remove('.png')
        writer.writerow(visinspectdata)
        numrows += 1
      elif showall:
        # handle cases where we found a user-uploaded image, but only if we're dumping all of the user's data
        writer.writerow([row['url'], 'LABELED'])
        numrows += 1
  return numrows


def dumpinspectordata(dsid=None, user="admin", passwd="passw0rd", url="http://ip/powerai-vision", output="out.csv", showall=False):
  # set up the auth token
  setupAPIAccess(url, user, passwd)

  # get list of all dataset
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
      file['datasetid'] = dataset['_id']
      file['datasetname'] = dataset['name']
      file['owner'] = dataset['owner']
      file['url'] = url + "/" + "#/datasets/" + dataset['_id'] + "/label?imageId=" + file['_id']
    # append this into the master list for csv processing...
    files.extend(dsfiles)

  # parse files and save user metadata to the file
  json = saveMetadata(files, output, showall)

  # output our CSV for additional parsing
  rowswritten = generateCSV(output, files, showall)
  logging.info("Wrote %d rows to %s. We filtered out %d items." % (rowswritten, output, len(files) - rowswritten))


if __name__ == '__main__':
  args = getInputs()
  loglevel = logging.DEBUG if args.debug else logging.INFO
  logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                      datefmt='%H:%M:%S',
                      level=loglevel)
  
  if args is not None:
    dumpinspectordata(dsid=args.dsid, user=args.user, passwd=args.passwd, url=args.url, output=args.output, showall=args.showall)
  else:
    exit(1)