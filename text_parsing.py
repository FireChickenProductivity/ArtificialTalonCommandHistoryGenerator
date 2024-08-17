from action_records import Command
from typing import Callable, List
from patterns import PatternMatcher, create_new_line_pattern_matcher, create_symbol_pattern_matcher, create_command_from_pattern_matcher, \
    create_word_pattern_matcher, create_formatted_words_pattern_matcher, create_formatted_word_pattern_matcher

class CurrentText:
    def __init__(self):
        self.text = ""
        self.next_character = ""
        self.index = -1
        self.is_current_text_at_end_of_text = False
    
    def append_character(self, character: str):
        if self.next_character: self.text += self.next_character
        self.next_character = character
        self.index += 1
    
    def remove_last_character(self):
        self.next_character = self.text[-1]
        self.text = self.text[:-1]
        self.index -= 1

    def reset_text_information(self):
        self.text = ""
        self.next_character = ""
        
    def get_text(self):
        return self.text

    def get_next_character(self):
        return self.next_character
    
    def compute_total_text(self):
        return self.text + self.next_character
    
    def set_index(self, index):
        self.index = index

    def get_index(self):
        return self.index

    def is_at_the_end_of_the_text(self):
        return self.is_current_text_at_end_of_text

    def acknowledge_that_the_end_of_the_text_has_been_reached(self):
        self.is_current_text_at_end_of_text = True
    
    def handle_backtracking_before_end_of_text(self):
        self.is_current_text_at_end_of_text = False

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return f"CurrentText(text: {self.text}, next_character: {self.next_character})"
    
    def clone(self):
        current_text = CurrentText()
        current_text.text = self.text
        current_text.next_character = self.next_character
        current_text.index = self.index
        return current_text

class Match:
    def __init__(self, pattern: PatternMatcher, text_information: CurrentText):
        self.pattern = pattern
        self.text_information = text_information

    def get_pattern(self):
        return self.pattern

    def get_text_information(self):
        return self.text_information

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return f"Match(pattern: {self.pattern.get_name()}, text_information: {self.text_information})"
    
    def __eq__(self, other):
        return self.pattern.get_name() == other.pattern.get_name() and \
            self.text_information.get_index() == other.text_information.get_index()

class PatternManager:
    def __init__(self):
        self.patterns: List[PatternMatcher] = [
            create_new_line_pattern_matcher(),
            create_symbol_pattern_matcher(),
            create_word_pattern_matcher(),
            create_formatted_words_pattern_matcher(),
            create_formatted_word_pattern_matcher(),
        ]
        self.matching_pattern = None
        self.patterns_that_could_match_on_first_character = None
        self.last_match: Match = None
        self.reset_matching_information()
    
    def has_match(self) -> bool:
        return self.matching_pattern is not None

    def had_intermediate_match(self) -> bool:
        return self.last_match is not None
    
    def get_last_match(self) -> Match:
        return self.last_match
    
    def get_command_from_pattern(self, text_information: CurrentText) -> Command:
        pattern = self.last_match.get_pattern()
        text_information = self.last_match.get_text_information()
        command = create_command_from_pattern_matcher(pattern, text_information.compute_total_text())
        return command

    def handle_text_information(self, text_information: CurrentText):
        text = text_information.get_text()
        next_character = text_information.get_next_character()
        if not self.patterns_that_could_match_on_first_character:
            self.patterns_that_could_match_on_first_character = [pattern 
                                                                 for pattern in self.patterns 
                                                                 if pattern.could_potentially_belong_to_pattern(text, next_character)]
        for pattern in self.patterns_that_could_match_on_first_character:
            if pattern.does_belong_to_pattern(text, next_character):
                self.last_match = Match(pattern, text_information.clone())
                self.matching_pattern = pattern
                return
        self.matching_pattern = None
    
    def no_pattern_could_potentially_match(self, text_information: CurrentText):
        text = text_information.get_text()
        next_character = text_information.get_next_character()
        is_end_of_text = text_information.is_at_the_end_of_the_text()
        for pattern in self.patterns:
            if pattern.could_potentially_belong_to_pattern(text, next_character, is_end_of_text):
                return False
        return True
    
    def reset_matching_information(self):
        self.matching_pattern = None
        self.patterns_that_could_match_on_first_character = None
        self.last_match = None

    def handle_match(self):
        self.reset_matching_information()

class TextParser:
    """Generates an artificial command history that could have created all or most of the input text."""
    def __init__(self, on_command_creation: Callable[[Command], None]):
        self.on_command_creation = on_command_creation
        self.text_information = CurrentText()
        self.pattern_manager = PatternManager()
        self.index = 0

    def backtrack(self):
        last_match = self.pattern_manager.get_last_match()
        self.index = last_match.get_text_information().get_index()
        self.text_information.set_index(self.index)
        self.text_information.handle_backtracking_before_end_of_text()

    def handle_match(self):
        command = self.pattern_manager.get_command_from_pattern(self.text_information)
        self.on_command_creation(command)
        if self.pattern_manager.had_intermediate_match():
            self.backtrack()
        else:
            self.index - 1
        self.reset_text_information()
        self.pattern_manager.handle_match()
        
    def reset_text_information(self):
        self.text_information.reset_text_information()

    def generate_command_history_for_text(self, text: str):
        match_found = False
        found_match_to_process = False
        while self.index < len(text):
            self.text_information.append_character(text[self.index])
            if self.index == len(text) - 1:
                self.text_information.acknowledge_that_the_end_of_the_text_has_been_reached()
            self.pattern_manager.handle_text_information(self.text_information)
            no_pattern_could_potentially_match = self.pattern_manager.no_pattern_could_potentially_match(self.text_information)
            if self.pattern_manager.has_match():
                match_found = True
            elif match_found and no_pattern_could_potentially_match:
                found_match_to_process = True
            elif no_pattern_could_potentially_match:
                self.reset_text_information()
            if found_match_to_process:
                self.text_information.remove_last_character()
                self.pattern_manager.handle_text_information(self.text_information)
                self.handle_match()
                found_match_to_process = False
                match_found = False
            self.index += 1
        if self.pattern_manager.has_match():
            self.handle_match()
            
def create_command_history_list_from_text(text: str):
    command_history = []
    def on_command_creation(command):
        command_history.append(command)
    text_parser = TextParser(on_command_creation)
    text_parser.generate_command_history_for_text(text)
    return command_history