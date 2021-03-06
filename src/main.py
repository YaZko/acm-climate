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

    parser = argparse.ArgumentParser(
        description="Carbon footprint analysis and demographic analysis provided by the acm-climate committee for conference planning."
    )
    parser.add_argument(
        "input_participants",
        help="Name of the .xml file containing the list of participants to the events. Must be located in ./input/input_participants.xml",
    )
    parser.add_argument(
        "input_events",
        help="Name of the .xml file containing the list of events to be processed. Must be located in ./input/input_events.xml",
    )
    parser.add_argument(
        "output_folder",
        help="Name of the destination folder to store the results of the analysis. Will be created in ./output/output_folder",
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Erase the content of the given output_folder if it already exists",
    )
    parser.add_argument(
        "-r",
        "--radiative",
        type=int,
        help="Set the value of the radiative forcing index. The default value used is 1.891",
    )
    parser.add_argument(
        "--no_radiative",
        action="store_true",
        help="Disable accounting for radiative forcing. This is equivalent to '--radiative 1'",
    )
    parser.add_argument(
        "-m",
        "--model",
        choices=["acm", "cool"],
        help="Changes the emission model to be used. Default value is acm",
    )
    parser.add_argument(
        "--no_id",
        action="store_true",
        help="Assert that participants to events are not uniquely identified, disabling overlap analyses",
    )
    parser.add_argument(
        "--east-west-coast",
        action="store_true",
        help="Distinguish the east and the west coast in demographic analyses",
    )
    parser.add_argument(
        "--multilocation",
        action="store_true",
        help="Estimate the carbon gain of multilocating conferences (hardcoded for SIGPLAN)",
    )
    parser.add_argument(
        "--log",
        default="info",
        choices=["info", "debug", "warning"],
        help="Set the level of logging",
    )

    args = parser.parse_args()

    GLOB = Globals(
        args.input_events,
        args.input_participants,
        args.output_folder,
        east_west=args.east_west_coast,
    )

    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
    }
    logging.basicConfig(
        filename="../output/analysis.log",
        filemode="w",
        format="%(asctime)s - %(levelname)s: %(message)s",
        level=log_levels[args.log],
    )

    logging.info(
        "Analyzing the set of participants from file {} having taken part to events from file {}. The results of the analysis will be stored in folder {}.".format(
            args.input_participants, args.input_events, args.output_folder
        )
    )

    # Checks whether the name provided for the output folder was not already taken. If not, creates the folder.
    # If taken but with the '--force' option on, erase the content of the folder.
    # Otherwise, aborts.
    exists_output = os.path.isdir(GLOB.output_prefix)
    if exists_output:
        if args.force:
            for the_file in os.listdir(GLOB.output_prefix):
                file_path = os.path.join(GLOB.output_prefix, the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(e)
        else:
            sys.exit(
                "Output folder '{}' already exists. Pick another name for the analysis or use the --force option is its content may be erased".format(
                    args.output_folder
                )
            )
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
    if args.multilocation:
        GLOB.multilocation = True

    return GLOB


def initialize(GLOB):
    cache = Cache(GLOB)
    data, confs = parser.parse(GLOB)
    db = DB(data, confs)

    return cache, db


def main():
    print("Setting up arguments\n")
    GLOB = setup_args()

    print("Initializing the cache\n")
    cache, db = initialize(GLOB)

    print("Pre-processing locations\n")
    db.preprocess(GLOB, cache)

    print("Computing footprints\n")
    db.footprint_per_conf(GLOB)

    print("Computing demographic distribution\n")
    db.analysis_demographic(GLOB)

    print("Computing temporal overlap\n")
    db.participation_overlap_intra_conf_generate_all(GLOB)
    print("Computing cross-conference overlap\n")
    db.participation_overlap_cross_conf_generate_all(GLOB)
    db.participation_overlap_general(GLOB)

    print("Computing number of participations per conference\n")
    db.get_number_of_participations(GLOB)
    print("Computing number of participations per year\n")
    db.get_number_of_participations_per_year(GLOB)

    print("Computing old timers\n")
    db.get_old_timers(GLOB)

    # print("Computing ideal location\n")
    # db.pick_optimal_loc(GLOB, cache)

    # if GLOB.multilocation:
    #     estimate_multilocation_gains(GLOB, cache, db)


def estimate_multilocation_gains(GLOB, cache, db):
    print("Computing ideal bi-location\n")
    db.pick_optimal_biloc(GLOB, cache)
    print("Computing ideal tri-location\n")
    db.pick_optimal_triloc(GLOB, cache)

    print("Computing ideal bilocations for sets of conferences\n")
    db.pick_optimal_for_set(
        GLOB,
        cache,
        2,
        GLOB.output_prefix + "biloc-ICFP-1012.csv",
        {("ICFP", y) for y in [10, 11, 12]},
        "ICFP 10-12",
    )
    db.pick_optimal_for_set(
        GLOB,
        cache,
        2,
        GLOB.output_prefix + "biloc-ICFP-1012",
        {("ICFP", y) for y in [16, 17, 18]},
        "ICFP 16-18",
    )
    db.pick_optimal_for_set(
        GLOB,
        cache,
        2,
        GLOB.output_prefix + "biloc-POPL-1517",
        {("POPL", y) for y in [15, 16, 17]},
        "POPL 15-17",
    )

    print("Computing ideal trilocations for sets of conferences\n")
    db.pick_optimal_for_set(
        GLOB,
        cache,
        3,
        GLOB.output_prefix + "triloc-ICFP-1012.csv",
        {("ICFP", y) for y in [10, 11, 12]},
        "ICFP 10-12",
    )
    db.pick_optimal_for_set(
        GLOB,
        cache,
        3,
        GLOB.output_prefix + "triloc-ICFP-1012.csv",
        {("ICFP", y) for y in [16, 17, 18]},
        "ICFP 16-18",
    )
    db.pick_optimal_for_set(
        GLOB,
        cache,
        3,
        GLOB.output_prefix + "triloc-POPL-1517.csv",
        {("POPL", y) for y in [15, 16, 17]},
        "POPL 15-17",
    )

    print("Computing ideal bi/tri-locations for the whole history of conferences\n")
    for conf in ["ICFP", "POPL", "PLDI", "SPLASH"]:
        for k, kname in [(2, "bi"), (3, "tri")]:
            db.pick_optimal_for_set(
                GLOB,
                cache,
                k,
                GLOB.output_prefix + f"{kname}loc-{conf}-history.csv",
                {(conf, y) for y in range(0, 20)},
                f"{conf} history",
            )


main()
