package org.mitre.synthea.engine;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;

import java.util.List;

import org.junit.Test;
import org.mitre.synthea.world.agents.Person;
import org.mitre.synthea.world.concepts.HealthRecord;

public class HealthRecordEditorsTest {
  class Dummy implements HealthRecordEditor {

    @Override
    public boolean shouldRun(Person person, HealthRecord record, long time) {
      return time > 1000;
    }

    @Override
    public void process(Person person, List<HealthRecord.Encounter> encounters, long time) {
      person.attributes.put(Person.ZIP, "01730");
    }
  }

  @Test
  public void getInstance() {
    assertNotNull(HealthRecordEditors.getInstance());
  }

  @Test
  public void executeAll() {
    HealthRecordEditors hrm = HealthRecordEditors.getInstance();
    hrm.registerEditor(new Dummy());
    Person p = new Person(1);
    hrm.executeAll(p, new HealthRecord(p), 1, 1);
    assertNull(p.attributes.get(Person.ZIP));
    hrm.executeAll(p, new HealthRecord(p), 1100, 1);
    assertEquals("01730", p.attributes.get(Person.ZIP));
    hrm.resetEditors();
  }
}