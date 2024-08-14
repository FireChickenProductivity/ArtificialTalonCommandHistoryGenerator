from patterns import SYMBOLS_TO_SPOKEN_FORM, create_new_line_pattern_matcher, create_symbol_pattern_matcher, create_command_from_pattern_matcher, \
    create_word_pattern_matcher, create_formatted_words_pattern_matcher
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
        valid_texts = ["chickenchicken", "chickenwords", "wordWords"]
        for valid_text in valid_texts:
            print('test start')
            self.assertTrue(pattern_matcher.does_belong_to_pattern(valid_text[:-1], valid_text[-1]))
            print('test ending')


def create_bang_command():
    action = BasicAction("insert", ["!"])
    return Command('bang', [action])

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
    
    def test_handles_words_only(self):
        expected_command_history = [
            Command('word test', [BasicAction("insert", ["test"])]),
            Command('word this', [BasicAction("insert", ["this"])]),
        ]
        text = "testthis"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)
    
    def test_handles_words_and_symbols(self):
        expected_command_history = [
            Command('word test', [BasicAction("insert", ["test"])]),
            create_bang_command(),
            Command('word this', [BasicAction("insert", ["this"])]),
            create_dot_command(),
            create_question_command(),
        ]
        text = "test!this.?"
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
            create_bang_command(),
        ]
        text = "ztest!"
        command_history = create_command_history_list_from_text(text)
        assert_command_histories_match(self, command_history, expected_command_history)

if __name__ == '__main__':
    unittest.main()