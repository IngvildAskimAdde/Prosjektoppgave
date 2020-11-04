# %%
import os

src_main_folder = r'/Volumes/Untitled/Results' #Change to your path
dst_main_folder = r'/Volumes/Untitled/Results_postprocessed' #Change to your path
#patient_identifier = 'LARC-RRP'
patient_identifier = 'ID'
#scan_time_point_folder = 'MRS1'

patient_list = [i for i in os.listdir(src_main_folder) if i.startswith(patient_identifier)]

for patient in patient_list:
    os.makedirs( os.path.join(dst_main_folder, patient))#, scan_time_point_folder) )
