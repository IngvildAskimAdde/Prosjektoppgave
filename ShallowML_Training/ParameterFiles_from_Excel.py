#%%
import os

import pandas as pd

excel_file = 'Experiments.xlsx'
dst_folder = 'Parameter_files'
sheet_name = 'Runs'
common_parameters = pd.read_excel(excel_file, sheet_name='FixedValues')


if not os.path.isdir(dst_folder):
    os.makedirs(dst_folder)


experiments = pd.read_excel(excel_file,
              header=0,
              sheet_name=sheet_name)

for _, row in experiments.iterrows():
    file = os.path.join(dst_folder, 'ID_{}.txt'.format(row['ID']))
    if not row['STATUS']==1:
        with open(file, 'a', newline='\n') as the_file:
            for _, entry in common_parameters.iterrows():
                if entry['Parameter']=='path_patient_image_data':
                    path_patient_image_data = entry['Value']
                else:
                    the_file.write('{} = {}\n'.format(entry['Parameter'], entry['Value']))

            images_to_use = []
            for item, value in row.items():
                if row.isnull()[item] or item in ['STATUS', 'COMMENT']:
                    pass
                elif item in ['T2']:
                    images_to_use.append(item)
                elif item == 'folder_data':
                    the_file.write('folder_patient_image_data = {}\n'.format(
                                os.path.join(path_patient_image_data, value)))
                                ##HACK this might cause problems when parameter files are created on a different os than the cluster 
                else:
                    the_file.write('{} = {}\n'.format(item, value))

            the_file.write('images_to_use = {}\n'.format(' '.join(images_to_use)))
