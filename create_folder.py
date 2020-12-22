
"""
@author: IngvildAskimAdde
"""

import os

def create_folder(src_main_folder, dst_main_folder, patient_identifier):
    """
    Input: Path to source folder, path to destination folder, patient
    identifier (LARC-RRP or ID)

    Output: New folder with the same structure as source folder
    """

    patient_list = [i for i in os.listdir(src_main_folder) if i.startswith(patient_identifier)]

    if patient_identifier == 'LARC-RRP':
        scan_time_point_folder = 'MRS1'
        for patient in patient_list:
            os.makedirs(os.path.join(dst_main_folder, patient, scan_time_point_folder))

    if patient_identifier == 'ID':
        for patient in patient_list:
            os.makedirs(os.path.join(dst_main_folder, patient))

    else:
        print('No valid patient identifier')




