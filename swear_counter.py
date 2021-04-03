import pprint
import os
import argparse
import pickle
from scriptanalyzer import ScriptAnalyzer

def main(args: argparse.Namespace):
    # Ensure filepath to script is valid
    if not os.path.isfile(args.script) or not args.script.endswith(".docx"):
        raise FileNotFoundError("Inputted script must be a valid .docx file.")

    # Create working directory if it does not exist
    if not os.path.isdir(args.working_dir):
        print("Inputted working directory %s does not exist, creating..."
              % args.working_dir)
        os.mkdir(args.working_dir)

    # Split document into an easily parseable format
    script = ScriptAnalyzer(script_filepath=args.script,
                            working_dir=args.working_dir)

    # Parse script for profanity and save results
    ignore_keys = [] if args.parse_all else 'default'
    profanity_dict = script.profanity_counter(ignore_keys=ignore_keys,
                                              do_print_result=True,
                                              do_save_result=args.save_profanity_results)

    # Saving the parsed dictionary, if desired
    if args.save_parsed_dict:
        with open(os.path.join(args.working_dir, 'parsed_dict.pkl'), 'wb') as file:
            pickle.dump(script.parsed_dict, file)

if __name__ == "__main__":
    # Read in the arguments
    parser = argparse.ArgumentParser(description="Parses the inputted script for swear words")

    ##################
    # Required Arguments
    ##################
    required = parser.add_argument_group("Required Arguments")
    required.add_argument(
             "--script",
             required=True,
             type=str,
             help="Path to the desired script .docx file")

    ##################
    # Parsing Settings
    ##################
    parse_settings = parser.add_argument_group("Parsing Settings")
    parse_settings.add_argument(
                   "--parse_all",
                   action="store_true",
                   help="Parses episode information, scene, and action text in addition to dialogue"
    )

    ##################
    # Saving Parameters
    ##################
    saving = parser.add_argument_group("Saving Parameters")
    saving.add_argument(
           "--working_dir",
           type=str,
           default=os.getcwd(),
           help="Working directory for saving results; default current directory"
    )

    saving.add_argument(
        "--save_profanity_results",
        action="store_true",
        help=("Saves .txt file containing profanity results, both overall and "
              "separated by text type (e.g. dialogue for each character, episode"
              "information, etc.)")
    )

    saving.add_argument(
        "--save_parsed_dict",
        action="store_true",
        help=("Saves dictionary of parsed script data; separates text by "
              "dialogue for each character, episode information, content warnings, "
              "scene descriptions, and action/sound tags")
    )


    # Start the parsing
    args = parser.parse_args()
    main(args)
