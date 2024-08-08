from action_records import Command
from typing import Callable, List
from patterns import PatternMatcher, create_new_line_pattern_matcher, create_symbol_pattern_matcher, create_command_from_pattern_matcher

class CurrentText:
    def __init__(self):
        self.text = ""
        self.next_character = ""
        self.index = -1 #this becomes zero when the first character is added
    
    def append_character(self, character: str):
        if self.next_character: self.text += self.next_character
        self.next_character = character
        self.index += 1
    
    def reset_text_information(self):
        self.text = ""
        self.next_character = ""
        
    def set_index_for_backtracking(self, starting_index: int):
        self.index = starting_index - 1
    
    def get_text(self):
        return self.text

    def get_next_character(self):
        return self.next_character
    
    def compute_total_text(self):
        return self.text + self.next_character
    
    def get_index(self):
        return self.index
    
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return f"CurrentText(text: {self.text}, next_character: {self.next_character}, index: {self.index})"

class PatternManager:
    def __init__(self):
        self.patterns: List[PatternMatcher] = [
            create_new_line_pattern_matcher(),
            create_symbol_pattern_matcher()
        ]
        self.matching_pattern = None
        self.patterns_to_consider = self.patterns
        self.ruled_out_patterns = []
    
    def has_match(self) -> bool:
        return self.matching_pattern is not None
    
    def get_command_from_pattern(self, text_information: CurrentText) -> Command:
        return create_command_from_pattern_matcher(self.matching_pattern, text_information.compute_total_text())

    def handle_text_information(self, text_information: CurrentText):
        text = text_information.get_text()
        next_character = text_information.get_next_character()
        for pattern in self.patterns:
            if pattern.does_belong_to_pattern(text, next_character):
                self.matching_pattern = pattern
                return
        self.matching_pattern = None
    
    def no_pattern_could_potentially_match(self, text_information: CurrentText):
        text = text_information.get_text()
        next_character = text_information.get_next_character()
        for pattern in self.patterns:
            if pattern.could_potentially_belong_to_pattern(text, next_character):
                return False
        return True
    
    def handle_match(self):
        self.matching_pattern = None
        self.patterns_to_consider = self.patterns
        self.ruled_out_patterns = []



class TextParser:
    """Generates an artificial command history that could have created all or most of the input text."""
    def __init__(self, on_command_creation: Callable[[Command], None]):
        self.on_command_creation = on_command_creation
        self.text_information = CurrentText()
        self.pattern_manager = PatternManager()

    def handle_match(self):
        command = self.pattern_manager.get_command_from_pattern(self.text_information)
        self.on_command_creation(command)
        self.reset_text_information()
        self.pattern_manager.handle_match()
        
    def reset_text_information(self):
        self.text_information.reset_text_information()

    def generate_command_history_for_text(self, text: str):
        for index, character in enumerate(text):
            self.text_information.append_character(character)
            self.pattern_manager.handle_text_information(self.text_information)
            if self.pattern_manager.has_match():
                self.handle_match()
            elif self.pattern_manager.no_pattern_could_potentially_match(self.text_information, self.next_character):
                self.reset_text_information()
                print('Could not find a match for: ', self.text_information)
            

def create_command_history_list_from_text(text: str):
    command_history = []
    def on_command_creation(command):
        command_history.append(command)
    text_parser = TextParser(on_command_creation)
    text_parser.generate_command_history_for_text(text)
    return command_history