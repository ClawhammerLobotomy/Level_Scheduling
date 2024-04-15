
def do_release_update(user_name, password, company_code, db, home_pcn,
                            input_file):
    # Initialize the user account to be used for login
    pcn = launch_pcn_dict[home_pcn]["pcn"]
    file_prefix = launch_pcn_dict[home_pcn]["prefix"]
    forecast_update = launch_pcn_dict[home_pcn]["forecast"]
    plex = Plex('classic', user_name, password, company_code, pcn, db=db,
                use_config=False, pcn_path=pcn_file, chromedriver_override=chromedriver_override)
    # Get the directory that script is running in
    # bundle_dir = plex.frozen_check()
    # plex.frozen_check()
    # ======Start of required code======#
    # Call the chrome driver download function
    # plex.download_chrome_driver(chromedriver_override)
    # Call the config function to initialize the file and set variables
    # plex.config()
    # Call the login function and return the chromedriver instance 
    #   and base URL used in the rest of the script
    try:
        driver, url_comb, url_token = plex.login(headless=args.headless)
        url_token = url_token
    except LoginError as e:
        debug_print(f'Login error.')
        debug_print(f'Plex Environment: {e.environment}')
        debug_print(f'Database: {e.db}')
        debug_print(f'PCN: {e.pcn}')
        debug_print(f'Error Message: {e.message}')
        status.config(text=e.message)
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
        # Adding initial check to validate the input file contains all data for all rows.
        try:
            dic_reader = csv.DictReader(fin)
            error_parts = []
            for row in dic_reader:
                if any(val in (None, "") for val in row.values()):
                    error_parts.append(row['Part'])
            error_parts = list(set(error_parts))
            if len(error_parts) > 0:
                error_parts = '\n'.join(error_parts)
                raise MissingInputData(f"Input file missing data for these parts:\n{error_parts}")
        except MissingInputData as e:
            status.config(text='Error: Missing data detected. Review input file.')
            print(e)
            showinfo(title="Missing data detected",message=e)
            plex.driver.quit()
            return
        fin.seek(0)
        csv_reader = csv.reader(fin, delimiter=',')
        # dic_reader = csv.DictReader(fin)
        for i, row in enumerate(csv_reader):
            if i == 0:
                column_dict = {}
                for x, i in enumerate(row):
                    column_dict[i] = x
                #     print(x, i)
                # print(column_dict)
            else:
                part_po_grouping[row[0], row[1], row[2], row[3],
                                row[4], row[5], row[6]].append(row[7:])
        # print(part_po_grouping)
        # 2. For each group, go to the PO line and perform actions
        for j, line in enumerate(part_po_grouping):
            debug_print(f"Part line details: {line[0]}, {line[1]}, {line[2]}, {line[3]}, {line[4]}")
            # pprint(part_po_grouping[line])
            # print(line)
            date_qty_set = []
            for x in part_po_grouping[line]:
                if {"Release_Status"} <= column_dict.keys():
                    release_status = x[7]
                    # print(release_status)
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
            debug_print(f"Current Releases: {release_list}")
            # print('')
            # 4. Separate out forecast releases
            forecasts =[line for i, line in enumerate(release_list)
                        if 'Forecast' in line]
            # print('Old Forecasts')
            # pprint(forecasts)
            debug_print(f"Old Forecasts: {forecasts}")
            cut_index = 0
            for i, line in enumerate(forecasts):
                # 5. Compare forecasts with date_qty_set
                for j, x in enumerate(date_qty_set): # pylint: disable=unused-variable
                    # print('Forecast to compare')
                    # print(line)
                    debug_print(f"Forecast to compare: {line}")
                    # print('Firm to compare')
                    # print(x)
                    debug_print(F"Firm to compare: {x}")
                    if datetime.strptime(line[0], '%m/%d/%y') <=\
                            datetime.strptime(x[0], '%m/%d/%Y'):
                        # print(line[0], '<=', x[0])
                        debug_print(F"Forecast date before firm date.")
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
            debug_print(f"New Forecast Releases: {new_forecasts}")
            # print('New original forecasts')
            # pprint(forecasts)
            debug_print(f"Original forecast: {forecasts}")
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
                    qty[i].value = parseFloat(
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
                # print(i, partials, release[1], release[0], release[2])
                debug_print(f"Updating release: QTY: {release[1]}, Date: {release[0]}, Status: {release[2]}")
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
            # 12. Add notes for time and date that it was updated
            qtys = driver.find_elements(By.XPATH,
                                    '//input[starts-with(@id, '
                                    '"txttxtQuantity")]')
            full_qty = [rel for i, rel in enumerate(qtys)
                        if rel.get_attribute('value') != '']
            notes = driver.find_elements(By.XPATH,
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
            # 13. Click update button
            # Changed to JS function to work when minimized
            driver.execute_script("FormSubmitStart('Update');")
            # 14. Go to MRP recommendations
            # 14a. Czech is not doing forecasts.
            if not forecast_update:
                continue
            driver.get(f'{url_comb}/requirements_planning'
                    f'/Release_Planning_By_Supplier_Schedule_Form.asp'
                    f'?Mode=Part'
                    f'&Part_Key={part_key}'
                    f'&Part_Operation_Key={op_key}')
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

            // Grab all PO dropdown elements
            var po_no = document.querySelectorAll(
                'select[id^="lstPO"]')

            // If order qty!= suggested order qty 
            // AND statuses are not firm, planned, or partial, 
            // then check the box and add a note
            for(var i=0;i<check.length;i++){{
            if (on_order_stat[i] != "Firm" && 
                on_order_stat[i] != "Partial" && 
                sug_order_stat[i] != "Firm" && 
                sug_order_stat[i] != "Planned" && 
                on_order_qty[i] != sug_order_qty[i]){{
            po_no[i].value = "{line_key}"
            check[i].checked = true
            note[i].value = "MRP recommendation updated by "+
                            "{user_name} on {rel_date}"
            }}}}
            """.format(user_name=user_name,rel_date=rel_date,line_key=line_key)
            driver.execute_script(script)
            # 16. Create suggested forecast releases.
            #     (Click create button)
            # Switched to JS function to work while minimized
            driver.execute_script("Create_Releases();")
    status.config(text=f"Process complete. {total_lines} total "
                        f"releases across {num_parts} part numbers "
                        f"updated.")
    driver.quit()
