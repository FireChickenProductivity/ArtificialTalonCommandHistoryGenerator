from typing import Callable
from typing import List
from action_records import Command, BasicAction
from enum import Enum
import os

class PatternMatcher:
    def does_belong_to_pattern(self, current_match: str, next_character: str) -> bool:
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
        for i in range(len(words_starting_at_index) - 1, -1, -1):
            word = words_starting_at_index[i]
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
    if not word:
        raise ValueError("Word must have at least one character to compute its casing")
    if word.islower():
        return Casing.LOWER
    elif word[0].isupper() and (len(word) == 1 or word[1:].islower()):
        return Casing.CAPITALIZED
    elif word.isupper():
        return Casing.UPPER
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

MAXIMUM_NUMBER_OF_WORDS_PER_UTTERANCE = 7

class FormattedWordsPatternMatcher(PatternMatcher):
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
        if len(words) > MAXIMUM_NUMBER_OF_WORDS_PER_UTTERANCE or compute_case_format_for_words(words) in [CaseFormat.OTHER, CaseFormat.CAMEL]:
            return False
        return True

    def _do_tokens_belong_to_pattern_without_separator(self, tokens: List[str]) -> bool:
        if len(tokens) > MAXIMUM_NUMBER_OF_WORDS_PER_UTTERANCE:
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
        is_last_token_separator = self._is_token_start_of_separator(last_token)
        if not is_last_token_separator and not self._could_potentially_be_start_of_word(last_token):
            return False
        if len(tokens) == 1:
            return True 
        if len(tokens) == 2:
            return self._is_text_a_word(tokens[0])
        presumably_properly_formed_formatted_words_ending_index = len(tokens) - 1
        if not is_last_token_separator:
            if not tokens[-2] in self.SEPARATORS_TO_FORMATTER_NAME:
                return False
            presumably_properly_formed_formatted_words_ending_index -= 1
        if presumably_properly_formed_formatted_words_ending_index == 1:
            return self._is_text_a_word(tokens[0])
        return self._do_tokens_belong_to_pattern(tokens[:presumably_properly_formed_formatted_words_ending_index])

    def get_name(self) -> str:
        return "formatted words"
    
    def get_priority(self) -> int:
        return 2

class FormattedWordPatternMatcher(PatternMatcher):
    def __init__(self, word_pattern_matcher: WordPatternMatcher):
        self.word_pattern_matcher = word_pattern_matcher
    
    def _does_text_have_valid_case(self, text: str) -> bool:
        return text.isupper() or text == text.capitalize()

    def _is_current_match_word(self, current_match: str, next_character: str) -> bool:
        return self.word_pattern_matcher.does_belong_to_pattern(current_match.lower(), next_character.lower())

    def does_belong_to_pattern(self, current_match: str, next_character: str) -> bool:
        total_text = current_match + next_character
        return self._does_text_have_valid_case(total_text) and self._is_current_match_word(current_match, next_character)
    
    def could_potentially_belong_to_pattern(self, current_match: str, next_character: str, is_end_of_text: bool = False) -> bool:
        total_text = current_match + next_character
        return self._does_text_have_valid_case(total_text) and self.word_pattern_matcher.could_potentially_belong_to_pattern(current_match.lower(), next_character.lower(), is_end_of_text)

    def get_name(self) -> str:
        return "formatted word"

    def get_priority(self) -> int:
        return 1

def compute_alphabetic_characters_and_punctuation_for_prose_token(token: str):
    final_alphabetic_index = 0
    for i in range(len(token) - 1, -1, -1):
        if token[i].isalpha():
            final_alphabetic_index = i
            break
    alphabetic_characters = token[:final_alphabetic_index + 1]
    punctuation = token[final_alphabetic_index + 1:]
    return alphabetic_characters, punctuation

PUNCTUATION_MARKS_TO_NAME = {
        ".": "period",
        "?": "question mark",
        "!": "exclamation mark",
        ",": "comma",
        ";": "semicolon",
        ":": "colon",
    }

def does_word_have_valid_prose_case(word: str):
    word_case = compute_casing_of_word(word)
    return word_case in [Casing.LOWER, Casing.CAPITALIZED]

def is_every_punctuation_character_supported_by_prose_commands(punctuation_characters: str):
    for punctuation_character in punctuation_characters:
        if not punctuation_character in PUNCTUATION_MARKS_TO_NAME:
            return False
    return True

def is_valid_prose_token(token: str, is_a_word: Callable[[str], bool]):
    """Determines of a token could have come from a prose command.
        This requires that the token starts with a word and optionally
        ends with punctuation. The word must also have an appropriate formatting.
    """
    reached_the_end_of_the_alphabetic_characters = False
    alphabetic_characters, punctuation = compute_alphabetic_characters_and_punctuation_for_prose_token(token)
    return is_a_word(alphabetic_characters) and \
        is_every_punctuation_character_supported_by_prose_commands(punctuation) \
        and (does_word_have_valid_prose_case(alphabetic_characters))

def are_tokens_valid_prose_tokens(tokens: List[str], is_a_word: Callable[[str], bool]):
    for token in tokens:
        if not is_valid_prose_token(token, is_a_word):
            return False
    return True

class ProsePatternMatcher(PatternMatcher):
    def __init__(self, word_pattern_matcher: WordPatternMatcher):
        self.word_pattern_matcher = word_pattern_matcher

    def _is_text_a_word(self, text: str) -> bool:
        return self.word_pattern_matcher.does_belong_to_pattern(text.lower(), "")

    def does_belong_to_pattern(self, current_match: str, next_character: str) -> bool:
        total_text = current_match + next_character
        tokens = total_text.split(" ")
        return len(tokens) <= MAXIMUM_NUMBER_OF_WORDS_PER_UTTERANCE and len(tokens) > 1 and \
                are_tokens_valid_prose_tokens(tokens, self._is_text_a_word)

    def could_potentially_belong_to_pattern(self, current_match: str, next_character: str, is_end_of_text: bool = False) -> bool:
        if next_character == " " and current_match and not is_end_of_text and not current_match.endswith(" "):
            return self.could_potentially_belong_to_pattern(current_match[:-1], current_match[-1], is_end_of_text)
        total_text = current_match + next_character
        tokens = total_text.split(" ")
        if len(tokens) > MAXIMUM_NUMBER_OF_WORDS_PER_UTTERANCE or \
            (len(tokens) > 1 and not are_tokens_valid_prose_tokens(tokens[:-1], self._is_text_a_word)) or \
            len(tokens) == 1 and is_end_of_text:
            return False
        last_token = tokens[-1]
        alphabetic_characters, punctuation = compute_alphabetic_characters_and_punctuation_for_prose_token(last_token)
        if punctuation and not is_every_punctuation_character_supported_by_prose_commands(punctuation):
            return False
        return alphabetic_characters and \
            self.word_pattern_matcher.could_potentially_belong_to_pattern(alphabetic_characters[:-1], alphabetic_characters[-1], is_end_of_text) \
            and does_word_have_valid_prose_case(alphabetic_characters)

    def get_name(self) -> str:
        return "prose"

    def get_priority(self) -> int:
        return 3

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

def create_insert_command(name: str, text: str):
    action = BasicAction("insert", [text])
    command = Command(name, [action])
    return command

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

def create_formatted_word_pattern_matcher():
    word_pattern_matcher = create_word_pattern_matcher()
    return FormattedWordPatternMatcher(word_pattern_matcher)

def create_prose_pattern_matcher():
    word_pattern_matcher = create_word_pattern_matcher()
    return ProsePatternMatcher(word_pattern_matcher)

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

def create_formatted_words_command(total_matching_text: str):
    tokens = separate_potentially_formatted_words_into_tokens(total_matching_text, is_word=lambda x: x.lower() in WORDS)
    separator = ""
    if tokens[1] in FormattedWordsPatternMatcher.SEPARATORS_TO_FORMATTER_NAME:
        separator = tokens[1]
        tokens = tokens[::2]
    casing = compute_case_format_for_words(tokens)
    name = ""
    if casing == CaseFormat.CAMEL:
        name = "camel "
    elif casing == CaseFormat.PASCAL:
        name = "hammer "
    elif casing == CaseFormat.ALL_CAPS:
        if separator == "_":
            name = "constant "
        else:
            name = "all cap "
    elif casing == CaseFormat.ALL_LOWER:
        name = "smash "

    if separator and not name == "constant ":
        if name == "smash ":
            name = ""
        name += FormattedWordsPatternMatcher.SEPARATORS_TO_FORMATTER_NAME[separator] + " "
    name += " ".join(tokens)
    action = BasicAction('insert', [total_matching_text])
    command = Command(name.lower(), [action])
    return command

def create_formatted_word_command(total_matching_text: str):
    name = "all cap"
    if total_matching_text[-1].islower():
        name = "proud"
    command = create_insert_command(name + " " + total_matching_text.lower(), total_matching_text)
    return command

#Taken from community
WORDS_FOR_TITLE_COMMAND_TO_LEAVE_LOWERCASE = set([
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "nor", "of", "on", "or", "per", "the", "to", "v", "via", "vs",
])

def create_prose_command(total_matching_text: str):
    tokens = total_matching_text.split(" ")
    action = BasicAction('insert', [total_matching_text])
    could_be_phrase_command = True
    could_be_sentence_command = tokens[0][0].isupper()
    could_be_title_command = True
    words = []
    for token in tokens:
        alphabetic_characters, punctuation = compute_alphabetic_characters_and_punctuation_for_prose_token(token)
        current_word = alphabetic_characters.lower()
        if alphabetic_characters[0].isupper():
            could_be_phrase_command = False
        elif current_word not in WORDS_FOR_TITLE_COMMAND_TO_LEAVE_LOWERCASE:
            could_be_title_command = False
        words.append(alphabetic_characters)
        for character in punctuation:   
            punctuation_word = PUNCTUATION_MARKS_TO_NAME[character]
            words.append(punctuation_word)
            could_be_phrase_command = False
    if could_be_title_command:
        could_be_sentence_command = False
    command_name = "say"
    if could_be_phrase_command:
        command_name = "phrase"
    elif could_be_title_command:
        command_name = "title"
    elif could_be_sentence_command:
        command_name = "sentence"
    should_capitalize_words_with_cap = not could_be_title_command and not could_be_sentence_command
    for word in words:
        if should_capitalize_words_with_cap and compute_casing_of_word(word) == Casing.CAPITALIZED:
            command_name += " " + "cap"
        if could_be_sentence_command:
            should_capitalize_words_with_cap = True
        command_name += " " + word.lower()
    command = Command(command_name, [action])
    return command

    
    

NAMES_TO_ACTION_CREATION_FUNCTIONS = {
    "symbol": create_symbol_command,
    "new line": create_new_line_command,
    "word": create_word_command,
    "formatted words": create_formatted_words_command,
    "formatted word": create_formatted_word_command,
    "prose": create_prose_command,
}

def create_command_from_pattern_matcher(pattern_matcher: PatternMatcher, total_matching_text: str) -> Command:
    name = pattern_matcher.get_name()
    action_creation_function = NAMES_TO_ACTION_CREATION_FUNCTIONS[name]
    command = action_creation_function(total_matching_text)
    return command