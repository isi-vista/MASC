# noqa
from typing import Any, List, MutableMapping, MutableSequence, Optional, Sequence, Set, Tuple
from unittest import TestCase

from pycurator.gpt2_component.filter import (
    AtLeastTwoWords,
    Criteria,
    FirstXElements,
    NoBadWords,
    NoDuplicates,
    NoJunkChars,
    NonEmpty,
    NoSemanticDuplicates,
    cut_trailing_quotes,
    cut_trailing_sentence,
    get_only_k,
    result_replace,
)


class TestFilterUtilities(TestCase):  # noqa
    def test_cut_trailing_sentence(self) -> None:  # noqa
        data = [
            ("First sent Second sent", ""),
            ("First sent. Second sent.", "First sent"),
            ("First sent? Second sent.", "First sent"),
            ("First sent! Second sent.", "First sent"),
            ("First sent < Second sent.", "First sent"),
            ("First sent > Second sent.", "First sent"),
        ]
        for input_data, expected in data:
            actual = cut_trailing_sentence(input_data)
            self.assertEqual(
                expected,
                actual,
                f"Failed with input <{input_data}>. Expected <{expected}>, but got <{actual}>.",
            )

    def test_cut_trailing_quotes(self) -> None:  # noqa
        data = [
            ("No quotes", "No quotes"),
            ("'Simple quotes''", "'Simple quotes''"),
            ('"One quote at the beginning', "One quote at the beginning"),
            ('"Three" quotes "and some stuff to cut', '"Three" quotes '),
            ('Three quotes at the end"""', 'Three quotes at the end""'),
        ]
        for input_data, expected in data:
            actual = cut_trailing_quotes(input_data)
            self.assertEqual(
                expected,
                actual,
                f"Failed with input <{input_data}>. Expected <{expected}>, but got <{actual}>.",
            )

    def test_result_replace(self) -> None:  # noqa
        data = [
            ("a", ""),
            ("a.", "a"),
            ('"a."', '"a"'),
            ("", ""),
            ("First sentence. Second sentence.", "first sentence"),
            ('"First sentence." Second sentence.', '"first sentence"'),
            ('"A."', '"a"'),
            ('A".""', 'a""'),
            ("#something.", "something"),
            ("some # thing.", "some thing"),
            ("*something.", "something"),
            ("some * thing.", "some thing"),
            ("first row \n\n second row.", "first row \n second row"),
            ("first row \r\n second row.", "first row \n second row"),
            ("first column \t second column.", "first column second column"),
            ("no trailing empty spaces .", "no trailing empty spaces"),
            ('no trailing "empty spaces" "even with quotes.', 'no trailing "empty spaces"'),
            ("ℍ𝕖𝕝𝕝𝕠, 𝕨𝕠𝕣𝕝𝕕!", "hello, world"),
        ]
        for input_data, expected in data:
            actual = result_replace(input_data)
            self.assertEqual(
                expected,
                actual,
                f"Failed with input <{input_data}>. Expected <{expected}>, but got <{actual}>.",
            )

    def test_get_only_k(self) -> None:  # noqa
        data: List[
            Tuple[
                MutableMapping[str, MutableSequence[str]],
                int,
                MutableMapping[str, MutableSequence[str]],
            ]
        ] = [
            ({"k1": ["1", "2", "3"]}, 3, {"k1": ["1", "2", "3"]}),
            ({"k1": ["1", "2", "3"]}, 6, {"k1": ["1", "2", "3"]}),
            ({"k1": ["1", "2", "3"]}, 2, {"k1": ["1", "2"]}),
            ({"k1": ["1"], "k2": ["2"], "k3": ["3"]}, 2, {"k2": ["2"], "k3": ["3"]}),
            (
                {"k1": ["1", "2", "3"], "k2": ["1", "2", "3"]},
                4,
                {"k1": ["1", "2"], "k2": ["1", "2"]},
            ),
            (
                {"k1": ["1", "2", "3"], "k2": ["1", "2", "3"]},
                5,
                {"k1": ["1", "2"], "k2": ["1", "2", "3"]},
            ),
        ]
        for input_data, k, expected in data:
            actual = get_only_k(input_data, k)
            self.assertEqual(
                expected,
                actual,
                f"Failed with input <{input_data}>. Expected <{expected}>, but got <{actual}>.",
            )


class TestFilters(TestCase):  # noqa
    def simple_test(self, data: Sequence[Tuple[Any, Any]], f: Criteria) -> None:  # noqa
        for input_data, expected in data:
            actual = f.meet_criteria(input_data)
            self.assertEqual(
                expected,
                actual,
                f"Failed with input {input_data}. Expected {expected}, but got {actual} "
                f"for filter {f}",
            )

    def test_non_empty(self) -> None:  # noqa
        # List of inputs and expected outputs
        data = [
            (["", "a"], ["a"]),
            ([], []),
            (["", "", ""], []),
        ]
        filter_to_test = NonEmpty()
        self.simple_test(data, filter_to_test)

    def test_at_least_two_words(self) -> None:  # noqa
        # List of inputs and expected outputs
        data = [
            (["", "oneword"], []),
            (["two words"], ["two words"]),
            (["more than two words", "", ""], ["more than two words"]),
            ([], []),
        ]
        filter_to_test = AtLeastTwoWords()
        self.simple_test(data, filter_to_test)

    def test_first_x(self) -> None:  # noqa
        # List of inputs and expected outputs
        data = [
            (["", "a", "b", "c"], ["", "a"], 2),
            (["a"], ["a"], 1),
            (["a", "", ""], ["a", ""], 2),
            ([], [], 5),
        ]
        for i, e, x in data:
            filter_to_test = FirstXElements(x=x)
            self.simple_test([(i, e)], filter_to_test)

    def test_no_duplicates(self) -> None:  # noqa
        # List of inputs and expected outputs
        data: List[Tuple[List[str], List[str], Optional[Set[str]]]] = [
            (["", "a", "b", "c"], ["", "a"], {"b", "c"}),
            (["", "a", "b", "c"], ["", "a", "b", "c"], {"d", "e"}),
            (["", "a", "b", "c"], ["", "a", "b", "c"], None),
            (["a"], ["a"], set()),
            (["a", "", ""], ["a", ""], None),
            (["a", "", ""], ["a", ""], {"b", "c"}),
            (["burn fuel.", "", ""], [""], {"Burn fuel.", "c"}),
            (["set fire.", "", ""], [""], {"set fire", "c"}),
            (["set fire.", "", ""], [""], {"set fire ", "c"}),
            (["set fire. ", "", ""], [""], {"set fire", "c"}),
            (["check shipping address.", "", ""], [""], {"Check shipping address.", "c"}),
            ([], [], {"b", "c"}),
        ]
        for input_data, expected, ref in data:
            f = NoDuplicates(reference=ref)
            actual = f.meet_criteria(input_data)
            self.assertEqual(
                expected,
                actual,
                f"Failed with input {input_data}. Expected {expected}, but got {actual} "
                f"for filter {f}",
            )

    def test_no_junk_chars(self) -> None:  # noqa
        # List of inputs and expected outputs
        data = [
            (["\n", "a"], ["a"]),
            (["ab️", "a"], ["ab️", "a"]),
            (["a\u200db️", "a"], ["a"]),  # Zero-width joiner
            (["suggestion__", "a"], ["a"]),
            (["event??", "a"], ["a"]),
            (["event!!", "a"], ["a"]),
            (["event???", "a"], ["a"]),
            (["event!!!", "a"], ["a"]),
            (["event(", "a"], ["a"]),
            (["event)", "a"], ["a"]),
            (["~~~set fire to self~~~ 6.", "a"], ["a"]),
            (["~~set fire to self", "a"], ["~~set fire to self", "a"]),
            ([], []),
        ]
        filter_to_test = NoJunkChars()
        self.simple_test(data, filter_to_test)

    def test_no_semantic_duplicates(self) -> None:  # noqa
        # List of inputs and expected outputs
        data: List[Tuple[List[str], List[str], Set[str]]] = [
            (
                ["organize the force", "some other event", ""],
                ["some other event", ""],
                {"organize the forces", "c"},
            ),
            (["analyze data."], [], {"analyze the data."}),
            (["build the software."], ["build the software."], {"design the software."}),
            (["build the software."], ["build the software."], {"share the software."}),
            (["BUILD SOFTWARE."], [], {"build the software."}),
            (
                ["a bomb squad is dispatched to the scene", "a bomb squad is called to the scene"],
                ["a bomb squad is dispatched to the scene"],
                {"a"},
            ),
            ([], [], {"b", "c"}),
        ]
        for input_data, expected, ref in data:
            f = NoSemanticDuplicates(reference=ref)
            actual = f.meet_criteria(input_data)
            self.assertEqual(
                expected,
                actual,
                f"Failed with input {input_data}. Expected {expected}, but got {actual} for "
                f"filter {f}",
            )

    def test_no_bad_words(self) -> None:  # noqa
        # List of inputs and expected outputs
        data: List[Tuple[List[str], List[str]]] = [
            ([], []),  # Do not crash on empty list
            ([""], [""]),  # Do not crash on empty string
            (["help"], ["help"]),  # Do not filter non-bad word
            (["nsfw"], []),  # Filter string that is bad word
            (["NSFW"], []),  # Filter string that is bad word, regardless of case
            (["nsfw stuff"], []),  # Filter string containing bad word
            (["class"], ["class"]),  # Do not filter string containing bad word as subword
        ]
        filter_to_test = NoBadWords()
        self.simple_test(data, filter_to_test)
