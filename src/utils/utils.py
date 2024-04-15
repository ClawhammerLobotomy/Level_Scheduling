from datetime import datetime, timedelta, date
from pathlib import Path
from collections import OrderedDict
from tkinter.messagebox import askokcancel, askyesno, showinfo
import os
import sys
import shutil
import configparser
import zipfile
import __main__
# from main import *
# from main import args,__main__
LOG_FILE = 'debug_log.log'

class Utility(object):
    def __init__(self):
        self.debug = True

def debug_print(message):
    if args.debug:
        print(f'{datetime.now()} - DEBUG - {message}\n')
        print(f'{datetime.now()} - DEBUG - {message}',file=open(LOG_FILE,'a'))

def folder_setup(source_folder):
    """
    Create the base folder if missing.
    """
    if not os.path.exists(source_folder):
        debug_print(f'Creating source folder: {source_folder}')
        os.makedirs(source_folder)


def file_setup(source_folder, dict, file_name):
    """
    Creates the Excel source files if missing.

    This is needed in order for the Excel workbooks not to break when run.
    """
    for x, y in dict.items():
        file = os.path.join(source_folder, y['prefix']+file_name)
        if not os.path.isfile(file):
            debug_print(f'{file} not detected. Creating placeholder file to prevent Excel errors.')
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


def config_setup(weeks):
    # config_path = Path(os.path.join(bundle_dir,'resources','config.ini'))
    # Path(os.getcwd()).parent.absolute()
    config_path = Path(os.path.join(os.getcwd(),'user_config.ini'))
    config = configparser.ConfigParser()
    config = configparser.ConfigParser()
    if not config_path.is_file():
        config['Plex'] = {}
        config['Plex']['number_of_weeks_for_daily_cust_demand'] = weeks
        with open(config_path, 'w+') as configfile:
            config.write(configfile)
    config.read(config_path)
    daily_release_weeks = config['Plex']['number_of_weeks_for_daily_cust_demand']
    return daily_release_weeks


def local_file_update(main):
    """
    Updates the local file version to match with the network.
    """
    for x in main.file_list:
        src = Path(os.path.join(main.master_source_dir, x))
        dst = Path(os.path.join(main.resource_dir, x))
        debug_print(f'Copying file: {src}\n To: {dst}')
        shutil.copyfile(src, dst)
    return
def version_check(main):
    """
    Checks current version against a file on the H: drive.

    If the latest version is greater than current version, download 
    and extract the new version.
    """
    if main.latest_version > __version__:
        debug_print(f'Current working directory: {os.getcwd()}')
        dl_path = Path(os.getcwd()).parent.absolute()
        # print(dl_path.parent.absolute())
        debug_print(dl_path)
        src = 'H:/OP-ShapeGlobal/0708-IT/Public/Level Scheduling'\
            '/Level_Scheduling_Helper_' + main.latest_version + \
            '_Portable.zip'
        dst = str(dl_path) + '/Level_Scheduling_Helper_' + latest_version + \
            '_Portable.zip'
        latest_file = Path(dst)
        latest_path = Path(str(dl_path) + '/Level_Scheduling_Helper_'
                                    + latest_version + '_Portable')
        # print(latest_file.is_file())
        if not latest_file.is_file() or not latest_path.is_dir():
            try:
                shutil.copyfile(src, dst)
                debug_print(f'Copying new version from {src} to {dst}.')
                with zipfile.ZipFile(dst, 'r') as zip_ref:
                    zip_ref.extractall(str(dl_path) + '/Level_Scheduling_Helper_'
                                    + latest_version + '_Portable')
                    debug_print(f'New version extracted to:\n{str(dl_path)}/Level_Scheduling_Helper_{latest_version}_Portable')
                showinfo('Update Available',f'There is a new version of the level'
                    f' scheduling tool.\n'
                    f'Your version \t{__version__}\n'
                    f'Latest version \t{latest_version}\n'
                    f'Please use the new version located here:\n'
                    + str(dl_path) + '\Level_Scheduling_Helper_'
                    + latest_version + '_Portable')
            except FileNotFoundError:
                debug_print(f'Could not find latest version of helper tool. Latest Version: {latest_version}. Current Version: {__version__}')
                showinfo(f'Update Error', 'Your helper tool does not match'
                f' the latest version.\n\n'
                f'Your version \t{__version__}\n'
                f'Latest version \t{latest_version}\n\n'
                f'Unable to find the latest version on the H: drive.\n\n'
                f'Contact {__maintainer__} at {__email__} for assistance.')
        else:
            debug_print(f'Latest version already available at location:\n{str(dl_path)}/Level_Scheduling_Helper_{latest_version}_Portable')
            showinfo('Update Available',f'There is a new version of the level'
                    f' scheduling tool.\n'
                    f'Your version \t{__version__}\n'
                    f'Latest version \t{latest_version}\n'
                    f'Please use the new version located here:\n'
                    + str(dl_path) + '\Level_Scheduling_Helper_'
                    + latest_version + '_Portable')
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

