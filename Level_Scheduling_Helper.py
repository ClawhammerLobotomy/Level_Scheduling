from plex_login_ux import Plex
import ux_data_source_tools as UDST
from requests import auth
# from requests import auth
from requests.auth import HTTPBasicAuth
from selenium.common.exceptions import (NoSuchElementException, 
                                        JavascriptException)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# import timeit
import sys
import csv
from pathlib import Path

from datetime import datetime, timedelta, date
import time

# import re

from tkinter import * # pylint: disable=unused-wildcard-import
from PIL import ImageTk, Image
from tkinter import filedialog, Tk, Label, Button, LabelFrame, Entry, ttk
from tkinter.messagebox import CANCEL, OK, askokcancel, askyesno, showinfo

import webbrowser
import os
import threading
import __main__

from selenium.webdriver.support.ui import Select


from threading import Thread
from itertools import groupby
from pprint import pprint
from collections import defaultdict

# Customer Releases Get
import operator

import configparser


import zipfile
import requests
# from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.util.retry import Retry

from shutil import copyfile


# Newly added imports for API
from collections import OrderedDict
import json
import pandas as pd
import numpy as np
from pandas import json_normalize 
from concurrent.futures import ThreadPoolExecutor, as_completed

__author__ = 'Dan Sleeman'
__copyright__ = 'Copyright 2020, Level Scheduling Assistant'
__credits__ = ['Dan Sleeman']
__license__ = 'GPL-3'
__version__ = '2.3.7'
__maintainer__ = 'Dan Sleeman'
__email__ = 'sleemand@shapecorp.com'
__status__ = 'Production'

# 9/23/2020 Fixed issue where forecasts weren't being removed from the list.
# 10/5/2020 Fixed issue where zero quantity releases wouldn't be considered 
#           properly to close forecasts during the same week.
# 10/9/2020 1.3 will be adding download for customer releases.
# 11/2/2020 Added the downloaded files into a specific directory to avoid  
#           issues with Excel workbook changes.
# 4/28/2021 Modified customer release download to account for extra column
#           in the CST PCN.
# 4/30/2021 Added check to release date in event that it is blank
#           Sets the release date to 01/01/90.
# 5/20/2021 Updated check for column positions which will work for any PCN.
# 5/20/2021 Fixed issue with Customer Release Get which would skip everything
#           if Chrome was minimized.
# 5/20/2021 Added top level variables that can be modified to easily switch PCN.
# 5/21/2021 Updated Release creation function to remove clicks and key sending.
#           This is required so the user can minimuze the Chrome window
# 5/24/2021 Added dropdown picker for PCN that you would working in.
#           Set up company code and PCN to be saved after selected.
#           Removed help buttons due to lack of use and maintenance with their
#           rapidly changing nature.
# 6/2/2021 Fixed issue with get_inventory function when the part detail update
#           permision is removed from a user.
# 6/15/2021 Fixed issue with get_releases function which was causing it to skip
#           all parts
# 6/15/2021 Fixed issue with missing config file on startup. Program will now
#           create the file on first run if missing.
# 6/28/2021 Changed release creation to remove the step of keeping the existing
#           forecast releases. This was causing large forecasts to remain in 
#           the system which messes with releases to the supplier.
# 7/7/2021 Rewrote the inventory get function to also grab subcontract inventory
#          This replaces the current inventory download
#          The part list file can be only part number + revision instead of
#           requiring the part key
# 7/7/2021 Removed Quit button
#          This was just causing unnecessary confusion and the X works to close.
# 7/27/2021 Set up version check against github file and notify user if there
#           is a new version to download
# 7/27/2021 Fixed issue with downloading inventory with the new subcontract
#           inventory process if a part did not have any inventory
# 7/27/2021 Added initialization for Excel file sources if missing.
# 8/6/2021 Fixed issue where the mrp excluded locations were being used for 
#           inventory download numbers
# 8/6/2021 Fixed issue with download going into the current directory rather 
#           than parent
# 8/11/2021 Fixed issue with github connection refusing.
# 8/17/2021 Changed the processes to headless instances.
#            This should eliminate the possibility of influencing the process
# 8/17/2021 Removed Github connections
# 8/17/2021 Moved 'source' files to an H drive location in order to avoid
#               using Github
# 2.0.0
# 8/17/2021 Inventory Download and Customer Release Download updated to API
# 8/20/2021 Added backwards compatibility to use Selenium if the data source
#           was not configured for a PCN
# 8/20/2021 Added MRP Demand download function for JNI file
# 8/20/2021 Changed the way the GUI tabs were getting created slightly
# 2.0.1
# 8/26/2021 Added check if the file is open when the API downloads are trying
#           to write to the files.
# 8/27/2021 Removed the averaging within the tool.
# 2.1.0
# 8/30/2021 Changed Inventory, Customer Releases, and MRP download functions
#           to use threaded requests to speed up operation.
#           Improved performance from around 10 minutes to less than 1 minute.
# 2.1.1
# 9/7/2021  Added functionality to set the release status based on the input
#           file.
# 9/7/2021  Added config option to decide if a PCN would use MRP
#           recommendations.
# 2.1.2
# 9/8/2021  Update the inventory download to include the zero inventory parts
#           if they are in the source file.
#           This was done in order to make any errors apparent in the workbook
# 9/8/2021  Tweaked the inventory download to only save the files once at the 
#           end instead of for every part.
# 9/13/2021 Added exception handling for API download in event of timeout error
# TODO - Replace Supplier Release upload with data source version
#        Kevin is fine with this not going faster.
#        I think I will try and use the release add/update data source first
#        Then, I'll run a Plex process to generate MRP recommendations after
# 1/17/2022 Changed the customer release download data source to 5565
#           This apparently is just the full customer releases, and I didn't
#           find this when I started looking for data sources.
#           I needed to change some column names, but overall, it behaves the same.
# 1/31/2022 Fixed auto update process
# 2.3.2
# 1/31/2022 Fixed issue where shipped release quantities were not being taken
#           into account for the balances.
#           This version still uses 1 week of daily demand only.
# 4/11/2022 Fixed version for Chrome. Went from 99 to 100 which broke the version check
# 2.3.5
# 7/18/2022 Changed login to IAM process.
# 2.3.6
# 8/16/2022 Adding support for PRP download
# 8/29/2022 Updated all df.append commands with pd.concat([df_1, df_2]) format
# 2.3.7
# 10/31/2022 Updated PRP download to use data source calls


def folder_setup(source_folder):
    """
    Create the base folder if missing.
    """
    if not os.path.exists(source_folder):
        os.makedirs(source_folder)


def file_setup(source_folder, dict, file_name):
    """
    Creates the Excel source files if missing.

    This is needed in order for the Excel workbooks not to break when run.
    """
    for x, y in dict.items():
        file = os.path.join(source_folder, y['prefix']+file_name)
        if not os.path.isfile(file):
            with open(file, 'w+', encoding='utf-8') as outfile:
                if "cust" in file_name:
                    outfile.write('Lookup_Key,Part_No,Week_Index,Release_Date,'
                                  'Quantity')
                else:
                    outfile.write('Part_No,Inventory')


def frozen_check():
    if getattr(sys, 'frozen', False):
    # Running in a bundle
        bundle_dir = sys._MEIPASS # pylint: disable=no-member
    else:
    # Running in a normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__main__.__file__))
    return bundle_dir


global bundle_dir
ux = UDST.UX_Data_Sources() # Static

bundle_dir = frozen_check()
master_file_dir = 'H:\\OP-ShapeGlobal\\0708-IT\\Public\\Level Scheduling\\'\
                  'Source_Files'
pcn_file = Path(os.path.join(bundle_dir,'resources/pcn.json'))

# Local
subcon_location_file_l = Path(os.path.join(bundle_dir,
                             'resources/subcon_locations.csv'))
# Network
subcon_location_file = Path(os.path.join(master_file_dir,
                             'subcon_locations.csv'))
# Local
container_status_file_l = Path(os.path.join(bundle_dir,
                            'resources/container_statuses.csv'))
# Network
container_status_file = Path(os.path.join(master_file_dir,
                            'container_statuses.csv'))
# Local
mrp_location_file_l = Path(os.path.join(bundle_dir,
                            'resources/mrp_locations.csv'))
# Network
mrp_location_file = Path(os.path.join(master_file_dir,
                            'mrp_locations.csv'))
# Local config file
pcn_config_file_l = Path(os.path.join(bundle_dir,
                            'resources/pcn_config.json'))
# Network config file
pcn_config_file = Path(os.path.join(master_file_dir,
                            'pcn_config.json'))

# try:
if not Path(master_file_dir).is_dir():
# except FileNotFoundError:
    container_status_file = container_status_file_l
    mrp_location_file = mrp_location_file_l
    pcn_config_file = pcn_config_file_l
    subcon_location_file = subcon_location_file_l



container_statuses = []
mrp_excluded_locations = []
launch_pcn_dict = {}
mrp_locations = []
subcon_locations = []

r = container_status_file.read_text()
container_statuses = r.split('\n')

r = mrp_location_file.read_text()
mrp_excluded_locations = r.split('\n')
mrp_locations = r.split('\n')

r = subcon_location_file.read_text()
subcon_locations = r.split('\n')

with open(pcn_config_file, 'r', encoding='utf-8') as c:
    launch_pcn_dict = json.load(c)


source_dir = 'C:\\Level Sched INV'
# Default variables
home_pcn = '79870'
file_prefix = ''

folder_setup(source_dir)

root = Tk()
root.title('Level Scheduling Helper')
root.iconbitmap(os.path.join(bundle_dir,'resources/Shape.ico'))
script_name = os.path.splitext(os.path.basename(__file__))[0]


try:
    latest_version = Path(os.path.join(master_file_dir,
                          'prod_version.txt')).read_text()
    print("Latest production version of the helper tool:", latest_version)
    print(f"You are running {__status__} version {__version__}")
    update = 1
except FileNotFoundError:
    print('Error getting version info.')
    print('If you are connected to the VPN already, please open the H: drive'
          ,'folder and re-launch this app to get the latest source data.')
    latest_version = __version__
    update = 0


def version_check():
    """
    Checks current version against a file on the H: drive.

    If the latest version is greater than current version, download 
    and extract the new version.
    """
    if latest_version > __version__:
        # print(os.getcwd())
        dl_path = Path(os.getcwd()).parent.absolute()
        # print(dl_path.parent.absolute())
        print(dl_path)
        src = 'H:/OP-ShapeGlobal/0708-IT/Public/Level Scheduling'\
            '/Level_Scheduling_Helper_' + latest_version + \
            '_Portable.zip'
        dst = str(dl_path) + '/Level_Scheduling_Helper_' + latest_version + \
            '_Portable.zip'
        latest_file = Path(dst)
        latest_path = Path(str(dl_path) + '/Level_Scheduling_Helper_'
                                    + latest_version + '_Portable')
        # print(latest_file.is_file())
        if not latest_file.is_file() or not latest_path.is_dir():
            try:
                copyfile(src, dst)
                with zipfile.ZipFile(dst, 'r') as zip_ref:
                    zip_ref.extractall(str(dl_path) + '/Level_Scheduling_Helper_'
                                    + latest_version + '_Portable')
                showinfo('Update Available',f'There is a new version of the level'
                    f' scheduling tool.\n'
                    f'Your version \t{__version__}\n'
                    f'Latest version \t{latest_version}\n'
                    f'Please use the new version located here:\n'
                    + str(dl_path) + '\Level_Scheduling_Helper_'
                    + latest_version + '_Portable')
            except FileNotFoundError:
                showinfo(f'Update Error', 'Your helper tool does not match'
                f' the latest version.\n\n'
                f'Your version \t{__version__}\n'
                f'Latest version \t{latest_version}\n\n'
                f'Unable to find the latest version on the H: drive.\n\n'
                f'Contact {__maintainer__} at {__email__} for assistance.')
        else:
            showinfo('Update Available',f'There is a new version of the level'
                    f' scheduling tool.\n'
                    f'Your version \t{__version__}\n'
                    f'Latest version \t{latest_version}\n'
                    f'Please use the new version located here:\n'
                    + str(dl_path) + '\Level_Scheduling_Helper_'
                    + latest_version + '_Portable')

# latest_version = "1.6.5"
if not __status__ == "Production" and latest_version >= __version__ and update ==1:
    askyesno('Update Available', f'You are using a beta version.'
    f'There is a new version available to download.\n'
    f'Would you like to download the latest version?')
    if YES:
        version_check()
if __status__ == "Production" and latest_version >= __version__ and update ==1:
    version_check()


# Color variables
shapeorange     = "#F37521"
shapeorange2    = "#DA691D"
shapeorange3    = "#F48237"
shapeorange4    = "#F69E63"
mywhite         = "#FFFFFF"
mywhite2        = "#E5E5E5"
mygray          = "#F1F1F1"
myblack         = "#000000"
mygraylight     = "#F8F8F8"
mygraydark      = "#9A9A9A"
shapenavy       = "#17242D"
plexdarkblue    = "#153C55"
plexlightblue   = "#61A9D5"

selector_text = "Press Browse to Select a File..."
pcn_error_text = "This PCN is not yet configured for this fucntion."
login_error_text = "Please enter login details before continuing."

# Shape theme creation
style = ttk.Style()
style.theme_create("shape", parent="alt", settings={
    "TNotebook": {
        "configure": {
            "tabmargins":[0, 0, 0, 0],
            "background":mygray,
            "borderwidth": 0}
        },
    "TNotebook.Tab":{
        "configure": {"padding": [5, 1],
                      "background": mygray,
                      "foreground": mygraydark,
                      "borderwidth": 0,
                      "tabmargins": [2,2,2,2]},
        "map":       {"background":[("selected", shapeorange),
                                    ("active", shapeorange4)],
                      "foreground":[("selected", mywhite),
                                    ("active", mygray)]}
        },
    "TButton":{
        "configure":{"background": shapeorange,
                     "foreground": mywhite,
                     "padding": [8,1,8,1],
                     "focuscolor": shapeorange},
        "map":{"background":[("disabled", mygray),
                             ("pressed" , shapeorange),
                             ("active"  , shapeorange4)],
               "foreground":[("disabled", mygraydark),
                             ("active"  , mygray)],
               "focuscolor":[("disabled", mygray),
                             ("pressed" , shapeorange),
                             ("active"  , shapeorange4)]}
        },
    "TMenubutton":{
        "configure":{
            "padding": 1,
            "arrowcolor": mywhite,
            "background": shapeorange,
            "foreground": mywhite
        }
    },
    "TRadiobutton":{
        "configure":{"background": mygray,
            "padding": [7,1],
            "indicatormargin": -10,
            "indicatordiameter": -1,
            "focuscolor": mygray,
            "anchor": CENTER,
            "foreground": mygraydark},
        "map":{
            "background":[("disabled", mygray),
                          ("selected" , shapeorange),
                          ("active"  , shapeorange4)],
            "foreground":[("disabled", mygraydark),
                          ("active"  , mygray),
                          ("selected", mywhite)],
            "focuscolor":[("disabled", mygray),
                          ("selected" , shapeorange),
                          ("active"  , shapeorange4)]
            }
        }
    }
)

style.theme_use("shape")



file_setup(source_dir, launch_pcn_dict, 'inventory.csv')
file_setup(source_dir, launch_pcn_dict, 'subcon_inventory.csv')
file_setup(source_dir, launch_pcn_dict, 'cust_releases.csv')
file_setup(source_dir, launch_pcn_dict, 'mrp_demand.csv')


def import_part_list(input_file):
    """
    Creates a list of part numbers given a csv file.
    
    This is compatible with the old part+key file 
    as well as the newer part only file.
    
    The API only requires a base part number
    so this will strip and consolidate into a unique list to avoid double
    quantities.
    """
    temp_list = []
    with open(input_file) as file:
        for i, line in enumerate(file):
            # print(i,line)
            if i == 0:
                continue
            line = line.strip() #preprocess line
            line = line.split(',')[0]
            line = line.split('-')
            line = line[0]
            temp_list.append(line)
    # print(temp_list)
    # print(len(temp_list))
    # Remove any duplicates
    part_list = list(OrderedDict.fromkeys(temp_list))
    # print(part_list)
    # print(len(part_list))
    return part_list


def help_file(event):
    if event.widget is help_icon:
        showinfo('About',f'Level Scheduling Helper Tool Version {__version__}\n'
                 f'For issues, contact {__maintainer__} - {__email__}')


def get_auth(home_pcn):
    """
    Creates a basic authentication string for use with Plex data source calls.
    """
    username = launch_pcn_dict[home_pcn]['api_user']
    password = launch_pcn_dict[home_pcn]['api_pass']
    authentication = HTTPBasicAuth(username, password)
    # print(authentication)
    return authentication


def weeks_for_year(year):
    """
    Used in the customer release download function to 
    get the last week in a year.
    """
    last_week = date(year, 12, 28)
    return last_week.isocalendar()[1]


def create_inv_json(part_no):
    """
    Creates the json for the threaded requests
    """
    form_data = {
    'inputs':{
        'Include_Containers': True,
        'Part_No': part_no
        }
    }
    return form_data


def create_cust_json(part_no):
    """
    Creates the json for the threaded requests
    """
    form_data = {
            'inputs':{
                'Part_No': part_no
                }
            }
    return form_data


def create_mrp_json(part_no):
    """
    Creates the json for the threaded requests
    """
    form_data = {
        'inputs':{
            "Part_No": part_no,
            # "Finished_Part_Key": finished_key,
            "Forecast_Window": 6
            }
        }
    return form_data


def create_json(*args):
    # print(args)
    return {'inputs': dict(args)}


def create_prp_json(part_no, end_date):
    """
    Creates the json for the threaded requests
    api_id  = '15851'
    query = (
        ('Part_Key', '3550251'), # 246807-22
        ('From_PRP', True),
        ('Begin_Date','2001-10-01T04:00:00.000Z'),
        ('End_Date','2022-12-10T04:00:00.000Z')
    )
    """
    form_data = {
        'inputs':{
            "Part_No": part_no,
            "From_PRP": True,
            "Begin_Date": '2001-10-01T04:00:00.000Z',
            'End_Date': end_date}
        }
    return form_data


def post_url(args):
    """
    Function used to thread requests.
    """
    while True:
        attempts = 0
        try:
            request = requests.post(args[0], json=args[1], auth=args[2])
            break
        except:
            print(f'Timeout for {args[1]}, trying again.')
            time.sleep(1)
            attempts +=1
            if attempts >= 10:
                print(f'too many timeouts for {args[1]}, going to next part.')
                break
            continue
    return request


def releases(user_name, password, company_code, db, home_pcn, input_file):
    """
    Selenium based function to create supplier releases.
    """
    if user_name == '' or password == '' or company_code == '':
        status.config(text=login_error_text)
        tab_control.select(0)
    else:
        # Initialize the user account to be used for login
        pcn = launch_pcn_dict[home_pcn]["pcn"]
        file_prefix = launch_pcn_dict[home_pcn]["prefix"]
        plex = Plex('classic', user_name, password, company_code, pcn, db=db,
                    use_config=False, pcn_path=pcn_file, legacy_login=0)
        # Get the directory that script is running in
        plex.frozen_check()
        # bundle_dir = plex.frozen_check()


        # Main function which performs all the Plex manipulation
        def do_release_update():
            # ======Start of required code======#
            # Call the chrome driver download function
            plex.download_chrome_driver()
            # Call the config function to initialize the file and set variables
            plex.config()
            # Call the login function and return the chromedriver instance 
            #   and base URL used in the rest of the script
            try:
                driver, url_comb, url_token = plex.login(headless=1)
                url_token = url_token
            except SystemExit:
                status.config(text="Username, Password, or "
                              "Company code incorrect."
                              " Please verify and try again.")
                tab_control.select(0)
                plex.driver.quit()
                return
            # ======End of required code======#
            file = input_file
            total_lines = len(open(input_file).readlines()) - 1
            part_po_grouping = defaultdict(list)
            # 1. Group the CSV into lists based on PO and part combination
            #    Will group the file into arrays based on the first X columns.
            with open(file, 'r', encoding="utf-8") as fin:
                csv_reader = csv.reader(fin, delimiter=',')
                for i, row in enumerate(csv_reader):
                    if i == 0:
                        column_dict = {}
                        for x, i in enumerate(row):
                            column_dict[i] = x
                            print(x, i)
                        print(column_dict)
                    else:
                        part_po_grouping[row[0], row[1], row[2], row[3],
                                        row[4], row[5], row[6]].append(row[7:])
                print(part_po_grouping)
                # 2. For each group, go to the PO line and perform actions
                for j, line in enumerate(part_po_grouping):
                    # print(line[0], line[1], line[2], line[3], line[4])
                    # pprint(part_po_grouping[line])
                    print(line)
                    date_qty_set = []
                    for x in part_po_grouping[line]:
                        date_qty_set.append(x[0:2])
                        part_no = x[3]
                    pcn_no = line[0] # pylint: disable=unused-variable
                    po_key = line[1]
                    line_key = line[2]
                    line_no = line[3]
                    supplier_no = line[4]
                    part_key = line[5]
                    op_key = line[6] # pylint: disable=unused-variable
                    if {"Release_Status"} <= column_dict.keys():
                        x = column_dict["Release_Status"]
                        release_status = part_po_grouping[x]
                        print(release_status)
                    # pprint(date_qty_set)
                    num_parts = len(part_po_grouping)
                    try:
                        status.config(text=f"Updating part {part_no}.    "
                                           f"[{j + 1}/{num_parts}]")
                    except RuntimeError:
                        driver.quit()
                    driver.get(f'{url_comb}/Purchasing/Line_Item_Form.asp?'
                            f'CameFrom=PO%2Easp'
                            f'&Supplier_No={supplier_no}'
                            f'&Do=Update&PO_Key={po_key}'
                            f'&Line_Item_Key={line_key}'
                            f'&Line_Item_No={line_no}'
                            f'&Print_Button_Pressed=False&ssAction=Same')
                    # time.sleep(10000)
                    # 3a. Get list of release quantities
                    script = """
                    a =[]
                    var qty = document.querySelectorAll(
                                                'input[id^="txttxtQuantity"]');
                    for (var i=0,max=qty.length; i<max;i++){
                        if(qty[i].value)
                            a.push(qty[i].value.replace(',',''))
                    }
                    return a
                    """
                    rel_qty = driver.execute_script(script)
                    # print(rel_qty)

                    # 3b. Get a list of all release dates
                    script = """
                    b =[]
                    var dates = document.querySelectorAll(
                                                   'input[id^="txtDue_Date"]');
                    for (var i=0,max=dates.length; i<max;i++){
                        if(dates[i].value)
                            b.push(dates[i].value)
                    }
                    return b
                    """
                    rel_date = driver.execute_script(script)
                    # print(rel_date)

                    # 3c. Get a list of all release statuses
                    script = """
                        a =[]
                    var qty = document.querySelectorAll(
                                                'input[id^="txttxtQuantity"]');
                    for (var i=0,max=qty.length; i<max;i++){
                        if(qty[i].value)
                            a.push(qty[i].value)
                    }
                    c =[]
                    var rel_status = document.querySelectorAll(
                                            'select[id^="lstRelease_Status"]');
                    for (var i=0,max=rel_status.length; i<max;i++){
                        if(rel_status[i].value && a[i])
                                //need to check against the quantity value
                                //to make the array length even
                            c.push(rel_status[i].value)
                    }
                    return c
                    """
                    rel_status = driver.execute_script(script)
                    # print(rel_status)

                    # 3d. Zip ABC arrays into list for comparison
                    release_list = [list(a) for a in zip(rel_date, rel_qty,
                                                         rel_status)]
                    # print('Current Releases')
                    # pprint(release_list)
                    # print('')
                    # time.sleep(100000)
                    # 4. Separate out forecast releases
                    forecasts =[line for i, line in enumerate(release_list)
                                if 'Forecast' in line]
                    # print('Old Forecasts')
                    # pprint(forecasts)
                    cut_index = 0
                    for i, line in enumerate(forecasts):
                        # 5. Compare forecasts with date_qty_set
                        for j, x in enumerate(date_qty_set): # pylint: disable=unused-variable
                            # print('Forecast to compare')
                            # print(line)
                            # print('Firm to compare')
                            # print(x)
                            if datetime.strptime(line[0], '%m/%d/%y') <=\
                                    datetime.strptime(x[0], '%m/%d/%Y'):
                                # print(line[0], '<=', x[0])
                                # 6. Remove forecasts if they are before any
                                #    date in the csv list
                                cut_index += 1
                                # new_forecasts = forecasts[i+1:]
                                # forecasts = forecasts[i+1:]
                                break
                            # else:
                            #     new_forecasts = forecasts
                    new_forecasts = forecasts[cut_index:]
                    # print('New forecast Releases')
                    # pprint(new_forecasts)
                    # print('New original forecasts')
                    # pprint(forecasts)
                    # time.sleep(100000)
                    # 7. Clear all release info for forecast releases
                    # 7a. Change status to firm
                    script = """
                    a =[]
                    var qty = document.querySelectorAll(
                                                'input[id^="txttxtQuantity"]');
                    for (var i=0,max=qty.length; i<max;i++){
                        if(qty[i].value)
                            a.push(qty[i].value)
                    }
                    b =[]
                    var dates = document.querySelectorAll(
                                                   'input[id^="txtDue_Date"]');
                    for (var i=0,max=dates.length; i<max;i++){
                        if(dates[i].value)
                            b.push(dates[i].value)
                    var rel_status = document.querySelectorAll(
                                            'select[id^="lstRelease_Status"]');
                    for (var i=0,max=rel_status.length; i<max;i++){
                        //if(rel_status[i].value == 'Forecast'){
                            rel_status[i].value = 'Firm'
                            qty[i].value = ''
                            dates[i].value = ''}
                    //}
                    }"""
                    driver.execute_script(script)
                    # 8. Close partial releases.
                    script = """
                    var u = []
                    var rcv_qty = document.querySelectorAll(
                                                'span[id="Receipt_Quantity"]');
                    var qty = document.querySelectorAll(
                                                'input[id^="txttxtQuantity"]');
                    var rel_status = document.querySelectorAll(
                                            'select[id^="lstRelease_Status"]');
                    for (var i=0,max=rcv_qty.length; i<max;i++){
                        if(rcv_qty[i].innerText != "0"){
                            qty[i].value = parseInt(
                                        rcv_qty[i].innerText.replace(",", ""))
                            qty[i].onblur()
                            rel_status[i].value = "Received"
                            u.push(qty[i].value)
                            }
                        }
                    return u.length
                    """
                    partials = driver.execute_script(script)
                    # time.sleep(100000)
                    partials += 0
                    rel_index = 0
                    # 9. Update releases using CSV data
                    # if the release quantity is 0, then skip it.
                    # for some reason, Plex stores 0 qty releases.
                    for i, release in enumerate(date_qty_set):
                        if release[1] == '0':
                            continue
                        # print(i, partials, release[1], release[0])
                        # time.sleep(10000)
                        script = """
                        var qty = document.querySelectorAll(
                                                'input[id^="txttxtQuantity"]');
                        var dates = document.querySelectorAll(
                                                   'input[id^="txtDue_Date"]');
                        qty[{i}+{partials}].value = {new_qty}
                        dates[{i}+{partials}].value = "{new_date}"
                        """.format(i=rel_index, partials=partials, 
                                   new_qty=release[1],
                                   new_date=release[0])
                        driver.execute_script(script)
                        rel_index += 1
                    # time.sleep(10000)
                    # 6/28/21
                    # No longer keeping existing forecast releases
                    # # 10. find the last empty release line
                    # status_index = driver.find_elements_by_xpath(
                    #                     '//select[starts-with(@id, '
                    #                     '"lstRelease_Status")]')
                    # qtys = driver.find_elements_by_xpath(
                    #                         '//input[starts-with(@id, '
                    #                         '"txttxtQuantity")]')
                    # full_qty = [rel.get_attribute('value') for i, rel in 
                    #             enumerate(qtys)]
                    # empty_rel = [rel for i, rel in enumerate(qtys)
                    #             if rel.get_attribute('value') == '']
                    # status_qty = [list(a) for a in zip(status_index, full_qty)]
                    # # pprint(status_qty)
                    # forecast_index = [i for i, rel in enumerate(status_qty)
                    #                 if rel[1] == '']
                    # # pprint(forecast_index)
                    # # 11. Start populating the forecast release data using
                    # for i, rel in enumerate(empty_rel):
                    #     if i < len(new_forecasts):
                    #         script = """
                    #             var qty = document.querySelectorAll(
                    #                             'input[id^="txttxtQuantity"]');
                    #             var dates = document.querySelectorAll(
                    #                                'input[id^="txtDue_Date"]');
                    #             var stat = document.querySelectorAll(
                    #                         'select[id^="lstRelease_Status"]');
                    #             qty[{x}].value = {new_qty}
                    #             dates[{x}].value = "{new_date}"
                    #             stat[{x}].value = "Forecast"
                    #             """.format(x=forecast_index[i],
                    #                     new_qty=new_forecasts[i][1],
                    #                     new_date=new_forecasts[i][0])
                    #         driver.execute_script(script)
                    # 12. Add notes for time and date that it was updated
                    qtys = driver.find_elements_by_xpath(
                                            '//input[starts-with(@id, '
                                            '"txttxtQuantity")]')
                    full_qty = [rel for i, rel in enumerate(qtys)
                                if rel.get_attribute('value') != '']
                    notes = driver.find_elements_by_xpath(
                                            '//input[starts-with(@id, '
                                            '"txtRelease_Note")]')
                    full_note = [rel for i, rel in enumerate(notes)]
                    full_note = full_note[:len(full_qty)]
                    now = datetime.now()
                    rel_date = now.strftime("%m/%d/%y %I:%M:%S %p")
                    update_note = f'Updated by {user_name} on {rel_date}'
                    for i, rel in enumerate(full_note):
                        script = """
                        var note = document.querySelectorAll(
                                               'input[id^="txtRelease_Note"]');
                        note[{i}].value = "{update_note}"
                        """.format(i=i, update_note=update_note)
                        driver.execute_script(script)
                    # time.sleep(10000)
                    # 13. Click update button
                    # Changed to JS function to work when minimized
                    driver.execute_script("FormSubmitStart('Update');")
                    # time.sleep(10000)
                    # 14. Go to MRP recommendations
                    driver.get(f'{url_comb}/requirements_planning'
                            f'/Release_Planning_By_Supplier_Schedule_Form.asp'
                            f'?Mode=Part'
                            f'&Part_Key={part_key}')
                    # 15. Get lists of relevant elements on screen
                    # 15a. Get checkboxes
                    script = """
                    // Grab all checkbox elements
                    var check = document.querySelectorAll(
                        'input[id^="chkCreate_Release"]') 

                    // Grab all on order elements
                    var on_order_qty = []
                    var on_order_stat = []
                    // Xpath starts at 1 needs to go 1 longer than array length
                    for(var i=1;i<check.length+1;i++){{
                    var x = document.evaluate(
                        '/html/body/div[1]/form/table/tbody/tr['+i+']/td[3]',
                        document,null,9,null).singleNodeValue.innerText
                    var qty = parseInt(x.split("\\n")[0].replace(",",""))
                    var stat = x.split("\\n")[1]
                    on_order_qty.push(qty)
                    on_order_stat.push(stat)}}

                    // Grab all suggested Order Elements
                    var sug_order_qty = []
                    for(var i=0;i<check.length;i++){{
                    var x = document.querySelectorAll(
                        'input[id^="txtQuantity"]')[i].value
                    sug_order_qty.push(parseInt(x))}}
                    // sug_order_qty

                    // Grab all suggested order status elements
                    var sug_order_stat = []
                    for(var i=0;i<check.length;i++){{
                    var x = document.querySelectorAll(
                        'select[id^="lstRelease_Status"]')[i].value
                    sug_order_stat.push(x)}}
                    // sug_order_stat

                    // Grab all note field elements
                    var note = document.querySelectorAll(
                        'input[id^="txtNote"]')

                    // If order qty!= suggested order qty 
                    // AND statuses are not firm, planned, or partial, 
                    // then check the box and add a note
                    for(var i=0;i<check.length;i++){{
                    if (on_order_stat[i] != "Firm" && 
                        on_order_stat[i] != "Partial" && 
                        sug_order_stat[i] != "Firm" && 
                        sug_order_stat[i] != "Planned" && 
                        on_order_qty[i] != sug_order_qty[i]){{
                    check[i].checked = true
                    note[i].value = "MRP recommendation updated by "+
                                    "{user_name} on {rel_date}"
                    }}}}
                    """.format(user_name=user_name,rel_date=rel_date)
                    driver.execute_script(script)
                    # 16. Create suggested forecast releases.
                    #     (Click create button)
                    # Switched to JS function to work while minimized
                    # time.sleep(10000)
                    driver.execute_script("Create_Releases();")
                    # time.sleep(10000)
            status.config(text=f"Process complete. {total_lines} total "
                               f"releases across {num_parts} part numbers "
                               f"updated.")
            driver.quit()
        # Start in a thread so the GUI doesn't hang.
        # t = threading.Thread(target=do_release_update)
        t = threading.Thread(target=lambda:do_release_update_czech(user_name,
                             password, company_code, db, home_pcn,input_file))
        t.start()
        status.config(text="Updating releases.")
        file_selector.config(text=selector_text, anchor=W)
        button_start.config(state=DISABLED)


def do_release_update_czech(user_name, password, company_code, db, home_pcn,
                            input_file):
    # Initialize the user account to be used for login
    pcn = launch_pcn_dict[home_pcn]["pcn"]
    file_prefix = launch_pcn_dict[home_pcn]["prefix"]
    forecast_update = launch_pcn_dict[home_pcn]["forecast"]
    plex = Plex('classic', user_name, password, company_code, pcn, db=db,
                use_config=False, pcn_path=pcn_file, legacy_login=0)
    # Get the directory that script is running in
    # bundle_dir = plex.frozen_check()
    plex.frozen_check()
    # ======Start of required code======#
    # Call the chrome driver download function
    plex.download_chrome_driver()
    # Call the config function to initialize the file and set variables
    plex.config()
    # Call the login function and return the chromedriver instance 
    #   and base URL used in the rest of the script
    try:
        driver, url_comb, url_token = plex.login(headless=1)
        url_token = url_token
    except SystemExit:
        status.config(text="Username, Password, or "
                        "Company code incorrect."
                        " Please verify and try again.")
        tab_control.select(0)
        plex.driver.quit()
        return
    # ======End of required code======#
    file = input_file
    total_lines = len(open(input_file).readlines()) - 1
    part_po_grouping = defaultdict(list)
    # 1. Group the CSV into lists based on PO and part combination
    #    Will group the file into arrays based on the first X columns.
    with open(file, 'r', encoding="utf-8") as fin:
        csv_reader = csv.reader(fin, delimiter=',')
        for i, row in enumerate(csv_reader):
            if i == 0:
                column_dict = {}
                for x, i in enumerate(row):
                    column_dict[i] = x
                    print(x, i)
                print(column_dict)
            else:
                part_po_grouping[row[0], row[1], row[2], row[3],
                                row[4], row[5], row[6]].append(row[7:])
        print(part_po_grouping)
        # 2. For each group, go to the PO line and perform actions
        for j, line in enumerate(part_po_grouping):
            # print(line[0], line[1], line[2], line[3], line[4])
            # pprint(part_po_grouping[line])
            print(line)
            date_qty_set = []
            for x in part_po_grouping[line]:
                if {"Release_Status"} <= column_dict.keys():
                    release_status = x[7]
                    print(release_status)
                else:
                    release_status = "Firm"
                date_qty_set.append(x[0:2]+[release_status])
                part_no = x[3]
                
                # date_qty_set.insert(-1,release_status)
                # date_qty_set.append(release_status)
            pcn_no = line[0] # pylint: disable=unused-variable
            po_key = line[1]
            line_key = line[2]
            line_no = line[3]
            supplier_no = line[4]
            part_key = line[5]
            op_key = line[6] # pylint: disable=unused-variable

            
            # pprint(date_qty_set)
            # time.sleep(100000)
            num_parts = len(part_po_grouping)
            try:
                status.config(text=f"Updating part {part_no}.    "
                                    f"[{j + 1}/{num_parts}]")
            except RuntimeError:
                driver.quit()
            driver.get(f'{url_comb}/Purchasing/Line_Item_Form.asp?'
                    f'CameFrom=PO%2Easp'
                    f'&Supplier_No={supplier_no}'
                    f'&Do=Update&PO_Key={po_key}'
                    f'&Line_Item_Key={line_key}'
                    f'&Line_Item_No={line_no}'
                    f'&Print_Button_Pressed=False&ssAction=Same')
            # time.sleep(10000)
            # 3a. Get list of release quantities
            script = """
            a =[]
            var qty = document.querySelectorAll(
                                        'input[id^="txttxtQuantity"]');
            for (var i=0,max=qty.length; i<max;i++){
                if(qty[i].value)
                    a.push(qty[i].value.replace(',',''))
            }
            return a
            """
            rel_qty = driver.execute_script(script)
            # print(rel_qty)

            # 3b. Get a list of all release dates
            script = """
            b =[]
            var dates = document.querySelectorAll(
                                            'input[id^="txtDue_Date"]');
            for (var i=0,max=dates.length; i<max;i++){
                if(dates[i].value)
                    b.push(dates[i].value)
            }
            return b
            """
            rel_date = driver.execute_script(script)
            # print(rel_date)

            # 3c. Get a list of all release statuses
            script = """
                a =[]
            var qty = document.querySelectorAll(
                                        'input[id^="txttxtQuantity"]');
            for (var i=0,max=qty.length; i<max;i++){
                if(qty[i].value)
                    a.push(qty[i].value)
            }
            c =[]
            var rel_status = document.querySelectorAll(
                                    'select[id^="lstRelease_Status"]');
            for (var i=0,max=rel_status.length; i<max;i++){
                if(rel_status[i].value && a[i])
                        //need to check against the quantity value
                        //to make the array length even
                    c.push(rel_status[i].value)
            }
            return c
            """
            rel_status = driver.execute_script(script)
            # print(rel_status)

            # 3d. Zip ABC arrays into list for comparison
            release_list = [list(a) for a in zip(rel_date, rel_qty,
                                                    rel_status)]
            # print('Current Releases')
            # pprint(release_list)
            # print('')
            # time.sleep(100000)
            # 4. Separate out forecast releases
            forecasts =[line for i, line in enumerate(release_list)
                        if 'Forecast' in line]
            # print('Old Forecasts')
            # pprint(forecasts)
            cut_index = 0
            for i, line in enumerate(forecasts):
                # 5. Compare forecasts with date_qty_set
                for j, x in enumerate(date_qty_set): # pylint: disable=unused-variable
                    # print('Forecast to compare')
                    # print(line)
                    # print('Firm to compare')
                    # print(x)
                    if datetime.strptime(line[0], '%m/%d/%y') <=\
                            datetime.strptime(x[0], '%m/%d/%Y'):
                        # print(line[0], '<=', x[0])
                        # 6. Remove forecasts if they are before any
                        #    date in the csv list
                        cut_index += 1
                        # new_forecasts = forecasts[i+1:]
                        # forecasts = forecasts[i+1:]
                        break
                    # else:
                    #     new_forecasts = forecasts
            new_forecasts = forecasts[cut_index:]
            # print('New forecast Releases')
            # pprint(new_forecasts)
            # print('New original forecasts')
            # pprint(forecasts)
            # time.sleep(100000)
            # 7. Clear all release info for forecast releases
            # 7a. Change status to firm
            script = """
            a =[]
            var qty = document.querySelectorAll(
                                        'input[id^="txttxtQuantity"]');
            for (var i=0,max=qty.length; i<max;i++){
                if(qty[i].value)
                    a.push(qty[i].value)
            }
            b =[]
            var dates = document.querySelectorAll(
                                            'input[id^="txtDue_Date"]');
            for (var i=0,max=dates.length; i<max;i++){
                if(dates[i].value)
                    b.push(dates[i].value)
            var rel_status = document.querySelectorAll(
                                    'select[id^="lstRelease_Status"]');
            for (var i=0,max=rel_status.length; i<max;i++){
                //if(rel_status[i].value == 'Forecast'){
                    rel_status[i].value = 'Firm'
                    qty[i].value = ''
                    dates[i].value = ''}
            //}
            }"""
            driver.execute_script(script)
            # 8. Close partial releases.
            script = """
            var u = []
            var rcv_qty = document.querySelectorAll(
                                        'span[id="Receipt_Quantity"]');
            var qty = document.querySelectorAll(
                                        'input[id^="txttxtQuantity"]');
            var rel_status = document.querySelectorAll(
                                    'select[id^="lstRelease_Status"]');
            for (var i=0,max=rcv_qty.length; i<max;i++){
                if(rcv_qty[i].innerText != "0"){
                    qty[i].value = parseInt(
                                rcv_qty[i].innerText.replace(",", ""))
                    qty[i].onblur()
                    rel_status[i].value = "Received"
                    u.push(qty[i].value)
                    }
                }
            return u.length
            """
            partials = driver.execute_script(script)
            # time.sleep(100000)
            partials += 0
            rel_index = 0
            # 9. Update releases using CSV data
            # if the release quantity is 0, then skip it.
            # for some reason, Plex stores 0 qty releases.
            for i, release in enumerate(date_qty_set):
                if release[1] == '0':
                    continue
                print(i, partials, release[1], release[0], release[2])
                # time.sleep(10000)
                script = """
                var qty = document.querySelectorAll(
                                        'input[id^="txttxtQuantity"]');
                var dates = document.querySelectorAll(
                                            'input[id^="txtDue_Date"]');
                var rel_status = document.querySelectorAll(
                                    'select[id^="lstRelease_Status"]');
                qty[{i}+{partials}].value = {new_qty}
                dates[{i}+{partials}].value = "{new_date}"
                rel_status[{i}+{partials}].value = "{new_stat}"
                """.format(i=rel_index, partials=partials, 
                            new_qty=release[1],
                            new_date=release[0],
                            new_stat=release[2])
                driver.execute_script(script)
                rel_index += 1
            # time.sleep(10000)
            # 6/28/21
            # No longer keeping existing forecast releases
            # # 10. find the last empty release line
            # status_index = driver.find_elements_by_xpath(
            #                     '//select[starts-with(@id, '
            #                     '"lstRelease_Status")]')
            # qtys = driver.find_elements_by_xpath(
            #                         '//input[starts-with(@id, '
            #                         '"txttxtQuantity")]')
            # full_qty = [rel.get_attribute('value') for i, rel in 
            #             enumerate(qtys)]
            # empty_rel = [rel for i, rel in enumerate(qtys)
            #             if rel.get_attribute('value') == '']
            # status_qty = [list(a) for a in zip(status_index, full_qty)]
            # # pprint(status_qty)
            # forecast_index = [i for i, rel in enumerate(status_qty)
            #                 if rel[1] == '']
            # # pprint(forecast_index)
            # # 11. Start populating the forecast release data using
            # for i, rel in enumerate(empty_rel):
            #     if i < len(new_forecasts):
            #         script = """
            #             var qty = document.querySelectorAll(
            #                             'input[id^="txttxtQuantity"]');
            #             var dates = document.querySelectorAll(
            #                                'input[id^="txtDue_Date"]');
            #             var stat = document.querySelectorAll(
            #                         'select[id^="lstRelease_Status"]');
            #             qty[{x}].value = {new_qty}
            #             dates[{x}].value = "{new_date}"
            #             stat[{x}].value = "Forecast"
            #             """.format(x=forecast_index[i],
            #                     new_qty=new_forecasts[i][1],
            #                     new_date=new_forecasts[i][0])
            #         driver.execute_script(script)
            # 12. Add notes for time and date that it was updated
            qtys = driver.find_elements_by_xpath(
                                    '//input[starts-with(@id, '
                                    '"txttxtQuantity")]')
            full_qty = [rel for i, rel in enumerate(qtys)
                        if rel.get_attribute('value') != '']
            notes = driver.find_elements_by_xpath(
                                    '//input[starts-with(@id, '
                                    '"txtRelease_Note")]')
            full_note = [rel for i, rel in enumerate(notes)]
            full_note = full_note[:len(full_qty)]
            now = datetime.now()
            rel_date = now.strftime("%m/%d/%y %I:%M:%S %p")
            update_note = f'Updated by {user_name} on {rel_date}'
            for i, rel in enumerate(full_note):
                script = """
                var note = document.querySelectorAll(
                                        'input[id^="txtRelease_Note"]');
                note[{i}].value = "{update_note}"
                """.format(i=i, update_note=update_note)
                driver.execute_script(script)
            # time.sleep(10000)
            # 13. Click update button
            # Changed to JS function to work when minimized
            driver.execute_script("FormSubmitStart('Update');")
            # time.sleep(10000)
            # 14. Go to MRP recommendations
            # 14a. Czech is not doing forecasts.
            if not forecast_update:
                continue
            driver.get(f'{url_comb}/requirements_planning'
                    f'/Release_Planning_By_Supplier_Schedule_Form.asp'
                    f'?Mode=Part'
                    f'&Part_Key={part_key}')
            # 15. Get lists of relevant elements on screen
            # 15a. Get checkboxes
            script = """
            // Grab all checkbox elements
            var check = document.querySelectorAll(
                'input[id^="chkCreate_Release"]') 

            // Grab all on order elements
            var on_order_qty = []
            var on_order_stat = []
            // Xpath starts at 1 needs to go 1 longer than array length
            for(var i=1;i<check.length+1;i++){{
            var x = document.evaluate(
                '/html/body/div[1]/form/table/tbody/tr['+i+']/td[3]',
                document,null,9,null).singleNodeValue.innerText
            var qty = parseInt(x.split("\\n")[0].replace(",",""))
            var stat = x.split("\\n")[1]
            on_order_qty.push(qty)
            on_order_stat.push(stat)}}

            // Grab all suggested Order Elements
            var sug_order_qty = []
            for(var i=0;i<check.length;i++){{
            var x = document.querySelectorAll(
                'input[id^="txtQuantity"]')[i].value
            sug_order_qty.push(parseInt(x))}}
            // sug_order_qty

            // Grab all suggested order status elements
            var sug_order_stat = []
            for(var i=0;i<check.length;i++){{
            var x = document.querySelectorAll(
                'select[id^="lstRelease_Status"]')[i].value
            sug_order_stat.push(x)}}
            // sug_order_stat

            // Grab all note field elements
            var note = document.querySelectorAll(
                'input[id^="txtNote"]')

            // If order qty!= suggested order qty 
            // AND statuses are not firm, planned, or partial, 
            // then check the box and add a note
            for(var i=0;i<check.length;i++){{
            if (on_order_stat[i] != "Firm" && 
                on_order_stat[i] != "Partial" && 
                sug_order_stat[i] != "Firm" && 
                sug_order_stat[i] != "Planned" && 
                on_order_qty[i] != sug_order_qty[i]){{
            check[i].checked = true
            note[i].value = "MRP recommendation updated by "+
                            "{user_name} on {rel_date}"
            }}}}
            """.format(user_name=user_name,rel_date=rel_date)
            driver.execute_script(script)
            # 16. Create suggested forecast releases.
            #     (Click create button)
            # Switched to JS function to work while minimized
            # time.sleep(10000)
            driver.execute_script("Create_Releases();")
            # time.sleep(10000)
    status.config(text=f"Process complete. {total_lines} total "
                        f"releases across {num_parts} part numbers "
                        f"updated.")
    driver.quit()


def subcon_inventory(user_name, password, company_code, db, home_pcn,
                     input_file):
    """
    Function to download inventory. 
    
    Compatible with API and Selenium downloads.
    """
    if user_name == '' or password == '' or company_code == '':
        status.config(text=login_error_text)
        tab_control.select(0)
    else:
        # Initialize the user account to be used for login
        # pcn = launch_pcn_dict[home_pcn]["pcn"]
        # file_prefix = launch_pcn_dict[home_pcn]["prefix"]
        authentication = get_auth(home_pcn)
        if authentication.username == '' or authentication.password == '':
            function_target = lambda: plex_inventory_get(user_name, password,
                              company_code, db, home_pcn, input_file)
        else:
            function_target = lambda: api_inventory_download_v2(authentication, 
                              db, home_pcn, input_file)
        # Call the function in a thread so the GUI doesn't hang while it runs.
        global t
        t = threading.Thread(target=function_target)
        t.start()
        status.config(text="Getting inventory numbers.")
        inv_selector.config(text=selector_text, anchor=W)
        inv_button_start.config(state=DISABLED)


def api_inventory_download_v2(authentication, db, home_pcn, input_file):
    """
    This function grabs inventory based on a list of part numbers.

    The list should contain only the base part number, without revision.

    There is a chance that a single part number has more than 1000 rows.
        If this happens, the download will grab them one status at a time.
        
        In testing, only one part in GH and 2 in CZ have this concern.
            225461-20 | 240527-80 | 240528-80
    """
    if db == 'test':
        db = 'test.'
    else:
        db = ''

    
    file_prefix = launch_pcn_dict[home_pcn]["prefix"]
    part_list = import_part_list(input_file)
    status_df = pd.DataFrame(container_statuses, columns=[
                                'Container_Status'])
    large_parts = []
    df_1 = pd.DataFrame()
    l_df_1 = pd.DataFrame()
    total_parts = len(part_list)
    # for i, part_no in enumerate(part_list):
    # print(i+1,"/",total_parts, part_no)
    
    # progress_text = f'Getting inventory for {part_no}    '\
    #                         f'[{i+1}/{total_parts}]'
    # status.config(text=progress_text)
    # query = {
    #     'inputs':{
    #         'Include_Containers': True,
    #         'Part_No': part_no
    #         }
    #     }
    api_id = '23733'
    url = f'https://{db}cloud.plex.com/api/datasources/{api_id}/execute'
    list_of_urls = [(url, form_data, authentication) 
        for form_data in map(create_inv_json, part_list)]

    with ThreadPoolExecutor(max_workers=25) as pool:
        response_list = list(pool.map(post_url,list_of_urls))

    for p, response in enumerate(response_list):
        # response = requests.post(url, json=query, auth=authentication)
        # print(response.text)
        json_data = json.loads(response.text)
        # print(json_data)
        # print(response.json())
        inventory_list = json_data['tables']
        if json_data['tables'][0]['rows'] == []:
            continue
        row_limit = inventory_list[0]['rowLimitExceeded']
        part_no = json_data['tables'][0]['rows'][0][1]
        # print(part_no)
        # print('row limit exceded:',row_limit)
        if row_limit == True:
            print(f"Inventory for {part_no} exceeds row limit,"
                    f" will run later.")
            large_parts.append(part_no)
            continue
        if df_1.empty:
            df_1 = json_normalize(inventory_list, 'rows')
            df_1.columns = json_data['tables'][0]['columns']
            # print('first')
            # print(df_1)
        else:
            df = json_normalize(inventory_list, 'rows')
            df.columns = json_data['tables'][0]['columns']
            # df_1 = df_1.append(df)
            df_1 = pd.concat([df_1,df])
            # print('next')
            # print (df_1)
        
        # need to loop back through the large_parts list separately
        if not large_parts == []:
            total_parts = len(large_parts)
            for i, part_no in enumerate(large_parts):
                for j, container_status in enumerate(container_statuses):
                    # print(i, part_no, "status:",status)
                    if j == 0:
                        continue
                    if status == '':
                        continue
                    progress_text = f'Getting large inventory for {part_no}    '\
                                    f'[{i+1}/{total_parts}]'
                    status.config(text=progress_text)
                    query = {
                        'inputs':{
                            'Include_Containers': False,
                            'Part_No': part_no,
                            'Container_Status':container_status
                            }
                        }
                    api_id = '23733'
                    url = f'https://{db}cloud.plex.com/api/datasources/'\
                            f'{api_id}/execute'
                    response = requests.post(url, json=query,
                                                auth=authentication)
                    json_data = json.loads(response.text)
                    # print(response.json())
                    inventory_list = json_data['tables']
                    if inventory_list[0]['rows'] == []:
                        continue
                    if l_df_1.empty:
                        l_df_1 = json_normalize(inventory_list, 'rows')
                        l_df_1.columns = json_data['tables'][0]['columns']
                    else:
                        l_df = json_normalize(inventory_list, 'rows')
                        l_df_1.columns = json_data['tables'][0]['columns']
                        # l_df_1 = l_df_1.append(l_df)
                        l_df_1 = pd.concat([l_df_1, l_df])
            l_df_1.columns = json_data['tables'][0]['columns']
            l_df_2 = l_df_1.groupby(['Part', 'Location_Type']).sum(
                    'Quantity').reset_index()[['Part','Location_Type',
                                                'Quantity']]
            l_df_2.columns = ['Part','Location_Type','Container_Quantity']
    if df_1.empty:
        status.config(text=
                    f"No inventory for provided part numbers.")
        return
    df_1.columns = json_data['tables'][0]['columns']
    df_1 = df_1.merge(status_df,on='Container_Status')
    df_2 = df_1.groupby(['Part', 'Location_Type']).sum(
                'Container_Quantity').reset_index()[['Part',
                                                'Location_Type',
                                                'Container_Quantity']]

    # Subcon inventory dataframe
    df_3 = df_2[df_2['Location_Type'] == 'Subcontractor']
    # MRP inventory dataframe
    df_4 = df_2[~df_2['Location_Type'].isin(mrp_excluded_locations)]
    # print(df_3)
    # print(df_4)
    df_4 = df_4.groupby('Part').sum('Container_Quantity').reset_index()
    if not l_df_1.empty:
        l_df_3 = l_df_2[l_df_2['Location_Type'] == 'Subcontractor']
        l_df_4 = l_df_2[~l_df_2['Location_Type'].isin(
                                        mrp_excluded_locations)]
        l_df_4 = l_df_4.groupby('Part').sum(
                            'Container_Quantity').reset_index()
        # df_3 = df_3.append(l_df_3)
        df_3 = pd.concat([df_3, l_df_3])
        # df_4 = df_4.append(l_df_4)
        df_4 = pd.concat([df_4, l_df_4])
    df_3.columns = ['Part_No','Location_Type','Inventory']
    df_4.columns = ['Part_No','Inventory']
    # Load the source part file as a dataframe
    df_source = pd.read_csv(input_file, sep=',')
    # Make sure the first column is called 'Part_No'
    df_source.columns.values[0] = 'Part_No'
    # Make sure the part number column has the proper type to merge
    df_source['Part_No'] = df_source['Part_No'].astype('object')
    # Merge the downloads with the source to include zero inventory parts
    df_4_final = df_4.merge(df_source, how='outer', on='Part_No', copy=False)
    df_4_final['Inventory'].fillna(0, inplace=True)
    df_3_final = df_3.merge(df_source, how='outer', on='Part_No', copy=False)
    df_3_final['Inventory'].fillna(0, inplace=True)
    # print(df_4_final)
    # print(df_3_final)
    # print("Subcontract Inventory")
    # print(df_3)
    # print("MRP Inventory")
    # print(df_4)
    inventory_parts = len(df_4_final.index)
    input_parts = len(df_source.index)
    # print(inventory_parts, input_parts)
    inventory_file = os.path.join(source_dir, 
                                    f'{file_prefix}inventory.csv')
    subcon_inventory_file = os.path.join(source_dir, 
                                    f'{file_prefix}subcon_inventory.csv')
    while True:
        try:
            df_3_final[['Part_No','Inventory']].to_csv(subcon_inventory_file,
                                            index=FALSE)
            df_4_final[['Part_No','Inventory']].to_csv(inventory_file,
                                            index=FALSE)
            status.config(text=f'{input_parts} provided, {inventory_parts} '
                        f'parts downloaded. Files saved to '
                        f'{source_dir} as {file_prefix}inventory.csv '
                        f'and {file_prefix}subcon_inventory.csv')
            break
        except PermissionError:
            if askokcancel('File In Use', f'Please close the file '
                        f'{subcon_inventory_file} or {inventory_file} '
                        f'in order to continue.'):
                continue
            else:
                status.config(text="Inventory download cancelled by user.")
                break

        # df_3[['Part','Container_Quantity']].to_csv(subcon_inventory_file,
        #                                         index=FALSE)
        # df_4[['Part','Container_Quantity']].to_csv(inventory_file,
        #                                         index=FALSE)
        # status.config(text=f'Inventory retrieved. Files saved to '
        #                     f'{source_dir} as {file_prefix}inventory.csv '
        #                     f'and {file_prefix}subcon_inventory.csv')


def api_inventory_download(authentication, db, home_pcn, input_file):
    """
    This function grabs inventory based on a list of part numbers.

    The list should contain only the base part number, without revision.

    There is a chance that a single part number has more than 1000 rows.
        If this happens, the download will grab them one status at a time.
        
        In testing, only one part in GH and 2 in CZ have this concern.
            225461-20 | 240527-80 | 240528-80
    """
    if db == 'test':
        db = 'test.'
    else:
        db = ''
    file_prefix = launch_pcn_dict[home_pcn]["prefix"]
    part_list = import_part_list(input_file)
    status_df = pd.DataFrame(container_statuses, columns=[
                                'Container_Status'])
    large_parts = []
    df_1 = pd.DataFrame()
    l_df_1 = pd.DataFrame()
    total_parts = len(part_list)
    for i, part_no in enumerate(part_list):
        # print(i+1,"/",total_parts, part_no)
        progress_text = f'Getting inventory for {part_no}    '\
                                f'[{i+1}/{total_parts}]'
        status.config(text=progress_text)
        query = {
            'inputs':{
                'Include_Containers': True,
                'Part_No': part_no
                }
            }
        api_id = '23733'
        url = f'https://{db}cloud.plex.com/api/datasources/'\
                f'{api_id}/execute'
        response = requests.post(url, json=query, auth=authentication)
        json_data = json.loads(response.text)
        # print(response.json())
        inventory_list = json_data['tables']
        if json_data['tables'][0]['rows'] == []:
            continue
        row_limit = inventory_list[0]['rowLimitExceeded']
        # print('row limit exceded:',row_limit)
        if row_limit == True:
            print(f"Inventory for {part_no} exceeds row limit,"
                    f" will run later.")
            large_parts.append(part_no)
            continue
        if df_1.empty:
            df_1 = json_normalize(inventory_list, 'rows')
        else:
            df = json_normalize(inventory_list, 'rows')
            df_1 = df_1.append(df)
            # print('next')
            # print (df_1)

    # need to loop back through the large_parts list separately
    if not large_parts == []:
        total_parts = len(large_parts)
        for i, part_no in enumerate(large_parts):
            for j, container_status in enumerate(container_statuses):
                # print(i, part_no, "status:",status)
                if j == 0:
                    continue
                if status == '':
                    continue
                progress_text = f'Getting large inventory for {part_no}    '\
                                f'[{i+1}/{total_parts}]'
                status.config(text=progress_text)
                query = {
                    'inputs':{
                        'Include_Containers': False,
                        'Part_No': part_no,
                        'Container_Status':container_status
                        }
                    }
                api_id = '23733'
                url = f'https://{db}cloud.plex.com/api/datasources/'\
                        f'{api_id}/execute'
                response = requests.post(url, json=query,
                                            auth=authentication)
                json_data = json.loads(response.text)
                # print(response.json())
                inventory_list = json_data['tables']
                if inventory_list[0]['rows'] == []:
                    continue
                if l_df_1.empty:
                    l_df_1 = json_normalize(inventory_list, 'rows')
                else:
                    l_df = json_normalize(inventory_list, 'rows')
                    # l_df_1 = l_df_1.append(l_df)
                    l_df_1 = pd.concat([l_df_1, l_df])
        l_df_1.columns = json_data['tables'][0]['columns']
        l_df_2 = l_df_1.groupby(['Part', 'Location_Type']).sum(
                'Quantity').reset_index()[['Part','Location_Type',
                                            'Quantity']]
        l_df_2.columns = ['Part','Location_Type','Container_Quantity']
    if df_1.empty:
        status.config(text=
                    f"No inventory for provided part numbers.")
        return
    df_1.columns = json_data['tables'][0]['columns']
    df_1 = df_1.merge(status_df,on='Container_Status')
    df_2 = df_1.groupby(['Part', 'Location_Type']).sum(
                'Container_Quantity').reset_index()[['Part',
                                                'Location_Type',
                                                'Container_Quantity']]

    # Subcon inventory dataframe
    df_3 = df_2[df_2['Location_Type'] == 'Subcontractor']
    # MRP inventory dataframe
    df_4 = df_2[~df_2['Location_Type'].isin(mrp_excluded_locations)]
    # print(df_3)
    # print(df_4)
    df_4 = df_4.groupby('Part').sum('Container_Quantity').reset_index()
    if not l_df_1.empty:
        l_df_3 = l_df_2[l_df_2['Location_Type'] == 'Subcontractor']
        l_df_4 = l_df_2[~l_df_2['Location_Type'].isin(
                                        mrp_excluded_locations)]
        l_df_4 = l_df_4.groupby('Part').sum(
                            'Container_Quantity').reset_index()
        # df_3 = df_3.append(l_df_3)
        df_3 = pd.concat([df_3, l_df_3])
        # df_4 = df_4.append(l_df_4)
        df_4 = pd.concat([df_4, l_df_4])
    # print("Subcontract Inventory")
    # print(df_3)
    # print("MRP Inventory")
    # print(df_4)
    inventory_file = os.path.join(source_dir, 
                                    f'{file_prefix}inventory.csv')
    subcon_inventory_file = os.path.join(source_dir, 
                                    f'{file_prefix}subcon_inventory.csv')
    while True:
        try:
            df_3[['Part','Container_Quantity']].to_csv(subcon_inventory_file,
                                            index=FALSE)
            df_4[['Part','Container_Quantity']].to_csv(inventory_file,
                                            index=FALSE)
            status.config(text=f'Inventory retrieved. Files saved to '
                        f'{source_dir} as {file_prefix}inventory.csv '
                        f'and {file_prefix}subcon_inventory.csv')
            break
        except PermissionError:
            if askokcancel('File In Use', f'Please close the file '
                        f'{subcon_inventory_file} or {inventory_file} '
                        f'in order to continue.'):
                continue
            else:
                status.config(text="Inventory download cancelled by user.")
                break

    # df_3[['Part','Container_Quantity']].to_csv(subcon_inventory_file,
    #                                         index=FALSE)
    # df_4[['Part','Container_Quantity']].to_csv(inventory_file,
    #                                         index=FALSE)
    # status.config(text=f'Inventory retrieved. Files saved to '
    #                     f'{source_dir} as {file_prefix}inventory.csv '
    #                     f'and {file_prefix}subcon_inventory.csv')


def plex_inventory_get(user_name, password, company_code, db, home_pcn,
                       input_file):
    """
    Selenium based inventory download. 
    
    Runs headless through Chrome.
    """
    # Initialize the user account to be used for login
    pcn = launch_pcn_dict[home_pcn]["pcn"]
    file_prefix = launch_pcn_dict[home_pcn]["prefix"]
    plex = Plex('classic', user_name, password, company_code, pcn, db=db,
                use_config=False, pcn_path=pcn_file, legacy_login=0)
    # Get the directory that script is running in
    # bundle_dir = plex.frozen_check()
    plex.frozen_check()
    plex.download_chrome_driver()
            # Call the config function to initialize the file and set variables
    plex.config()
    # Call the login function and return the chromedriver instance and
    #   base URL used in the rest of the script
    try:
        driver, url_comb, url_token = plex.login(headless=1)
        url_token = url_token
    except SystemExit:
        status.config(text="Username, Password, or Company code "
                        "incorrect. Please verify and try again.")
        tab_control.select(0)
        plex.driver.quit()
        return
    # print(driver)
    # print(url_comb)
    # ======End of required code======#
    # Subcon Locations
    """
    subcon_locations = []
    try:
        r = Path(os.path.join(master_file_dir,
                    'subcon_locations.csv')).read_text()
        # r = requests.get('https://raw.githubusercontent.com/'
        #              'ClawhammerLobotomy/Level_Scheduling/main/'
        #              'subcon_locations.csv')
        # r.raise_for_status()
        subcon_locations = r.split('\n')
    except FileNotFoundError:
        print('Error getting file. Using local file')
        with open(subcon_location_file, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    subcon_locations.append(row[0])
                except IndexError:
                    continue
    # MRP excluded Locations
    mrp_locations = []
    try:
        r = Path(os.path.join(master_file_dir,
                    'mrp_locations.csv')).read_text()
        # r = requests.get('https://raw.githubusercontent.com/'
        #              'ClawhammerLobotomy/Level_Scheduling/main/'
        #              'mrp_locations.csv')
        # r.raise_for_status()
        mrp_locations = r.split('\n')
        # print(mrp_locations)
    except FileNotFoundError:
        print('Error getting file. Using local file')
        with open(mrp_location_file, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    mrp_locations.append(row[0])
                except IndexError:
                    continue
    # Container Statuses
    container_statuses = []
    try:
        r = Path(os.path.join(master_file_dir,
                    'container_statuses.csv')).read_text()
        # r = requests.get('https://raw.githubusercontent.com/'
        #              'ClawhammerLobotomy/Level_Scheduling/main/'
        #              'container_statuses.csv')
        # r.raise_for_status()
        container_statuses = r.split('\n')
    except FileNotFoundError:
        print('Error getting file. Using local file')
        with open(container_status_file, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    container_statuses.append(row[0])
                except IndexError:
                    continue
    # print(subcon_locations)
    """
    file = input_file
    total_lines = len(open(input_file).readlines()) - 1
    with open(file, 'r', encoding="utf-8") as part_numbers:
        csv_reader = csv.reader(part_numbers, delimiter=',')
        full_part_list = {}
        subcon_part_list = {}
        for i, part in enumerate(csv_reader):
            # print(i, part)
            if i == 0:
                driver.get(f'{url_comb}/Rendering_Engine/Default.aspx?'
                            'Request=Show&RequestData='
                            'SourceType(Screen)SourceKey(245)')
            else:
                progress_text = f'Getting inventory for {part[0]}    '\
                                f'[{i}/{total_lines}]'
                try:
                    status.config(text=progress_text)
                except RuntimeError:
                    driver.quit()
                part_no = part[0]
                # supplier_name = part[1]
                # Enter the part number and search the screen
                script = """
                var x = document.getElementById('Layout1_el_285725')
                x.value = '{part_no}'
                ShowPopupLayer('Please Wait...');
                HandleToolbar('Search');
                """.format(part_no=part_no)
                driver.execute_script(script)
                # Need to find the column headers because they differ
                #   between PCNs
                script = """
                var length = document.evaluate(
                    '//*[@id="GRID_PANEL_3_28"]/thead/tr', 
                    document, null, 
                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                    null).singleNodeValue.children.length
                var a = []
                for(var i=1;i<length+1;i++){
                var x = document.evaluate(
                    '//*[@id="GRID_PANEL_3_28"]/thead/tr/th['
                        +i+']', document, null, 
                        XPathResult.FIRST_ORDERED_NODE_TYPE, 
                        null).singleNodeValue.textContent
                a.push(x.replace(/\\n/ig, ""))}
                return a
                """
                try:
                    column_names = driver.execute_script(script)
                except JavascriptException:
                    print(part[0], "Java exception with column names")
                    quantities = [0,0]
                    full_part_list[part_no] = quantities[0]
                    subcon_part_list[part_no] = quantities[1]
                    continue
                # make dictionary of column names
                column_dict = {}
                for x, i in enumerate(column_names):
                    # print("column names:",x,i)
                    column_dict[i] = x+1
                try:
                    qty_col = column_dict["Quantity"]
                    location_col = column_dict["Location"]
                    if {"Status"} <= column_dict.keys():
                        status_col = column_dict["Status"]
                    else:
                        status_col = column_dict["Container Status"]
                except KeyError:
                    print(part[0], "Key error")
                    quantities = [0,0]
                    full_part_list[part_no] = quantities[0]
                    subcon_part_list[part_no] = quantities[1]
                    continue
                expected_length = len(column_dict)
                # print("expected length:",expected_length)
                script = """
                var status = {container_statuses}
                var subcon_loc = {subcon_locations}
                var mrp_loc = {mrp_locations}
                var quantities = []
                var b = '/html/body/div[1]/form/div[5]/table/tbody/tr/'
                        +'td/div/div/table/tbody'
                var length = document.evaluate(b,document, null, 
                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                    null).singleNodeValue.rows.length
                var total = 0
                var subcon_total = 0
                var expected_length = {expected_length}
                for (i=2;i<length;i++){{
                var columns = document.evaluate(b+'/tr['+i+']',
                    document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, 
                    null).singleNodeValue.children.length
                var offset = expected_length - columns
                var x = document.evaluate(b+'/tr['+i+']/td['
                    +({qty_col}-offset).toString()+']',document, null, 
                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                    null).singleNodeValue.innerText
                x = x.split(' ',1)[0]
                x = x.replace(',','')
                var container_status = document.evaluate(b+'/tr['+i
                    +']/td['+({status_col}-offset).toString()+']',
                    document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, 
                    null).singleNodeValue.innerText
                var container_location = document.evaluate(b+'/tr['+i
                    +']/td['+({location_col}-offset).toString()+']',
                    document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, 
                    null).singleNodeValue.innerText
                if (status.includes(container_status)){{
                if (subcon_loc.includes(container_location)){{
                subcon_total += +x
                }}
                else if (mrp_loc.includes(container_location)){{
                    continue
                }}
                else{{
                total += +x
                }}
                }}
                }}
                quantities.push(total)
                quantities.push(subcon_total)
                return quantities
                """.format(subcon_locations=subcon_locations,
                            mrp_locations=mrp_locations,
                            qty_col=qty_col,
                            location_col=location_col,
                            status_col=status_col,
                            expected_length=expected_length,
                            container_statuses=container_statuses)
                try:
                    print(part[0], 'trying to get inventory')
                    quantities = driver.execute_script(script)
                except JavascriptException:
                    # Assumed no inventory
                    print(part[0], 'failed to get inventory')
                    quantities = [0,0]
                    full_part_list[part_no] = quantities[0]
                    subcon_part_list[part_no] = quantities[1]
                    continue
                print(quantities)
                # print(inv_val)
                # print(inv_list)
                full_part_list[part_no] = quantities[0]
                subcon_part_list[part_no] = quantities[1]
    # pprint(full_part_list)
    # print(len(full_part_list))
    inventory_file = os.path.join(source_dir, 
                                    f'{file_prefix}inventory.csv')
    subcon_inventory_file = os.path.join(source_dir, 
                                    f'{file_prefix}subcon_inventory.csv')
    with open(inventory_file, 'w', newline='') as w, \
            open(subcon_inventory_file, 'w', newline='') as s:
        row = csv.writer(w)
        row.writerow(['Part_No', 'Inventory'])
        for key, val in full_part_list.items():
            row.writerow([key, val])
        s_row = csv.writer(s)
        s_row.writerow(['Part_No', 'Inventory'])
        for key, val in subcon_part_list.items():
            s_row.writerow([key, val])
    # time.sleep(10000)
    # inventory
    status.config(text=f'Inventory retrieved. Files saved to '
                        f'{source_dir} as {file_prefix}inventory.csv '
                        f'and {file_prefix}subcon_inventory.csv')
    driver.quit()


def cust_rel(user_name, password, company_code, db, home_pcn, input_file):
    """
    Function to download customer releases. 
    
    Compatible with API and Selenium download versions.
    """
    if user_name == '' or password == '' or company_code == '':
        status.config(text=login_error_text)
        tab_control.select(0)
    else:
        # Initialize the user account to be used for login
        # pcn = launch_pcn_dict[home_pcn]["pcn"]
        # file_prefix = launch_pcn_dict[home_pcn]["prefix"]
        authentication = get_auth(home_pcn)
        if authentication.username == '' or authentication.password == '':
            function_target = lambda: plex_customer_release_get(user_name, 
                            password, company_code, db, home_pcn, input_file)
        else:
            function_target = lambda: api_customer_release_get_v2(authentication, 
                              db, home_pcn, input_file)
        # Call the function in a thread so the GUI doesn't hang while it runs.
        global t
        t = threading.Thread(target=function_target)
        t.start()
        status.config(text="Getting customer releases.")
        cust_selector.config(text=selector_text, anchor=W)
        cust_button_start.config(state=DISABLED)


def plex_customer_release_get(user_name, password, company_code, db, home_pcn,
                              input_file):
    """
    Selenium customer release download version.
    """
    pcn = launch_pcn_dict[home_pcn]["pcn"]
    file_prefix = launch_pcn_dict[home_pcn]["prefix"]
    # pcn = home_PCN      # enter pcn number
    plex = Plex('classic', user_name, password, company_code, pcn, db=db,
                use_config=False, pcn_path=pcn_file, legacy_login=0)
    # Get the directory that script is running in
    # bundle_dir = plex.frozen_check()
    plex.frozen_check()
    # global driver
    # ======Start of required code======#
    # Call the chrome driver download function
    plex.download_chrome_driver()
    # Call the config function to initialize the file and set variables
    plex.config()
    # Call the login function and return the chromedriver instance and
    #   base URL used in the rest of the script
    try:
        driver, url_comb, url_token = plex.login(headless=1)
        url_token = url_token
    except SystemExit:
        status.config(text="Username, Password, or Company code "
                        "incorrect. Please verify and try again.")
        tab_control.select(0)
        plex.driver.quit()
        return
    # print(driver)
    # print(url_comb)
    # ======End of required code======#
    # Start with clean csv for customer releases
    release_file = os.path.join(source_dir, 
                                f'{file_prefix}cust_releases.csv')
    file = open(release_file, 'w+', newline='', encoding='utf-8')
    with file:
        write = csv.writer(file)
        write.writerow(('Lookup_Key', 'Part_No', 'Week_Index', 
                        'Release_Date', 'Quantity'))
    file = input_file
    total_lines = len(open(input_file).readlines()) - 1
    csv_formula_index = 2
    with open(file, 'r', encoding="utf-8") as part_numbers:
        csv_reader = csv.reader(part_numbers, delimiter=',')
        # full_rel_list = {}
        for i, part in enumerate(csv_reader):
            # print(i, part)
            if i == 0:
                driver.get(f'{url_comb}/Sales/Release.asp')
            else:
                part_no = part[0]
                progress_text = f'Getting releases for {part[0]}    '\
                                f'[{i}/{total_lines}]'
                try:
                    status.config(text=progress_text)
                except RuntimeError:
                    driver.quit()
                # Chromedriver doesn't work minimized if you are 
                #   simulating key presses and clicks.
                # Switching to using JS scripts instead
                script = """
                document.getElementById(
                    'fltRELPart_No').value = "{part}"
                FormSubmit();
                """.format(part=part[0])
                driver.execute_script(script)
                script = """
                var length = document.evaluate(
                    '//*[@id="ReleaseGridResultTable"]/thead/tr', 
                    document, null, 
                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                    null).singleNodeValue.children.length
                var a = []
                for(var i=1;i<length+1;i++){
                var x = document.evaluate(
                    '//*[@id="ReleaseGridResultTable"]/thead/tr/th['
                        +i+']', document, null, 
                        XPathResult.FIRST_ORDERED_NODE_TYPE, 
                        null).singleNodeValue.textContent
                a.push(x.replace(/\\n/ig, ""))}
                return a
                """
                try:
                    column_names = driver.execute_script(script)
                except JavascriptException:
                    print(part[0],"Java exception with column names")
                    continue
                # make dictionary of column names
                column_dict = {}
                for x, i in enumerate(column_names):
                    column_dict[i] = x+1
                try:
                    qty_load_col = column_dict["QtyLoaded"]
                    ship_date_col = column_dict["Ship DateShipper No"]
                    rel_bal_col = column_dict["RelBal"]
                except KeyError:
                    print("Key error")
                    continue
                script = """
                var length = document.getElementById(
                    'ReleaseGridResultTable').rows.length
                var a = []
                for(var i = 1;i<length;i++){{
                    var y = document.evaluate(
                        '//*[@id="ReleaseGridResultTable"]/tbody/tr['
                            +i+']/td[{ship_date_col}]/a', document, 
                            null, XPathResult.FIRST_ORDERED_NODE_TYPE, 
                            null).singleNodeValue
                    a.push(y.text.replace(/\\n/ig, ''))}}
                return a
                """.format(ship_date_col=ship_date_col)
                try:
                    ship_date = driver.execute_script(script)
                except JavascriptException:
                    print(part[0],"ship date error exception")
                    continue
                script = """
                var length = document.getElementById(
                    'ReleaseGridResultTable').rows.length
                var a = []
                for(var i = 1;i<length;i++){{
                    var y = document.evaluate(
                        '//*[@id="ReleaseGridResultTable"]/tbody/tr['
                            +i+']/td[{qty_load_col}]', document, null,
                                XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                null).singleNodeValue
                    a.push(parseInt(y.textContent.replace(/,/g, "")))}}
                return a
                """.format(qty_load_col=qty_load_col)
                qty_load = driver.execute_script(script)
                script = """
                var length = document.getElementById(
                    'ReleaseGridResultTable').rows.length
                var a = []
                for(var i = 1;i<length;i++){{
                    var y = document.evaluate(
                        '//*[@id="ReleaseGridResultTable"]/tbody/tr['
                            +i+']/td[{rel_bal_col}]', document, null, 
                            XPathResult.FIRST_ORDERED_NODE_TYPE, 
                            null).singleNodeValue
                    a.push(parseInt(y.textContent.replace(/,/g, "")))}}
                return a
                """.format(rel_bal_col=rel_bal_col)
                rel_bal = driver.execute_script(script)
                # Sum the loaded and balance lists
                rel_sum = [x+y for x, y in zip(qty_load, rel_bal)]
                # Combine the date and release sum lists
                release_list = [a for a in zip(ship_date, rel_sum)]
                # Group an sum the release quantities by ship date 
                #   into a list of tuples
                date_grouped_rel = [(k, sum(t[1] for t in g))
                        for k,g in groupby(release_list,
                                    operator.itemgetter(0))]
                today = datetime.today()
                # today_date = today.strftime("%#m/%#d/%y")
                monday = today - timedelta(days=today.weekday())
                date_grouped_rel = [list(ele) for ele in 
                                    date_grouped_rel] 
                # print(part[0])
                # pprint(date_grouped_rel)
                # index_list = []
                for x, y in enumerate(date_grouped_rel):
                    # print(x,y)
                    # 4/30/21
                    #   Ran into releases which had no date.
                    #   Accounting for this and setting that date to
                    #     01/01/90 which marks it past due.
                    try:
                        eval_date = datetime.strptime(y[0], "%m/%d/%y")
                    except ValueError:
                        eval_date = datetime.strptime("01/01/90", 
                                                        "%m/%d/%y")
                    year_offest = weeks_for_year(int(
                                            eval_date.strftime("%Y")))
                    # print(year_offest)
                    # Creates an index value based on how many weeks 
                    #   away the date is from the current week's monday
                    # Negative values would be past due.
                    index = int(eval_date.strftime("%W")) \
                            - int(monday.strftime("%W")) \
                            + ((int(eval_date.strftime("%Y")) \
                            - int(monday.strftime("%Y"))) \
                            * year_offest)
                    # print(index)
                    group_start_date = monday + timedelta(weeks=index)
                    # index_list.append(index)
                    # Inserts the index value into the release list
                    date_grouped_rel[x].insert(0,index)
                    # Inserts the monday of each release for later 
                    #   grouping
                    date_grouped_rel[x].insert(1,
                        group_start_date.strftime("%#m/%#d/%y"))
                current_week_rel = [i for i in date_grouped_rel if 
                                    i[0] == 0]
                # Removes the "monday" value since it isn't needed for 
                #   current week
                current_week_rel = [[i[0]] + i[2:] for i in 
                                    current_week_rel]
                # Groups the releases based on start of the week, 
                #   excluding current week.
                week_grouped_releases = [(*k, sum(t[3] for t in g))
                        for k,g in groupby(date_grouped_rel, 
                                    operator.itemgetter(0, 1))]
                week_grouped_releases = [list(ele) for ele in 
                                week_grouped_releases if ele[0] != 0]
                # print("List of releases grouped by week's Monday")
                # pprint(week_grouped_releases)

                # Combines current week and grouped week releases
                combined_grouped_releases = current_week_rel \
                                            + week_grouped_releases
                # print("Combined list of releases")
                # pprint(combined_grouped_releases)
                for y, x in enumerate(combined_grouped_releases):
                    x.insert(0, part_no)
                    # This is a stupid hack to create an excel based 
                    #   lookup key based on the part+serial date 
                    #   value in Excel using a text formula so I don't 
                    #   need to re-do the Excel calculation function
                    x.insert(0, 
                        f"=B{csv_formula_index}&D{csv_formula_index}")
                    csv_formula_index +=1
                # pprint(combined_grouped_releases)
                file = open(release_file, 'a+', newline='', 
                            encoding='utf-8')
                with file:
                    write = csv.writer(file)
                    write.writerows(combined_grouped_releases)
    # time.sleep(10000)
    status.config(text=f"Releases retrieved. File saved to {release_file}")
    driver.quit()


def api_customer_release_get_v2(authentication, db, home_pcn, input_file):
    """
    Downloads and formats customer releases based on an input part list.
    
    Saves file to static location to be used with Level Scheduling 
    Excel workbooks
    """
    if db == 'test':
        db = 'test.'
    else:
        db = ''
    file_prefix = launch_pcn_dict[home_pcn]["prefix"]
    part_list = import_part_list(input_file)
    total_parts = len(part_list)
    df_1 = pd.DataFrame()
    api_id = '5565'
    url = f'https://{db}cloud.plex.com/api/datasources/{api_id}/execute'
    list_of_urls = [(url, form_data, authentication) 
        for form_data in map(create_cust_json, part_list)]
    
    with ThreadPoolExecutor(max_workers=25) as pool:
        response_list = list(pool.map(post_url,list_of_urls))
    
    for p, response in enumerate(response_list):
    # for i, part_no in enumerate(part_list):
        # progress_text = f'Getting releases for {part_no}    '\
        #                         f'[{i+1}/{total_parts}]'
        # status.config(text=progress_text)
        # query = {
        #     'inputs':{
        #         'Part_No': part_no
        #         }
        #     }
        # api_id = '15596'
        # url = f'https://{db}cloud.plex.com/api/datasources/'\
        #         f'{api_id}/execute'
        # response = requests.post(url, json=query, auth=authentication)
        json_data = json.loads(response.text)
        print(json_data)
        inventory_list = json_data['tables']
        if json_data['tables'][0]['rows'] == []:
            continue
        if df_1.empty:
            df_1 = json_normalize(inventory_list, 'rows')
            print('first')
            print(df_1)
        else:
            df = json_normalize(inventory_list, 'rows')
            # df_1 = df_1.append(df,ignore_index=True)
            df_1 = pd.concat([df_1, df],ignore_index=True)
            # print('next')
            # print (df_1)
    if df_1.empty:
        status.config(text=f"No releases for provided part numbers.")
        return
    df_1.columns = json_data['tables'][0]['columns']
    # Added exclusion for "Audit" operation types. This may cause issues with
    #   Other parts. Would need to query to see.
    # Can't use this. There are enough parts with only Audit operation types
    #   that this won't work.
    # Need to figure out how to remove duplicates from the results.
    # df_1 = df_1[df_1['Operation_Type'] != 'Audit']

    # Added conversion for Time zone. Plex API uses UTC, but that is causing
    #   some releases to be grouped with other dates. Converting to Eastern
    #   fixes this.
    df_1['Ship_Date'] = pd.to_datetime(df_1['Ship_Date'])
    df_1['Ship_Date'] = df_1['Ship_Date'].dt.tz_convert("US/Eastern")
    df_1['Ship_Date'] = pd.to_datetime(df_1['Ship_Date'],
                                        format='%Y-%m-%d')
    df_1['Ship_Date'] = df_1['Ship_Date'].dt.strftime('%m/%d/%y')
    print('Original release set')
    print(df_1)
    df_2 = df_1.groupby(['Part_No_Revision', 'Ship_Date']).sum(
                    'Quantity').reset_index()
    df_2['Ship_Date'] = pd.to_datetime(df_2['Ship_Date'],
                                format='%m/%d/%y')
    # print(df_2)
    df_2.sort_values(by=['Part_No_Revision','Ship_Date'],inplace=True)
    # print(df_2)
    df_2['Ship_Date'] = df_2['Ship_Date'].dt.strftime('%#m/%#d/%y')
    df_2['Quantity'] = df_2['Quantity'] - df_2['Shipped']
    print('Grouped releases')
    print(df_2)
    # Removes any duplicate operation types.
    # TODO - 1/17/2022 - Check if still needed after switching data sources
    df_2 = df_2.drop_duplicates(subset=['Part_No_Revision','Ship_Date','Quantity'])
    print('after dropping duplicates')
    print(df_2)
    release_list = df_2[['Part_No_Revision','Ship_Date',
                            'Quantity']].values.tolist()
    # print(release_list)
    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    for x, y in enumerate(release_list):
        # print(x,y)
        try:
            eval_date = datetime.strptime(y[1], "%m/%d/%y")
        except ValueError:
            eval_date = datetime.strptime("01/01/90", 
                                            "%m/%d/%y")
        year_offest = weeks_for_year(int(
                                eval_date.strftime("%Y")))
        index = int(eval_date.strftime("%W")) \
                - int(monday.strftime("%W")) \
                + ((int(eval_date.strftime("%Y")) \
                - int(monday.strftime("%Y"))) \
                * year_offest)
        # print(index)
        group_start_date = monday + timedelta(weeks=index)
        # Inserts the index value into the release list
        release_list[x].insert(0,index)
        # Inserts the monday of each release for later grouping
        release_list[x].insert(1,
            group_start_date.strftime("%#m/%#d/%y"))
    # print(release_list)
    current_week_rel = [i for i in release_list if 
                        i[0] == 0]
    # print(current_week_rel)
    # Removes the "monday" value since it isn't needed for current week
    # This awkward list splitting is to keep the API download
    #   matching with the original level scheduling tool
    current_week_rel = [[i[2]] + [i[0]] + i[3:] for i in 
                        current_week_rel]
    # print(current_week_rel)
    # Groups the releases based on start of the week, excluding current week.
    week_grouped_releases = [(*k, sum(t[4] for t in g))
            for k,g in groupby(release_list, 
                        operator.itemgetter(2, 0, 1))]
    week_grouped_releases = [list(ele) for ele in 
                    week_grouped_releases if ele[1] != 0]
    # print("List of releases grouped by week's Monday")
    # pprint(week_grouped_releases)

    # Combines current week and grouped week releases
    combined_grouped_releases = current_week_rel \
                                + week_grouped_releases
    # print(combined_grouped_releases)
    for y, x in enumerate(combined_grouped_releases):
        """
        This is a stupid hack to create an excel based 
        lookup key based on the part+serial date 
        value in Excel using a text formula so I don't 
        need to re-do the Excel calculation function
        """
        x.insert(0, 
            f"=B{y+2}&D{y+2}")
    # pprint(combined_grouped_releases)
    df_3 = pd.DataFrame(combined_grouped_releases, columns=[
        'Lookup_Key','Part_No','Week_Index','Release_Date','Quantity'])
    release_file = os.path.join(source_dir, 
                                f'{file_prefix}cust_releases.csv')
    while True:
        try:
            df_3.to_csv(release_file, index=False)
            status.config(text=
                    f"Releases retrieved. File saved to {release_file}")
            break
        except PermissionError:
            if askokcancel('File In Use', f'Please close the file '
                        f'{release_file} in order to continue.'):
                continue
            else:
                status.config(text="Release download cancelled by user.")
                break


def api_customer_release_get(authentication, db, home_pcn, input_file):
    """
    Downloads and formats customer releases based on an input part list.
    
    Saves file to static location to be used with Level Scheduling 
    Excel workbooks
    """
    if db == 'test':
        db = 'test.'
    else:
        db = ''
    file_prefix = launch_pcn_dict[home_pcn]["prefix"]
    part_list = import_part_list(input_file)
    total_parts = len(part_list)
    df_1 = pd.DataFrame()
    for i, part_no in enumerate(part_list):
        progress_text = f'Getting releases for {part_no}    '\
                                f'[{i+1}/{total_parts}]'
        status.config(text=progress_text)
        query = {
            'inputs':{
                'Part_No': part_no
                }
            }
        api_id = '15596'
        url = f'https://{db}cloud.plex.com/api/datasources/'\
                f'{api_id}/execute'
        response = requests.post(url, json=query, auth=authentication)
        json_data = json.loads(response.text)
        # print(json_data)
        inventory_list = json_data['tables']
        if json_data['tables'][0]['rows'] == []:
            continue
        if df_1.empty:
            df_1 = json_normalize(inventory_list, 'rows')
            # print('first')
            # print(df_1)
        else:
            df = json_normalize(inventory_list, 'rows')
            # df_1 = df_1.append(df)
            df_1 = pd.concat([df_1, df])
            # print('next')
            # print (df_1)
    if df_1.empty:
        status.config(text=f"No releases for provided part numbers.")
        return
    df_1.columns = json_data['tables'][0]['columns']
    # Added exclusion for "Audit" operation types. This may cause issues with
    #   Other parts. Would need to query to see.
    # Can't use this. There are enough parts with only Audit operation types
    #   that this won't work.
    # Need to figure out how to remove duplicates from the results.
    # df_1 = df_1[df_1['Operation_Type'] != 'Audit']

    # Added conversion for Time zone. Plex API uses UTC, but that is causing
    #   some releases to be grouped with other dates. Converting to Eastern
    #   fixes this.
    df_1['Ship_Date'] = pd.to_datetime(df_1['Ship_Date'])
    df_1['Ship_Date'] = df_1['Ship_Date'].dt.tz_convert("US/Eastern")
    df_1['Ship_Date'] = pd.to_datetime(df_1['Ship_Date'],
                                        format='%Y-%m-%d')
    df_1['Ship_Date'] = df_1['Ship_Date'].dt.strftime('%m/%d/%y')
    # print(df_1)
    df_2 = df_1.groupby(['Part_No_Revision', 'Ship_Date', 'Operation_Type']).sum(
                    'Release_Balance').reset_index()
    df_2['Ship_Date'] = pd.to_datetime(df_2['Ship_Date'],
                                format='%m/%d/%y')
    # print(df_2)
    df_2.sort_values(by=['Part_No_Revision','Ship_Date'],inplace=True)
    # print(df_2)
    df_2['Ship_Date'] = df_2['Ship_Date'].dt.strftime('%#m/%#d/%y')
    df_2['Quantity'] = df_2['Quantity'] - df_2['Shipped']
    # print(df_2)
    # Removes any duplicate operation types.
    df_2 = df_2.drop_duplicates(subset=['Part_No_Revision','Ship_Date','Release_Balance'])
    # print('after dropping duplicates')
    # print(df_2)
    release_list = df_2[['Part_No_Revision','Ship_Date',
                            'Release_Balance']].values.tolist()
    # print(release_list)
    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    for x, y in enumerate(release_list):
        # print(x,y)
        try:
            eval_date = datetime.strptime(y[1], "%m/%d/%y")
        except ValueError:
            eval_date = datetime.strptime("01/01/90", 
                                            "%m/%d/%y")
        year_offest = weeks_for_year(int(
                                eval_date.strftime("%Y")))
        index = int(eval_date.strftime("%W")) \
                - int(monday.strftime("%W")) \
                + ((int(eval_date.strftime("%Y")) \
                - int(monday.strftime("%Y"))) \
                * year_offest)
        # print(index)
        group_start_date = monday + timedelta(weeks=index)
        # Inserts the index value into the release list
        release_list[x].insert(0,index)
        # Inserts the monday of each release for later grouping
        release_list[x].insert(1,
            group_start_date.strftime("%#m/%#d/%y"))
    # print(release_list)
    current_week_rel = [i for i in release_list if 
                        i[0] == 0]
    # print(current_week_rel)
    # Removes the "monday" value since it isn't needed for current week
    # This awkward list splitting is to keep the API download
    #   matching with the original level scheduling tool
    current_week_rel = [[i[2]] + [i[0]] + i[3:] for i in 
                        current_week_rel]
    # print(current_week_rel)
    # Groups the releases based on start of the week, excluding current week.
    week_grouped_releases = [(*k, sum(t[4] for t in g))
            for k,g in groupby(release_list, 
                        operator.itemgetter(2, 0, 1))]
    week_grouped_releases = [list(ele) for ele in 
                    week_grouped_releases if ele[1] != 0]
    # print("List of releases grouped by week's Monday")
    # pprint(week_grouped_releases)

    # Combines current week and grouped week releases
    combined_grouped_releases = current_week_rel \
                                + week_grouped_releases
    # print(combined_grouped_releases)
    for y, x in enumerate(combined_grouped_releases):
        """
        This is a stupid hack to create an excel based 
        lookup key based on the part+serial date 
        value in Excel using a text formula so I don't 
        need to re-do the Excel calculation function
        """
        x.insert(0, 
            f"=B{y+2}&D{y+2}")
    # pprint(combined_grouped_releases)
    df_3 = pd.DataFrame(combined_grouped_releases, columns=[
        'Lookup_Key','Part_No','Week_Index','Release_Date','Quantity'])
    release_file = os.path.join(source_dir, 
                                f'{file_prefix}cust_releases.csv')
    while True:
        try:
            df_3.to_csv(release_file, index=False)
            status.config(text=
                    f"Releases retrieved. File saved to {release_file}")
            break
        except PermissionError:
            if askokcancel('File In Use', f'Please close the file '
                        f'{release_file} in order to continue.'):
                continue
            else:
                status.config(text="Release download cancelled by user.")
                break


def mrp(user_name, password, company_code, db, home_pcn, input_file):
    """
    Function to download MRP demand. 
    
    Only available with API download.
    """
    if user_name == '' or password == '' or company_code == '':
        status.config(text=login_error_text)
        tab_control.select(0)
    else:
        # Initialize the user account to be used for login
        pcn = launch_pcn_dict[home_pcn]["pcn"]
        file_prefix = launch_pcn_dict[home_pcn]["prefix"]
        authentication = get_auth(home_pcn)

        if authentication.username == '' or authentication.password == '':
            status.config(text=pcn_error_text)
            tab_control.select(0)
            mrp_selector.config(text=selector_text, anchor=W)
            mrp_button_start.config(state=DISABLED)
            return
        # Call the function in a thread so the GUI doesn't hang while it runs.
        global t
        t = threading.Thread(target=lambda: mrp_get(authentication, db, 
                                home_pcn, input_file))
        t.start()
        status.config(text="Getting MRP demand.")
        mrp_selector.config(text=selector_text, anchor=W)
        mrp_button_start.config(state=DISABLED)


def mrp_get(authentication, db, home_pcn, input_file):
    if db == 'test':
        db = 'test.'
    else:
        db = ''
    """
    Forecast_Window is the number of weeks to return
    Releases seems to always include an extra day in calculation
        I.E. 1 will return 8 days of releases
            2 will return 15 days of releases
    Sales Requirements are returned based on the exact forecast window provided
    Job Requirements is not really clear based on my testing so far
        241269-20 shows job req of 2475
        Plex seems to show 1350 job demand and 1232 net demand job
            This becomes 2582, which is 107 over what the API shows
    """
    file_prefix = launch_pcn_dict[home_pcn]["prefix"]
    part_list = import_part_list(input_file)
    df_1 = pd.DataFrame()
    total_parts = len(part_list)
    api_id = '3367'
    url = f'https://{db}cloud.plex.com/api/datasources/'\
                f'{api_id}/execute'
    list_of_urls = [(url, form_data, authentication) 
        for form_data in map(create_mrp_json, part_list)]
    
    with ThreadPoolExecutor(max_workers=25) as pool:
        response_list = list(pool.map(post_url,list_of_urls))
    
    for p, response in enumerate(response_list):
    # for i, part_no in enumerate(part_list):
        # progress_text = f'Getting releases for {part_no}    '\
        #                         f'[{i+1}/{total_parts}]'
        # status.config(text=progress_text)
        # api_id = '3367'
        # query = {
        #     'inputs':{
        #         "Part_No": part_no,
        #         # "Finished_Part_Key": finished_key,
        #         "Forecast_Window": 6
        #         }
        #     }
        # url = f'https://{db}cloud.plex.com/api/datasources/'\
        #         f'{api_id}/execute'
        # response = requests.post(url, json=query, auth=authentication)
        # file.write(json.dumps(response.json()))
        json_data = json.loads(response.text)
        # print(json_data)
        release_list = json_data['tables']
        if json_data['tables'][0]['rows'] == []:
            continue
        if df_1.empty:
            df_1 = json_normalize(release_list, 'rows')
        else:
            df = json_normalize(release_list, 'rows')
            # df_1 = df_1.append(df)
            df_1 = pd.concat([df_1, df])
        # print(df_1)
    if df_1.empty:
        status.config(text=
                    f"No demand for provided part numbers.")
        return
    df_1.columns = json_data['tables'][0]['columns']
    df_1['Sales_Requirements'] = round(
                                    df_1['Sales_Requirements'])
    mrp_file = os.path.join(source_dir, 
                                f'{file_prefix}mrp_demand.csv')
    while True:
        try:
            df_1[['Part_No_Revision','Sales_Requirements']].to_csv(
                mrp_file, index=FALSE)
            status.config(text=
                    f"MRP demand retrieved. File saved to {mrp_file}")
            break
        except PermissionError:
            if askokcancel('File In Use', f'Please close the file '
                        f'{mrp_file} in order to continue.'):
                continue
            else:
                status.config(text="MRP download cancelled by user.")
                break


def prp(user_name, password, company_code, db, home_pcn, input_file):
    """
    Function to download PRP demand. 
    
    Only available with web service download.
    """
    if user_name == '' or password == '' or company_code == '':
        status.config(text=login_error_text)
        tab_control.select(0)
    else:
        # Initialize the user account to be used for login
        pcn = launch_pcn_dict[home_pcn]["pcn"]
        file_prefix = launch_pcn_dict[home_pcn]["prefix"]
        authentication = get_auth(home_pcn)

        if authentication.username == '' or authentication.password == '':
            status.config(text=pcn_error_text)
            tab_control.select(0)
            prp_selector.config(text=selector_text, anchor=W)
            prp_button_start.config(state=DISABLED)
            return
        # Call the function in a thread so the GUI doesn't hang while it runs.
        global t
        # t = threading.Thread(target=lambda: prp_get_plex(user_name, password, 
        #                      company_code, pcn, db, home_pcn, input_file))
        t = threading.Thread(target=lambda: prp_get_api(authentication, 
                             db, home_pcn, input_file))
        t.start()
        status.config(text="Getting PRP demand.")
        prp_selector.config(text=selector_text, anchor=W)
        prp_button_start.config(state=DISABLED)


def prp_get_api(authentication, db, home_pcn, input_file):
    if db == 'test':
        db = 'test.'
    else:
        db = ''
    """
    authentication = get_auth('Magnode')
    api_id  = '15851'
    query = (
        ('Part_Key', '3550251'), # 246807-22
        ('From_PRP', True),
        ('Begin_Date','2001-10-01T04:00:00.000Z'),
        ('End_Date','2022-12-10T04:00:00.000Z')
)
    """
    api_id = '9094' #Part_Key_Get 
    file_prefix = launch_pcn_dict[home_pcn]["prefix"]
    part_key_dict = {}
    # Read input file and create query strings to get part keys
    with open(input_file) as infile:
        part_rev = []
        csv_reader = csv.reader(infile)
        for i, row in enumerate(csv_reader):
            if i==0:
                continue
            if not row:
                continue
            part = row[0].rpartition('-')[0]
            revision = row[0].rpartition('-')[-1]

            query = (
                ('Part_No', part),
                ('Revision', revision)
            )
            part_rev.append(query)
    # Get all part keys for the above list
    with ThreadPoolExecutor(max_workers=100) as executor:
        url = f'https://{db}cloud.plex.com/api/datasources/{api_id}/execute'
        list_of_urls = [(url,{'inputs': dict(query)}, authentication) for query in part_rev]
        futures = [executor.submit(ux.post_url, parts) for parts in list_of_urls]

        for future in as_completed(futures):
            result = future.result()
            part_key = str(json.loads(result.text)['outputs']['Part_Key'])
            inputs = json.loads(result.request.body.decode('utf-8'))['inputs']
            if part_key not in part_key_dict.items():
                part_key_dict[part_key] = inputs
    
    part_list = import_part_list(input_file)
    df_1 = pd.DataFrame()
    total_parts = len(part_list)
    prp_list = []
    today = date.today()
    ed = ux.plex_date_formater(today, date_offset=56)

    # Create Query string for part keys
    for i, (key,item) in enumerate(part_key_dict.items()):
        
        part = part_key_dict[key]['Part_No']
        revision = part_key_dict[key]['Revision']
        query = (
            ('Part_Key', key),
            ('From_PRP', True),
            ('Begin_Date', '2001-10-01T04:00:00.000Z'), # Do I need to make this dynamic?
            ('End_Date',ed)
        )
        prp_list.append(query)
    api_id  = '15851' # Part_Requirement_Plan_Parent_Demand_Detail_Get 
    with ThreadPoolExecutor(max_workers=100) as executor:
        url = f'https://{db}cloud.plex.com/api/datasources/{api_id}/execute'
        list_of_urls = [(url,{'inputs': dict(query)}, authentication) 
                        for query in prp_list]
        futures = [executor.submit(ux.post_url, prp) for prp in list_of_urls]
        for future in as_completed(futures):
            result = future.result()
            part_key = json.loads(result.request.body.decode('utf-8')
                                 )['inputs']['Part_Key']
            part_no = part_key_dict[part_key]['Part_No']
            rev = part_key_dict[part_key]['Revision']
            json_result = json.loads(result.text)
            response_list = json_result['tables'][0]
            if json_result['tables'][0]['rows'] == []:
                continue
            if df_1.empty:
                df_1 = json_normalize(response_list, 'rows')
                df_1.insert(0,'Component_Part_No_Rev', [part_no+'-'+rev 
                            for p in response_list['rows']])
            else:
                df = json_normalize(response_list, 'rows')
                df.insert(0,'Component_Part_No_Rev', [part_no+'-'+rev 
                            for p in response_list['rows']])
                df_1 = pd.concat([df_1, df])
        df_1.columns = ['Component_Part_No_Rev']+json_result['tables'][0]['columns']
        df_1 = df_1.assign(Calc_Demand= lambda x: x.Quantity*x.BOM_Conversion)
    index = None
    group_start_date = None

    df_1 = df_1.assign(Week_Index= lambda x :index)
    df_1 = df_1.assign(Week_Start= lambda x :group_start_date)
    df_1['Week_Index'] = df_1.apply(lambda p: ux.get_week_index(
                         p['Due_Date'],-1)[1], axis=1).astype(str)
    df_1['Week_Start'] = df_1.apply(lambda p: ux.get_week_index(
                         p['Due_Date'],-1)[0], axis=1)
    # df_1.to_csv('prp_group_test.csv', index=0)
    df_g = df_1.groupby(by=['Component_Part_No_Rev',
                            'Week_Index',
                            'Week_Start']).sum().reset_index()
    df_r = df_g
    df_r['Calc_Demand'] = df_g['Calc_Demand'].apply(np.ceil)
    df_r.insert(0,'Lookup', df_r[['Component_Part_No_Rev',
                                  'Week_Index']].agg('-'.join, axis=1))

    # api_id = '15851'
    # url = f'https://{db}cloud.plex.com/api/datasources/'\
    #             f'{api_id}/execute'
    # list_of_urls = [(url, form_data, authentication) 
    #     for form_data in map(create_prp_json, part_list)]
    
    # with ThreadPoolExecutor(max_workers=25) as pool:
    #     response_list = list(pool.map(post_url,list_of_urls))
    
    # for p, response in enumerate(response_list):
    # # for i, part_no in enumerate(part_list):
    #     # progress_text = f'Getting releases for {part_no}    '\
    #     #                         f'[{i+1}/{total_parts}]'
    #     # status.config(text=progress_text)
    #     # api_id = '3367'
    #     # query = {
    #     #     'inputs':{
    #     #         "Part_No": part_no,
    #     #         # "Finished_Part_Key": finished_key,
    #     #         "Forecast_Window": 6
    #     #         }
    #     #     }
    #     # url = f'https://{db}cloud.plex.com/api/datasources/'\
    #     #         f'{api_id}/execute'
    #     # response = requests.post(url, json=query, auth=authentication)
    #     # file.write(json.dumps(response.json()))
    #     json_data = json.loads(response.text)
    #     # print(json_data)
    #     release_list = json_data['tables']
    #     if json_data['tables'][0]['rows'] == []:
    #         continue
    #     if df_1.empty:
    #         df_1 = json_normalize(release_list, 'rows')
    #     else:
    #         df = json_normalize(release_list, 'rows')
    #         df_1 = pd.concat([df_1, df])
        # print(df_1)
    if df_1.empty:
        status.config(text=
                    f"No demand for provided part numbers.")
        return
    # df_1.columns = json_data['tables'][0]['columns']
    # df_1['Net_Demand'] = round(df_1['Net_Demand'])
    df_r.sort_values(by=['Lookup'], inplace=True)
    prp_file = os.path.join(source_dir, 
                                f'{file_prefix}prp_demand.csv')
    while True:
        try:
            df_r.to_csv(prp_file, index=FALSE)
            # df_1[[
            #       'Part_No_Revision',
            #       'Inventory',
            #       'Past_Due',
            #       'Demand_Date',
            #       'Scheduled',
            #       'Net_Demand'
            #       ]].to_csv(
            #     prp_file, index=FALSE)
            status.config(text=
                    f"PRP demand retrieved. File saved to {prp_file}")
            break
        except PermissionError:
            if askokcancel('File In Use', f'Please close the file '
                        f'{prp_file} in order to continue.'):
                continue
            else:
                status.config(text="PRP download cancelled by user.")
                break


def prp_get_plex(u, p, c, pcn, db, home_pcn, parts_file):
    file_prefix = launch_pcn_dict[home_pcn]["prefix"]
    plex = Plex('UX', u, p, c, pcn, db=db, use_config=False,
                pcn_path=pcn_file, cumulus=0)
    plex.frozen_check()
    plex.download_chrome_driver()
    plex.config()
    driver, url_comb, url_token = plex.login()
    # logger = plex.setup_logger('PRP Download')
    plex.switch_pcn(pcn)
    df_2 = pd.DataFrame()
    total_parts = len(open(parts_file).readlines()) - 1
    with open(parts_file, 'r', encoding='utf-8-sig') as fin:
        csv_reader = csv.reader(fin, delimiter=',')
        for i, row in enumerate(csv_reader):
            if not row:
                continue
            if i == 0:
                col_dict = plex.make_csv_dict(row)
                continue
            part_no = row[col_dict['Part No']]
            status.config(text=f"Getting PRP demand. {part_no} - {i}/{total_parts}")
            driver.get(f'{url_comb}/Scheduling/ProductionRequirementsPlanning'
                       f'?PartNo={part_no}'
                       f'&Search=1'
                       f'&Window=3'
                       f'&WindowUnit=Weeks'
                       f'&xPCN={pcn}'
                       )
            time.sleep(1)
            prp_columns=[]
            prp_rows=[]
            tables=WebDriverWait(driver,20).until(
                EC.presence_of_element_located(
                (By.XPATH,
                "//*[@id='ProductionRequirementsPlanningGrid']/div[2]"
                "/table/tbody/tr[1]/td[1]/a/span")
                ))
            table_header = driver.find_element(By.XPATH,
                "//*[@id='ProductionRequirementsPlanningGrid']/div[2]"
                "/table/thead")
            table_body = driver.find_element(By.XPATH,
                "//*[@id='ProductionRequirementsPlanningGrid']/div[2]"
                "/table/tbody")
            for i, row in enumerate(table_header.find_elements(By.XPATH,
                                    ".//tr")):
                # print('row', i)
                for j, header in enumerate(row.find_elements(By.XPATH,
                                           './th')):
                    # print('header', j)
                    try:
                        element = header.find_element(By.XPATH, './div/abbr'
                        ).get_attribute('textContent')
                        # print('abbr', element)
                        prp_columns.append(element)
                    except NoSuchElementException:
                        try:
                            element = header.find_element(By.XPATH, 
                                            './div/span'
                            ).get_attribute('textContent')
                            # print('span', element)
                            prp_columns.append(element)
                        except NoSuchElementException:
                            # print('skipping row', i)
                            continue 
            # for table in table_body:
            for i, row in enumerate(table_body.find_elements(By.XPATH,
                                    ".//tr")):
                # print(row)
                row_list = []
                body_cells = row.find_elements(By.XPATH,'./td')
                pad_list = True
                for j, body in enumerate(body_cells):
                    # print('body', j)
                    row_cells = row.find_elements(By.XPATH,'./td')
                    if len(body_cells)  < len(prp_columns) and pad_list:
                        col_index = int(body.get_attribute('data-col-index'))
                        index = len(prp_columns) - col_index
                        for z in range(index):
                            row_list.append('')
                        pad_list = False
                    try:
                        element = body.find_element(By.XPATH,'./a/span'
                        ).get_attribute('textContent')
                        row_list.append(element)
                    except NoSuchElementException:
                        try:
                            element = body.find_element(By.XPATH,'./a'
                            ).get_attribute('textContent')
                            row_list.append(element)
                        except NoSuchElementException:
                            try:
                                element = body.find_element(By.XPATH,'.'
                                ).get_attribute('textContent')
                                row_list.append(element)
                            except NoSuchElementException:
                                row_list.append('')
                                # print('skipping row', i)
                                continue 
                prp_rows.append(row_list)
                df = pd.DataFrame(columns=prp_columns, data=prp_rows)
            if df_2.empty:
                # print('empty df_2')
                df_2 = df
            else:
                # print('df_2', df_2)
                df_2 = pd.concat([df_2, df])
    # print(prp_rows)
    # print(prp_columns)
    # df = pd.DataFrame(columns=prp_columns, data=prp_rows)
    # print(df)
    df_2 = pd.melt(df_2,id_vars=prp_columns[::5], value_vars=prp_columns[6::])
    # print(df_2)
    df_2['Part No / Name'] = df_2['Part No / Name'].fillna('')
    df_2.loc[df_2['Part No / Name']=='','Part No / Name'] = np.nan
    df_2 = df_2.ffill(axis = 0)
    # print(df_2)
    df_2['Lookup'] = df_2[['Part No / Name', 'Demand Type', 'variable']].agg(''.join, axis=1)
    df_2 = df_2[['Lookup','Part No / Name', 'Demand Type', 'variable','value']]
    print(df_2)
    # df_2 = df_2.sort_values(by=['Lookup'])
    # df_2.to_csv('prp_test.csv')
    # status.config(text='Finished')
    prp_file = os.path.join(source_dir, f'{file_prefix}prp_demand.csv')
    while True:
        try:
            df_2.to_csv(prp_file, index=False)
            status.config(text=
                    f"PRP demand retrieved. File saved to {prp_file}")
            break
        except PermissionError:
            if askokcancel('File In Use', f'Please close the file '
                        f'{prp_file} in order to continue.'):
                continue
            else:
                status.config(text="PRP download cancelled by user.")
                break


def browse_release():
    root.filename = \
        filedialog.askopenfilename(initialdir="",
                                   title="Select the csv file containing the"
                                   " release information",
                                   filetypes=(("csv files", "*.csv"),
                                              ("all files", "*.*")))
    if root.filename:
        file_selector.config(text=root.filename, anchor=E)
        status.config(text="File selected. Ready to begin.")
        button_start.config(state=NORMAL)


def browse_inv():
    root.filename = \
        filedialog.askopenfilename(initialdir="",
                                   title="Select the csv file containing part"
                                   " information",
                                   filetypes=(("csv files", "*.csv"),
                                              ("all files", "*.*")))
    if root.filename:
        inv_selector.config(text=root.filename, anchor=E)
        status.config(text="File selected. Ready to begin.")
        inv_button_start.config(state=NORMAL)


def browse_mrp():
    root.filename = \
        filedialog.askopenfilename(initialdir="",
                                   title="Select the csv file containing part"
                                   " information",
                                   filetypes=(("csv files", "*.csv"),
                                              ("all files", "*.*")))
    if root.filename:
        mrp_selector.config(text=root.filename, anchor=E)
        status.config(text="File selected. Ready to begin.")
        mrp_button_start.config(state=NORMAL)


def browse_prp():
    root.filename = \
        filedialog.askopenfilename(initialdir="",
                                   title="Select the csv file containing part"
                                   " information",
                                   filetypes=(("csv files", "*.csv"),
                                              ("all files", "*.*")))
    if root.filename:
        prp_selector.config(text=root.filename, anchor=E)
        status.config(text="File selected. Ready to begin.")
        prp_button_start.config(state=NORMAL)


def browse_cust():
    root.filename = \
        filedialog.askopenfilename(initialdir="",
                                   title="Select the csv file containing part"
                                   " information",
                                   filetypes=(("csv files", "*.csv"),
                                              ("all files", "*.*")))
    if root.filename:
        cust_selector.config(text=root.filename, anchor=E)
        status.config(text="File selected. Ready to begin.")
        cust_button_start.config(state=NORMAL)


def pcn_changed(event):
    config_path = Path(os.path.join(source_dir,'config.ini'))
    config = configparser.ConfigParser()
    if not config_path.is_file():
        config['Plex'] = {}
        config['Plex']['Launch_PCN'] = 'Grand Haven'
        config['Plex']['Company_Code'] = 'Shape-Corp'
        with open(config_path, 'w+') as configfile:
            config.write(configfile)
    else:
        config['Plex'] = {}
        config['Plex']['Launch_PCN'] = clicked.get()
        config['Plex']['Company_Code'] = entry_pcn.get()
        with open(config_path, 'w+') as configfile:
            config.write(configfile)


def pcn_get():
    config_path = Path(os.path.join(source_dir,'config.ini'))
    config = configparser.ConfigParser()
    if not config_path.is_file():
        config['Plex'] = {}
        config['Plex']['Launch_PCN'] = 'Grand Haven'
        config['Plex']['Company_Code'] = 'Shape-Corp'
        with open(config_path, 'w+') as configfile:
            config.write(configfile)
    config.read(config_path)
    launch_pcn = config['Plex']['Launch_PCN']
    company_code = config['Plex']['Company_Code']
    return launch_pcn, company_code


# Creating Logos and images
im = Image.open(os.path.join(bundle_dir,'resources/Shape-CorpUS.png'))
im = im.resize((round(im.size[0]*0.25), round(im.size[1]*0.25)), resample=4)
shape_image = ImageTk.PhotoImage(im)
shape_icon = Label(bg=mygray, image=shape_image)

h = Image.open(os.path.join(bundle_dir,'resources/help.png'))
h = h.resize((round(h.size[0]*0.15), round(h.size[1]*0.15)), resample=4)
help_image = ImageTk.PhotoImage(h)
help_icon = Label(bg=mygray, image=help_image, anchor=NE)

pl = Image.open(os.path.join(bundle_dir,'resources/Plex.png'))
plex_image = ImageTk.PhotoImage(pl)


# Creating widgets

def tab_creator(title_list):
    """
    Create GUI tabs from a list of titles.
    """
    tabs = {}
    for i, title in enumerate(title_list):
        tab_text = title
        tab = Frame(tab_control)
        tabs[f"frame_{i+1}"] = Frame(tab, padx=5, pady=5)
        tab.pack(fill="both", expand=1)
        tab_control.add(tab, text=tab_text)
        tabs[f"frame_{i+1}"].grid(row=1, column=0, columnspan=3, padx=10, 
                                  pady=10)
    return tabs

tab_control = ttk.Notebook(root)
title_list = [
    'Login Details',
    'Get Current Inventory',
    'Get Customer Releases',
    'Create Supplier Releases',
    'Get MRP Demand',
    'Get PRP Demand'
    ]
tabs = tab_creator(title_list)
# print(tabs)
tab_control.grid(row=1, column=0, columnspan=3, padx=10, pady=10)


# Login widgets
db = StringVar(value="prod")
entry_user = Entry(tabs["frame_1"], width=25, relief=SOLID)
entry_pass = Entry(tabs["frame_1"], width=25, relief=SOLID, show="*")
entry_pcn = Entry(tabs["frame_1"], width=25, relief=SOLID)
entry_pcn.bind('<FocusOut>', pcn_changed)
label_user = Label(tabs["frame_1"], text="User ID:")
label_pass = Label(tabs["frame_1"], text="Password:")
label_pcn = Label(tabs["frame_1"], text="Company Code:")
label_home_pcn = Label(tabs["frame_1"], text="PCN:")
label_db = Label(tabs["frame_1"], text="Database:")

# PCN Dropdown list
clicked = StringVar()
clicked.set(pcn_get()[0])
options = ["Grand Haven",
    "Athens",
    "Czech",
    "Mexico",
    "Kunshan",
    "Guangzhou",
    "Magnode"]
launch_pcn = ttk.OptionMenu(tabs["frame_1"], clicked, pcn_get()[0], *options,
                            command=pcn_changed)
db_frame = Frame(tabs["frame_1"])
db_prod = ttk.Radiobutton(db_frame, width=10, variable=db, text="Production", 
                          value="prod")
db_test = ttk.Radiobutton(db_frame, width=10,  variable=db, text="Test", 
                          value="test")
plex_logo = Label(tabs["frame_1"], bg=plexdarkblue, image=plex_image)

# Login Layout
label_user.grid(row=0, column=0, sticky=E)
label_pass.grid(row=1, column=0, sticky=E)
label_pcn.grid(row=2, column=0, sticky=E)
label_home_pcn.grid(row=3, column=0, sticky=E)
label_db.grid(row=4, column=0, sticky=E)
entry_user.grid(row=0, column=1)
entry_pass.grid(row=1, column=1)
entry_pcn.grid(row=2, column=1)
launch_pcn.grid(row=3, column=1, sticky="ew", padx=(1,1), pady=(1,1))
db_frame.grid(row=4, column=1)
db_prod.grid(row=0, column=0, pady=1, padx=1)
db_test.grid(row=0, column=2, pady=1, padx=1)

# Sets the text variables
content = StringVar()
text = content.get()
content.set(text)

# Set default company code.
entry_pcn.insert(0, pcn_get()[1])

# Plex logo
plex_logo.grid(row=0, column=2, rowspan=3, padx=(25,0))


# Get Inventory widgets
inv_selector = Label(tabs["frame_2"], width=50, padx=3, pady=3, text=selector_text,
                     relief=SOLID, anchor=W, bd=1)
inv_button_browse = ttk.Button(tabs["frame_2"], text="Browse", width=15,
                               command=browse_inv)
inv_button_start = ttk.Button(tabs["frame_2"], text="Start", width=15, state=DISABLED,
                              command=lambda: subcon_inventory(entry_user.get(),
                                                        entry_pass.get(),
                                                        entry_pcn.get(),
                                                        db.get(),
                                                        clicked.get(),
                                                        inv_selector.cget(
                                                                    "text")))
inv_selector.grid(row=1, column=1, sticky=W+E)
inv_button_browse.grid(row=1, column=2, padx=3, pady=1)
inv_button_start.grid(row=2, column=2, padx=3, pady=1)


# Get Customer Release widgets
cust_selector = Label(tabs["frame_3"], width=50, padx=3, pady=3, text=selector_text,
                     relief=SOLID, anchor=W, bd=1)
cust_button_browse = ttk.Button(tabs["frame_3"], text="Browse", width=15,
                               command=browse_cust)
cust_button_start = ttk.Button(tabs["frame_3"], text="Start", width=15, state=DISABLED,
                              command=lambda: cust_rel(entry_user.get(),
                                                        entry_pass.get(),
                                                        entry_pcn.get(),
                                                        db.get(),
                                                        clicked.get(),
                                                        cust_selector.cget(
                                                                    "text")))
cust_selector.grid(row=1, column=1, sticky=W+E)
cust_button_browse.grid(row=1, column=2, padx=3, pady=1)
cust_button_start.grid(row=2, column=2, padx=3, pady=1)


# Create Release widgets
file_selector = Label(tabs["frame_4"], width=50, padx=3, pady=3, text=selector_text,
                      relief=SOLID, anchor=W, bd=1)
button_browse = ttk.Button(tabs["frame_4"], width=15, text="Browse",
                           command=browse_release)
button_start = ttk.Button(tabs["frame_4"], text="Start", width=15, state=DISABLED,
                          command=lambda: releases(entry_user.get(),
                                                   entry_pass.get(),
                                                   entry_pcn.get(),
                                                   db.get(),
                                                   clicked.get(),
                                                   file_selector.cget("text")))
file_selector.grid(row=1, column=1, sticky=W+E)
button_browse.grid(row=1, column=2, padx=3, pady=1)
button_start.grid(row=2, column=2, padx=3, pady=1)


# Get MRP Demand widgets
mrp_selector = Label(tabs["frame_5"], width=50, padx=3, pady=3, text=selector_text,
                      relief=SOLID, anchor=W, bd=1)
mrp_button_browse = ttk.Button(tabs["frame_5"], width=15, text="Browse",
                           command=browse_mrp)
mrp_button_start = ttk.Button(tabs["frame_5"], text="Start", width=15, state=DISABLED,
                          command=lambda: mrp(entry_user.get(),
                                                   entry_pass.get(),
                                                   entry_pcn.get(),
                                                   db.get(),
                                                   clicked.get(),
                                                   mrp_selector.cget(
                                                                      "text")))
mrp_selector.grid(row=1, column=1, sticky=W+E)
mrp_button_browse.grid(row=1, column=2, padx=3, pady=1)
mrp_button_start.grid(row=2, column=2, padx=3, pady=1)

# PRP Buttons
prp_selector = Label(tabs["frame_6"], width=50, padx=3, pady=3, text=selector_text,
                      relief=SOLID, anchor=W, bd=1)
prp_button_browse = ttk.Button(tabs["frame_6"], width=15, text="Browse",
                           command=browse_prp)
prp_button_start = ttk.Button(tabs["frame_6"], text="Start", width=15, state=DISABLED,
                          command=lambda: prp(entry_user.get(),
                                                   entry_pass.get(),
                                                   entry_pcn.get(),
                                                   db.get(),
                                                   clicked.get(),
                                                   prp_selector.cget(
                                                                      "text")))
prp_selector.grid(row=1, column=1, sticky=W+E)
prp_button_browse.grid(row=1, column=2, padx=3, pady=1)
prp_button_start.grid(row=2, column=2, padx=3, pady=1)
# Main widgets

# Status bar
status = Label(root, text="Ready.", bd=1, relief=FLAT, anchor=E, bg=mygray)
status.grid(row=3, column=0, columnspan=3, sticky=W+E)

# Icons
shape_icon.grid(row=0, column=0, padx=10, pady=5, sticky=N+W)
help_icon.grid(row=0, column=1, padx=10, pady=5, sticky=N+E)

# Setting root variables
root.grid_rowconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.configure(bg=mygray)
root.focus()
root.bind('<Button-1>', help_file)

# Starting the GUI
root.mainloop()
