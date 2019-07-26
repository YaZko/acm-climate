import parser
from caching import Cache
from data_processing import DB
from parameters import Globals
from datastructure import *

import argparse
import logging
import sys
import os

# Builds the global parameters that will be manipulated (read only after this function returns) by all parts of the analysis.
# They are wrapped in an object 'GLOB' to simplify passing them around.
def setup_args():

    parser = argparse.ArgumentParser(description='Carbon footprint analysis and demographic analysis provided by the acm-climate committee for conference planning.')
    parser.add_argument('input_participants', help='Name of the .xml file containing the list of participants to the events. Must be located in ./input/input_participants.xml')
    parser.add_argument('input_events',       help='Name of the .xml file containing the list of events to be processed. Must be located in ./input/input_events.xml')
    parser.add_argument('output_folder',      help='Name of the destination folder to store the results of the analysis. Will be created in ./output/output_folder')

    parser.add_argument('-f','--force', action='store_true', help='Erase the content of the given output_folder if it already exists')
    parser.add_argument('-r','--radiative', type=int, help='Set the value of the radiative forcing index. The default value used is 1.891')
    parser.add_argument('--no_radiative', action='store_true', help='Disable accounting for radiative forcing. This is equivalent to \'--radiative 1\'')
    parser.add_argument('-m','--model', choices=['acm','cool'], help='Changes the emission model to be used. Default value is acm')
    parser.add_argument('--no_id', action='store_true', help='Assert that participants to events are not uniquely identified, disabling overlap analyses')

    args = parser.parse_args()

    GLOB = Globals(args.input_events,args.input_participants,args.output_folder)

    logging.info("Analyzing the set of participants from file {} having taken part to events from file {}. The results of the analysis will be stored in folder {}.".format(args.input_participants, args.input_events,args.output_folder))

    # Checks whether the name provided for the output folder was not already taken. If not, creates the folder.
    # If taken but with the '--force' option on, erase the content of the folder.
    # Otherwise, aborts.
    exists_output = os.path.isdir(GLOB.output_prefix)
    if exists_output:
        if args.force:
            for the_file in os.listdir(GLOB.output_prefix):
                file_path = os.path.join(GLOB.output_prefix,the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(e)
        else:
            sys.exit("Output folder '{}' already exists. Pick another name for the analysis or use the --force option is its content may be erased".format(args.output_folder))
    else:
        os.mkdir(GLOB.output_prefix)

    if not args.radiative is None:
        logging.info("Radiative factor index modified to {}.".format(args.radiative))
        GLOB.radiative_factor_index = args.radiative
    if args.no_radiative:
        logging.info("Radiative factor index set to 1.")
        GLOB.radiative_factor_index = 1
    if args.model:
        logging.info("Model {} selected".format(args.model))
        GLOB.model = args.model
    if args.no_id:
        logging.info("Disabling cross-participation analyses")
        GLOB.unique_id = False

    return GLOB

def initialize(GLOB):

    # TODO: Backup the logger and clean it up when starting a new session
    logging.basicConfig(filename='../output/analysis.log',level=logging.DEBUG)

    cache = Cache(GLOB)
    data,confs = parser.parse(GLOB)
    db = DB(data,confs)

    return cache,db

def analysis():

    GLOB = setup_args()

    cache,db = initialize(GLOB)

    db.preprocess(GLOB,cache)

    # db.analysis_demographic(GLOB)


# initialize_user_db(raw_users_path, raw_user_types, users_path, raw_user_types,
#                    raw_confs_path, confs_path, conf_names, raw_conf_types)

# db = DB(data,confs)
# db.preprocess(users_path,confs_path)
# db.analysis_demographic(output_demographic)

# db.get_number_of_participations(output_number_of_participations,conf_names)
# db.get_old_timers(output_old_timer,conf_names,conf_years)
# db.pick_optimals(output_optimals,conf_names,conf_years,city_candidates)

# print(db.speculate_cost_at_loc("POPL",18,Location("Anchorage","AK","USA")))
# print(db.speculate_cost_at_loc("POPL",18,Location("Los Angeles","CA","USA")))

# db.participation_overlap_conf_generate_all(output_overlap_cross_conf,conf_names,conf_years)
# db.participation_overlap_year_generate_all(output_overlap_cross_year,conf_names,conf_years)

# db.participation_overlap_conf("POPL", )

# dest = Location("Paris",None,"France")
# for i in range(9,19):
#     db.speculate_cost_at_loc("POPL",i,dest)
#     db.speculate_cost_split("POPL",i,dest)

# db.analysis(output_path)



############# BEGIN DEPRECATED ############

# Check if the chosen target files for the databases exists.
# If not, parses the raw source and output them with the right format in the target files.
def initialize_user_db(raw_users_path, raw_user_types, users_path, user_types,
                       raw_confs_path, confs_path, conf_names, raw_conf_types):
    print("Checking for existing db")
    exists_db_users = os.path.isfile(users_path)
    exists_db_confs = os.path.isfile(confs_path)
    if not exists_db_users or not exists_db_confs:
        print("Found no db, initializing")
        users,confs = parser.parse(raw_users_path, raw_user_types,
                                   raw_confs_path, conf_names, raw_conf_types)
        db = DB(users,confs)
        if not exists_db_users:
            print('Initialized the user database.')
            db.print_user_db(users_path)
        if not exists_db_confs:
            print('Initialized the conference database.')
            db.print_conf_db(confs_path)
    else:
        print("Found existing db, skipping initialization")

############# END DEPRECATED ############
