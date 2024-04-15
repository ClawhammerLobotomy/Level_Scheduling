# New package structure imports
import utils

from datetime import datetime, timedelta, date
import argparse
log_file = 'debug_log.log'
parser = argparse.ArgumentParser()
parser.add_argument('-d','--debug',action='store_true',help='Use this to print and log debug messages.')
parser.add_argument('--headless',action='store_false',help='Use this to launch the supplier release creation with a visible browser session.')
args = parser.parse_args()

utils.debug_print(f"Initial print command. Before any imports besides datetime and argparse modules.")

from plex_login_ux import Plex, LoginError
import ux_data_source_tools as UDST

from requests.auth import HTTPBasicAuth
from selenium.webdriver.common.by import By

import sys

import csv
from pathlib import Path

import time

import tkinter as tk
from PIL import ImageTk, Image
from tkinter import filedialog, Tk, Label, Entry, ttk, Checkbutton
from tkinter.messagebox import askokcancel, askyesno, showinfo

import os
import threading
import __main__

from itertools import groupby
from collections import defaultdict
import operator

import configparser

import zipfile
import requests

from shutil import copyfile

# Newly added imports for API
from collections import OrderedDict
import json
import pandas as pd
import numpy as np
from pandas import json_normalize 
from concurrent.futures import ThreadPoolExecutor, as_completed




utils.debug_print(f"All imports completed")

__author__ = 'Dan Sleeman'
__copyright__ = 'Copyright 2020, Level Scheduling Assistant'
__credits__ = ['Dan Sleeman']
__license__ = 'GPL-3'
__version__ = '2.3.21'
__maintainer__ = 'Dan Sleeman'
__email__ = 'sleemand@shapecorp.com'
__status__ = 'Production'



# file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8',delay=True)
# memory_handler = logging.handlers.MemoryHandler(capacity=100, flushLevel=logging.ERROR,target=file_handler)
# file_handler.setLevel(logging.DEBUG)
# logger = logging.getLogger(__name__)
# logger.addHandler(memory_handler)

# parser = argparse.ArgumentParser("simple_example")
# parser.add_argument('-d','--debug',action='store_true')
# args = parser.parse_args()

MASTER_FILE_DIR = 'H:\\OP-ShapeGlobal\\0708-IT\\Public\\Level Scheduling'
MASTER_SOURCE_DIR = os.path.join(MASTER_FILE_DIR,'Source_Files')
MAX_WORKERS = 8

CONTAINER_STATUS_FILE = 'container_statuses.csv'
MRP_LOCATION_FILE = 'mrp_locations.csv'
PCN_CONFIG_FILE = 'pcn_config.json'
SUBCON_LOCATION_FILE = 'subcon_locations.csv'
PCN_FILE = 'pcn.json'

SOURCE_FILE_LIST = [
    CONTAINER_STATUS_FILE,
    MRP_LOCATION_FILE,
    PCN_CONFIG_FILE,
    SUBCON_LOCATION_FILE,
    PCN_FILE
]

SOURCE_DIR = 'C:\\Level Sched INV'
# Default variables
HOME_PCN = '79870'
FILE_PREFIX = ''


class MissingInputData(Exception):
    pass

class LevelScheduling(object):
    def __init__(self):
        self.save_dir = SOURCE_DIR
        self.master_file_dir = MASTER_FILE_DIR
        self.master_source_dir = MASTER_SOURCE_DIR
        self.bundle_dir = utils.frozen_check()
        self.daily_release_weeks = utils.config_setup(1)
        self.source_file_list = SOURCE_FILE_LIST
        self.resource_dir = os.path.join(self.bundle_dir,'resources')
        self.get_latest_version()
    def network_presence(self):
        if not Path(self.master_source_dir).is_dir():
            debug_print(f'Could not find H: drive source files. Using local copies.')
            self.network_connected = False
        else:
            debug_print('Using H: drive source files.')
            utils.local_file_update(self)
            self.network_connected = True
        return
    def source_file_init(self):
        self.container_status_file = os.path.join(self.resource_dir,CONTAINER_STATUS_FILE)
        self.mrp_location_file = os.path.join(self.resource_dir,MRP_LOCATION_FILE)
        self.pcn_config_file = os.path.join(self.resource_dir,PCN_CONFIG_FILE)
        self.subcon_location_file = os.path.join(self.resource_dir,SUBCON_LOCATION_FILE)
        self.pcn_file = os.path.join(self.resource_dir,PCN_FILE)
        self.container_statuses = self.read_source_file(self.container_status_file)
        self.mrp_locations = self.read_source_file(self.mrp_location_file)
        self.subcon_locations = self.read_source_file(self.subcon_location_file)
        self.launch_pcn_dict = self.read_source_json(self.pcn_config_file)
        
        return
    def read_source_file(self,filename):
        with open(filename,'r',encoding='utf-8') as f:
            return f.read().split('\n')
    def read_source_json(self,filename):
        with open(filename, 'r', encoding='utf-8') as c:
            return json.load(c)
    def get_latest_version(self):
        try:
            self.latest_version = Path(os.path.join(self.master_source_dir,
                                'prod_version.txt')).read_text()
            print("Latest production version of the helper tool:", self.latest_version)
            print(f"You are running {__status__} version {__version__}")
            self.update = 1
        except FileNotFoundError:
            print('Error getting version info.')
            print('If you are connected to the VPN already, please open the H: drive'
                ,'folder and re-launch this app to get the latest source data.')
            self.latest_version = __version__
            self.update = 0
        if not __status__ == "Production" and self.latest_version >= __version__ and self.update == 1:
            askyesno('Update Available', f'You are using a beta version.'
            f'There is a new version available to download.\n'
            f'Would you like to download the latest version?')
            if tk.YES:
                utils.version_check()
        if __status__ == "Production" and self.latest_version >= __version__ and self.update == 1:
            utils.version_check()

    def chromedriver_override(self):
        try:
            self.chromedriver_override = Path(os.path.join(self.master_source_dir,
                                'chromedriver_override.txt')).read_text()
            print(f"Using chromedriver_version override: {self.chromedriver_override}")
        except FileNotFoundError:
            self.chromedriver_override = None


mainConf = LevelScheduling()
mainConf.source_file_init()
debug_print('Initializing UX_Data_Sources module')
ux = UDST.UX_Data_Sources()
debug_print('UX_Data_Sources module initialized')
debug_print(f'bundle directory: {mainConf.bundle_dir}')
debug_print(f'source file directory: {mainConf.master_source_dir}')


container_status_count = len(mainConf.container_statuses)
container_status_subset = max([round(container_status_count*.2),10])
debug_print(f'{container_status_count} Inventory container statuses.')
debug_print(f'Showing first {container_status_subset}: {mainConf.container_statuses[:container_status_subset]}')

mrp_location_count = len(mainConf.mrp_locations)
mrp_location_subset = max([round(mrp_location_count*.2),10])
debug_print(f'{mrp_location_count} MRP locations.')
debug_print(f'Showing first {mrp_location_subset}: {mainConf.mrp_locations[:mrp_location_subset]}')

subcon_location_count = len(mainConf.subcon_locations)
subcon_location_subset = max([round(subcon_location_count*.2),10])
debug_print(f'{subcon_location_count} Subcon locations.')
debug_print(f'Showing first {subcon_location_subset}: {mainConf.subcon_locations[:subcon_location_subset]}')

utils.folder_setup(mainConf.save_dir)

root = Tk()
root.title('Level Scheduling Helper')
root.iconbitmap(os.path.join(mainConf.resource_dir,'Shape.ico'))


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
            "anchor": tk.CENTER,
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





def help_file(event):
    if event.widget is help_icon:
        showinfo('About',f'Level Scheduling Helper Tool Version {__version__}\n'
                 f'For issues, contact {__maintainer__} - {__email__}')




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
            debug_print(f"Calling inventory for {args[1]}")
            request = requests.post(args[0], json=args[1], auth=args[2])
            break
        except Exception as e:
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
        # pcn = launch_pcn_dict[home_pcn]["pcn"]
        # file_prefix = launch_pcn_dict[home_pcn]["prefix"]
        # plex = Plex('classic', user_name, password, company_code, pcn, db=db,
        #             use_config=False, pcn_path=pcn_file, chromedriver_override=chromedriver_override)
        # Get the directory that script is running in
        # plex.frozen_check()
        # bundle_dir = plex.frozen_check()


        # Main function which performs all the Plex manipulation
        # Start in a thread so the GUI doesn't hang.
        # t = threading.Thread(target=do_release_update)
        t = threading.Thread(target=lambda:do_release_update(user_name,
                             password, company_code, db, home_pcn,input_file))
        t.start()
        status.config(text="Updating releases.")
        file_selector.config(text=selector_text, anchor=tk.W)
        button_start.config(state=tk.DISABLED)



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
        function_target = lambda: api_inventory_download(authentication, 
                              db, home_pcn, input_file)
        # Call the function in a thread so the GUI doesn't hang while it runs.
        global t
        t = threading.Thread(target=function_target)
        t.start()
        status.config(text="Getting inventory numbers.")
        inv_selector.config(text=selector_text, anchor=tk.W)
        inv_button_start.config(state=tk.DISABLED)



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
        function_target = lambda: api_customer_release_get(authentication, 
                              db, home_pcn, input_file)
        # Call the function in a thread so the GUI doesn't hang while it runs.
        global t
        t = threading.Thread(target=function_target)
        t.start()
        status.config(text="Getting customer releases.")
        cust_selector.config(text=selector_text, anchor=tk.W)
        cust_button_start.config(state=tk.DISABLED)



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
            mrp_selector.config(text=selector_text, anchor=tk.W)
            mrp_button_start.config(state=tk.DISABLED)
            return
        # Call the function in a thread so the GUI doesn't hang while it runs.
        global t
        t = threading.Thread(target=lambda: mrp_get(authentication, db, 
                                home_pcn, input_file))
        t.start()
        status.config(text="Getting MRP demand.")
        mrp_selector.config(text=selector_text, anchor=tk.W)
        mrp_button_start.config(state=tk.DISABLED)



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
            prp_selector.config(text=selector_text, anchor=tk.W)
            prp_button_start.config(state=tk.DISABLED)
            return
        # Call the function in a thread so the GUI doesn't hang while it runs.
        global t
        t = threading.Thread(target=lambda: prp_get_api(authentication, 
                             db, home_pcn, input_file))
        t.start()
        status.config(text="Getting PRP demand.")
        prp_selector.config(text=selector_text, anchor=tk.W)
        prp_button_start.config(state=tk.DISABLED)



def browse_release():
    root.filename = \
        filedialog.askopenfilename(initialdir="",
                                   title="Select the csv file containing the"
                                   " release information",
                                   filetypes=(("csv files", "*.csv"),
                                              ("all files", "*.*")))
    if root.filename:
        file_selector.config(text=root.filename, anchor=tk.E)
        status.config(text="File selected. Ready to begin.")
        button_start.config(state=tk.NORMAL)


def browse_inv():
    root.filename = \
        filedialog.askopenfilename(initialdir="",
                                   title="Select the csv file containing part"
                                   " information",
                                   filetypes=(("csv files", "*.csv"),
                                              ("all files", "*.*")))
    if root.filename:
        inv_selector.config(text=root.filename, anchor=tk.E)
        status.config(text="File selected. Ready to begin.")
        inv_button_start.config(state=tk.NORMAL)


def browse_mrp():
    root.filename = \
        filedialog.askopenfilename(initialdir="",
                                   title="Select the csv file containing part"
                                   " information",
                                   filetypes=(("csv files", "*.csv"),
                                              ("all files", "*.*")))
    if root.filename:
        mrp_selector.config(text=root.filename, anchor=tk.E)
        status.config(text="File selected. Ready to begin.")
        mrp_button_start.config(state=tk.NORMAL)


def browse_prp():
    root.filename = \
        filedialog.askopenfilename(initialdir="",
                                   title="Select the csv file containing part"
                                   " information",
                                   filetypes=(("csv files", "*.csv"),
                                              ("all files", "*.*")))
    if root.filename:
        prp_selector.config(text=root.filename, anchor=tk.E)
        status.config(text="File selected. Ready to begin.")
        prp_button_start.config(state=tk.NORMAL)


def browse_cust():
    root.filename = \
        filedialog.askopenfilename(initialdir="",
                                   title="Select the csv file containing part"
                                   " information",
                                   filetypes=(("csv files", "*.csv"),
                                              ("all files", "*.*")))
    if root.filename:
        cust_selector.config(text=root.filename, anchor=tk.E)
        status.config(text="File selected. Ready to begin.")
        cust_button_start.config(state=tk.NORMAL)


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


def toggle_password():
    if entry_pass.cget('show') == '':
        entry_pass.config(show='*')
    else:
        entry_pass.config(show='')


# Creating Logos and images
im = Image.open(os.path.join(bundle_dir,'resources/Shape-CorpUS.png'))
im = im.resize((round(im.size[0]*0.25), round(im.size[1]*0.25)), resample=4)
shape_image = ImageTk.PhotoImage(im)
shape_icon = Label(bg=mygray, image=shape_image)

h = Image.open(os.path.join(bundle_dir,'resources/help.png'))
h = h.resize((round(h.size[0]*0.15), round(h.size[1]*0.15)), resample=4)
help_image = ImageTk.PhotoImage(h)
help_icon = Label(bg=mygray, image=help_image, anchor=tk.NE)

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
        tab = tk.Frame(tab_control)
        tabs[f"frame_{i+1}"] = tk.Frame(tab, padx=5, pady=5)
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
db = tk.StringVar(value="prod")
entry_user = Entry(tabs["frame_1"], width=25, relief=tk.SOLID)
entry_pass = Entry(tabs["frame_1"], width=25, relief=tk.SOLID, show="*")
check_pass = Checkbutton(tabs["frame_1"],text='Show Password', onvalue=1,offvalue=0,command=toggle_password)
entry_pcn = Entry(tabs["frame_1"], width=25, relief=tk.SOLID)
entry_pcn.bind('<FocusOut>', pcn_changed)
label_user = Label(tabs["frame_1"], text="User ID:")
label_pass = Label(tabs["frame_1"], text="Password:")
label_pcn = Label(tabs["frame_1"], text="Company Code:")
label_home_pcn = Label(tabs["frame_1"], text="PCN:")
label_db = Label(tabs["frame_1"], text="Database:")

# PCN Dropdown list
clicked = tk.StringVar()
clicked.set(pcn_get()[0])
options = ["Grand Haven",
    "Athens",
    "Czech",
    "Mexico",
    "Kunshan",
    "Guangzhou",
    "Trenton"]
daily_release_weeks = config_setup(launch_pcn_dict[pcn_get()[0]]['default_week_no'])
launch_pcn = ttk.OptionMenu(tabs["frame_1"], clicked, pcn_get()[0], *options,
                            command=pcn_changed)
db_frame = tk.Frame(tabs["frame_1"])
db_prod = ttk.Radiobutton(db_frame, width=10, variable=db, text="Production", 
                          value="prod")
db_test = ttk.Radiobutton(db_frame, width=10,  variable=db, text="Test", 
                          value="test")
plex_logo = Label(tabs["frame_1"], bg=plexdarkblue, image=plex_image)

# Login Layout
label_user.grid(row=0, column=0, sticky=tk.E)
label_pass.grid(row=1, column=0, sticky=tk.E)
label_pcn.grid(row=3, column=0, sticky=tk.E)
label_home_pcn.grid(row=4, column=0, sticky=tk.E)
label_db.grid(row=5, column=0, sticky=tk.E)
entry_user.grid(row=0, column=1)
entry_pass.grid(row=1, column=1)
check_pass.grid(row=2,column=0,columnspan=2, sticky='ew', padx=(1,1), pady=(1,1))
entry_pcn.grid(row=3, column=1)
launch_pcn.grid(row=4, column=1, sticky="ew", padx=(1,1), pady=(1,1))
db_frame.grid(row=5, column=1)
db_prod.grid(row=0, column=0, pady=1, padx=1)
db_test.grid(row=0, column=2, pady=1, padx=1)

# Sets the text variables
content = tk.StringVar()
text = content.get()
content.set(text)

# Set default company code.
entry_pcn.insert(0, pcn_get()[1])

# Plex logo
plex_logo.grid(row=0, column=2, rowspan=3, padx=(25,0))


# Get Inventory widgets
inv_selector = Label(tabs["frame_2"], width=50, padx=3, pady=3, text=selector_text,
                     relief=tk.SOLID, anchor=tk.W, bd=1)
inv_button_browse = ttk.Button(tabs["frame_2"], text="Browse", width=15,
                               command=browse_inv)
inv_button_start = ttk.Button(tabs["frame_2"], text="Start", width=15, state=tk.DISABLED,
                              command=lambda: subcon_inventory(entry_user.get(),
                                                        entry_pass.get(),
                                                        entry_pcn.get(),
                                                        db.get(),
                                                        clicked.get(),
                                                        inv_selector.cget(
                                                                    "text")))
inv_selector.grid(row=1, column=1, sticky=tk.W+tk.E)
inv_button_browse.grid(row=1, column=2, padx=3, pady=1)
inv_button_start.grid(row=2, column=2, padx=3, pady=1)


# Get Customer Release widgets
cust_selector = Label(tabs["frame_3"], width=50, padx=3, pady=3, text=selector_text,
                     relief=tk.SOLID, anchor=tk.W, bd=1)
cust_button_browse = ttk.Button(tabs["frame_3"], text="Browse", width=15,
                               command=browse_cust)
cust_button_start = ttk.Button(tabs["frame_3"], text="Start", width=15, state=tk.DISABLED,
                              command=lambda: cust_rel(entry_user.get(),
                                                        entry_pass.get(),
                                                        entry_pcn.get(),
                                                        db.get(),
                                                        clicked.get(),
                                                        cust_selector.cget(
                                                                    "text")))
cust_selector.grid(row=1, column=1, sticky=tk.W+tk.E)
cust_button_browse.grid(row=1, column=2, padx=3, pady=1)
cust_button_start.grid(row=2, column=2, padx=3, pady=1)


# Create Release widgets
file_selector = Label(tabs["frame_4"], width=50, padx=3, pady=3, text=selector_text,
                      relief=tk.SOLID, anchor=tk.W, bd=1)
button_browse = ttk.Button(tabs["frame_4"], width=15, text="Browse",
                           command=browse_release)
button_start = ttk.Button(tabs["frame_4"], text="Start", width=15, state=tk.DISABLED,
                          command=lambda: releases(entry_user.get(),
                                                   entry_pass.get(),
                                                   entry_pcn.get(),
                                                   db.get(),
                                                   clicked.get(),
                                                   file_selector.cget("text")))
file_selector.grid(row=1, column=1, sticky=tk.W+tk.E)
button_browse.grid(row=1, column=2, padx=3, pady=1)
button_start.grid(row=2, column=2, padx=3, pady=1)


# Get MRP Demand widgets
mrp_selector = Label(tabs["frame_5"], width=50, padx=3, pady=3, text=selector_text,
                      relief=tk.SOLID, anchor=tk.W, bd=1)
mrp_button_browse = ttk.Button(tabs["frame_5"], width=15, text="Browse",
                           command=browse_mrp)
mrp_button_start = ttk.Button(tabs["frame_5"], text="Start", width=15, state=tk.DISABLED,
                          command=lambda: mrp(entry_user.get(),
                                                   entry_pass.get(),
                                                   entry_pcn.get(),
                                                   db.get(),
                                                   clicked.get(),
                                                   mrp_selector.cget(
                                                                      "text")))
mrp_selector.grid(row=1, column=1, sticky=tk.W+tk.E)
mrp_button_browse.grid(row=1, column=2, padx=3, pady=1)
mrp_button_start.grid(row=2, column=2, padx=3, pady=1)

# PRP Buttons
prp_selector = Label(tabs["frame_6"], width=50, padx=3, pady=3, text=selector_text,
                      relief=tk.SOLID, anchor=tk.W, bd=1)
prp_button_browse = ttk.Button(tabs["frame_6"], width=15, text="Browse",
                           command=browse_prp)
prp_button_start = ttk.Button(tabs["frame_6"], text="Start", width=15, state=tk.DISABLED,
                          command=lambda: prp(entry_user.get(),
                                                   entry_pass.get(),
                                                   entry_pcn.get(),
                                                   db.get(),
                                                   clicked.get(),
                                                   prp_selector.cget(
                                                                      "text")))
prp_selector.grid(row=1, column=1, sticky=tk.W+tk.E)
prp_button_browse.grid(row=1, column=2, padx=3, pady=1)
prp_button_start.grid(row=2, column=2, padx=3, pady=1)
# Main widgets

# Status bar
status = Label(root, text="Ready.", bd=1, relief=tk.FLAT, anchor=tk.E, bg=mygray)
status.grid(row=3, column=0, columnspan=3, sticky=tk.W+tk.E)

# Icons
shape_icon.grid(row=0, column=0, padx=10, pady=5, sticky=tk.N+tk.W)
help_icon.grid(row=0, column=1, padx=10, pady=5, sticky=tk.N+tk.E)

# Setting root variables
root.grid_rowconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.configure(bg=mygray)
root.focus()
root.bind('<Button-1>', help_file)

# Starting the GUI
root.mainloop()
