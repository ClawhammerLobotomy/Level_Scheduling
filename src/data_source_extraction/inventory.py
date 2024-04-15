import pandas as pd
import json
import ux_data_source_tools as UDST
import utils

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
    part_list = utils.import_part_list(input_file)
    status_df = pd.DataFrame(container_statuses, columns=[
                                'Container_Status'])
    large_parts = []
    df_1 = pd.DataFrame()
    l_df_1 = pd.DataFrame()
    total_parts = len(part_list)

    api_id = '23733'
    url = f'https://{db}cloud.plex.com/api/datasources/{api_id}/execute'
    list_of_urls = [(url, form_data, authentication) 
        for form_data in map(create_inv_json, part_list)]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
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
                                            index=False)
            df_4_final[['Part_No','Inventory']].to_csv(inventory_file,
                                            index=False)
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