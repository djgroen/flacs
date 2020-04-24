import flacs.flacs as flacs
import flacs.measures as measures
from readers import read_age_csv
import numpy as np
from readers import read_building_csv
from readers import read_cases_csv
from readers import read_disease_yml
import sys

from os import makedirs, path
import argparse
import csv
from pprint import pprint


if __name__ == "__main__":

    # Instantiate the parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--location', action="store", default="brent")
    parser.add_argument('--transition_scenario', action="store", default="no-measures")
    parser.add_argument('--transition_mode', action="store",
                        type=int, default='1')
    parser.add_argument('--output_dir', action="store", default=".")
    parser.add_argument('--data_dir', action="store", default="covid_data")
    parser.add_argument('--start_date', action="store", default="3/1/2020")
    parser.add_argument('-q', '--quicktest', action="store_true", help="set house_ratio to 100 to do quicker (but less accurate) runs for populous regions.")
    args = parser.parse_args()

    house_ratio = 2
    if args.quicktest is not None:
      house_ratio = 100
    location = args.location
    transition_scenario = args.transition_scenario.lower()
    transition_mode = args.transition_mode
    output_dir = args.output_dir
    data_dir = args.data_dir

    # if simsetting.csv exists -> overwrite the simulation setting parameters
    if path.isfile('simsetting.csv'):
        with open('simsetting.csv', newline='') as csvfile:
            values = csv.reader(csvfile)
            for row in values:
                if len(row) > 0:  # skip empty lines in csv
                    if row[0][0] == "#":
                        pass
                    elif row[0].lower() == "transition_scenario":
                        transition_scenario = str(row[1]).lower()
                    elif row[0].lower() == "transition_mode":
                        transition_mode = int(row[1])

    transition_day = -1
    if transition_mode == 1:
        transition_day = 62  # 30th of April
    if transition_mode == 2:
        transition_day = 77  # 15th of May
    if transition_mode == 3:
        transition_day = 93  # 31st of May
    if transition_mode > 10:
        transition_day = transition_mode

    # check the transition scenario argument
    AcceptableTransitionScenario = ['no-measures', 'extend-lockdown',
                                    'open-all', 'open-schools', 'open-shopping',
                                    'open-leisure', 'work50', 'work75',
                                    'work100', 'dynamic-lockdown']
    if transition_scenario not in AcceptableTransitionScenario:
        print("\nError !\n\tThe input transition scenario, %s , is not VALID" %
              (transition_scenario))
        print("\tThe acceptable inputs are : [%s]" %
              (",".join(AcceptableTransitionScenario)))
        sys.exit()

    # check if output_dir is exists
    if not path.exists(output_dir):
        makedirs(output_dir)
    outfile = "{}/{}-{}-{}.csv".format(output_dir,
                                       location,
                                       transition_scenario,
                                       transition_day)

    end_time = 180
    if transition_scenario == "dynamic-lockdown":
      end_time = 730

    print("Running basic Covid-19 simulation kernel.")
    print("scenario = %s" % (location))
    print("transition_scenario = %s" % (transition_scenario))
    print("transition_mode = %d" % (transition_mode))
    print("transition_day = %d" % (transition_day))
    print("end_time = %d" % (end_time))
    print("output_dir  = %s" % (output_dir))
    print("outfile  = %s" % (outfile))

    e = flacs.Ecosystem(end_time)

    e.ages = read_age_csv.read_age_csv("{}/age-distr.csv".format(data_dir), location)

    print("age distribution in system:", e.ages, file=sys.stderr)

    e.disease = read_disease_yml.read_disease_yml(
        "covid_data/disease_covid19.yml".format(data_dir))

    building_file = "{}/{}_buildings.csv".format(data_dir, location)
    read_building_csv.read_building_csv(e,
                                        building_file,
                                        "{}/building_types_map.yml".format(data_dir),
                                        house_ratio=house_ratio)
    # Can only be done after houses are in.
    read_cases_csv.read_cases_csv(e,
                                  "{}/{}_cases.csv".format(data_dir, location),
                                  start_date=args.start_date,
                                  date_format="%m/%d/%Y")

    e.time = -30
    e.print_header(outfile)
    for i in range(0, 30):
        e.evolve()
        print(e.time)
        #e.print_status(outfile)

    for t in range(0, end_time):

        if t == transition_day:
            if transition_scenario == "extend-lockdown":
                pass
            elif transition_scenario == "open-all":
                e.remove_all_measures()
            elif transition_scenario == "open-schools":
                e.remove_closure("school")
            elif transition_scenario == "open-shopping":
                e.undo_partial_closure("shopping", 0.8)
            elif transition_scenario == "open-leisure":
                e.remove_closure("leisure")
            elif transition_scenario == "work50":
                measures.work50(e)
            elif transition_scenario == "work75":
                measures.work75(e)
            elif transition_scenario == "work100":
                measures.work100(e)

        if t>22 and transition_scenario == "dynamic-lockdown" and t%7 == 0:
            measures.enact_dynamic_lockdown(e, measures.work50, flacs.num_infections_today, 100)

        # Recording of existing measures
        if transition_scenario not in ["no-measures"]:
            if t == 15:  # 16th of March
                measures.uk_lockdown(e, phase=1)
            if t == 22:  # 23rd of March
                measures.uk_lockdown(e, phase=2)

        # Propagate the model by one time step.
        e.evolve()

        print(t)
        e.print_status(outfile)

    print("Simulation complete.", file=sys.stderr)