#Particle Health CCDA Point In Time Document Generator

#import relevant packages
import jinja2
from jinja2 import Environment
from jinja2 import FileSystemLoader
from lxml import etree
from io import StringIO, BytesIO
import os
import csv
import string
import re


#lxml method
#parses Synthea CCD document to save variables we want to populated the template CCDAs with

#loop through n synthea files we want to populate CCDAs for
for filename in os.listdir('Synthea_CCDs'):
    #skip .DS_Store files
    if not filename.startswith('.'):
        #take file n
        with open("Synthea_CCDs/" + filename) as openfile:
            #reset variables to as if section in Synthea CCD didnt exist to avoid
            # populating template with previous ccd information
            encounter_tr = "<tr><td>Data Unknown</td></tr>"
            vital_signs_text = "<text>Data Unknown</text>"
            diagnostic_results_text = "<text>Data Unknown</text>"
            plan_of_care_text = "<text>Data Unknown</text>"
            social_history_text = "<text>Data Unknown</text>"
            problems_text = "<text>Data Unknown</text>"
            medications_text = "<text>Data Unknown</text>"
            allergies_text = "<text>Data Unknown</text>"
            immunizations_text = "<text>Data Unknown</text>"
            encounter_entry = ""
            vital_signs_entry = ""
            diagnostic_results_entry = ""
            plan_of_care_entry = ""
            social_history_entry = ""
            problems_entry = ""
            medications_entry = ""
            allergies_entry = ""
            immunizations_entry = ""

            #parse file n and save template variables for information we want to populate
            tree = etree.parse(openfile)
            root = tree.getroot()

            #capture demographics for output folder structure and future templating
            name_div = tree.find("{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole/{urn:hl7-org:v3}patient/{urn:hl7-org:v3}name")
            given = name_div.find("{urn:hl7-org:v3}given").text
            family = name_div.find("{urn:hl7-org:v3}family").text
            given = ''.join([i for i in given if not i.isdigit()])
            family = ''.join([i for i in family if not i.isdigit()])
            exclude = set(string.punctuation)
            given = ''.join(ch for ch in given if ch not in exclude)
            family = ''.join(ch for ch in family if ch not in exclude)
            author_institution = tree.find("{urn:hl7-org:v3}author/{urn:hl7-org:v3}assignedAuthor/{urn:hl7-org:v3}representedOrganization/{urn:hl7-org:v3}name").text
            author_institution = ''.join(ch for ch in author_institution if ch not in exclude)
            author_institution = author_institution.replace(" ", "_")
            creation_time = tree.find("{urn:hl7-org:v3}author/{urn:hl7-org:v3}time").attrib['value']
            creation_time = creation_time[0:4] + "-" + creation_time[4:6] + "-" + creation_time[6:8] + "T" + creation_time[8:10] + creation_time[10:12] + creation_time[12:14]

            #change title
            title = tree.find("{urn:hl7-org:v3}title")
            title.text = "Continuity of Care Document"

            #capture common CCDA header sections from synthea CCD:
            #Captures document creation time
            effective_time = tree.find('{urn:hl7-org:v3}effectiveTime')
            effective_time = etree.tounicode(effective_time, pretty_print=True)

            #Captures recordTarget portion, aka patient demographics
            record_target = tree.find('{urn:hl7-org:v3}recordTarget')
            record_target = etree.tounicode(record_target, pretty_print=True)

            #Captures author portion
            author = tree.find('{urn:hl7-org:v3}author')
            author = etree.tounicode(author, pretty_print=True)

            #Captures custodian portion
            custodian =  tree.find('{urn:hl7-org:v3}custodian')
            custodian = etree.tounicode(custodian, pretty_print=True)

            #Captures documentationOf portion
            documentation_of =  tree.find('{urn:hl7-org:v3}documentationOf')
            documentation_of = etree.tounicode(documentation_of, pretty_print=True)

            #capture hospital encounter specific CCDA sections from synthea CCD:
            #accesses encounter component, parses and stores last td encounter text element and last entry associated
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '46240-8':
                            encounter_tr = tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody/{urn:hl7-org:v3}component[6]/{urn:hl7-org:v3}section/{urn:hl7-org:v3}text/{urn:hl7-org:v3}table/{urn:hl7-org:v3}tbody")[-1]
                            encounter_tr = etree.tounicode(encounter_tr, pretty_print=True)

                            encounter_entry = tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody/{urn:hl7-org:v3}component[6]/{urn:hl7-org:v3}section")[-1]
                            if encounter_entry != None:
                                encounter_entry = etree.tounicode(encounter_entry, pretty_print=True)
                            else:
                                encounter_entry = ""

            #checks for vital signs component, and if exists, parses and stores data
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '8716-3':
                            vital_signs_text = child.find("{urn:hl7-org:v3}section/{urn:hl7-org:v3}text")
                            vital_signs_text = etree.tounicode(vital_signs_text, pretty_print=True)

                            vital_signs_entries = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                            vital_signs_entry = []
                            for entry in vital_signs_entries:
                                if entry != None:
                                    vital_signs_entry.append(etree.tounicode(entry, pretty_print=True))
                                else:
                                    vital_signs_entry = ""
                            vital_signs_entry = "".join(vital_signs_entry)

            #checks for Diagnostic results component, and if exists, parses and stores data
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '30954-2':
                            diagnostic_results_text = child.find("{urn:hl7-org:v3}section/{urn:hl7-org:v3}text")
                            diagnostic_results_text = etree.tounicode(diagnostic_results_text, pretty_print=True)

                            diagnostic_results_entries = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                            diagnostic_results_entry = []
                            for entry in diagnostic_results_entries:
                                if entry != None:
                                    diagnostic_results_entry.append(etree.tounicode(entry, pretty_print=True))
                                else:
                                    diagnostic_results_entry = ""
                            diagnostic_results_entry = "".join(diagnostic_results_entry)

            #checks for plan of care component, and if exists, parses and stores data
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '18776-5':
                            plan_of_care_text = child.find("{urn:hl7-org:v3}section/{urn:hl7-org:v3}text")
                            plan_of_care_text = etree.tounicode(plan_of_care_text, pretty_print=True)

                            plan_of_care_entries = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                            plan_of_care_entry = []
                            for entry in plan_of_care_entries:
                                if entry != None:
                                    plan_of_care_entry.append(etree.tounicode(entry, pretty_print=True))
                                else:
                                    plan_of_care_entry = ""
                            plan_of_care_entry = "".join(plan_of_care_entry)

            #checks for Social History section, and if exists, parses and stores data
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '29762-2':
                            social_history_text = child.find("{urn:hl7-org:v3}section/{urn:hl7-org:v3}text")
                            social_history_text = etree.tounicode(social_history_text, pretty_print=True)

                            social_history_entries = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                            social_history_entry =[]
                            for entry in social_history_entries:
                                if entry != None:
                                    social_history_entry.append(etree.tounicode(entry, pretty_print=True))
                                else:
                                    social_history_entry = ""
                            social_history_entry = "".join(social_history_entry)

            #checks for Problems List section, and if exists, parses and stores data
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '11450-4':
                            problems_text = child.find("{urn:hl7-org:v3}section/{urn:hl7-org:v3}text")
                            problems_text = etree.tounicode(problems_text, pretty_print=True)

                            problems_entries = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                            problems_entry = []
                            for entry in problems_entries:
                                if entry != None:
                                    problems_entry.append(etree.tounicode(entry, pretty_print=True))
                                else:
                                    problems_entry = ""
                            problems_entry = "".join(problems_entry)

            #checks for Medications section, and if exists, parses and stores data
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '10160-0':
                            medications_text = child.find("{urn:hl7-org:v3}section/{urn:hl7-org:v3}text")
                            medications_text = etree.tounicode(medications_text, pretty_print=True)

                            medications_entries = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                            medications_entry = []
                            for entry in medications_entries:
                                if entry != None:
                                    medications_entry.append(etree.tounicode(entry, pretty_print=True))
                                else:
                                    medications_entry = ""
                            medications_entry = "".join(medications_entry)

            #checks for Allergies section, and if exists, parses and stores data
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '48765-2':
                            allergies_text = child.find("{urn:hl7-org:v3}section/{urn:hl7-org:v3}text")
                            allergies_text = etree.tounicode(allergies_text, pretty_print=True)

                            allergies_entries = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                            allergies_entry = []
                            for entry in allergies_entries:
                                if entry != None:
                                    allergies_entry.append(etree.tounicode(entry, pretty_print=True))
                                else:
                                    allergies_entry = ""
                            allergies_entry = "".join(allergies_entry)

            #checks for Immunizations section, and if exists, parses and stores data
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '11369-6':
                            immunizations_text = child.find("{urn:hl7-org:v3}section/{urn:hl7-org:v3}text")
                            immunizations_text = etree.tounicode(immunizations_text, pretty_print=True)

                            immunizations_entries = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                            immunizations_entry = []
                            for entry in immunizations_entries:
                                if entry != None:
                                    immunizations_entry.append(etree.tounicode(entry, pretty_print=True))
                                else:
                                    immunizations_entry = ""
                            immunizations_entry = "".join(immunizations_entry)

            #fix null imaging section error:
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '18748-4':
                            child.getparent().remove(child)

            #jinja2 populate template:
            #fills blank templates with saved data parsed from synthea ccd above
            #load templates and set up environment for jinja2
            template_file_loader = FileSystemLoader('templates')
            env = Environment(loader=template_file_loader)
            encounter_summary_template = env.get_template('Encounter_Summary_Template.xml')
            refill_summary_template = env.get_template('Refill_Summary_Template.xml')
            lab_summary_template = env.get_template('Lab_Summary_Template.xml')
            immunizations_summary_template = env.get_template('Immunizations_Summary_Template.xml')

            #render encounter summary template with saved variables and save to output
            encounter_summary_output = encounter_summary_template.render(Effective_Time = effective_time,
                                                                            Record_Target = record_target,
                                                                            Author = author,
                                                                            Custodian = custodian,
                                                                            Documentation_Of = documentation_of,
                                                                            Encounter_TR = encounter_tr,
                                                                            Encounter_Entry = encounter_entry,
                                                                            Vital_Signs_Text = vital_signs_text,
                                                                            Vital_Signs_Entry = vital_signs_entry,
                                                                            Diagnostic_Results_Text = diagnostic_results_text,
                                                                            Diagnostic_Results_Entry = diagnostic_results_entry,
                                                                            Plan_Of_Care_Text = plan_of_care_text,
                                                                            Plan_Of_Care_Entry = plan_of_care_entry,
                                                                            Social_History_Text = social_history_text,
                                                                            Social_History_Entry = social_history_entry)

            #render refill summary template with saved variables and save to output
            refill_summary_output = refill_summary_template.render(Effective_Time = effective_time,
                                                                    Record_Target = record_target,
                                                                    Author = author,
                                                                    Custodian = custodian,
                                                                    Documentation_Of = documentation_of,
                                                                    Encounter_TR = encounter_tr,
                                                                    Encounter_Entry = encounter_entry,
                                                                    Plan_Of_Care_Text = plan_of_care_text,
                                                                    Plan_Of_Care_Entry = plan_of_care_entry,
                                                                    Social_History_Text = social_history_text,
                                                                    Social_History_Entry = social_history_entry,
                                                                    Problems_Text = problems_text,
                                                                    Problems_Entry = problems_entry,
                                                                    Medications_Text = medications_text,
                                                                    Medications_Entry = medications_entry,
                                                                    Allergies_Text = allergies_text,
                                                                    Allergies_Entry = allergies_entry)

            #render lab summary template with saved variables and save to output
            lab_summary_output = lab_summary_template.render(Effective_Time = effective_time,
                                                                Record_Target = record_target,
                                                                Author = author,
                                                                Custodian = custodian,
                                                                Documentation_Of = documentation_of,
                                                                Encounter_TR = encounter_tr,
                                                                Encounter_Entry = encounter_entry,
                                                                Social_History_Text = social_history_text,
                                                                Social_History_Entry = social_history_entry,
                                                                Problems_Text = problems_text,
                                                                Problems_Entry = problems_entry,
                                                                Vital_Signs_Text = vital_signs_text,
                                                                Vital_Signs_Entry = vital_signs_entry,
                                                                Diagnostic_Results_Text = diagnostic_results_text,
                                                                Diagnostic_Results_Entry = diagnostic_results_entry)

            #render immunizations summary template with saved variables and save to output
            immunizations_summary_output = immunizations_summary_template.render(Effective_Time = effective_time,
                                                                Record_Target = record_target,
                                                                Author = author,
                                                                Custodian = custodian,
                                                                Documentation_Of = documentation_of,
                                                                Encounter_TR = encounter_tr,
                                                                Encounter_Entry = encounter_entry,
                                                                Social_History_Text = social_history_text,
                                                                Social_History_Entry = social_history_entry,
                                                                Plan_Of_Care_Text = plan_of_care_text,
                                                                Plan_Of_Care_Entry = plan_of_care_entry,
                                                                Immunizations_Text = immunizations_text,
                                                                Immunizations_Entry = immunizations_entry)


            #write output files with new data:
            #create folder for patient
            if not os.path.exists("pitd_gen_output/" + given + "_" + family):
                folder = os.makedirs("pitd_gen_output/" + given + "_" + family)

            #create folder for ccd set
            if not os.path.exists("pitd_gen_output/" + given + "_" + family + "/" + os.path.splitext(filename)[0]):
                folder = os.makedirs("pitd_gen_output/" + given + "_" + family + "/" + os.path.splitext(filename)[0])

            # checks if CCD has encounter section with content, if so saves file ~ Encounter_Summary.xml
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '46240-8':
                            is_pop = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                            if len(is_pop) > 0:
                                myfile = open("pitd_gen_output/" + given + "_" + family + "/" + os.path.splitext(filename)[0] + "/Encounter_Summary___" + author_institution + "___" + creation_time + ".xml", "w")
                                myfile.write(encounter_summary_output)
                                # add encounters note from last encounter
                                rx = r"\s+(?=\d{4}-\d{2}-\d{2})"
                                for notesname in os.listdir('Notes'):
                                    #skip .DS_Store files
                                    if not notesname.startswith('.'):
                                        if os.path.splitext(notesname)[0] == os.path.splitext(filename)[0]:
                                            #find corresponding notes file
                                            with open("Notes/" + os.path.splitext(notesname)[0] + ".txt") as openfile:
                                                if os.path.getsize(openfile.name) > 1:
                                                    notes_paragraph = openfile.readlines()
                                                    notes_paragraph = "<br /> ".join(notes_paragraph)
                                                    notes_paragraph = re.split(rx, notes_paragraph)[1]
                                                    #creates notes xml componenet and fills paragraph element with notes
                                                    content = ('''
                                                    <component>
                                                        <section>
                                                          <code code="34109-9" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Note" />
                                                          <title>Miscellaneous Notes</title>
                                                          <text>
                                                            <list styleCode="TOC">
                                                              <item>
                                                                <paragraph>
                                                                    <br />{notes_paragraph}<br />
                                                                </paragraph>
                                                              </item>
                                                            </list>
                                                          </text>
                                                        </section>
                                                    </component>
                                                    ''').format(notes_paragraph = notes_paragraph)
                                                    #inserts filled notes component above into CCDA as last element in tree:
                                                    content = etree.XML(content)
                                                    parser = etree.XMLParser(remove_blank_text=True)
                                                    with open("pitd_gen_output/" + given + "_" + family + "/" + os.path.splitext(filename)[0] + "/Encounter_Summary___" + author_institution + "___" + creation_time + ".xml") as encounter_file:
                                                        encounter_tree = etree.parse(encounter_file, parser)
                                                        contentnav = encounter_tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody")[-1]
                                                        contentdiv = contentnav.getparent()
                                                        contentdiv.insert(contentdiv.index(contentnav)+1, content)
                                                    myfile = open("pitd_gen_output/" + given + "_" + family + "/" + os.path.splitext(filename)[0] + "/Encounter_Summary___" + author_institution + "___" + creation_time + ".xml", "w")
                                                    myfile.write(etree.tounicode(encounter_tree))

            # checks if CCD has refill section with content, if so saves file ~ Refill_Summary.xml
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '10160-0':
                            is_pop = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                            if len(is_pop) > 0:
                                myfile2 = open("pitd_gen_output/" + given + "_" + family + "/" + os.path.splitext(filename)[0] + "/Refill_Summary___" + author_institution + "___" + creation_time + ".xml", "w")
                                myfile2.write(refill_summary_output)
                                # add medications note from last encounter
                                rx = r"\s+(?=\d{4}-\d{2}-\d{2})"
                                for notesname in os.listdir('Notes'):
                                    #skip .DS_Store files
                                    if not notesname.startswith('.'):
                                        if os.path.splitext(notesname)[0] == os.path.splitext(filename)[0]:
                                            #find corresponding notes file
                                            with open("Notes/" + os.path.splitext(notesname)[0] + ".txt") as openfile:
                                                if os.path.getsize(openfile.name) > 1:
                                                    notes_paragraph = openfile.readlines()
                                                    notes_paragraph = "".join(notes_paragraph)
                                                    notes_paragraph = re.split(rx, notes_paragraph)[1]
                                                    notes_paragraph = re.split("#", notes_paragraph)
                                                    meds_note = []
                                                    meds_note.append(notes_paragraph[0])
                                                    for i in notes_paragraph:
                                                        if i.startswith((" Medications", " Plan")):
                                                            meds_note.append(i)
                                                    meds_note = [x.replace('\n', '<br />') for x in meds_note]
                                                    meds_note = "<br />".join(meds_note)
                                                    #creates notes xml componenet and fills paragraph element with notes
                                                    content = ('''
                                                    <component>
                                                        <section>
                                                          <code code="34109-9" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Note" />
                                                          <title>Miscellaneous Notes</title>
                                                          <text>
                                                            <list styleCode="TOC">
                                                              <item>
                                                                <paragraph>
                                                                    <br />{notes_paragraph}<br />
                                                                </paragraph>
                                                              </item>
                                                            </list>
                                                          </text>
                                                        </section>
                                                    </component>
                                                    ''').format(notes_paragraph = meds_note)
                                                    #inserts filled notes component above into CCDA as last element in tree:
                                                    content = etree.XML(content)
                                                    parser = etree.XMLParser(remove_blank_text=True)
                                                    with open("pitd_gen_output/" + given + "_" + family + "/" + os.path.splitext(filename)[0] + "/Refill_Summary___" + author_institution + "___" + creation_time + ".xml") as med_file:
                                                        med_tree = etree.parse(med_file, parser)
                                                        contentnav = med_tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody")[-1]
                                                        contentdiv = contentnav.getparent()
                                                        contentdiv.insert(contentdiv.index(contentnav)+1, content)
                                                    myfile2 = open("pitd_gen_output/" + given + "_" + family + "/" + os.path.splitext(filename)[0] + "/Refill_Summary___" + author_institution + "___" + creation_time + ".xml", "w")
                                                    myfile2.write(etree.tounicode(med_tree))

            # checks if CCD has lab section with content, if so saves file ~ Lab_Summary.xml
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '8716-3':
                            is_pop = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                            if len(is_pop) > 0:
                                myfile3 = open("pitd_gen_output/" + given + "_" + family + "/" + os.path.splitext(filename)[0] + "/Lab_Summary___" + author_institution + "___" + creation_time + ".xml", "w")
                                myfile3.write(lab_summary_output)

            # checks if CCD has immunization section with content, if so saves file ~ Immunizations_Summary.xml
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                for i in child.find("{urn:hl7-org:v3}section"):
                    if i.tag == "{urn:hl7-org:v3}code":
                        if i.attrib['code'] == '11369-6':
                            is_pop = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                            if len(is_pop) > 0:
                                myfile4 = open("pitd_gen_output/" + given + "_" + family + "/" + os.path.splitext(filename)[0] + "/Immunizations_Summary___" + author_institution + "___" + creation_time + ".xml", "w")
                                myfile4.write(immunizations_summary_output)

            #ADD NOTES TO CCD before writing new CCD to output:
            #gets matching notes file for ccd and grabs text, formats as xml fragment
            for notesname in os.listdir('Notes'):
                #skip .DS_Store files
                if not notesname.startswith('.'):
                    if os.path.splitext(notesname)[0] == os.path.splitext(filename)[0]:
                        #find corresponding notes file
                        with open("Notes/" + os.path.splitext(notesname)[0] + ".txt") as openfile:
                            if os.path.getsize(openfile.name) > 1:
                                notes_paragraph = openfile.readlines()
                                notes_paragraph = "<br />".join(notes_paragraph)

                                #creates notes xml componenet and fills paragraph element with xml fragment parsed from CCD
                                content = ('''
                                <component>
                                    <section>
                                      <code code="34109-9" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Note" />
                                      <title>Miscellaneous Notes</title>
                                      <text>
                                        <list styleCode="TOC">
                                          <item>
                                            <paragraph>
                                                {notes_paragraph}
                                            </paragraph>
                                          </item>
                                        </list>
                                      </text>
                                    </section>
                                </component>
                                ''').format(notes_paragraph = notes_paragraph)

                                #inserts filled notes component above into CCD as last element in tree:
                                content = etree.XML(content)
                                contentnav = tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody")[-1]
                                contentdiv = contentnav.getparent()
                                contentdiv.insert(contentdiv.index(contentnav)+1, content)


            #write original CCD to output folder with notes added - check if theres a populated encounter - if not dont write
            for child in tree.find("{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody"):
                section_exists = child.find("{urn:hl7-org:v3}section")
                if section_exists != None:
                    for i in child.find("{urn:hl7-org:v3}section"):
                        if i.tag == "{urn:hl7-org:v3}code":
                            if i.attrib['code'] == '46240-8':
                                is_pop = child.findall("{urn:hl7-org:v3}section/{urn:hl7-org:v3}entry")
                                if len(is_pop) > 0:
                                    myfile5 = open("pitd_gen_output/" + given + "_" + family + "/" + os.path.splitext(filename)[0] + "/Continuity_of_Care_Document___" + author_institution + "___" + creation_time + ".xml", "w")
                                    myfile5.write(etree.tounicode(tree))


#loop through each output CCDA file - reformat xml spacing, name, and zip by parsing tree with lxml and rewrite
csv_output = []
for output_patient in os.listdir('pitd_gen_output'):
    if not output_patient.startswith('.'):
        filecount = 0
        for output_folder in os.listdir('pitd_gen_output/' + output_patient):
            if not output_folder.startswith('.'):
                for output_file in os.listdir('pitd_gen_output/' + output_patient + "/" + output_folder):
                    if not output_file.startswith('.'):
                        with open("pitd_gen_output/" + output_patient + "/" + output_folder + "/" + output_file) as openfile:
                            parser = etree.XMLParser(remove_blank_text=True)
                            x = etree.parse(openfile, parser)
                            name_div = x.find("{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole/{urn:hl7-org:v3}patient/{urn:hl7-org:v3}name")
                            given = name_div.find("{urn:hl7-org:v3}given").text
                            family = name_div.find("{urn:hl7-org:v3}family").text
                            given = ''.join([i for i in given if not i.isdigit()])
                            family = ''.join([i for i in family if not i.isdigit()])
                            exclude = set(string.punctuation)
                            given = ''.join(ch for ch in given if ch not in exclude)
                            family = ''.join(ch for ch in family if ch not in exclude)
                            name_div.find("{urn:hl7-org:v3}given").text = given
                            name_div.find("{urn:hl7-org:v3}family").text = family
                            zip_code_patient = x.find("{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole/{urn:hl7-org:v3}addr/{urn:hl7-org:v3}postalCode").text
                            zip_code_organization = x.find("{urn:hl7-org:v3}author/{urn:hl7-org:v3}assignedAuthor/{urn:hl7-org:v3}representedOrganization/{urn:hl7-org:v3}addr/{urn:hl7-org:v3}postalCode").text
                            zip_code_organization = zip_code_organization.split("-", 1)
                            zip_code_organization = zip_code_organization[0]
                            if zip_code_patient == None:
                                x.find("{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole/{urn:hl7-org:v3}addr/{urn:hl7-org:v3}postalCode").text = zip_code_organization
                                x.find("{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole/{urn:hl7-org:v3}addr/{urn:hl7-org:v3}postalCode").attrib.pop("nullFlavor", None)
                            write_file = open("pitd_gen_output/" + output_patient + "/" + output_folder + "/" + output_file, 'w')
                            write_file.write(etree.tounicode(x, pretty_print = True))

                            #csv output:
                            zip_code_patient = x.find("{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole/{urn:hl7-org:v3}addr/{urn:hl7-org:v3}postalCode").text
                            patient_dob_full = x.find("{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole/{urn:hl7-org:v3}patient/{urn:hl7-org:v3}birthTime").attrib["value"]
                            patient_dob = patient_dob_full[0:4] + "-" + patient_dob_full[4:6] + "-" + patient_dob_full[6:8]
                            patient_gender = x.find("{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole/{urn:hl7-org:v3}patient/{urn:hl7-org:v3}administrativeGenderCode").attrib["code"]
                            if patient_gender == "M":
                                patient_gender = "Male"
                            if patient_gender == "F":
                                patient_gender = "Female"
                            patient_address = x.find("{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole/{urn:hl7-org:v3}addr/{urn:hl7-org:v3}streetAddressLine").text
                            patient_city = x.find("{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole/{urn:hl7-org:v3}addr/{urn:hl7-org:v3}city").text
                            patient_state = x.find("{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole/{urn:hl7-org:v3}addr/{urn:hl7-org:v3}state").text
                            demographic_json = ('''
                                                {{
                                                  "address_city": "{patient_city}",
                                                  "address_lines": [
                                                    "{patient_address}"
                                                  ],
                                                  "address_state": "{patient_state}",
                                                  "date_of_birth": "{patient_dob}",
                                                  "email": "{given}@doe.com",
                                                  "family_name": "{family}",
                                                  "gender": "{patient_gender}",
                                                  "given_name": "{given}",
                                                  "npi": "1234",
                                                  "postal_code": "{zip_code_patient}",
                                                  "purpose_of_use": "TREATMENT",
                                                  "ssn": "123-45-6789",
                                                  "telephone": "1-234-567-8910"
                                                }}
                                                ''').format(patient_city = patient_city,
                                                    patient_address = patient_address,
                                                    patient_state = patient_state,
                                                    patient_dob = patient_dob,
                                                    given = given,
                                                    family = family,
                                                    patient_gender = patient_gender,
                                                    zip_code_patient = zip_code_patient)

                    filecount = filecount + 1
        line = ["dataset", family, given, patient_dob, zip_code_patient, patient_gender, "age", filecount, patient_address, patient_city, patient_state, demographic_json]
        csv_output.append(line)

#get rid of DS Store files:
for output_patient in os.listdir('pitd_gen_output'):
    if output_patient.startswith('.'):
        os.remove("pitd_gen_output/" + output_patient)
    else:
        for output_folder in os.listdir('pitd_gen_output/' + output_patient):
            if output_folder.startswith('.'):
                os.remove("pitd_gen_output/" + output_patient + "/" + output_folder)
            else:
                for output_file in os.listdir('pitd_gen_output/' + output_patient + "/" + output_folder):
                    if output_file.startswith('.'):
                        os.remove("pitd_gen_output/" + output_patient + "/" + output_folder + "/" + output_file)
        print(output_patient)

#write patient directory csv
with open("output_directory.csv", "w") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerows(csv_output)
