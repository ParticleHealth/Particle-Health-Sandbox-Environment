package org.mitre.synthea.helpers;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertTrue;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.HashSet;
import java.util.List;

import org.junit.Test;
import org.mitre.synthea.helpers.physiology.IoMapper;
import org.mitre.synthea.helpers.physiology.PhysiologyGeneratorConfig;
import org.mitre.synthea.helpers.physiology.SimRunner;
import org.mitre.synthea.world.agents.Person;
import org.mitre.synthea.world.concepts.VitalSign;

public class PhysiologyValueGeneratorTest {
  
  private static final SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd");
  
  long dateToSimTime(String dateStr) {
    try {
      return dateFormat.parse(dateStr).getTime();
    } catch (ParseException e) {
      throw new RuntimeException(e);
    }
  }
  
  @Test
  public void testValueGenerator() {
    
    Person person = new Person(0);
    
    // Person born on July 25, 1988
    person.attributes.put(Person.BIRTHDATE, dateToSimTime("1988-07-25"));
    
    // Set their BMI to a normal 22 kg/m^2
    person.setVitalSign(VitalSign.BMI, 22.0);
    
    PhysiologyGeneratorConfig config = PhysiologyValueGenerator.getConfig(
        "circulation_hemodynamics.yml");
    
    // Don't use pre generators so the model will run initially
    config.setUsePreGenerators(false);
    
    // Set the input variance threshold for R_sys to 0.1 so a small change will not
    // cause a re-run of the simulation
    for (IoMapper mapper : config.getInputs()) {
      if (mapper.getTo() == "R_sys") {
        mapper.setVariance(0.1);
      }
    }
    
    // Set our current simulation time
    long simTime = dateToSimTime("2019-09-19");
    
    SimRunner runner = new SimRunner(config, person);
    
    // Get the generator for systolic BP
    PhysiologyValueGenerator generator = new PhysiologyValueGenerator(config, runner,
        VitalSign.SYSTOLIC_BLOOD_PRESSURE, person, 0.0);
    
    double sys1 = generator.getValue(simTime);
    
    // Make sure it's a reasonable value
    assertTrue("sys1 is a reasonable systolic bp value", (100 < sys1) && (sys1 < 160));
    
    // Change the time by just a few seconds. The simulation should not run again,
    // which means the output value will be exactly the same.
    
    simTime += 30000;
    double sys2 = generator.getValue(simTime);
    assertEquals(sys1, sys2, 0);
    
    // Change the time by several years. Now the simulation should definitely run
    // again, which will change the output value.
    simTime = dateToSimTime("2070-09-19");
    double sys3 = generator.getValue(simTime);
    
    // Make sure it's a reasonable value
    assertTrue("sys3 is a reasonable systolic bp value", (100 < sys1) && (sys1 < 160));
    
    assertNotEquals(sys1, sys3);
    
    // Change the output variance to a small amount and verify that the result is no longer
    // exactly the same but within the variance amount.
    generator.setOutputVariance(1.0);
    double sys4 = generator.getValue(simTime);
    assertEquals(sys3, sys4, 1.0);
    assertNotEquals(sys3, sys4);
    
  }
  
  @Test
  public void testMultiLoad() {
    // Verify that we can load all ValueGenerators defined in a configuration file
    
    Person person = new Person(0);
    person.attributes.put(Person.BIRTHDATE, dateToSimTime("1988-07-25"));
    person.setVitalSign(VitalSign.BMI, 22.0);
    
    PhysiologyGeneratorConfig config = PhysiologyValueGenerator.getConfig(
        "circulation_hemodynamics.yml");
    
    List<PhysiologyValueGenerator> generators = PhysiologyValueGenerator.fromConfig(config, person);
    
    // Create a Set with each VitalSign in the config
    HashSet<VitalSign> cfgVitals = new HashSet<VitalSign>();
    for (IoMapper mapper : config.getOutputs()) {
      if (mapper.getType() == IoMapper.IoType.VITAL_SIGN) {
        cfgVitals.add(VitalSign.fromString(mapper.getTo()));
      }
    }
    
    // Create a Set with each VitalSign generator
    HashSet<VitalSign> genVitals = new HashSet<VitalSign>();
    for (PhysiologyValueGenerator generator : generators) {
      genVitals.add(generator.getVitalSign());
    }
    
    assertEquals(cfgVitals, genVitals);
  }
  
  @Test
  public void testLoadAll() {
    // Verify that we can load all ValueGenerators defined in a configuration file
    
    Person person = new Person(0);
    
    List<PhysiologyValueGenerator> generators = PhysiologyValueGenerator.loadAll(person);
    
    assertTrue("At least one generator loaded", generators.size() > 0);
  }
  
  @Test
  public void testToString() {
    Person person = new Person(0);
    person.attributes.put(Person.BIRTHDATE, dateToSimTime("1988-07-25"));
    person.setVitalSign(VitalSign.BMI, 22.0);
    
    PhysiologyGeneratorConfig config = PhysiologyValueGenerator.getConfig(
        "circulation_hemodynamics.yml");
    
    SimRunner runner = new SimRunner(config, person);
    
    // Get the generator for systolic BP
    PhysiologyValueGenerator generator = new PhysiologyValueGenerator(config, runner,
        VitalSign.SYSTOLIC_BLOOD_PRESSURE, person, 0.0);
    
    assertEquals("PhysiologyValueGenerator {model=circulation/Smith2004_CVS_human.xml, "
        + "VitalSigns=[LVEF, SYSTOLIC_BLOOD_PRESSURE, DIASTOLIC_BLOOD_PRESSURE], "
        + "Attributes=[]}", generator.toString());
  }
}