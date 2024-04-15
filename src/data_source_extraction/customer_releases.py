
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
    api_id = '5565'
    url = f'https://{db}cloud.plex.com/api/datasources/{api_id}/execute'
    list_of_urls = [(url, form_data, authentication) 
        for form_data in map(create_cust_json, part_list)]
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        response_list = list(pool.map(post_url,list_of_urls))
    
    for p, response in enumerate(response_list):

        json_data = json.loads(response.text)
        debug_print(json_data)
        inventory_list = json_data['tables']
        if json_data['tables'][0]['rows'] == []:
            continue
        if df_1.empty:
            df_1 = json_normalize(inventory_list, 'rows')
            # print('first')
            # print(df_1)
            debug_print(f"First: {df_1}")
        else:
            df = json_normalize(inventory_list, 'rows')
            df_1 = pd.concat([df_1, df],ignore_index=True)
            # print('next')
            # print (df_1)
            debug_print(f"Next: {df_1}")
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
    # print('Original release set')
    # print(df_1)
    debug_print(f"Original release set: {df_1}")
    df_2 = df_1.groupby(['Part_No_Revision', 'Ship_Date']).sum(
                    'Quantity').reset_index()
    df_2['Ship_Date'] = pd.to_datetime(df_2['Ship_Date'],
                                format='%m/%d/%y')
    # print(df_2)
    df_2.sort_values(by=['Part_No_Revision','Ship_Date'],inplace=True)
    # print(df_2)
    df_2['Ship_Date'] = df_2['Ship_Date'].dt.strftime('%#m/%#d/%y')
    df_2['Quantity'] = df_2['Quantity'] - df_2['Shipped']
    # print('Grouped releases')
    # print(df_2)
    debug_print(f"Grouped releases: {df_2}")
    # Removes any duplicate operation types.
    # TODO - 1/17/2022 - Check if still needed after switching data sources
    df_2 = df_2.drop_duplicates(subset=['Part_No_Revision','Ship_Date','Quantity'])
    # print('after dropping duplicates')
    # print(df_2)
    debug_print(f"After dropping duplicates: {df_2}")
    release_list = df_2[['Part_No_Revision','Ship_Date',
                            'Quantity']].values.tolist()
    # print(release_list)
    debug_print(f"Release list: {release_list}")
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
    daily_release_weeks = config_setup(launch_pcn_dict[pcn_get()[0]]['default_week_no'])
    firm_range = [*range(int(daily_release_weeks))]
    current_week_rel = [i for i in release_list if 
                        i[0] in firm_range]
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
                    week_grouped_releases if ele[1] not in  firm_range] 
    # print("List of releases grouped by week's Monday")
    # pprint(week_grouped_releases)
    debug_print(f"Releases grouped by week: {week_grouped_releases}")
    # Combines current week and grouped week releases
    combined_grouped_releases = current_week_rel \
                                + week_grouped_releases
    # print(combined_grouped_releases)
    debug_print(f"Daily and weekly releases: {combined_grouped_releases}")
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
