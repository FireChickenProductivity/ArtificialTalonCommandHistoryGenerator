from action_records import Command
from typing import Callable, List
from patterns import PatternMatcher, create_new_line_pattern_matcher, create_symbol_pattern_matcher, create_command_from_pattern_matcher

class PatternManager:
    def __init__(self):
        self.patterns: List[PatternMatcher] = [
            create_new_line_pattern_matcher(),
            create_symbol_pattern_matcher()
        ]
        self.matching_pattern = None
    
    def has_match(self) -> bool:
        return self.matching_pattern is not None
    
    def get_command_from_pattern(self, text: str) -> Command:
        return create_command_from_pattern_matcher(self.matching_pattern, text)

    def handle_text_and_next_character(self, text: str, next_character: str):
        for pattern in self.patterns:
            if pattern.does_belong_to_pattern(text, next_character):
                self.matching_pattern = pattern
                return
        self.matching_pattern = None
    
    def no_pattern_could_potentially_match(self, text: str, next_character: str):
        for pattern in self.patterns:
            if pattern.could_potentially_belong_to_pattern(text, next_character):
                return False
        return True

class TextParser:
    """Generates an artificial command history that could have created all or most of the input text."""
    def __init__(self, on_command_creation: Callable[[Command], None]):
        self.on_command_creation = on_command_creation
        self.next_character = ""
        self.current_text = ""
        self.pattern_manager = PatternManager()

    def handle_match(self):
        command = self.pattern_manager.get_command_from_pattern(self.current_text)
        self.on_command_creation(command)
        self.current_text = ""
        
    def reset_text_information(self):
        self.next_character = ""
        self.current_text = ""

    def generate_command_history_for_text(self, text: str):
        for character in text:
            self.next_character = character
            self.pattern_manager.handle_text_and_next_character(self.current_text, self.next_character)
            self.current_text += self.next_character
            if self.pattern_manager.has_match():
                self.handle_match()
            elif self.pattern_manager.no_pattern_could_potentially_match(self.current_text, self.next_character):
                self.reset_text_information()
                print('Could not find a match for: ', self.current_text, ' with next character ', self.next_character)
            

def create_command_history_list_from_text(text: str):
    command_history = []
    def on_command_creation(command):
        command_history.append(command)
    text_parser = TextParser(on_command_creation)
    text_parser.generate_command_history_for_text(text)
    return command_history