from typing import Callable
from action_records import Command, BasicAction
import os

class PatternMatcher:
    def does_belong_to_pattern(current_match: str, next_character: str) -> bool:
        pass

    def could_potentially_belong_to_pattern(current_match: str, next_character: str) -> bool:
        pass

    def get_name(self) -> str:
        pass

class SingleCharacterPatternMatcher(PatternMatcher):
    def __init__(self, is_valid_character: Callable[[str], bool], name: str):
        self.is_valid_character = is_valid_character
        self.name = name

    def does_belong_to_pattern(self, current_match: str, next_character: str) -> bool:
        return len(current_match) == 0 and self.is_valid_character(next_character)
    
    def could_potentially_belong_to_pattern(self, current_match: str, next_character: str) -> bool:
        return self.does_belong_to_pattern(current_match, next_character)
    
    def get_name(self) -> str:
        return self.name

class WordPatternMatcher(PatternMatcher):
    def __init__(self, word_set, maximum_word_length):
        self.word_set = word_set
        self.maximum_word_length = maximum_word_length

    def does_belong_to_pattern(self, current_match: str, next_character: str) -> bool:
        total_match = current_match + next_character
        return total_match in self.word_set
    
    def could_potentially_belong_to_pattern(self, current_match: str, next_character: str) -> bool:
        if self.maximum_word_length < len(current_match) + 1:
            return False
        total_match = current_match + next_character
        for character in total_match:
            if not (character.isalpha() or character == "'"):
                return False
        return True
    
    def get_name(self) -> str:
        return "word"

def load_words_from_text():
    current_directory = os.path.dirname(__file__)
    resources_directory = os.path.join(current_directory, 'resources')
    words_file_path = os.path.join(resources_directory, 'words.txt')
    with open(words_file_path, 'r') as words_file:
        words = words_file.read().splitlines()
    words = set(words)
    return words

def compute_maximum_text_length_from_set(input_set):
    max_length = 0
    for word in input_set:
        max_length = max(max_length, len(word))
    return max_length

WORDS = load_words_from_text()
MAXIMUM_WORD_LENGTH = compute_maximum_text_length_from_set(WORDS)

#Based largely on talon's community repository
SYMBOLS_TO_SPOKEN_FORM = {
    ".": "dot",
    "'": "quote",
    "?": "question",
    "[": "square",
    "]": "right square",
    "/": "slash",
    "\\": "backslash",
    "-": "dash",
    "=": "equals",
    "+": "plus",
    "`": "grave",
    "~": "tilde",
    "!": "bang",
    "_": "underscore",
    "(": "paren",
    "{": "brace",
    "}": "right brace",
    "<": "angle",
    ">": "rangle",
    "*": "star",
    "#": "hash",
    "%": "percent",
    "^": "caret",
    "&": "amper",
    "|": "pipe",
    '"': "double",
    "$": "dollar",
    "£": "pound",
    "@": "at",
    ":": "colon",
    ";": "semicolon",
    ",": "comma",
    "a": "air",
    "b": "bat",
    "c": "cap",
    "d": "drum",
    "e": "each",
    "f": "fine",
    "g": "gust",
    "h": "harp",
    "i": "sit",
    "j": "jury",
    "k": "crunch",
    "l": "look",
    "m": "made",
    "n": "near",
    "o": "odd",
    "p": "pit",
    "q": "quench",
    "r": "red",
    "s": "sun",
    "t": "trap",
    "u": "urge",
    "v": "vest",
    "w": "whale",
    "x": "plex",
    "y": "yank",
    "z": "zip",
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
    "A": "arch",
    "B": "barn",
    "C": "cow",
    "D": "dime",
    "E": "earth",
    "F": "faint",
    "G": "gnome",
    "H": "ham",
    "I": "knight",
    "J": "Jane",
    "K": "keen",
    "L": "lime",
    "M": "moon",
    "N": "nice",
    "O": "old",
    "P": "peach",
    "Q": "quip",
    "R": "rhyme",
    "S": "sand",
    "T": "treat",
    "U": "um",
    "V": "veil",
    "W": "whip",
    "X": "sphinx",
    "Y": "year",
    "Z": "cheese",
    " ": "space",
}

def create_symbol_pattern_matcher():
    def is_valid_character(character: str) -> bool:
        return character in SYMBOLS_TO_SPOKEN_FORM

    return SingleCharacterPatternMatcher(is_valid_character, "symbol")

def create_new_line_pattern_matcher():
    def is_valid_character(character: str) -> bool:
        return character == '\n'

    return SingleCharacterPatternMatcher(is_valid_character, "new line")

def create_word_pattern_matcher():
    return WordPatternMatcher(WORDS, MAXIMUM_WORD_LENGTH)

def create_symbol_command(symbol: str):
    action = BasicAction('insert', [symbol])
    command = Command(SYMBOLS_TO_SPOKEN_FORM[symbol], [action])
    return command

def create_new_line_command(total_matching_text: str):
    action = BasicAction('insert', ['\n'])
    command = Command("enter", [action])
    return command

def create_word_command(total_matching_text: str):
    action = BasicAction('insert', [total_matching_text])
    command_name = "word " + total_matching_text
    command = Command(command_name, [action])
    return command

NAMES_TO_ACTION_CREATION_FUNCTIONS = {
    "symbol": create_symbol_command,
    "new line": create_new_line_command,
    "word": create_word_command
}

def create_command_from_pattern_matcher(pattern_matcher: PatternMatcher, total_matching_text: str) -> Command:
    name = pattern_matcher.get_name()
    action_creation_function = NAMES_TO_ACTION_CREATION_FUNCTIONS[name]
    command = action_creation_function(total_matching_text)
    return command