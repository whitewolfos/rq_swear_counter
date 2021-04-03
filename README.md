# Rusty Quill Script Swear Counter

A script for parsing Rusty Quill scripts to determine the amount of profanity. The code will separate the script into the following groups, and provide results for each individual section as well as overall:

| Group Type | Description                    |
| ------------- | ------------------------------ |
| episode_info      | The text describing the episode / cast / editors       |
| content_warnings   | The text describing the content warnings |
| scenes | The text describing the current scene |
| actions | The text describing actions / non-dialogue sounds |
| CHARACTER | One field for each character. Contains all of their dialogue for the episode. |

## Known Limitations

Currently, the code only words for The Magnus Archives and Inexplicables scripts. Stella Firma scripts are in an entirely different format, so unfortunately the code cannot parse those.

In addition, the code relies on the script format shown in the more recent episodes, so may fail for older script files.

## Installation

After cloning the reposity locally, there are two ways of installing the dependencies:

##### Poetry Method
1) If you have not installed poetry before, following the instructions [here](https://python-poetry.org/docs/ "here").
2) In the git folder, run `poetry install`

##### requirements.txt Method

`pip3 install -r requirements.txt`

## Example Usage

1) Download script .docx file from [Rusty Quill's Patreon](https://www.patreon.com/rustyquill/posts "Rusty Quill's Patreon").
2) Run the script using the following command:
```
python3 swear_counter.py --script /path/to/script/docx
```
By default, the code will output the profanity results to the command line.

## Inputs

#### Required Arguments
Argument  | Description
------------- | -------------
`--script`  | Path to the script .docx file taken from Rusty Quill's Patreon

#### Parsing Settings
| Argument  | Description |
| ------------- | ------------- |
| `--parse_all`  | Parses episode information, scene, and action text in addition to dialogue |

#### Saving Parameters
| Argument | Description                    |
| ------------- | ------------------------------ |
| `--working_dir`      | Working directory for saving results; default current directory       |
| `--save_profanity_results`   | Saves .txt file containing profanity results, both overall and separated by text type (e.g. dialogue for each character, episode information, etc.) |
| `--save_parsed_dict` | Saves dictionary of parsed script data; separates text by dialogue for each character, episode information, content warnings, scene descriptions, and action/sound tags
