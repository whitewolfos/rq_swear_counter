import docx2txt
import re
from collections import Counter
from tqdm import tqdm
import os
from typing import List, Tuple, Union
from profanityfilter import ProfanityFilter

class ScriptAnalyzer():
    def __init__(self, script_filepath: str, working_dir: str):
        """
        Object for analyzing RQ scripts for profanity.
        Inputs:
            script_filepath: Filepath to the script .docx file
                             (Download from Patreon)
            working_dir: Working directory for saving information in
        """
        # Initializing variables
        self.script_filepath = script_filepath
        self.working_dir = working_dir

        # Initialize a profanity filter
        self.pf = ProfanityFilter()

        # Load in the script, split the text
        self.load_script()
        self.split_script()

    def load_script(self):
        """
        Loads in the script text data
        """
        try:
            self.raw_text = docx2txt.process(self.script_filepath)
        except Exception as err:
            raise RuntimeError("Script failed to load with the following error: ", err)

    def split_script(self):
        """
        Splits the script into an easily parseable dictionary format
        Creates:
            parsed_dict: The parsed dictionary. Has the following fields:
                episode_info -> The text describing the episode / cast / editors
                content_warnings -> The text describing the content warnings
                scenes -> The text describing the current scene
                actions -> The text describing actions / non-dialogue sounds
                CHARACTER -> One field for each character. Contains all of their
                             dialogue for the episode.
        """
        # Initialize the dictionary
        self.parsed_dict = {'episode_info': [],
                            'content_warnings': [],
                            'scenes': [],
                            'actions': []}

        # Perform rough splitting of the text
        text_chunks = self.raw_text.split("\n\n\n\n")

        # Determine which podcast this is a script of
        podcast_name = text_chunks[0].split('–')[0].rstrip()

        # Parse all other text
        last_speaker = None
        beginning_info = True
        content_warnings = False
        ending_info = False
        for i in range(len(text_chunks)):
            # Get the current chunk of text
            chunk = text_chunks[i].strip()

            # If it has reached the "X is a podcast..." stage, the episode is over
            if '%s is a podcast distributed by' % podcast_name in chunk:
                ending_info = True

            # Parse information differently if the script is not in the episode
            #   proper
            if beginning_info or content_warnings or ending_info:
                # Check to see if it has transitioned from the beginning episode
                #   information to the content warnings section
                if 'Content Warnings' in chunk:
                    beginning_info = False
                    content_warnings = True

                # Check if it has transitioned from the content warnings section
                #   to the episode itself
                if (chunk.startswith('[') and chunk.endswith(']')) or \
                    (('-' in chunk or '–' in chunk) and chunk.isupper()):
                    content_warnings = False
                else:
                    # Add information into appropriate section
                    if beginning_info or ending_info:
                        section = "episode_info"
                    elif content_warnings:
                        section = "content_warnings"
                    self.parsed_dict[section].extend(chunk.split('\n\n'))
                    continue

            # Determine if the current chunk is an action
            if chunk.startswith('[') and chunk.endswith(']'):
                for cur_action in chunk.replace('\n\n', '').split(']')[:-1]:
                    self.parsed_dict['actions'].append(cur_action + "]")
                continue

            # Determing if the current chunk is a scene description
            if ('-' in chunk or '–' in chunk) and chunk.isupper():
                self.parsed_dict['scenes'].append(chunk.replace('\n\n',''))
                continue

            # Determine who is speaking
            #   If the character name is not included, assume the last speaker
            #   is continuing to speak
            split_chunk_list = chunk.split('\n\n')
            if split_chunk_list[0].isupper():
                speaker = re.split(r"[^\w\s]", split_chunk_list[0])[0].rstrip()
                remaining_text = ' '.join(val for val in split_chunk_list[1:])
            else:
                speaker = last_speaker
                remaining_text = chunk

            # Add text to dict divided by speaker name
            if speaker not in self.parsed_dict:
                self.parsed_dict[speaker] = [remaining_text]
            else:
                self.parsed_dict[speaker].append(remaining_text)

            # Update who spoke last
            last_speaker = speaker

    def profanity_counter(self,
                          ignore_keys='default',
                          do_print_result=False,
                          do_save_result=False) -> dict:
        """
        Function for counting uses of profanity in the script
        Inputs:
            ignore_keys: Keys of parsed_dict (see split_script) to ignore. By
                         default, these are the non-dialogue sections
                         (episode_info, content_warnings, scenes, actions)
            do_print_result: Prints profanity results to the command line;
                             profane words will be bolded and underlined
            do_save_result: Saves profanity results to a .txt file;
                             words will be saved as raw text (no bold / underline)
        Outputs:
            profanity_dict: Dictionary containing data of profanity results.
                            Results are separated into the sections described in
                            parsed_dict, and contains the following information:
                                index: Index of the chunk that contains a profane
                                       word
                                profane_words: List of lists conatining profane
                                        words; the length of profane_words is how
                                        many chunks contain a profane word, the
                                        inner list are all of the instances of
                                        profane words for that particular chunk
                                profane_counter: Counter object; shows how many
                                        times each profane word appears
                            In addition, there is an "overall" key describing
                            the profane words across the entire examined script.
                            It only contains the "profane_counter" value, not
                            "index" or "profane_words".
        """
        # By default: ignore the non-dialogue text
        if ignore_keys == 'default':
            ignore_keys = ['episode_info',
                           'content_warnings',
                           'scenes',
                           'actions']

        # Make the keys to ignore a list, if not already
        if not isinstance(ignore_keys, list):
            ignore_keys = list(ignore_keys)

        # Initialize a dictionary to store profrane information
        profanity_dict = dict()
        for key in self.parsed_dict.keys():
            profanity_dict[key] = {'index': [],
                                   'profane_words': [],
                                   'profane_counter': None}

        # For all of the text in the parsed dictionary
        all_profane_words = []
        most_profane = [None, 0]
        censored_words = self.pf.get_profane_words()
        regex_string_pattern = r'\b{0}\b'
        for key, text_section in self.parsed_dict.items():
            # Ignore designated keys
            if key in ignore_keys:
                continue

            print("Analyzing %s text for profanity..." % key.replace("_"," "))

            # For each of the chunks of text
            for i in tqdm(range(len(text_section))):
                # Search through the censored words to determine if it ever
                # appears
                chunk = text_section[i]
                cur_profane_words = []
                for word in censored_words:
                    regex_string = regex_string_pattern.format(word)
                    number_of_occurrences = len(re.findall(regex_string, chunk, re.IGNORECASE))
                    cur_profane_words.extend([word] * number_of_occurrences)

                # If a profane word appeared, store the information
                if cur_profane_words:
                    profanity_dict[key]['index'].append(i)
                    profanity_dict[key]['profane_words'].append(cur_profane_words)

            # After going through all of the text for a particular section,
            #   count up the usage of all of the profane words
            if profanity_dict[key]['index']:
                section_profane_words = [item for sublist in \
                                          profanity_dict[key]['profane_words'] \
                                          for item in sublist]
                all_profane_words.extend(section_profane_words)
                profanity_dict[key]['profane_counter'] = Counter(section_profane_words)

                # Update what the most profane section was
                if most_profane[1] < len(section_profane_words):
                    most_profane = [key, len(section_profane_words)]

        # Now that all of the text has been analyzed, examine the number of
        #   profane words throughout the entire script
        profanity_dict['overall'] = Counter(all_profane_words)

        # Get strings which contain the result
        print_string, save_string = self.create_profanity_string(profanity_dict,
                                                                 all_profane_words,
                                                                 most_profane)

        # Plotting results if desired
        if do_print_result:
            print(print_string)

        # Save results if desired
        if do_save_result:
            with open(os.path.join(self.working_dir, 'results.txt'), 'w') as file:
                file.write(save_string)

        return profanity_dict

    def create_profanity_string(self,
                                profanity_dict: dict,
                                all_profane_words: List[str],
                                most_profane: List[Union[str, int]]) -> Tuple[str, str]:
        """
        Function for formatting the profanity results in an easy-to-read format
        Inputs:
            profanity_dict: Dictionary containing profanity information; see
                            profanity_counter for more details
            all_profane_words: List of all of the profane words in the script
            most_profane: A list containing information about which section was
                          the most profane
                                -> [Key name, # of profane words]
        Outputs:
            print_string: String containing the results; profane words are
                          bolded / underlined in the outputted text
            save_string: String containing the results; does not contain
                          bolded / underlined text so it can be saved in a .txt
                          file
        """
        # Expressions for bold / underline
        BOLD = '\033[1m'
        UNDERLINE = "\033[4m"
        END = '\033[0m'

        # Initializing variables
        regex_string_pattern = r'(?i)\b{0}\b'
        regex_string_pattern_case = r'\b{0}\b'
        cleaned_file = os.path.splitext(os.path.basename(self.script_filepath))[0]
        print_list = ["=====================\n" + cleaned_file]

        # If no profane words were found, then only return that nothing could be
        #   found
        if not all_profane_words:
            print_list.append('No profane words could be found in the inputted script.')
            print_string = '\n'.join([val for val in print_list])
            save_string = print_string
            return print_string, save_string

        # Get information in correct format
        cur_counter = profanity_dict['overall']
        formatted_instances = ' '.join(['%s (%i),' % (word[0], word[1]) \
                                  for word in cur_counter.most_common()])[:-1]

        # Building up the string for printing / saving
        print_list.append("=====================\n=====================")
        print_list.append("Overall Profanity Statistics")
        print_list.append("Total number of swears: %i" % sum(cur_counter.values()))
        print_list.append("Most profane (# of instances): %s (%i)" % (most_profane[0], most_profane[1]))
        print_list.append("Overall count (# of instances): " + formatted_instances)
        print_list.append("=====================")

        for key, profanity_info in profanity_dict.items():
            if not profanity_info['index']:
                continue

            # Get information in correct format
            cur_counter = profanity_info['profane_counter']
            profanity_count = sum(cur_counter.values())
            formatted_instances = ' '.join(['%s (%i),' % (word[0], word[1]) \
                                      for word in cur_counter.most_common()])[:-1]

            # Print result
            print_list.append("=====================")
            print_list.append(key)
            print_list.append("Overall count: %i" % profanity_count)
            print_list.append("Profane words (# of instances): " + formatted_instances)
            print_list.append("Occurrences in script:")
            for num, index in enumerate(profanity_info['index']):
                chunk = self.parsed_dict[key][index]
                for word in set(profanity_info['profane_words'][num]):
                    pattern_string = regex_string_pattern.format(word)
                    profane_instances = re.findall(pattern_string, chunk)
                    for instance in set(profane_instances):
                        pattern = re.compile(regex_string_pattern_case.format(instance))
                        chunk = pattern.sub(BOLD + UNDERLINE + instance + END, chunk)
                print_list.append("-- " + chunk)

        # Get the string for printing by combining all of the parts
        print_string = '\n'.join([val for val in print_list])

        # Get the string for saving (no bold / underline)
        save_string = print_string
        save_string = save_string.replace(BOLD, '')
        save_string = save_string.replace(UNDERLINE, '')
        save_string = save_string.replace(END, '')

        return print_string, save_string
