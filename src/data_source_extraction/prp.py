
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
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        url = f'https://{db}cloud.plex.com/api/datasources/{api_id}/execute'
        list_of_urls = [(url,{'inputs': dict(query)}, authentication) for query in part_rev]
        futures = [executor.submit(ux.post_url, parts) for parts in list_of_urls]

        for future in as_completed(futures):
            result = future.result()
            part_key = str(json.loads(result.text)['outputs']['Part_Key'])
            inputs = json.loads(result.request.body.decode('utf-8'))['inputs']
            if part_key != 'None' and part_key not in part_key_dict.items():
                part_key_dict[part_key] = inputs
    
    part_list = import_part_list(input_file)
    df_1 = pd.DataFrame()
    total_parts = len(part_list)
    prp_list = []
    today = date.today()
    ed = ux.plex_date_formatter(today, date_offset=56)
    sd = ux.plex_date_formatter(today, date_offset=-365)

    # Create Query string for part keys
    for i, (key,item) in enumerate(part_key_dict.items()):
        
        part = part_key_dict[key]['Part_No']
        revision = part_key_dict[key]['Revision']
        query = (
            ('Part_Key', key),
            ('From_PRP', True),
            ('Begin_Date', sd),
            ('End_Date',ed)
        )
        prp_list.append(query)
    api_id  = '15851' # Part_Requirement_Plan_Parent_Demand_Detail_Get 
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
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
                         p['Due_Date'],-1).week_index, axis=1).astype(str)
    df_1['Week_Start'] = df_1.apply(lambda p: ux.get_week_index(
                         p['Due_Date'],-1).formatted_date, axis=1)
    df_g = df_1.groupby(by=['Component_Part_No_Rev',
                            'Week_Index',
                            'Week_Start']).sum().reset_index()
    df_r = df_g
    df_r['Calc_Demand'] = df_g['Calc_Demand'].apply(np.ceil)
    df_r.insert(0,'Lookup', df_r[['Component_Part_No_Rev',
                                  'Week_Index']].agg('-'.join, axis=1))

    if df_1.empty:
        status.config(text=
                    f"No demand for provided part numbers.")
        return

    df_r.sort_values(by=['Lookup'], inplace=True)
    prp_file = os.path.join(source_dir, 
                                f'{file_prefix}prp_demand.csv')
    while True:
        try:
            df_r.to_csv(prp_file, index=False)
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
