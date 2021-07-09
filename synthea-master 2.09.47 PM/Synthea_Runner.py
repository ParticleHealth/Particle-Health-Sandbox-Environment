#import relevant libraries
import os
import argparse
import sys
from difflib import get_close_matches
import re
import shutil
from shutil import copyfile
from datetime import date
import pandas as pd
import json
import requests
import urllib3


#requirements:
#brew install jenv
#os.system('brew install jenv')
#os.system('jenv local 1.8')

#gather input values to run module and find condition of interest
list_of_conditions = ['covid19', 'diabetes', 'lung cancer', 'opioid addiction']
parser = argparse.ArgumentParser()
parser.add_argument("--num-patients", type=str, required=True)
parser.add_argument("--condition", type=str, required=True, choices=list_of_conditions)
args = parser.parse_args(sys.argv[1:])

num_patients = args.num_patients
condition = args.condition

list_of_modules = ["covid19", "metabolic*", "lung_cancer*", "opioid_addiction"]
if condition == 'covid19':
    module = list_of_modules[0]
if condition == 'diabetes':
    module = list_of_modules[1]
if condition == 'lung cancer':
    module = list_of_modules[2]
    num_patients = '2500'
if condition == 'opioid addiction':
    module = list_of_modules[3]

#run synthea with module and number of patients specified
print('\n' + 'Running Synthea to Generate Base Synthetic Patient Data' + '\n')
os.system('./run_synthea -p ' + num_patients + ' -m ' + module + ' -a 0-95')


#load csv produced from synthea with conditions of population generated
print('\n' + "Finding Patients with Conditiions of Interest"+ '\n')
symptoms_csv_load = []
with open('./output/symptoms/csv/symptoms.csv') as symptoms_csv:
    for i in symptoms_csv:
        symptoms_csv_load.append(i)

#define function to find condition of interest
def check_if_match(words):
    patterns = re.split('(\s|\,)', words)
    for i in range(len(patterns)):
        patterns[i] = patterns[i].lower()
    results = get_close_matches(condition, patterns)
    return results, patterns[0]

#change opioid addiction to terms found in symptom csv
if condition =='opioid addiction':
    condition = 'drug overdose'

#get unique patient ids for patients with condition of interest
patient_ids_of_interest = []
for i in symptoms_csv_load:
    match, patient_id = check_if_match(i)
    if match:
        patient_ids_of_interest.append(patient_id)

patient_ids_of_interest = set(patient_ids_of_interest)

#get FHIR docs for patient ids of interest and copy them to point in time doc generation input folder:
#make directory for synthea output and point in time document generation output
print('\n' + "Transferring Files to Generate Point-In-Time CCDA Documents" + '\n')
today = date.today()
if not os.path.isdir('../' + condition + '_output_' + str(today)):
    os.mkdir('../' + condition + '_output_' + str(today))
if not os.path.isdir('../' + condition + '_output_' + str(today) + '/synthea_fhir'):
    os.mkdir('../' + condition + '_output_' + str(today) + '/synthea_fhir')
if not os.path.isdir('../' + condition + '_output_' + str(today) + '/synthea_ccda'):
    os.mkdir('../' + condition + '_output_' + str(today) + '/synthea_ccda')
if not os.path.isdir('../' + condition + '_output_' + str(today) + '/synthea_notes'):
    os.mkdir('../' + condition + '_output_' + str(today) + '/synthea_notes')
if not os.path.isdir('../' + condition + '_output_' + str(today) + '/generator_output'):
    os.mkdir('../' + condition + '_output_' + str(today) + '/generator_output')

#copy fhir to record folder
for i in os.listdir('./output/fhir'):
    for j in patient_ids_of_interest:
        if j in i:
            copyfile('./output/fhir/' + i, '../' + condition + '_output_' + str(today) + '/synthea_fhir/' + i)
#copy ccdas to record and input folders
for i in os.listdir('./output/ccda'):
    for j in patient_ids_of_interest:
        if j in i:
            copyfile('./output/ccda/' + i, '../' + condition + '_output_' + str(today) + '/synthea_ccda/' + i)
            copyfile('./output/ccda/' + i, './Synthea_CCDs/' + i)
#copy notes to record and input folders
for i in os.listdir('./output/notes'):
    for j in patient_ids_of_interest:
        if j in i:
            copyfile('./output/notes/' + i, '../' + condition + '_output_' + str(today) + '/synthea_notes/' + i)
            copyfile('./output/notes/' + i, './Notes/' + i)

#run point in time document generator script
print('\n' + "Generating Point-In-Time CCDA Documents" + '\n')
os.system('python point_in_time_document_generator.py')

#copy output files and directory to output folder:
for i in os.listdir('./pitd_gen_output'):
    shutil.copytree('./pitd_gen_output/' + i, '../' + condition + '_output_' + str(today) + '/generator_output/' + i)

copyfile('./output_directory.csv', '../' + condition + '_output_' + str(today) + '/output_directory.csv')

#clear notes, synthea ccds, pitd gen output_file, directory
for i in os.listdir("./Notes"):
    os.remove('./Notes/' + i)
for i in os.listdir("./Synthea_CCDs"):
    os.remove('./Synthea_CCDs/' + i)
for i in os.listdir("./output"):
    if i.startswith('.'):
        os.remove('./output/' + i)
    else:
        shutil.rmtree('./output/' + i, ignore_errors = True)
for i in os.listdir("./pitd_gen_output"):
    shutil.rmtree('./pitd_gen_output/' + i, ignore_errors = True)
os.remove('./output_directory.csv')

print('\n' + 'Generation Complete' + '\n')

#validate point in time ccda documents
print('\n' + 'Validating Output Point In Time CCDA Documents' + '/n')

#loop thru output files to validate
patients = []
val_output = []
urllib3.disable_warnings()
for i in os.listdir('../' + condition + '_output_' + str(today) + '/generator_output'):
    if not i.startswith('.'):
        print(i)
        #loop thru folders for patient
        counter = 0
        for j in os.listdir('../' + condition + '_output_' + str(today) + '/generator_output/' + i):
            if not j.startswith('.'):
                print('\tFOLDER:' + j)
                #loop thru files for patient
                for k in os.listdir('../' + condition + '_output_' + str(today) + '/generator_output/' + i +"/" + j):
                    if not k.startswith('.'):
                        print('\t\tFile: ' + k)
                        patients.append(i)
                        folder_name = i
                        data_file = '../' + condition + '_output_' + str(today) + '/generator_output/' + i +"/" + j + '/' + k

                        url = "https://ccda.healthit.gov/scorecard/ccdascorecardservice2"
                        myfile = {"ccdaFile": (k, open(data_file, "rb"))}
                        r = requests.post(url, files = myfile, verify = False).json()
                        val_output.append(list(r.items()))

val_table = pd.DataFrame(data = val_output, columns = ['ErrorMessage','FileName', 'CCDADocumentType', 'Results', 'ReferenceResults', 'ErrorList', 'SchemaErrors', 'Success'])
val_table.insert(0, "Patient", patients, True)

#write validation output to csv
val_table.to_csv('../' + condition + '_output_' + str(today) + '/validation_results.csv')

print('\n' + 'Validation Complete' + '\n')
