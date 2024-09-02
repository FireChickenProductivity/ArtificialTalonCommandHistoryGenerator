from text_parsing import create_command_history_list_from_text
from action_records import Command, BasicAction
import argparse



def create_command_history_list_from_text_file(file_path: str, spaces_per_tab=0):
    with open(file_path, 'r') as file:
        text = file.read()
    if spaces_per_tab > 0:
        text = text.replace(' ' * spaces_per_tab, '\t')
    return create_command_history_list_from_text(text)

def record_command_to_file(command: Command, file):
    file.write("Command: " + command.get_name() + '\n')
    for action in command.get_actions():
        file.write(action.to_json() + '\n')

def output_command_history_to_file(command_history, file_path):
    with open(file_path, 'w') as file:
        for command in command_history:
            record_command_to_file(command, file)

if __name__ == '__main__':
    argument_parser = argparse.ArgumentParser(description='Generates an artificial talon voice command history that could have generated the text in a text file')
    argument_parser.add_argument('input_file', type=str, help='The path for the text file to generate the artificial command history from')
    argument_parser.add_argument('output_file', type=str, help='The path for the file to output the artificial command history to')
    argument_parser.add_argument('-t', type=int, default=0, help='The number of spaces that represent a tab in the input file')
    arguments = argument_parser.parse_args()
    input_path = arguments.input_file
    output_path = arguments.output_file
    spaces_per_tab = arguments.t
    print("Starting...")
    command_history = create_command_history_list_from_text_file(input_path, spaces_per_tab)
    output_command_history_to_file(command_history, output_path)
    print("Done. Generated a history with " + str(len(command_history)) + " items.")