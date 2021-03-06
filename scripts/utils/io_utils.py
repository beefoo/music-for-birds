# -*- coding: utf-8 -*-

import csv
import glob
import json
import os

def parseHeadings(arr, headings):
    newArr = []
    headingKeys = [key for key in headings]
    for i, item in enumerate(arr):
        newItem = {}
        for key in item:
            if key in headingKeys:
                newItem[headings[key]] = item[key]
        newArr.append(newItem)
    return newArr

def parseNumber(string):
    try:
        num = float(string)
        if "." not in string and "e" not in string:
            num = int(string)
        return num
    except ValueError:
        # print("Value error: %s" % string)
        return string

def parseNumbers(arr):
    for i, item in enumerate(arr):
        for key in item:
            arr[i][key] = parseNumber(item[key])
    return arr

def readFiles(inputString, dirString=""):
    fileGroups = inputString.split(",")
    files = []
    for group in fileGroups:
        if "*" in group:
            files += glob.glob(group)
        elif ".csv" in group:
            files += readCsv(group)
        elif ".json" in group:
            with open(group) as f:
                files += [dirString % fn for fn in json.load(f)]
    return (fileGroups, files)

def readCsv(filename, headings=False, doParseNumbers=True):
    rows = []
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            lines = [line for line in f if not line.startswith("#")]
            reader = csv.DictReader(lines, skipinitialspace=True)
            rows = list(reader)
            if headings:
                rows = parseHeadings(rows, headings)
            if doParseNumbers:
                rows = parseNumbers(rows)
    return rows
