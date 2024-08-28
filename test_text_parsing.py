from patterns import SYMBOLS_TO_SPOKEN_FORM, create_new_line_pattern_matcher, create_symbol_pattern_matcher, create_command_from_pattern_matcher, \
    create_word_pattern_matcher, create_formatted_words_pattern_matcher, create_formatted_word_pattern_matcher, create_prose_pattern_matcher, \
    is_valid_prose_token
from text_parsing import create_command_history_list_from_text
from action_records import Command, BasicAction
import unittest

def assert_insert_command_matches_text(assertion_class, command, text):
    assertion_class.assertEqual(len(command.get_actions()), 1)
    action = command.get_actions()[0]
    assertion_class.assertEqual(action.get_name(), 'insert')
    assertion_class.assertEqual(len(action.get_arguments()), 1)
    argument_text = action.get_arguments()[0]
    assertion_class.assertEqual(argument_text, text)

def assert_command_has_correct_name(assertion_class, command, expected_name):
    assertion_class.assertEqual(command.get_name(), expected_name)

def assert_commands_match(assertion_class, actual: Command, expected: Command):
    assertion_class.assertEqual(actual.get_name(), expected.get_name())
    assertion_class.assertEqual(len(actual.get_actions()), len(expected.get_actions()))
    for actual_action, expected_action in zip(actual.get_actions(), expected.get_actions()):
        assertion_class.assertEqual(actual_action, expected_action)

def assert_command_histories_match(assertion_class, actual, expected):
    assertion_class.assertEqual(len(actual), len(expected), f"actual: {actual}, expected: {expected}")
    for actual_command, expected_command in zip(actual, expected):
        assert_commands_match(assertion_class, actual_command, expected_command)

def assert_command_history_matches_that_for_text(assertion_class, expected_history, text):
    actual_history = create_command_history_list_from_text(text)
    assert_command_histories_match(assertion_class, actual_history, expected_history)

def assert_pattern_matcher_match_outcome_is_expected(assertion_class, pattern_matcher, text, expected_outcome):
    actual_outcome = pattern_matcher.does_belong_to_pattern(text[:-1], text[-1])
    assertion_class.assertEqual(actual_outcome, expected_outcome)
    if expected_outcome:
        assertion_class.assertTrue(pattern_matcher.could_potentially_belong_to_pattern(text[:-1], text[-1]))

def assert_pattern_matcher_matches_text(assertion_class, pattern_matcher, text):
    assert_pattern_matcher_match_outcome_is_expected(assertion_class, pattern_matcher, text, True)

def assert_pattern_matcher_does_not_match_text(assertion_class, pattern_matcher, text):
    assert_pattern_matcher_match_outcome_is_expected(assertion_class, pattern_matcher, text, False)

def assert_pattern_matcher_potential_match_outcome_matches_expected(assertion_class, pattern_matcher, text, expected_outcome):
    actual_outcome = pattern_matcher.could_potentially_belong_to_pattern(text[:-1], text[-1])
    assertion_class.assertEqual(actual_outcome, expected_outcome)

def assert_pattern_matcher_could_potentially_match(assertion_class, pattern_matcher, text):
    assert_pattern_matcher_potential_match_outcome_matches_expected(assertion_class, pattern_matcher, text, True)

def assert_pattern_matcher_could_not_potentially_match(assertion_class, pattern_matcher, text):
    assert_pattern_matcher_potential_match_outcome_matches_expected(assertion_class, pattern_matcher, text, False)

def is_a_word(word: str) -> bool:
    matcher = create_word_pattern_matcher()
    return matcher.does_belong_to_pattern(word.lower(), "")

class IsTextProseToken(unittest.TestCase):
    def test_handles_capital_word(self):
        self.assertTrue(is_valid_prose_token("Word", is_a_word))
    
    def test_handles_lowercase_word(self):
        self.assertTrue(is_valid_prose_token("word", is_a_word))
    
class NewLinePatternMatcherTestCase(unittest.TestCase):
    def _create_non_matching_text_list(self):
        return ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', ' ']
    
    def test_handles_valid_character(self):
        pattern_matcher = create_new_line_pattern_matcher()
        valid_starting_text = ""
        self.assertTrue(pattern_matcher.does_belong_to_pattern(valid_starting_text, '\n'))
        self.assertTrue(pattern_matcher.could_potentially_belong_to_pattern(valid_starting_text, '\n'))
        for in_valid_starting_text in ['\n', 'chicken'] :
            self.assertFalse(pattern_matcher.does_belong_to_pattern(in_valid_starting_text, '\n'))
            self.assertFalse(pattern_matcher.could_potentially_belong_to_pattern(in_valid_starting_text, '\n'))
        
    def test_handles_invalid_character(self):
        pattern_matcher = create_new_line_pattern_matcher()
        valid_starting_text = ""
        for non_matching_text in self._create_non_matching_text_list():
            self.assertFalse(pattern_matcher.does_belong_to_pattern(valid_starting_text, non_matching_text))
            self.assertFalse(pattern_matcher.could_potentially_belong_to_pattern(valid_starting_text, non_matching_text))

    def test_creates_correct_command(self):
        pattern_matcher = create_new_line_pattern_matcher()
        command = create_command_from_pattern_matcher(pattern_matcher, '\n')
        assert_command_has_correct_name(self, command, 'enter')
        assert_insert_command_matches_text(self, command, '\n')

class WordPatternMatcherTestCase(unittest.TestCase):
    def test_handles_not_a_word(self):
        pattern_matcher = create_word_pattern_matcher()
        invalid_word = "chickenl"
        self.assertFalse(pattern_matcher.does_belong_to_pattern(invalid_word, "c"))
    
    def test_handles_valid_word(self):
        pattern_matcher = create_word_pattern_matcher()
        valid_word = "test"
        self.assertTrue(pattern_matcher.does_belong_to_pattern(valid_word[:-1], valid_word[-1]))
    
    def test_handles_valid_next_character(self):
        pattern_matcher = create_word_pattern_matcher()
        valid_word = "test"
        self.assertTrue(pattern_matcher.could_potentially_belong_to_pattern(valid_word, "c"))
    
    def test_handles_invalid_next_character(self):
        pattern_matcher = create_word_pattern_matcher()
        valid_word = "test"
        invalid_characters = ["1", " ", "\n"]
        for invalid_character in invalid_characters:
            self.assertFalse(pattern_matcher.could_potentially_belong_to_pattern(valid_word, invalid_character))
        
    def test_creates_correct_command(self):
        text = "test"
        pattern_matcher = create_word_pattern_matcher()
        command = create_command_from_pattern_matcher(pattern_matcher, text)
        expected_command = Command('word test', [BasicAction("insert", [text])])
        assert_commands_match(self, command, expected_command)

class SymbolPatternMatcherTestCase(unittest.TestCase):
    def _create_non_matching_text_list(self):
        return ["å"]

    def test_handles_invalid_character(self):
        pattern_matcher = create_symbol_pattern_matcher()
        valid_starting_text = ""
        for non_matching_text in self._create_non_matching_text_list():
            self.assertFalse(pattern_matcher.does_belong_to_pattern(valid_starting_text, non_matching_text))
            self.assertFalse(pattern_matcher.could_potentially_belong_to_pattern(valid_starting_text, non_matching_text))
        
    def test_handles_valid_character(self):
        pattern_matcher = create_symbol_pattern_matcher()
        valid_starting_text = ""
        for valid_text in SYMBOLS_TO_SPOKEN_FORM.keys():
            self.assertTrue(pattern_matcher.does_belong_to_pattern(valid_starting_text, valid_text))
            self.assertTrue(pattern_matcher.could_potentially_belong_to_pattern(valid_starting_text, valid_text))
        
    def test_creates_correct_command(self):
        pattern_matcher = create_symbol_pattern_matcher()
        command = create_command_from_pattern_matcher(pattern_matcher, '!')
        assert_command_has_correct_name(self, command, 'bang')
        assert_insert_command_matches_text(self, command, '!')

class FormattedWordsPatternMatcherTestCase(unittest.TestCase):
    def test_rejects_invalid_stuff(self):
        pattern_matcher = create_formatted_words_pattern_matcher()
        invalid_texts = ["chicken", "chickenl", "chickenl ", "chickenl 1", "chickenl 1\n", "13", "chick13", "2apple", "chicken_chicken_", "chicken!!!!!chicken", "_chicken_chicken", "chicken_chicken-chicken",
                         "chicken_chicken_chicken_chicken_chicken_chicken_chicken_chicken", "chickenchickenchickenchickenchickenchickenchickenchicken", "CHICKEN_chicken", "chickenCHICKEN", 
                         "chicken_Chicken"]
        for invalid_text in invalid_texts:
            self.assertFalse(pattern_matcher.does_belong_to_pattern(invalid_text[:-1], invalid_text[-1]))
   
    def test_accepts_words_with_separator(self):
        pattern_matcher = create_formatted_words_pattern_matcher()
        valid_texts = ["chicken_test", "chicken_testing_this", "yet-another-test", "another__test__here", "another/test/a", "another::test", "a.test.with.dots", "Chicken_Test"]
        for valid_text in valid_texts:
            self.assertTrue(pattern_matcher.does_belong_to_pattern(valid_text[:-1], valid_text[-1]))
        
    def test_accepts_words_without_separator(self):
        pattern_matcher = create_formatted_words_pattern_matcher()
        valid_texts = ["chickenchicken", "chickenwords", "WordWords", "CHICKENWORDS", "pizzaPizza"]
        for valid_text in valid_texts:
            self.assertTrue(pattern_matcher.does_belong_to_pattern(valid_text[:-1], valid_text[-1]))

    def test_rejects_stuff_that_could_not_potentially_match(self):
        pattern_matcher = create_formatted_words_pattern_matcher()
        invalid_texts = ["1", " ", "?", "zrrr_chicken", "chicken_9", "word?chicken", "test?", "_", "-"]
        for invalid_text in invalid_texts:
            self.assertFalse(pattern_matcher.could_potentially_belong_to_pattern(invalid_text[:-1], invalid_text[-1]))

    def test_accepts_stuff_that_could_potentially_match(self):
        pattern_matcher = create_formatted_words_pattern_matcher()
        valid_texts = ["abbb",
        ]
        for valid_text in valid_texts:
            self.assertTrue(pattern_matcher.could_potentially_belong_to_pattern(valid_text[:-1], valid_text[-1]))

class ProsePatternMatcherTestCase(unittest.TestCase):
    def _assert_text_match_outcome_is_expected(self, text, expected_outcome):
        pattern_matcher = create_prose_pattern_matcher()
        assert_pattern_matcher_match_outcome_is_expected(self, pattern_matcher, text, expected_outcome)
    
    def _assert_text_match_outcomes_are_expected(self, texts, expected_outcome):
        for text in texts:
            self._assert_text_match_outcome_is_expected(text, expected_outcome)

    def _assert_text_matches(self, text):
        self._assert_text_match_outcome_is_expected(text, True)
    
    def _assert_text_does_not_match(self, text):
        self._assert_text_match_outcome_is_expected(text, False)

    def _assert_text_could_match(self, text):
        pattern_matcher = create_prose_pattern_matcher()
        assert_pattern_matcher_could_potentially_match(self, pattern_matcher, text)
    
    def _assert_text_could_not_match(self, text):
        pattern_matcher = create_prose_pattern_matcher()
        assert_pattern_matcher_could_not_potentially_match(self, pattern_matcher, text)

    def test_rejects_single_token(self):
        tokens = ["chicken", "chicken."]
        self._assert_text_match_outcomes_are_expected(tokens, False)

    def test_accepts_simple_prose(self):
        text = "chicken chicken, chicken. Chicken"
        self._assert_text_matches(text)
    
    def test_rejects_invalid_case(self):
        texts = ["CHICKEN CHICKEN", "chicken CHICKEN", "CHICKEN chicken", "this is some tExt"]
        self._assert_text_match_outcomes_are_expected(texts, False)
    
    def test_accepts_with_no_punctuation(self):
        pattern_matcher = create_prose_pattern_matcher()
        text = "this is some text"
        self._assert_text_matches(text)
    
    def test_rejects_with_too_many_tokens(self):
        text = "this is some text. This is some more"
        self._assert_text_does_not_match(text)
    
    def test_accepts_with_only_two_tokens(self):
        text = "this is"
        self._assert_text_matches(text)

    def test_accepts_with_maximum_number_of_tokens(self):
        text = "one two, three four five six seven."
        self._assert_text_matches(text)    

    def test_rejects_unsupported_punctuation(self):
        text = "this is some text}"
        self._assert_text_does_not_match(text)
    
    def test_rejects_punctuation_in_invalid_location(self):
        text = "this is so,me text"
        self._assert_text_does_not_match(text)
    
    def test_accepts_consecutive_punctuation_marks(self):
        text = "this is.,! some text!!"
        self._assert_text_matches(text)
    
    def test_accepts_valid_punctuation_marks(self):
        text = "this is a test,!.?:;"
        self._assert_text_matches(text)

    def test_single_character_could_match(self):
        text = "c"
        self._assert_text_could_match(text)
    
    def test_single_word_could_match(self):
        text = "chicken"
        self._assert_text_could_match(text)

    def test_symbol_could_not_match(self):
        text = "}"
        self._assert_text_could_not_match(text)
    
    def test_word_with_symbol_could_not_match(self):
        text = "chicken}"
        self._assert_text_could_not_match(text)
    
    def test_middle_punctuation_could_not_match(self):
        text = "ch,icken"
        self._assert_text_could_not_match(text)

    def test_simple_prose_could_match_throughout(self):
        text = "this is a test"
        current_text = ""
        for character in text:
            current_text += character
            self._assert_text_could_match(current_text)
        
    def test_consecutive_spaces_could_not_match(self):
        text = "this  is"
        self._assert_text_could_not_match(text)
    
    def test_single_token_could_not_match_at_the_end(self):
        word = "chicken"
        matcher = create_prose_pattern_matcher()
        self.assertFalse(matcher.could_potentially_belong_to_pattern(word, ".", True))

def create_insert_command(utterance: str, text: str):
    action = BasicAction("insert", [text])
    return Command(utterance, [action])

def create_bang_command():
    action = BasicAction("insert", ["!"])
    return Command('bang', [action])

def create_brace_command():
    action = BasicAction("insert", ["{"])
    return Command('brace', [action])

def create_dollar_sign_command():
    return create_insert_command("dollar", "$")

def create_dot_command():
    action = BasicAction("insert", ["."])
    return Command('dot', [action])

def create_question_command():
    action = BasicAction("insert", ["?"])
    return Command('question', [action])

def create_enter_command():
    action = BasicAction("insert", ["\n"])
    return Command('enter', [action])

def create_z_command():
    action = BasicAction("insert", ["z"])
    return Command('zip', [action])

def create_type_word_test_command():
    return Command('word test', [BasicAction("insert", ["test"])])


class FormattedWordPatternMatcherTest(unittest.TestCase):
    def test_matches_capitalized_word(self):
        pattern_matcher = create_formatted_word_pattern_matcher()
        start = "Wor"
        next_character = "d"
        result = pattern_matcher.does_belong_to_pattern(start, next_character)
        self.assertTrue(result)
    
    def test_matches_fully_capitalized_word(self):
        pattern_matcher = create_formatted_word_pattern_matcher()
        start = "WOR"
        next_character = "D"
        result = pattern_matcher.does_belong_to_pattern(start, next_character)
        self.assertTrue(result)
    
    def test_rejects_invalid_stuff(self):
        invalid_stuff = ["word", "9", "Chicken9", "ChICken", "CHICKeN"]
        pattern_matcher = create_formatted_word_pattern_matcher()
        for text in invalid_stuff:
            current_text = text[:-1]
            next_character = text[-1]
            self.assertFalse(pattern_matcher.could_potentially_belong_to_pattern(current_text, next_character))
            self.assertFalse(pattern_matcher.does_belong_to_pattern(current_text, next_character))

class TextParsingTest(unittest.TestCase):
    def test_handles_symbols_only(self):
        expected_command_history = [create_bang_command(), create_dot_command(), create_question_command()]
        text = "!.?"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)

    def test_handles_new_line_only(self):
        expected_command_history = [create_enter_command()]
        text = "\n"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)

    def test_handles_symbols_and_new_line(self):
        expected_command_history = [create_bang_command(), create_dot_command(), create_enter_command(), create_question_command()]
        text = "!.\n?"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)
    
    def test_handles_single_word_only(self):
        expected_command_history = [
            Command('word test', [BasicAction("insert", ["test"])]),
        ]
        text = "test"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)
    
    def test_handles_smash(self):
        expected_command_history = [
            Command('smash test this', [BasicAction("insert", ["testthis"])]),
        ]
        text = "testthis"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)
    
    def test_handles_words_and_symbols(self):
        expected_command_history = [
            Command('word test', [BasicAction("insert", ["test"])]),
            create_brace_command(),
            Command('word this', [BasicAction("insert", ["this"])]),
            create_dollar_sign_command(),
            create_dot_command(),
        ]
        text = "test{this$."
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)
    
    def test_handles_words_and_symbols_without_mistakenly_detecting_prose(self):
        expected_command_history = [
            Command('word test', [BasicAction("insert", ["test"])]),
            create_question_command(),
        ]
        text = "test?"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)

    def test_handles_word_and_letter(self):
        expected_command_history = [
            create_type_word_test_command(),
            create_z_command(),
        ]
        text = "testz"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)

    def test_handles_letter_and_word(self):
        expected_command_history = [
            create_z_command(),
            create_type_word_test_command(),
        ]
        text = "ztest"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)
    
    def test_handles_word_letter_and_symbol(self):
        expected_command_history = [
            create_type_word_test_command(),
            create_z_command(),
            create_bang_command(),
        ]
        text = "testz!"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)

    def test_handles_letter_word_and_symbol(self):
        expected_command_history = [
            create_z_command(),
            create_type_word_test_command(),
            create_brace_command(),
        ]
        text = "ztest{"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)
    
    def test_handles_snake_case(self):
        expected_command_history = [
            Command('snake test this', [BasicAction("insert", ["test_this"])]),
        ]
        text = "test_this"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)

    def test_handles_extended_snake_case(self):
        expected_command_history = [
            Command('snake test this more', [BasicAction("insert", ["test_this_more"])]),
        ]
        text = "test_this_more"
        assert_command_history_matches_that_for_text(self, expected_command_history, text)
        expected_command_history = [
            Command('snake test this even more', [BasicAction("insert", ["test_this_even_more"])]),
        ]
        text = "test_this_even_more"
        assert_command_history_matches_that_for_text(self, expected_command_history, text)
        expected_command_history = [
            Command('snake test this even more', [BasicAction("insert", ["test_this_even_more"])]),
            Command("underscore", [BasicAction("insert", ["_"])]),
            Command("zip", [BasicAction("insert", ["z"])]),
        ]
        text = "test_this_even_more_z"
        assert_command_history_matches_that_for_text(self, expected_command_history, text)

    def test_handles_camel_case(self):
        expected_command_history = [
            Command('camel test this', [BasicAction("insert", ["testThis"])]),
        ]
        text = "testThis"
        assert_command_history_matches_that_for_text(self, expected_command_history, text)
        expected_command_history = [
            Command('camel this a test', [BasicAction("insert", ["thisATest"])]),
        ]
        text = "thisATest"
        assert_command_history_matches_that_for_text(self, expected_command_history, text)
    
    def test_handles_pascal_case(self):
        words = ["is", "a", "test"]
        utterance = "hammer this"
        text ="This"
        for word in words:
            utterance += " " + word
            text += word.capitalize()
            insert_command = create_insert_command(utterance, text)
            assert_command_history_matches_that_for_text(self, [insert_command], text)
        
    def test_handles_kabab_case(self):
        words = ["is", "a", "test"]
        utterance = "kabab this"
        text ="this"
        for word in words:
            utterance += " " + word
            text += "-" + word
            insert_command = create_insert_command(utterance, text)
            assert_command_history_matches_that_for_text(self, [insert_command], text)

    def test_handles_constant_case(self):
        words = ["is", "a", "test"]
        utterance = "constant this"
        text ="THIS"
        for word in words:
            utterance += " " + word
            text += "_" + word.upper()
            insert_command = create_insert_command(utterance, text)
            assert_command_history_matches_that_for_text(self, [insert_command], text)

    def test_all_kabab_case(self):
        words = ["is", "another", "test"]
        utterance = "all cap kabab this"
        text ="THIS"
        for word in words:
            utterance += " " + word
            text += "-" + word.upper()
            insert_command = create_insert_command(utterance, text)
            assert_command_history_matches_that_for_text(self, [insert_command], text)

    def test_handles_a_as_a_word_with_formatter(self):
        text = "this_is_a_test"
        command = create_insert_command("snake this is a test", text)
        command_history = [command]
        assert_command_history_matches_that_for_text(self, command_history, text)
    
    def test_handles_formatted_words_only(self):
        text = "Word"
        command = create_insert_command("proud word", text)
        command_history = [command]
        assert_command_history_matches_that_for_text(self, command_history, text)
        text = "WORD"
        command = create_insert_command("all cap word", text)
        command_history = [command]
        assert_command_history_matches_that_for_text(self, command_history, text)

    def test_handles_simple_prose(self):
        text = "this is a test"
        command = create_insert_command("phrase this is a test", text)
        command_history = [command]
        assert_command_history_matches_that_for_text(self, command_history, text)
    
    def test_handles_title_command(self):
        text = "What of Home, New York"
        command = create_insert_command("title what of home comma new york", text)
        command_history = [command]
        assert_command_history_matches_that_for_text(self, command_history, text)

    def test_handles_prose_with_capital_words(self):
        text = "This is my Test"
        command = create_insert_command("sentence this is my cap test", text)
        command_history = [command]
        assert_command_history_matches_that_for_text(self, command_history, text)
    
    def test_handles_prose_with_first_word_capital(self):
        text = "This is my test"
        command = create_insert_command("sentence this is my test", text)
        command_history = [command]
        assert_command_history_matches_that_for_text(self, command_history, text)
    
    def test_handles_punctuation_in_prose(self):
        text = "This, is a test."
        command = create_insert_command("sentence this comma is a test period", text)
        command_history = [command]
        assert_command_history_matches_that_for_text(self, command_history, text)
    
    def test_handles_punctuation_in_prose_with_lowercase(self):
        text = "is this, another test!?"
        command = create_insert_command("say is this comma another test exclamation mark question mark", text)
        command_history = [command]
        assert_command_history_matches_that_for_text(self, command_history, text)

if __name__ == '__main__':
    unittest.main()