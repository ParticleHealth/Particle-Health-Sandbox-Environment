package org.mitre.synthea.engine;

import java.util.List;

import org.mitre.synthea.world.agents.Person;
import org.mitre.synthea.world.concepts.HealthRecord;

/**
 * The HealthRecordEditor offers an interface that can be implemented to modify a Synthea Person's
 * HealthRecord. At the end of every time step in the simulation, the Synthea framework will invoke
 * the shouldRun method. If the shouldRun function returns true, the framework will then invoke
 * the process method. The process method will be passed any encounters that were created in the
 * past time step.
 * <p>
 * HealthRecordEditors are intended to simulate actions that happen to an individual's health
 * record. This includes loss or corruption of information through user entry error or information
 * system defects.
 * </p>
 * <p>
 * HealthRecordEditors SHOULD NOT be used to simulate clinical interactions on the underlying
 * physical state / circumstances of the Synthea Person. Those should be implemented in Synthea
 * modules.
 * </p>
 */
public interface HealthRecordEditor {
  /**
   * Determine whether the editor should be run at the given time step.
   * This will be invoked for the editor at each time step. It is possible for modules to "skip"
   * steps. So an editor may return false and then return true later. An example of this would be
   * for a editor that only works on adults.
   *
   * @param person The Synthea person to check on whether the module should be run
   * @param record The person's HealthRecord
   * @param time The current time in the simulation
   * @return True if the editor should be invoked by calling process. False otherwise.
   */
  boolean shouldRun(Person person, HealthRecord record, long time);

  /**
   * Perform the operation on the HealthRecord.Encounter(s). HealthRecordEditors do not need to
   * modify the HealthRecord.Encounters(s). HealthRecordModules SHOULD NOT modify the Person. If the
   * person must be modified, then the desired functionality should be implemented as a regular
   * Synthea module.
   * @param person The Synthea person that will have their HealthRecord edited
   * @param encounters The encounters that took place during the last time step of the simulation
   * @param time The current time in the simulation
   */
  void process(Person person, List<HealthRecord.Encounter> encounters, long time);
}
