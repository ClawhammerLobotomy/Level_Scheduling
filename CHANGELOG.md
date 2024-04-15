# Change Log

## [2.3.21] - 2024-4-15

### Added

Added more debug printing.

### Changed

Changed `do_release_update()` function to return `mrp_forecast_count` variable count of MRP recommendations for debugging.

## [2.3.21] - 2024-4-10

### Added

Added debug command line flag. -d, --debug

Added debug printing throughout.

Added headless command line flag. --headless

Added show/hide password toggle.

### Changed

Changed `prp_get_api` to use a dynamic start date of 365 days before current date.  
Runs were taking forever to process with the static date of 2001.

Changed import of tkinter to not import everything.  
Prefixed all tkinter variables and functions with `tk.`

Changed name of function `do_update_release_czech()` to `do_update_release()` to avoid confusion with errors.

Changed name of function `api_inventory_download_v2()` to `api_inventory_download`.

Changed name of function `api_customer_release_get_v2()` to `api_customer_release_get`.

Changed pyinstaller path to use Python311 from Python310 in compile.bat

Fixed prp_get_api() function to skip parts which do not return a part_key. If the part is obsolete it does not return a key value from data source 9094.

### Removed

Removed dead, commented code.

Removed unused functions.
* prp_get_plex()
* api_inventory_download()
* plex_inventory_get()
* api_customer_release_get()
* plex_customer_release_get()

Cleaned up unused imports

## [2.3.20] - 2023-09-29

### Changed
Updated login functions to remove deprecated kwargs in `Plex` class.

Updated login functions to use new `LoginError` class.

Updated `get_week_index` call to use the class attributes.

### Fixed
Fixed issue with classic login where accounts had only a single PCN access.

## [2.3.19] - 2023-09-05

### Added
Added validation check for the input file to check if all the data is present.  
This records the part numbers with missing data and prints/alerts that there is missing data to review

## [2.3.17] - 2023-08-18

### Fixed
Fix to issue with MRP recommendations not getting added  
Needed to include the `part_operation_key` URL parameter. Without this, parts which had receiving inspections (or any multiple operations) were doubling the PO release quantities, and the recommendations were not showing at all.

## [2.3.15] - 2023-07-31

### Changed 
Updated to selenium 4.10 which depricates `find_element_by_*****`.  
Replaced all instances of this call.

### Fixed
Fix to issue with google not having the latest chromedriver available for the latest chrome browser.  
Now downloading the latest available stable version for base chrome version.

## [2.3.11] - 2023-06-29

### Added
Added functionality to copy network config files each time they are available to keep local files current without needing new revisions each time.

### Fixed
Fixed issue with string defaults in config file.

Fixed function name call in prp download.

## [2.3.10] - 2023-02-02

### Added
Added support for configurable number of weeks of firm releases.

## [2.3.9] - 2022-12-14

### Fixed
Fixed issue with float release balances in the release cleanup.

## [2.3.8] - 2022-11-11

### Changed
Updated PCN values to reflect the change from Magnode to Shape - Aluminum.

## [2.3.7] - 2022-10-31

### Changed
Updated PRP download to use data source calls.

## [2.3.6] - 2022-08-29

### Added
Adding support for PRP download.

### Changed
Updated all `df.append` commands with `pd.concat([df_1, df_2])` format.

## [2.3.5] - 2022-07-18

### Changed
Changed login to IAM process.

## [2.3.2] - 2022-04-11

### Fixed
Fixed issue where shipped release quantities were not being taken into account for the balances.  
This version still uses 1 week of daily demand only.

Fixed version checking for Chrome.  
Went from 99 to 100 which broke the version check.

## [2.1.2] - 2022-01-31

### Added
Added exception handling for API download in event of timeout error.

### Changed
Update the inventory download to include the zero inventory parts if they are in the source file.  
This was done in order to make any errors apparent in the workbook.

Tweaked the inventory download to only save the files once at the end instead of for every part.

Changed the customer release download data source to 5565.  
This apparently is just the full customer releases, and I didn't find this when I started looking for data sources.  
I needed to change some column names, but overall, it behaves the same.

### Fixed
Fixed auto update process for version changes.

## [2.1.1]

## Added
Added functionality to set the release status based on the input file.

Added config option to decide if a PCN would use MRP recommendations.

## [2.1.0] - 2021-08-30

### Changed
Changed Inventory, Customer Releases, and MRP download functions to use threaded requests to speed up operation.  
Improved performance from around 10 minutes to less than 1 minute.

## [2.0.1] - 2021-08-27

### Added
Added check if the file is open when the API downloads are trying to write to the files.

### Changed
Removed the averaging of quantities within the tool.

## [2.0.0] - 2021-08-20

### Added
Added backwards compatibility to use Selenium if the data source was not configured for a PCN.

Added MRP Demand download function for JNI file.

### Changed
Inventory Download and Customer Release Download updated to API.

Changed the way the GUI tabs were getting created slightly.

# [Previous Versions]

## [2021-8-17] 

### Changed
Moved 'source' files to an H drive location in order to avoid using Github.

Removed Github connections for source files.

Changed the processes to headless instances.  
This should eliminate the possibility of influencing the process.

## [2021-8-11] 

### Fixed
Fixed issue with github connection refusing.

## [2021-8-6] 

### Fixed
Fixed issue with download going into the current directory rather than parent.

## [2021-8-6]

### Fixed
Fixed issue where the mrp excluded locations were being used for inventory download numbers.

## [2021-7-27]

### Added
Added initialization for Excel file sources if missing.

Set up version check against github file and notify user if there is a new version to download.

### Fixed
Fixed issue with downloading inventory with the new subcontract inventory process if a part did not have any inventory.

## [2021-7-7] 

### Changed
Removed Quit button This was just causing unnecessary confusion and the X works to close.

Rewrote the inventory get function to also grab subcontract inventory.  
This replaces the current inventory download.  
The part list file can now be just a part number + revision instead of requiring the part key.

## [2021-6-28] 

### Changed
Changed release creation to remove the step of keeping the existing forecast releases.  
This was causing large forecasts to remain in the system which messes with releases to the supplier.

## [2021-6-15] 

### Fixed
Fixed issue with missing config file on startup.  
Program will now create the file on first run if missing.

Fixed issue with `get_releases` function which was causing it to skip all parts.

## [2021-6-2] 

Fixed issue with `get_inventory` function when the part detail update permision is removed from a user.

## [2021-5-24] 

### Added
Added dropdown picker for PCN that you would working in.

Set up company code and PCN to be saved after selected.

### Removed
Removed help buttons due to lack of use and maintenance with their rapidly changing nature.

## [2021-5-21] 

### Changed
Updated Release creation function to remove clicks and key sending.  
This is required so the user can minimuze the Chrome window.

## [2021-5-20] 

### Added
Added top level variables that can be modified to easily switch PCN.

### Fixed
Fixed issue with Customer Release Get which would skip everything if Chrome was minimized.

### Changed
Updated check for column positions which will work for any PCN.

## [2021-4-30] 

### Added
Added check to release date in event that it is blank.  
Sets the release date to 1990-01-01 in these instances.

## [2021-4-28] 

### Changed
Modified customer release download to account for extra column in the CST PCN.

## [2020-11-2] 

### Added
Added the downloaded files into a specific directory to avoid issues with Excel workbook changes.

## [2020-10-5] 

### Fixed
Fixed issue where zero quantity releases wouldn't be considered properly to close forecasts during the same week.

## [2020-9-23] 

### Fixed
Fixed issue where forecasts weren't being removed from the list.

## TODO
[ ] Replace Supplier Release upload with data source version.  
There is no web service for generating MRP recommendations.  
I think I will try and use the release add/update data source first.  
Then, I'll run a Plex process to generate MRP recommendations after.