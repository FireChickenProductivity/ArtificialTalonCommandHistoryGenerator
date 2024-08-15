from typing import Callable
from typing import List
from action_records import Command, BasicAction
from enum import Enum
import os

class PatternMatcher:
    def does_belong_to_pattern(current_match: str, next_character: str) -> bool:
        pass

    def could_potentially_belong_to_pattern(self, current_match: str, next_character: str, is_end_of_text: bool = False) -> bool:
        pass

    def get_name(self) -> str:
        pass

    def get_priority(self) -> int:
        return 0

class SingleCharacterPatternMatcher(PatternMatcher):
    def __init__(self, is_valid_character: Callable[[str], bool], name: str):
        self.is_valid_character = is_valid_character
        self.name = name

    def does_belong_to_pattern(self, current_match: str, next_character: str) -> bool:
        return len(current_match) == 0 and self.is_valid_character(next_character)
    
    def could_potentially_belong_to_pattern(self, current_match: str, next_character: str, is_end_of_text: bool = False) -> bool:
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
    
    def could_potentially_belong_to_pattern(self, current_match: str, next_character: str, is_end_of_text: bool = False) -> bool:
        if self.maximum_word_length < len(current_match) + 1:
            return False
        if is_end_of_text:
            return self.does_belong_to_pattern(current_match, next_character)
        total_match = current_match + next_character
        for character in total_match:
            if not (character.isalpha() or character == "'"):
                return False
        return True
    
    def get_name(self) -> str:
        return "word"

    def get_priority(self) -> int:
        return 1

def separate_words_smashed_together(words: str, is_word, current_word_start: int = 0) -> List[str]:
    words_starting_at_index = []
    current_word = ""
    for i in range(current_word_start, len(words)):
        current_word += words[i]
        if is_word(current_word):
            words_starting_at_index.append(current_word[:])
    if words_starting_at_index:
        for word in words_starting_at_index:
            ending_index = current_word_start + len(word)
            if ending_index == len(words):
                return [word]
            else:
                remaining_words = separate_words_smashed_together(words, is_word, ending_index)
                if remaining_words:
                    return [word] + remaining_words
                else:
                    continue
        return None
    else:
        return None


class InvalidFormattedWordsTextException(Exception): pass


def separate_potentially_formatted_words_into_tokens(text: str, is_word) -> List[str]:
    tokens = []
    current_token = ""
    is_alphabetic_token = False
    for character in text:
        if not current_token:
            is_alphabetic_token = character.isalpha()
        is_alphabetic_character = character.isalpha()
        if is_alphabetic_token == is_alphabetic_character:
            current_token += character
        else:
            tokens.append(current_token)
            current_token = character
            is_alphabetic_token = is_alphabetic_character
    tokens.append(current_token)
    if len(tokens) == 1 and not is_word(tokens[0]):
        tokens = separate_words_smashed_together(text, is_word)
        if not tokens:
            raise InvalidFormattedWordsTextException
    return tokens

def is_odd_length_list(input_list: List[str]) -> bool:
    return len(input_list) % 2 == 1

class Casing(Enum):
    LOWER = 1
    UPPER = 2
    CAPITALIZED = 3
    OTHER = 4

def compute_casing_of_word(word: str) -> Casing:
    if word.islower():
        return Casing.LOWER
    elif word.isupper():
        return Casing.UPPER
    elif word[0].isupper() and word[1:].islower():
        return Casing.CAPITALIZED
    else:
        return Casing.OTHER

class CaseFormat(Enum):
    CAMEL = 1
    PASCAL = 2
    ALL_CAPS = 3
    ALL_LOWER = 4
    OTHER = 5

def compute_case_format_for_words(words: List[str]) -> CaseFormat:
    current_guess = None
    first_casing = compute_casing_of_word(words[0])
    previous_casing = first_casing
    for word in words[1:]:
        current_casing = compute_casing_of_word(word)
        if current_casing == Casing.OTHER:
            return CaseFormat.OTHER
        elif current_casing == Casing.CAPITALIZED:
            if first_casing == Casing.LOWER:
                current_guess = CaseFormat.CAMEL
            elif current_guess == None:
                current_guess = CaseFormat.PASCAL
        elif current_casing == Casing.UPPER:
            current_guess = CaseFormat.ALL_CAPS
        elif current_casing == Casing.LOWER:
            current_guess = CaseFormat.ALL_LOWER
        if current_casing != previous_casing and not (current_casing == Casing.CAPITALIZED and previous_casing == Casing.LOWER and current_guess == CaseFormat.CAMEL):
            return CaseFormat.OTHER
        previous_casing = current_casing
    return current_guess

class FormattedWordsPatternMatcher(PatternMatcher):
    MAXIMUM_NUMBER_OF_WORDS_PER_UTTERANCE = 7
    SEPARATORS_TO_FORMATTER_NAME = {
        "-": 'kabab',
        "_": 'snake',
        ".": 'dotted',
        "/": 'conga',
        "::": 'packed',
        "__": 'dunder',
    }
    """Detects a series of formatted words"""
    def __init__(self, word_pattern_matcher: WordPatternMatcher):
        self.word_pattern_matcher = word_pattern_matcher
    
    def _is_text_a_word(self, text: str) -> bool:
        return self.word_pattern_matcher.does_belong_to_pattern(text.lower(), "")

    def _do_tokens_belong_to_pattern_with_separator(self, tokens: List[str], separator: str) -> bool:
        expecting_word = True
        words = []
        for token in tokens:
            if expecting_word and not self._is_text_a_word(token):
                return False
            if not expecting_word:
                if token not in self.SEPARATORS_TO_FORMATTER_NAME:
                    return False
                else:
                    if token != separator:
                        return False
            if expecting_word:
                words.append(token)
            expecting_word = not expecting_word
        if len(words) > self.MAXIMUM_NUMBER_OF_WORDS_PER_UTTERANCE or compute_case_format_for_words(words) in [CaseFormat.OTHER, CaseFormat.CAMEL]:
            return False
        return True

    def _do_tokens_belong_to_pattern_without_separator(self, tokens: List[str]) -> bool:
        if len(tokens) > self.MAXIMUM_NUMBER_OF_WORDS_PER_UTTERANCE:
            return False
        case_formatting = compute_case_format_for_words(tokens)
        if case_formatting == CaseFormat.OTHER:
            return False
        for token in tokens:
            if not self._is_text_a_word(token):
                return False
        return True

    def _do_tokens_belong_to_pattern(self, tokens: List[str]) -> bool:
        if len(tokens) < 2:
            return False
        separator = ""
        if is_odd_length_list(tokens) and not self._is_text_a_word(tokens[1]):
            separator = tokens[1]
            return self._do_tokens_belong_to_pattern_with_separator(tokens, separator)
        else:
            return self._do_tokens_belong_to_pattern_without_separator(tokens)

    def does_belong_to_pattern(self, current_match: str, next_character: str) -> bool:
        try:
            tokens = separate_potentially_formatted_words_into_tokens(current_match + next_character, self._is_text_a_word)
        except InvalidFormattedWordsTextException:
            return False
        return self._do_tokens_belong_to_pattern(tokens)

    def _is_token_start_of_separator(self, token: str) -> bool:
        for separator in self.SEPARATORS_TO_FORMATTER_NAME:
            if separator.startswith(token):
                return True
        return False

    def _could_final_token_potentially_belong_to_pattern(self, last_token: str) -> bool:
        return self._is_token_start_of_separator(last_token) or self.word_pattern_matcher.could_potentially_belong_to_pattern(last_token[:-1], last_token[-1])

    def _could_potentially_be_start_of_word(self, text: str) -> bool:
        return self.word_pattern_matcher.could_potentially_belong_to_pattern(text[:-1], text[-1])

    def could_potentially_belong_to_pattern(self, current_match: str, next_character: str, is_end_of_text: bool = False) -> bool:
        total_text = current_match + next_character
        if is_end_of_text:
            return self.does_belong_to_pattern(current_match, next_character)
        try:
            tokens = separate_potentially_formatted_words_into_tokens(total_text, self._is_text_a_word)
        except InvalidFormattedWordsTextException:
            #This branch is usually reached by a single series of alphabetic characters with no separator
            return self._could_potentially_be_start_of_word(total_text)
        last_token = tokens[-1]
        if not self._is_token_start_of_separator(last_token) and not self._could_potentially_be_start_of_word(last_token):
            return False
        if len(tokens) == 1:
            return True 
        if len(tokens) == 2:
            return self._is_text_a_word(tokens[0])
        return self._do_tokens_belong_to_pattern(tokens[:-1])

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

def create_formatted_words_pattern_matcher():
    word_pattern_matcher = create_word_pattern_matcher()
    return FormattedWordsPatternMatcher(word_pattern_matcher)

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