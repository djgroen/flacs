import sys

def full_lockdown(e):
  e.remove_all_measures()
  e.add_closure("school", 0)
  e.add_closure("leisure", 0)
  e.add_partial_closure("shopping", 0.8)
  # mimicking a 75% reduction in social contacts.
  e.add_social_distance_imp9()
  e.add_work_from_home()
  e.add_case_isolation()
  e.add_household_isolation()

def uk_lockdown(e, phase=1, transition_fraction=1.0, keyworker_fraction=0.18):
  e.remove_all_measures()
  transition_fraction = max(0.0, min(1.0, transition_fraction))
  keyworker_fraction = max(0.0, min(1.0, keyworker_fraction))

  if phase == 1: # Enacted March 16th
    e.add_partial_closure("leisure", 0.5)
    e.add_social_distance(compliance=transition_fraction*0.75, mask_uptake=transition_fraction*0.05)
    # light work from home instruction, with ascending compliance to 60%.
    e.add_work_from_home(0.65*transition_fraction)
  if phase == 2: # Enacted March 23rd
    e.add_partial_closure("school", 1.0 - keyworker_fraction)
    e.add_closure("leisure", 0)
    e.add_partial_closure("shopping", 0.6 + (transition_fraction * 0.2))
    e.add_social_distance(compliance=0.65 + (transition_fraction * 0.1), mask_uptake=0.05)
    e.add_work_from_home(0.9 - keyworker_fraction + (transition_fraction * 0.1)) # www.ifs.org.uk/publications/14763 (18% are key worker in London)
  if phase == 3: # Enacted April 22nd
    e.add_partial_closure("school", 1.0 - keyworker_fraction)
    e.add_closure("leisure", 0)
    e.add_partial_closure("shopping", 0.8)
    e.add_social_distance(compliance=0.8, mask_uptake=0.15)
    e.add_work_from_home(1.0 - keyworker_fraction) # www.ifs.org.uk/publications/14763 (18% are key worker in London)
  if phase == 4: # Enacted May 13th
    e.add_partial_closure("school", 1.0 - keyworker_fraction)
    e.add_closure("leisure", 0)
    e.add_partial_closure("shopping", 0.6)
    e.add_social_distance(compliance=0.8, mask_uptake=0.2)
    e.add_work_from_home(0.7)
    e.ci_multiplier *= 0.7 # Assumption: additional directives for those with anosmia to stay home improves compliance by 30%.

  # mimicking a 75% reduction in social contacts.
  #e.add_social_distance_imp9()

  e.add_case_isolation()
  e.add_household_isolation()


def update_hospital_protection_factor_uk(e, t):
  if t == 10:
    e.hospital_protection_factor = 0.4
  if t == 20:
    e.hospital_protection_factor = 0.37
  if t == 30: # start of testing ramp up in early april.
    e.hospital_protection_factor = 0.34
  if t == 40:
    e.hospital_protection_factor = 0.29
  if t == 50:
    e.hospital_protection_factor = 0.23
  if t == 60: # testing ramped up considerably by the end of April.
    e.hospital_protection_factor = 0.16
  if t == 80:
    e.hospital_protection_factor = 0.12
  if t == 100:
    e.hospital_protection_factor = 0.10
  if t == 120:
    e.hospital_protection_factor = 0.08

    


def work50(e):
  e.remove_all_measures()
  e.add_closure("school", 0)
  e.add_closure("leisure", 0)
  e.add_partial_closure("shopping", 0.4)
  # mimicking a 75% reduction in social contacts.
  e.add_social_distance_imp9()
  # light work from home instruction, with 50% compliance
  e.add_work_from_home(0.5)
  e.add_case_isolation()
  e.add_household_isolation()


def work75(e):
  e.remove_all_measures()
  e.add_partial_closure("leisure", 0.5)
  # mimicking a 75% reduction in social contacts.
  e.add_social_distance_imp9()
  # light work from home instruction, with 25% compliance
  e.add_work_from_home(0.25)
  e.add_case_isolation()
  e.add_household_isolation()

def work100(e):
  e.remove_all_measures()
  # mimicking a 75% reduction in social contacts.
  e.add_social_distance_imp9()
  e.add_case_isolation()
  e.add_household_isolation()

_dyn_lock_full = True # we assume this mechanism starts in lockdown mode.
def enact_dynamic_lockdown(e, light_lockdown_func, kpi_value, threshold):
  """
  Dynamic lockdown based on threshold KPI assessment.
  """
  global _dyn_lock_full
  if kpi_value > threshold:
    if not _dyn_lock_full:
      print("DYNAMIC: Full lockdown", file=sys.stderr)
      full_lockdown(e)
      _dyn_lock_full = True
  else:
    if _dyn_lock_full:
      print("DYNAMIC: Light lockdown", file=sys.stderr)
      light_lockdown_func(e)
      _dyn_lock_full = False


def enact_periodic_lockdown(e, light_lockdown_func):
  """
  Dynamic lockdown based on static time intervals.
  """
  global _dyn_lock_full
  if not _dyn_lock_full:
    print("PERIODIC: Full lockdown", file=sys.stderr)
    full_lockdown(e)
    _dyn_lock_full = True
  else:
    print("PERIODIC: Light lockdown", file=sys.stderr)
    light_lockdown_func(e)
    _dyn_lock_full = False
