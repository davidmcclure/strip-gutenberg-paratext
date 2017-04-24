

import re

from textblob import TextBlob
from cached_property import cached_property
from bs4 import BeautifulSoup
from collections import Counter


class Text:

    @classmethod
    def from_file(cls, path):
        """Read from a file.
        """
        with open(path) as fh:
            return cls(fh.read())

    def __init__(self, text):
        """Strip the Gutenberg header / footer.
        """
        i1 = None
        i2 = None

        lines = text.splitlines()

        tokens = ['***', 'PROJECT', 'GUTENBERG']
        s_tokens = tokens + ['START']
        e_tokens = tokens + ['END']

        for i, line in enumerate(lines):

            # Match "start" line.
            if False not in [token in line for token in s_tokens]:
                i1 = i+1

            # Match "end" line.
            if False not in [token in line for token in e_tokens]:
                i2 = i

        self.text = '\n'.join(lines[i1:i2])


class TrainingText(Text):

    def __init__(self, text):
        """Strip the Gutenberg header / footer.
        """
        super().__init__(text)

        self.tree = BeautifulSoup(text, 'html.parser')

    def front_text(self):
        """Get the <front> text.
        """
        tag = self.tree.select_one('front')
        return tag.text or None

    def back_text(self):
        """Get the <back> text.
        """
        tag = self.tree.select_one('back')
        return tag.text or None


class Snippet:

    def __init__(self, text):
        self.text = text

    @cached_property
    def blob(self):
        return TextBlob(self.text)

    @cached_property
    def tags(self):
        return self.blob.tags

    @cached_property
    def tag_counts(self):
        """Build a counter of (tag -> count).
        """
        counts = Counter()

        for token, tag in self.tags:
            counts[tag] += 1

        return counts

    def tag_ratio(self, *tags):
        """Given a POS tag, return a ratio of (tag count / total tokens).
        """
        return sum([self.tag_counts[t] for t in tags]) / len(self.tags)

    def blank_line_ratio(self):
        """Ratio of lines that are blank.
        """
        lines = self.text.splitlines()

        blank_count = len([line for line in lines if not line])

        return blank_count / len(lines)

    def digit_ratio(self):
        """Ratio of digit characters.
        """
        digits = re.findall('[0-9]', self.text)

        return len(digits) / len(self.text)

    def caps_ratio(self):
        """Ratio of digit characters.
        """
        caps = re.findall('[A-Z]', self.text)

        return len(caps) / len(self.text)

    def features(self):
        """Assembly a features row.
        """
        return dict(

            blank_line_ratio=self.blank_line_ratio(),
            digit_ratio=self.digit_ratio(),
            caps_ratio=self.caps_ratio(),

            pos_cd_ratio=self.tag_ratio('CD'),
            pos_dt_ratio=self.tag_ratio('DT'),
            pos_jj_ratio=self.tag_ratio('JJ', 'JJR', 'JJS'),
            pos_nn_ratio=self.tag_ratio('NN', 'NNS', 'NNP', 'NNPS'),
            pos_rb_ratio=self.tag_ratio('RB', 'RBR', 'RBS'),

            pos_vb_ratio=self.tag_ratio(
                'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'
            ),

        )
