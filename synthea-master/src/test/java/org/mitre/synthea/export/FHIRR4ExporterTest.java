package org.mitre.synthea.export;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import ca.uhn.fhir.context.FhirContext;
import ca.uhn.fhir.parser.IParser;
import ca.uhn.fhir.validation.SingleValidationMessage;
import ca.uhn.fhir.validation.ValidationResult;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;

import org.apache.commons.codec.binary.Base64;
import org.hl7.fhir.instance.model.api.IBaseResource;
import org.hl7.fhir.r4.model.Bundle;
import org.hl7.fhir.r4.model.Bundle.BundleEntryComponent;
import org.hl7.fhir.r4.model.Media;
import org.hl7.fhir.r4.model.Observation;
import org.hl7.fhir.r4.model.Quantity;
import org.hl7.fhir.r4.model.SampledData;
import org.junit.After;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import org.mitre.synthea.TestHelper;
import org.mitre.synthea.engine.Generator;
import org.mitre.synthea.engine.Module;
import org.mitre.synthea.engine.State;
import org.mitre.synthea.helpers.Config;
import org.mitre.synthea.helpers.Utilities;
import org.mitre.synthea.world.agents.Payer;
import org.mitre.synthea.world.agents.Person;
import org.mitre.synthea.world.agents.Provider;
import org.mitre.synthea.world.concepts.HealthRecord.EncounterType;
import org.mitre.synthea.world.concepts.VitalSign;
import org.mockito.Mockito;

/**
 * Uses HAPI FHIR project to validate FHIR export. http://hapifhir.io/doc_validation.html
 */
public class FHIRR4ExporterTest {
  private boolean physStateEnabled;
  
  /**
   * Temporary folder for any exported files, guaranteed to be deleted at the end of the test.
   */
  @Rule
  public TemporaryFolder tempFolder = new TemporaryFolder();
  
  /**
   * Setup state for exporter test.
   */
  @Before
  public void setup() {
    // Ensure Physiology state is enabled
    physStateEnabled = State.ENABLE_PHYSIOLOGY_STATE;
    State.ENABLE_PHYSIOLOGY_STATE = true;
  }
  
  /**
   * Reset state after exporter test.
   */
  @After
  public void tearDown() {
    State.ENABLE_PHYSIOLOGY_STATE = physStateEnabled;
  }
  
  @Test
  public void testDecimalRounding() {
    Integer i = 123456;
    Object v = FhirR4.mapValueToFHIRType(i,"fake");
    assertTrue(v instanceof Quantity);
    Quantity q = (Quantity)v;
    assertTrue(q.getValue().compareTo(BigDecimal.valueOf(123460)) == 0);

    Double d = 0.000123456;
    v = FhirR4.mapValueToFHIRType(d, "fake");
    assertTrue(v instanceof Quantity);
    q = (Quantity)v;
    assertTrue(q.getValue().compareTo(BigDecimal.valueOf(0.00012346)) == 0);

    d = 0.00012345678901234;
    v = FhirR4.mapValueToFHIRType(d, "fake");
    assertTrue(v instanceof Quantity);
    q = (Quantity)v;
    assertTrue(q.getValue().compareTo(BigDecimal.valueOf(0.00012346)) == 0);
  }

  @Test
  public void testFHIRR4Export() throws Exception {
    TestHelper.loadTestProperties();
    Generator.DEFAULT_STATE = Config.get("test_state.default", "Massachusetts");
    Config.set("exporter.baseDirectory", tempFolder.newFolder().toString());

    FhirContext ctx = FhirContext.forR4();
    IParser parser = ctx.newJsonParser().setPrettyPrint(true);
    ValidationResources validator = new ValidationResources();
    List<String> validationErrors = new ArrayList<String>();

    int numberOfPeople = 10;
    Generator generator = new Generator(numberOfPeople);
    
    generator.options.overflow = false;

    for (int i = 0; i < numberOfPeople; i++) {
      int x = validationErrors.size();
      TestHelper.exportOff();
      Person person = generator.generatePerson(i);
      FhirR4.TRANSACTION_BUNDLE = person.randBoolean();
      FhirR4.USE_US_CORE_IG = person.randBoolean();
      FhirR4.USE_SHR_EXTENSIONS = false;
      String fhirJson = FhirR4.convertToFHIRJson(person, System.currentTimeMillis());
      // Check that the fhirJSON doesn't contain unresolved SNOMED-CT strings
      // (these should have been converted into URIs)
      if (fhirJson.contains("SNOMED-CT")) {
        validationErrors.add(
            "JSON contains unconverted references to 'SNOMED-CT' (should be URIs)");
      }
      // Now validate the resource...
      IBaseResource resource = ctx.newJsonParser().parseResource(fhirJson);
      ValidationResult result = validator.validateR4(resource);
      if (!result.isSuccessful()) {
        // If the validation failed, let's crack open the Bundle and validate
        // each individual entry.resource to get context-sensitive error
        // messages...
        Bundle bundle = parser.parseResource(Bundle.class, fhirJson);
        for (Bundle.BundleEntryComponent entry : bundle.getEntry()) {
          ValidationResult eresult = validator.validateR4(entry.getResource());
          if (!eresult.isSuccessful()) {
            for (SingleValidationMessage emessage : eresult.getMessages()) {
              boolean valid = false;
              if (emessage.getMessage().contains("@ AllergyIntolerance ait-2")) {
                /*
                 * The ait-2 invariant:
                 * Description:
                 * AllergyIntolerance.clinicalStatus SHALL NOT be present
                 * if verification Status is entered-in-error
                 * Expression:
                 * verificationStatus!='entered-in-error' or clinicalStatus.empty()
                 */
                valid = true;
              } else if (emessage.getMessage().contains("@ ExplanationOfBenefit dom-3")) {
                /*
                 * For some reason, it doesn't like the contained ServiceRequest and contained
                 * Coverage resources in the ExplanationOfBenefit, both of which are
                 * properly referenced. Running $validate on test servers finds this valid...
                 */
                valid = true;
              } else if (emessage.getMessage().contains(
                  "per-1: If present, start SHALL have a lower value than end")) {
                /*
                 * The per-1 invariant does not account for daylight savings time... so, if the
                 * daylight savings switch happens between the start and end, the validation
                 * fails, even if it is valid.
                 */
                valid = true; // ignore this error
              } else if (emessage.getMessage().contains("[active, inactive, entered-in-error]")
                  || emessage.getMessage().contains("MedicationStatusCodes-list")) {
                /*
                 * MedicationStatement.status has more legal values than this... including
                 * completed and stopped.
                 */
                valid = true;
              }
              if (!valid) {
                System.out.println(parser.encodeResourceToString(entry.getResource()));
                System.out.println("ERROR: " + emessage.getMessage());
                validationErrors.add(emessage.getMessage());
              }
            }
          }
        }
      }
      int y = validationErrors.size();
      if (x != y) {
        Exporter.export(person, System.currentTimeMillis());
      }
    }
    assertTrue("Validation of exported FHIR bundle failed: "
        + String.join("|", validationErrors), validationErrors.size() == 0);
  }
  
  @Test
  public void testSampledDataExport() throws Exception {

    Person person = new Person(0L);
    person.attributes.put(Person.GENDER, "F");
    person.attributes.put(Person.FIRST_LANGUAGE, "spanish");
    person.attributes.put(Person.RACE, "other");
    person.attributes.put(Person.ETHNICITY, "hispanic");
    person.attributes.put(Person.INCOME, Integer.parseInt(Config
        .get("generate.demographics.socioeconomic.income.poverty")) * 2);
    person.attributes.put(Person.OCCUPATION_LEVEL, 1.0);

    person.history = new LinkedList<>();
    Provider mock = Mockito.mock(Provider.class);
    Mockito.when(mock.getResourceID()).thenReturn("Mock-UUID");
    person.setProvider(EncounterType.AMBULATORY, mock);
    person.setProvider(EncounterType.WELLNESS, mock);
    person.setProvider(EncounterType.EMERGENCY, mock);
    person.setProvider(EncounterType.INPATIENT, mock);

    Long time = System.currentTimeMillis();
    long birthTime = time - Utilities.convertTime("years", 35);
    person.attributes.put(Person.BIRTHDATE, birthTime);

    Payer.loadNoInsurance();
    for (int i = 0; i < person.payerHistory.length; i++) {
      person.setPayerAtAge(i, Payer.noInsurance);
    }
    
    Module module = TestHelper.getFixture("observation.json");
    
    State encounter = module.getState("SomeEncounter");
    assertTrue(encounter.process(person, time));
    person.history.add(encounter);
    
    State physiology = module.getState("Simulate_CVS");
    assertTrue(physiology.process(person, time));
    person.history.add(physiology);
    
    State sampleObs = module.getState("SampledDataObservation");
    assertTrue(sampleObs.process(person, time));
    person.history.add(sampleObs);
    
    FhirContext ctx = FhirContext.forR4();
    IParser parser = ctx.newJsonParser().setPrettyPrint(true);
    String fhirJson = FhirR4.convertToFHIRJson(person, System.currentTimeMillis());
    Bundle bundle = parser.parseResource(Bundle.class, fhirJson);
    
    for (BundleEntryComponent entry : bundle.getEntry()) {
      if (entry.getResource() instanceof Observation) {
        Observation obs = (Observation) entry.getResource();
        assertTrue(obs.getValue() instanceof SampledData);
        SampledData data = (SampledData) obs.getValue();
        assertEquals(10, data.getPeriod().doubleValue(), 0.001); // 0.01s == 10ms
        assertEquals(3, (int) data.getDimensions());
      }
    }
  }
  
  @Test
  public void testObservationAttachment() throws Exception {

    Person person = new Person(0L);
    person.attributes.put(Person.GENDER, "F");
    person.attributes.put(Person.FIRST_LANGUAGE, "spanish");
    person.attributes.put(Person.RACE, "other");
    person.attributes.put(Person.ETHNICITY, "hispanic");
    person.attributes.put(Person.INCOME, Integer.parseInt(Config
        .get("generate.demographics.socioeconomic.income.poverty")) * 2);
    person.attributes.put(Person.OCCUPATION_LEVEL, 1.0);
    person.attributes.put("Pulmonary Resistance", 0.1552);
    person.attributes.put("BMI Multiplier", 0.055);
    person.setVitalSign(VitalSign.BMI, 21.0);

    person.history = new LinkedList<>();
    Provider mock = Mockito.mock(Provider.class);
    Mockito.when(mock.getResourceID()).thenReturn("Mock-Provider");
    person.setProvider(EncounterType.AMBULATORY, mock);
    person.setProvider(EncounterType.WELLNESS, mock);
    person.setProvider(EncounterType.EMERGENCY, mock);
    person.setProvider(EncounterType.INPATIENT, mock);

    Long time = System.currentTimeMillis();
    long birthTime = time - Utilities.convertTime("years", 35);
    person.attributes.put(Person.BIRTHDATE, birthTime);

    Payer.loadNoInsurance();
    for (int i = 0; i < person.payerHistory.length; i++) {
      person.setPayerAtAge(i, Payer.noInsurance);
    }
    
    Module module = TestHelper.getFixture("observation.json");
    
    State physiology = module.getState("Simulate_CVS");
    assertTrue(physiology.process(person, time));
    person.history.add(physiology);
    
    State encounter = module.getState("SomeEncounter");
    assertTrue(encounter.process(person, time));
    person.history.add(encounter);
    
    State chartState = module.getState("ChartObservation");
    assertTrue(chartState.process(person, time));
    person.history.add(chartState);
    
    State urlState = module.getState("UrlObservation");
    assertTrue(urlState.process(person, time));
    person.history.add(urlState);
    
    FhirContext ctx = FhirContext.forR4();
    IParser parser = ctx.newJsonParser().setPrettyPrint(true);
    String fhirJson = FhirR4.convertToFHIRJson(person, System.currentTimeMillis());
    Bundle bundle = parser.parseResource(Bundle.class, fhirJson);
    
    for (BundleEntryComponent entry : bundle.getEntry()) {
      if (entry.getResource() instanceof Media) {
        Media media = (Media) entry.getResource();
        if (media.getContent().getData() != null) {
          assertEquals(400, media.getWidth());
          assertEquals(200, media.getHeight());
          assertEquals("Invasive arterial pressure", media.getReasonCode().get(0).getText());
          assertTrue(Base64.isBase64(media.getContent().getDataElement().getValueAsString()));
        } else if (media.getContent().getUrl() != null) {
          assertEquals("https://example.com/image/12498596132", media.getContent().getUrl());
          assertEquals("en-US", media.getContent().getLanguage());
          assertTrue(media.getContent().getSize() > 0);
        } else {
          fail("Invalid Media element in output JSON");
        }
      }
    }
  }
}
