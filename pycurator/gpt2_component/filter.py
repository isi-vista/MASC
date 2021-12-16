"""Filtering functions for GPT-2 generated outputs."""
from abc import ABC, abstractmethod
import copy
from difflib import SequenceMatcher
from pathlib import Path
import re
from typing import MutableMapping, MutableSequence, Optional, Set
import unicodedata

import nltk

DEFAULT_BAD_WORDS_FILE = Path(__file__).resolve().parent / "bad_words_en.txt"
SENT_DETECTOR: nltk.tokenize.punkt.PunktSentenceTokenizer = nltk.data.load(
    "tokenizers/punkt/english.pickle"
)


def standardize_punctuation(text: str) -> str:
    """Standardizes punctuation in the text.

    Args:
        text: Input text.

    Returns:
        Punctuation-standardized text.
    """
    text = text.replace("’", "'")
    text = text.replace("`", "'")
    text = text.replace("“", '"')
    text = text.replace("”", '"')
    return text


def cut_trailing_quotes(text: str) -> str:
    """Cut trailing quotes into one quote.

    Args:
        text: Input text.

    Returns:
        Text up to the dangling double quote.
    """
    num_quotes = text.count('"')
    if num_quotes == 1:
        return text.replace('"', "")
    elif num_quotes % 2 == 0:
        return text
    else:
        final_ind = text.rfind('"')
        return text[:final_ind]


def cut_trailing_sentence(text: str) -> str:
    """Discards all but the first sentence. Assumes punctuation is standardized.

    Args:
        text: Input text.

    Returns:
        Clean text.
    """
    # Serves as heuristic to prevent overly repetitive sequences
    punctuation_match = re.search(pattern=r"[.?!]", string=text, flags=re.IGNORECASE)
    if punctuation_match is None:
        return ""

    # Use Punkt to select the first sentence
    text = SENT_DETECTOR.tokenize(text)[0]

    # Remove trailing punctuation
    last_p = len(text)
    if text[-1] in ".?!":
        last_p -= 1

    et_token = text.find("<")
    if et_token > 0:
        last_p = min(last_p, et_token)

    act_token = text.find(">")
    if act_token > 0:
        last_p = min(last_p, act_token)

    text = text[:last_p]

    return text.strip()


def result_replace(result: str) -> str:
    """Clean result with filtering character.

    Args:
        result: Input text.

    Returns:
        Clean result.
    """
    # Normalize Unicode strings using Normalization Form KC
    # For example, converts non-breaking space to normal space or "ℍ" -> "H"
    # See "Unicode Normalization Forms" (https://unicode.org/reports/tr15/) for more details
    result = unicodedata.normalize("NFKC", result)

    result = re.sub(r"[#*]+", "", result)

    # Converts and merges all newlines to single \n
    result = re.sub(r"[\n\r]+", "\n", result)
    # Converts and merges all non-newline whitespace to a single space
    result = re.sub(r"[^\S\n]+", " ", result)

    result = result.replace('."', '".')
    result = standardize_punctuation(result)
    result = cut_trailing_sentence(result)
    result = cut_trailing_quotes(result)
    result = result.strip("\n .?!")
    if not result:
        return ""

    # Find the first letter and lower case it
    first_alpha = re.search(pattern=r"[a-zA-Z]", string=result, flags=re.IGNORECASE)
    if first_alpha is not None:
        idx = first_alpha.start(0)
        result = result[:idx] + result[idx].lower() + result[idx + 1 :]

    result = result.strip()
    return result


class Criteria(ABC):
    """Base class for filters."""

    @abstractmethod
    def meet_criteria(self, elements: MutableSequence[str]) -> MutableSequence[str]:
        """Filters the given elements based on the class's filtering criteria.

        Args:
            elements: Elements to filter.

        Returns:
            Elements that meet the filter's criteria.
        """


class NonEmpty(Criteria):
    """Remove empty strings."""

    def meet_criteria(self, elements: MutableSequence[str]) -> MutableSequence[str]:
        """Filter the input.

        Args:
            elements: Sequence to filter.

        Returns:
            Filtered sequence.
        """
        keep = [e for e in elements if e]
        return keep


class NoJunkChars(Criteria):
    """Removes junk characters.

    See the regular expressions in the constructor for the characters this filter removes. In
    addition, it filters all non-printable characters except standard spaces.
    """

    def __init__(self) -> None:
        """Constructor."""
        super().__init__()

        self.regexes = [
            re.compile(r"[_?!]+", re.IGNORECASE),
            re.compile(r"[\n()]", re.IGNORECASE),
            re.compile(r"[^a-z\s]{3,}", re.IGNORECASE),
        ]

    def meet_criteria(self, elements: MutableSequence[str]) -> MutableSequence[str]:
        """Filter the input.

        Args:
            elements: Sequence to filter.

        Returns:
            Filtered sequence.
        """
        keep = elements
        for p in self.regexes:
            keep = [k for k in keep if p.search(k) is None]

        # Remove strings with unusual characters caused by BPE
        keep = [k for k in keep if str.isprintable(k)]

        return keep


class AtLeastTwoWords(Criteria):
    """Keeps only strings that have at least two words."""

    def meet_criteria(self, elements: MutableSequence[str]) -> MutableSequence[str]:
        """Filter the input.

        Args:
            elements: Sequence to filter.

        Returns:
            Filtered sequence.
        """
        keep = [e for e in elements if len(e.split(" ")) >= 2]
        return keep


class And(Criteria):
    """A logical AND of two or more filters.

    Filters are applied in the order of their parameters.
    """

    def __init__(self, *criteria: Criteria) -> None:
        """Constructor.

        Args:
            *criteria: One or more filters.
        """
        super().__init__()
        self.criteria = criteria

    def meet_criteria(self, elements: MutableSequence[str]) -> MutableSequence[str]:
        """Filter the input.

        Args:
            elements: Sequence to filter.

        Returns:
            Filtered sequence.
        """
        keep = elements
        for c in self.criteria:
            keep = c.meet_criteria(keep)
        return keep


class NoDuplicates(Criteria):
    """Removes strings that are duplicated within the input or that appear in a reference set."""

    @staticmethod
    def clean_string(s: str) -> str:
        """String normalization: strip trailing space, remove periods, lower-case.

        Args:
            s: Input string.

        Returns:
            Normalized string.
        """
        return s.rstrip().replace(".", "").lower()

    def __init__(self, reference: Optional[Set[str]] = None) -> None:
        """Constructor.

        Args:
            reference: Set of strings to always remove.
        """
        super().__init__()
        if reference is not None:
            self.reference = {self.clean_string(e) for e in reference}
        else:
            self.reference = set()

    def meet_criteria(self, elements: MutableSequence[str]) -> MutableSequence[str]:
        """Filter the input.

        Args:
            elements: Sequence to filter.

        Returns:
            Filtered sequence.
        """
        event_set = copy.deepcopy(self.reference)
        keep = []
        for e in elements:
            clean_e = self.clean_string(e)
            if clean_e not in event_set:
                keep.append(e)
                event_set.add(clean_e)
        return keep

    def __repr__(self) -> str:
        """Constructs a human-readable representation.

        Returns:
            Human-readable representation.
        """
        return super().__repr__() + f" Reference set: {sorted(self.reference)}"


class NoSemanticDuplicates(NoDuplicates):
    """Removes strings that are semantic duplicates in a reference set."""

    def __init__(
        self, reference: Optional[Set[str]] = None, similarity_threshold: float = 0.8
    ) -> None:
        """Constructor.

        Args:
            reference: Set of strings to always remove.
            similarity_threshold: Threshold for string similarity.
        """
        super().__init__(reference)
        self.threshold = similarity_threshold

    def meet_criteria(self, elements: MutableSequence[str]) -> MutableSequence[str]:
        """Filter the input.

        Args:
            elements: Sequence to filter.

        Returns:
            Filtered sequence.
        """
        # Remove duplicates
        nd = NoDuplicates(reference=self.reference)
        keep = nd.meet_criteria(elements=elements)
        # Remove semantic duplicates occurring in reference
        for r in sorted(self.reference):
            new_keep = []
            for k in keep:
                similarity = SequenceMatcher(None, k.lower(), r.lower()).ratio()
                if similarity < self.threshold:
                    new_keep.append(k)
            keep = new_keep
        # Remove semantic duplicates occurring in input
        candidates = list(reversed(keep))
        keep = []
        while candidates:
            r = candidates.pop()
            keep.append(r)
            new_candidates = []
            for k in candidates:
                similarity = SequenceMatcher(None, k.lower(), r.lower()).ratio()
                if similarity < self.threshold:
                    new_candidates.append(k)
            candidates = new_candidates
        return keep

    def __repr__(self) -> str:
        """Constructs a human-readable representation.

        Returns:
            Human-readable representation.
        """
        return super().__repr__() + f" Threshold: {self.threshold}"


class FirstXElements(Criteria):
    """Keeps only the first X elements."""

    def __init__(self, x: int) -> None:
        """Constructor.

        Args:
            x: The number of elements to keep.
        """
        super().__init__()
        self.x_threshold = x

    def meet_criteria(self, elements: MutableSequence[str]) -> MutableSequence[str]:
        """Filter the input.

        Args:
            elements: Sequence to filter.

        Returns:
            Filtered sequence.
        """
        return elements[: self.x_threshold]


class NoBadWords(Criteria):
    """Removes strings that contain dirty, naughty, obscene and otherwise bad words."""

    def __init__(self, bad_words_file: Path = DEFAULT_BAD_WORDS_FILE) -> None:
        """Constructor.

        Args:
            bad_words_file: File containing list of bad words.
        """
        super().__init__()
        with open(bad_words_file) as file:
            self.bad_words = set(w.strip() for w in file)

    def meet_criteria(self, elements: MutableSequence[str]) -> MutableSequence[str]:
        """Filter the input.

        Args:
            elements: Sequence to filter.

        Returns:
            Filtered sequence.
        """
        keep = [e for e in elements if not any(w in self.bad_words for w in e.lower().split())]
        return keep


class DefaultCriteria(Criteria):
    """Default collection of criteria to use."""

    def __init__(self, existing_events: Set[str], keep: int) -> None:
        """Constructor.

        Args:
            existing_events: Set of strings to always remove.
            keep: The number of elements to keep.
        """
        super().__init__()
        self.criteria = And(
            NonEmpty(),
            NoJunkChars(),
            AtLeastTwoWords(),
            NoBadWords(),
            NoDuplicates(reference=existing_events),
            NoSemanticDuplicates(reference=existing_events),
            FirstXElements(x=keep),
        )

    def meet_criteria(self, elements: MutableSequence[str]) -> MutableSequence[str]:
        """Filter the input.

        Args:
            elements: Sequence to filter.

        Returns:
            Filtered sequence.
        """
        return self.criteria.meet_criteria(elements)


def get_only_k(
    recommendations: MutableMapping[str, MutableSequence[str]], k: int
) -> MutableMapping[str, MutableSequence[str]]:
    """Filters the recommendations in a round-robin fashion to keep only k recommendations.

    Args:
        recommendations: The recommendations to filter.
        k: The total number of recommendations to keep.
    """
    num_events = sum(len(v) for v in recommendations.values())
    if num_events <= k:
        return recommendations
    else:
        recs_to_return: MutableMapping[str, MutableSequence[str]] = recommendations
        while num_events > k:
            removed = 0
            new_recs_to_return = copy.deepcopy(recs_to_return)
            for key, v in recs_to_return.items():
                if num_events - removed > k:
                    if len(v) > 1:
                        new_recs_to_return[key] = v[:-1]
                    else:
                        del new_recs_to_return[key]
                    removed += 1
            recs_to_return = new_recs_to_return
            num_events = sum(len(v) for v in recs_to_return.values())
        return recs_to_return
