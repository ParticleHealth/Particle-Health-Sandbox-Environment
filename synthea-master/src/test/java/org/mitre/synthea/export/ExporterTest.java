package org.mitre.synthea.export;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.mitre.synthea.TestHelper.years;

import org.junit.Before;
import org.junit.Test;
import org.mitre.synthea.TestHelper;
import org.mitre.synthea.engine.Generator;
import org.mitre.synthea.helpers.Config;
import org.mitre.synthea.modules.DeathModule;
import org.mitre.synthea.world.agents.Payer;
import org.mitre.synthea.world.agents.Person;
import org.mitre.synthea.world.agents.Provider;
import org.mitre.synthea.world.concepts.HealthRecord;
import org.mitre.synthea.world.concepts.HealthRecord.Code;
import org.mitre.synthea.world.concepts.HealthRecord.Encounter;
import org.mitre.synthea.world.concepts.HealthRecord.EncounterType;
import org.mitre.synthea.world.concepts.HealthRecord.Medication;
import org.mitre.synthea.world.geography.Location;

public class ExporterTest {

  private long time;
  private long endTime;
  private int yearsToKeep;
  private Person patient;
  private HealthRecord record;
  
  private static final HealthRecord.Code DUMMY_CODE = new HealthRecord.Code("", "", "");
  
  /**
   * Setup test data.
   * @throws Exception on configuration loading error.
   */
  @Before
  public void setup() throws Exception {
    Config.set("exporter.split_records", "false");
    endTime = time = System.currentTimeMillis();
    yearsToKeep = 5;
    patient = new Person(12345L);
    patient.attributes.put(Person.BIRTHDATE, time - years(30));
    // Give person an income to prevent null pointer.
    patient.attributes.put(Person.INCOME, 100000);
    TestHelper.loadTestProperties();
    Generator.DEFAULT_STATE = Config.get("test_state.default", "Massachusetts");
    Location location = new Location(Generator.DEFAULT_STATE, null);
    location.assignPoint(patient, location.randomCityName(patient));
    Provider.loadProviders(location, 1L);
    record = patient.record;
    // Ensure Person's Payer is not null.
    Payer.loadNoInsurance();
    for (int i = 0; i < patient.payerHistory.length; i++) {
      patient.setPayerAtAge(i, Payer.noInsurance);
    }
  }

  @Test
  public void testExportFilterSimpleCutoff() {
    record.encounterStart(time - years(8), EncounterType.WELLNESS);
    record.observation(time - years(8), "height", 64);
    
    record.encounterStart(time - years(4), EncounterType.WELLNESS);
    record.observation(time - years(4), "weight", 128);

    // observations should be filtered to the cutoff date

    Person filtered = Exporter.filterForExport(patient, yearsToKeep, endTime);

    Encounter encounter = filtered.record.currentEncounter(time);
    assertEquals(1, encounter.observations.size());
    assertEquals("weight", encounter.observations.get(0).type);
    assertEquals(time - years(4), encounter.observations.get(0).start);
    assertEquals(128, encounter.observations.get(0).value);
  }

  @Test
  public void testExportFilterShouldKeepOldActiveMedication() {

    Code code = new Code("SNOMED-CT","705129","Fake Code");

    record.encounterStart(time - years(10), EncounterType.AMBULATORY);
    record.medicationStart(time - years(10), "fakeitol", true);

    record.encounterStart(time - years(8), EncounterType.AMBULATORY);
    Medication med = record.medicationStart(time - years(8), "placebitol", true);
    med.codes.add(code);

    record.medicationEnd(time - years(6), "placebitol", DUMMY_CODE);

    Person filtered = Exporter.filterForExport(patient, yearsToKeep, endTime);

    Encounter encounter = filtered.record.currentEncounter(time);
    assertEquals(1, encounter.medications.size());
    assertEquals("fakeitol", encounter.medications.get(0).type);
    assertEquals(time - years(10), encounter.medications.get(0).start);
  }

  @Test
  public void testExportFilterShouldKeepMedicationThatEndedDuringTarget() {

    Code code = new Code("SNOMED-CT","705129","Fake Code");

    record.encounterStart(time - years(10), EncounterType.AMBULATORY);
    Medication med = record.medicationStart(time - years(10), "dimoxinil", false);
    med.codes.add(code);
    record.medicationEnd(time - years(9), "dimoxinil", DUMMY_CODE);

    record.encounterStart(time - years(8), EncounterType.AMBULATORY);
    med = record.medicationStart(time - years(8), "placebitol", true);
    med.codes.add(code);

    record.medicationEnd(time - years(4), "placebitol", DUMMY_CODE);

    Person filtered = Exporter.filterForExport(patient, yearsToKeep, endTime);

    Encounter encounter = filtered.record.currentEncounter(time);
    assertEquals(1, encounter.medications.size());
    assertEquals("placebitol", encounter.medications.get(0).type);
    assertEquals(time - years(8), encounter.medications.get(0).start);
    assertEquals(time - years(4), encounter.medications.get(0).stop);
  }

  @Test
  public void testExportFilterShouldKeepOldActiveCareplan() {
    record.encounterStart(time - years(10), EncounterType.WELLNESS);
    record.careplanStart(time - years(10), "stop_smoking");
    record.careplanEnd(time - years(8), "stop_smoking", DUMMY_CODE);

    record.encounterStart(time - years(12), EncounterType.WELLNESS);
    record.careplanStart(time - years(12), "healthy_diet");

    Person filtered = Exporter.filterForExport(patient, yearsToKeep, endTime);

    Encounter encounter = filtered.record.currentEncounter(time);
    assertEquals(1, encounter.careplans.size());
    assertEquals("healthy_diet", encounter.careplans.get(0).type);
    assertEquals(time - years(12), encounter.careplans.get(0).start);
  }

  @Test
  public void testExportFilterShouldKeepCareplanThatEndedDuringTarget() {
    record.encounterStart(time - years(10), EncounterType.WELLNESS);
    record.careplanStart(time - years(10), "stop_smoking");
    record.careplanEnd(time - years(1), "stop_smoking", DUMMY_CODE);

    Person filtered = Exporter.filterForExport(patient, yearsToKeep, endTime);

    Encounter encounter = filtered.record.currentEncounter(time);
    assertEquals(1, encounter.careplans.size());
    assertEquals("stop_smoking", encounter.careplans.get(0).type);
    assertEquals(time - years(10), encounter.careplans.get(0).start);
    assertEquals(time - years(1), encounter.careplans.get(0).stop);
  }

  @Test
  public void testExportFilterShouldKeepOldActiveConditions() {
    record.encounterStart(time - years(10), EncounterType.WELLNESS);
    record.conditionStart(time - years(10), "fakitis");
    record.conditionEnd(time - years(8), "fakitis");

    record.encounterStart(time - years(10), EncounterType.WELLNESS);
    record.conditionStart(time - years(10), "fakosis");

    Person filtered = Exporter.filterForExport(patient, yearsToKeep, endTime);

    Encounter encounter = filtered.record.currentEncounter(time);
    assertEquals(1, encounter.conditions.size());
    assertEquals("fakosis", encounter.conditions.get(0).type);
    assertEquals(time - years(10), encounter.conditions.get(0).start);
  }

  @Test
  public void testExportFilterShouldKeepConditionThatEndedDuringTarget() {
    record.encounterStart(time - years(10), EncounterType.WELLNESS);
    record.conditionStart(time - years(10), "boneitis");
    record.conditionEnd(time - years(2), "boneitis");

    record.encounterStart(time - years(10), EncounterType.WELLNESS);
    record.conditionStart(time - years(10), "smallpox");
    record.conditionEnd(time - years(9), "smallpox");

    Person filtered = Exporter.filterForExport(patient, yearsToKeep, endTime);

    Encounter encounter = filtered.record.currentEncounter(time);
    assertEquals(1, encounter.conditions.size());
    assertEquals("boneitis", encounter.conditions.get(0).type);
    assertEquals(time - years(10), encounter.conditions.get(0).start);
  }

  @Test
  public void testExportFilterShouldKeepCauseOfDeath() {
    HealthRecord.Code causeOfDeath = 
        new HealthRecord.Code("SNOMED-CT", "Todo-lookup-code", "Rabies");
    patient.recordDeath(time - years(20), causeOfDeath);
    
    DeathModule.process(patient, time - years(20));
    Person filtered = Exporter.filterForExport(patient, yearsToKeep, endTime);

    assertEquals(1, filtered.record.encounters.size());
    Encounter encounter = filtered.record.encounters.get(0);
    assertEquals(DeathModule.DEATH_CERTIFICATION, encounter.codes.get(0));
    assertEquals(time - years(20), encounter.start);

    assertEquals(1, encounter.observations.size());
    assertEquals(DeathModule.CAUSE_OF_DEATH_CODE.code, encounter.observations.get(0).type);
    assertEquals(time - years(20), encounter.observations.get(0).start);

    assertEquals(1, encounter.reports.size());
    assertEquals(DeathModule.DEATH_CERTIFICATE.code, encounter.reports.get(0).type);
    assertEquals(time - years(20), encounter.reports.get(0).start);
  }

  @Test
  public void testExportFilterShouldNotKeepOldStuff() {
    record.encounterStart(time - years(18), EncounterType.EMERGENCY);
    record.procedure(time - years(20), "appendectomy");
    record.immunization(time - years(12), "flu_shot");
    record.observation(time - years(10), "weight", 123);

    Person filtered = Exporter.filterForExport(patient, yearsToKeep, endTime);

    assertTrue(filtered.record.encounters.isEmpty());
  }

  @Test
  public void testExportFilterShouldKeepOldActiveStuff() {
    // create an old encounter with a diagnosis that isn't ended
    record.encounterStart(time - years(18), EncounterType.EMERGENCY);
    record.conditionStart(time - years(18), "diabetes");

    Person filtered = Exporter.filterForExport(patient, yearsToKeep, endTime);

    assertEquals(1, filtered.record.encounters.size());
    assertEquals(1, filtered.record.encounters.get(0).conditions.size());
    assertEquals("diabetes", filtered.record.encounters.get(0).conditions.get(0).type);
  }
  
  @Test
  public void testExportFilterShouldFilterClaimItems() {
    record.encounterStart(time - years(10), EncounterType.EMERGENCY);
    record.conditionStart(time - years(10), "something_permanent");
    record.procedure(time - years(10), "xray");
    
    assertEquals(1, record.encounters.size());
    assertEquals(2, record.encounters.get(0).claim.items.size()); // 1 condition, 1 procedure
    
    Person filtered = Exporter.filterForExport(patient, yearsToKeep, endTime);
    // filter removes the procedure but keeps the open condition
    assertEquals(1, filtered.record.encounters.size());
    assertEquals(1, filtered.record.encounters.get(0).conditions.size());
    assertEquals("something_permanent", filtered.record.encounters.get(0).conditions.get(0).type);
    assertEquals(1, record.encounters.get(0).claim.items.size());
    assertEquals("something_permanent", record.encounters.get(0).claim.items.get(0).type);
  }

}
