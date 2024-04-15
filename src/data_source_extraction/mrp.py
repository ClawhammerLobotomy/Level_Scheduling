
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
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        response_list = list(pool.map(post_url,list_of_urls))
    
    for p, response in enumerate(response_list):
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
                mrp_file, index=False)
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
