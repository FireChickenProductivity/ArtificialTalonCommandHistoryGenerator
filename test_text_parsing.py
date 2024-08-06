from patterns import SYMBOLS_TO_SPOKEN_FORM, create_new_line_pattern_matcher, create_symbol_pattern_matcher, create_command_from_pattern_matcher
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
    assertion_class.assertEqual(len(actual), len(expected))
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
        
if __name__ == '__main__':
    unittest.main()