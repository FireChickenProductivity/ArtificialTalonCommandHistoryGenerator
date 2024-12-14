# Credit for Word List
The project's understanding of what counts is a word is largely based on

https://github.com/lorenbrichter/Words/

# Purpose
This generates an approximate artificial talon voice command history that could have produced all or most of the text in the target file. This history could then be fed to any analysis programs working with my basic action record format, such as this: https://github.com/FireChickenProductivity/BasicActionRecordAnalyzer. Obvious applications would be artificial command generation based on a history, action prediction systems, and estimating how difficult a task would be by voice without a proper voice command set.

# Usage
python main.py input_filepath, output_filepath (optional argument for converting spaces to tabs: -t number_of_spaces) (optional argument for ignoring leading spaces on every line: -i)