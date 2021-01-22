#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import os
from dateutil.parser import parse
from datetime import date, timedelta
import numpy as np
from dateutil.parser import parse
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

"""
Function to download a single required file on a date requested by users
@param doc_type
@param date_request
@param url
"""
def download(doc_type, date_request, url):
    file_name = get_file_name(date_request, doc_type)
    # Not download again if the file already exists
    if os.path.exists(filename):
        return ("Failed: " + str(filename) + " already exists! Remove the file or download another file")

    # Download the file from URL and save it in `filename`
    # Case 1: zip file
    if doc_type[-3:]=='zip':
        r = requests.get(url, stream=True)
        if r.ok != True:
            raise Exception("Failed: to download {}, {}: {}".format(filename, r.status_code, r.reason))
            
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=128):
                f.write(chunk)
                
    # Case 2: not zip file
    else:
        r = requests.get(url)
        if r.ok != True:
            raise Exception("Failed to download {}, {}: {}".format(filename, r.status_code, r.reason))
        
        with open(filename, 'w', encoding = 'utf-8') as f:
            f.write(r.text.replace("\r\n","\n"))

    return ("Success: "+ str(filename) + " downloaded!")

# xpath to the report type drop down
report_type_xpath = '/html/body/div[1]/main/div[1]/article/template-base/div/div/section[1]/div/sgx-widgets-wrapper/widget-research-and-reports-download[1]/widget-reports-derivatives-tick-and-trade-cancellation/div/sgx-input-select[1]/label/span[2]'
# xpath to the report date drop down
report_date_xpath = "/html/body/div[1]/main/div[1]/article/template-base/div/div/section[1]/div/sgx-widgets-wrapper/widget-research-and-reports-download[1]/widget-reports-derivatives-tick-and-trade-cancellation/div/sgx-input-select[2]/label/span[2]"
# xpath to the download button
download_button_xpath = "/html/body/div[1]/main/div[1]/article/template-base/div/div/section[1]/div/sgx-widgets-wrapper/widget-research-and-reports-download[1]/widget-reports-derivatives-tick-and-trade-cancellation/div/button"
# url of the data source
url = 'https://www.sgx.com/research-education/derivatives'
# close if there is any open browser
os.system("pkill chrome")
    
options = Options()
# use headless mode for better automation
options.headless = True
driver = webdriver.Chrome(options = options)

driver.get(url)

"""
Function to download the file by selenium if download by GET request does not work
@param driver: the webdriver to download
@param date_request
@param doc_type
@param logger
"""
def selenium_downloader(driver, date_request, doc_type, logger):
    # get the element
    report_type = driver.find_element_by_xpath(report_type_xpath)
    report_date = driver.find_element_by_xpath(report_date_xpath)
    download_button = driver.find_element_by_xpath(download_button_xpath)
    
    # if the element cannot be clicked on, chain the click so that the dropdown is activated
    try:
        report_type.click()
    except ElementClickInterceptedException:
        webdriver.ActionChains(driver).move_to_element(report_type).click(report_type).perform()

    # pick the doc type that is requested
    pick = None
    for i in opt:
        if i.text == doc_type:
            i.click()
            break
       
    # raise exception if the doc type is not offered
    if pick == None:
        raise Exception("No such document type")
    
    # if the element cannot be clicked on, chain the click so that the dropdown is activated
    try:
        report_date.click()
    except ElementClickInterceptedException:
        webdriver.ActionChains(driver).move_to_element(report_date).click(report_date).perform()
    
    # pick the date that is requested
    pick = None
    for i in opt:
        try:
            parse(i.text).date() == date
            i.click()
        except ParserError:
            pass
        
    # raise exception if the date is not within 5 days of the last working day when the data is offered
    if pick == None:
        raise Exception("The date is not within 5 days of the last working day, so cannot be downloaded by Selenium")
        
    # Click download
    download_button.click()
    
    filename = get_file_name(date_request, doc_type)
    if os.path.exists(filename):
        return ("[Selenium] Success: " + str(filename) + " downloaded")
    else:
        raise Exception(f"[Selenium] Failed: to download {filename}")

"""
Helper function to create the file name based on the format of the files on the website
"""
def get_file_name(date_request, doc_type):
    month = str(date_request.month)
    day = str(date_request.day)
    if len(month) < 2:
        month = "0"+month
    if len(day) < 2:
        day = "0"+day
        
    if doc_type in ["TickData_structure.dat", "TC_structure.dat"]:
        filename = doc_type
    elif doc_type[-3:]=='zip':
        filename = doc_type[:-4] + "-" + str(date_request.year) + month + day + doc_type[-4:]
    else:
        filename = doc_type[:-4] + "_" + str(date_request.year) + month + day + doc_type[-4:]
        
    return filename


# In[2]:


"""A single run with log that download 4 required files in a date
@param date
@param logger
"""
data_type = ["TC.txt", "WEBPXTICK_DT.zip", "TickData_structure.dat", "TC_structure.dat"]
def run(date, logger):
    
    try:    
        logger.debug("Check date validity")
        _date = getDate(date)
        logger.debug("Valid date")
    
        logger.debug("Get the key for downloading data")
        key = getKey(_date)
        logger.debug("Valid key")
        
        logger.debug("Getting data")
        for _data in data_type:
            logger.debug("Obtaining url for {} file".format(_data))
            url = getUrl(_data, key)
    
            logger.debug("Downloading")
            trial = 1
            # Attempt to download 3 times if failed before going to other downloads
            while trial <= 3:
                try:
                    logger.info(download(_data, _date, url))
                    break
                except Exception as e:
                    logger.debug(e)
                    logger.debug('Attempt to download again, trial number: ' + str(trial))
                    trial += 1
                    if trial == 4:
                        logger.error(e)
                        # Return the date that failed to download
                        return date
    
    except Exception as e:
        logger.error(e)


# In[3]:


"""
Helper method to concat the url for each type of doc with given key
@param doc_type
@param key
"""
def getUrl(doc_type, key):
    return "https://links.sgx.com/1.0.0/derivatives-historical/"+str(key)+"/"+str(doc_type)


# In[4]:


"""
Helper method to parse the date from user input
@param date_request
"""
def getDate(date_request):
    # Check date format validity: yy/mm/dd
    date_formated = parse(date_request, fuzzy = True).date()
        
    
    # Check if date is in the future
    if (date_formated - date.today()).days > 0:
        #Raise error
        raise Exception("There has not been report for this day yet")
    
    # Check if it is weekend
    if date_formated.isoweekday() == 7 or date_formated.isoweekday() == 6:
        # Raise error
        raise Exception("There is no report on the weekends")
    
    return date_formated

"""
Helper method to calculate the key correspond to the date needs getting data
"""
def getKey(date_request):
    # Milstone to calculate distance
    date_milestone = date(2020, 8, 27)
    key_milestone = 4710
    
    # Calculate key
    key = key_milestone + np.busday_count(date_milestone, date_request)
    if key < 0:
        raise Exception("There was no report on SGX back then on this day")
    
    return key


# In[5]:


"""
Helper generator to generate list of dates between 2 dates"""
def date_range(d1, d2):
    for n in range(int ((d2 - d1).days)+1):
        yield d1 + timedelta(n)


# In[6]:


import argparse
import configparser

parser = argparse.ArgumentParser(description="Download data from https://www.sgx.com/research-education/derivatives")

parser.add_argument('--date', type=str, default=date.today, help='Date of the request document (yy/mm/dd)')
parser.add_argument('--automate', type=int, default = 0, help='Run automatically download all files from the specified date until interupted. Default set to 0, set to 1 or other number to run automatically')

args = parser.parse_args()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

fmt = logging.Formatter('%(asctime)s: %(message)s', '%m/%d/%Y %I:%M:%S %p')

# Console log
console = logging.StreamHandler()
console.setFormatter(fmt)
console.setLevel(logging.DEBUG)
logger.addHandler(console)

# All log file
log = logging.FileHandler("log.log")
log.setFormatter(fmt)
log.setLevel(logging.DEBUG)
logger.addHandler(log)

# Download history file
history = logging.FileHandler("history.log")
history.setFormatter(fmt)
history.setLevel(logging.INFO)
logger.addHandler(history)

logger.debug("""User input:
1. Date: {}
2. Config file: {}
3. Automate: {}""".format(args.date, args.automate))

# Single download
if args.automate == 0:
    if run(args.date, logger) != None:
        for doc in data_type:
            try:
                selenium_downloader(driver, args.date, doc, logger)
            except Exception as e:
                logger.info(e)
                continue

# Automatic download
else:
    # Set of dates that failed to download data
    failed = set()
    
    # Download data up to "today" if the date request by user is before today
    try:
        date_formated = parse(args.date, fuzzy = True).date()
        for i in date_range(date_formated, date.today()):
            logger.debug("Download data for the date {}".format(str(i)))
            failed.add(run(str(i), logger))
            failed.discard(None)
        
        logger.debug("Going to sleep and wait until the next day")
        # 24 hours
        time.sleep(86400)
    except Exception as e:
        logger.debug(e)
        
    # Download data daily
    while True:
        logger.debug("Download data for the date {}".format(str(date.today())))
        failed_date = run(str(date.today())
        if failed_date != None:
            fail_count = 0
            for doc in data_type:
                try:
                    selenium_downloader(driver, args.date, doc, logger)
                except Exception as e:
                    fail_count += 1
                    logger.info(e)
                    continue
            if fail_count > 0:
                failed.add(failed_date, logger))
        
        # Retry getting failed download files everyday
        while len(failed) != 0:
            re_download = failed.pop()
            logger.debug("Re-download data for the date {}".format(str(re_download)))
            failed.add(run(str(re_download), logger))
            failed.discard(None)
        
        logger.debug("Going to sleep and wait until the next day")
        time.sleep(86400)


# In[ ]:




