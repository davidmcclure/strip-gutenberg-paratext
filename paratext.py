

import re
import scandir
import os
import attr

import pandas as pd

from textblob import TextBlob
from cached_property import cached_property
from bs4 import BeautifulSoup
from collections import Counter


def scan_paths(root, pattern=None):
    """Walk a directory and yield file paths that match a pattern.

    Args:
        root (str)
        pattern (str)

    Yields: str
    """
    for root, dirs, files in scandir.walk(root, followlinks=True):
        for name in files:

            # Match the extension.
            if not pattern or re.search(pattern, name):
                yield os.path.join(root, name)


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
        """Parse the markup.
        """
        super().__init__(text)

        self.tree = BeautifulSoup(text, 'html.parser')

    def get_text(self, tag):
        """Get plain text content of a tag.
        """
        tag = self.tree.select_one(tag)
        return tag.text or None

    def get_front(self):
        """Get the frontmatter.
        """
        return self.get_text('front')

    def get_body_beginning(self, num_chars=2000):
        """Get the first N chars from the body text.

        Args:
            num_chars (int)
        """
        text = self.get_text('body')
        return text[:num_chars] if text else None


@attr.s
class Snippet:

    text = attr.ib()

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

    def chapter_ratio(self):
        """Ratio of words that are "chapter."
        """
        return self.blob.words.count('chapter') / len(self.blob.words)

    def features(self, tags=None):
        """Assembly a features row.
        """
        return dict(

            digit_ratio=self.digit_ratio(),
            blank_line_ratio=self.blank_line_ratio(),
            caps_ratio=self.caps_ratio(),
            chapter_ratio=self.chapter_ratio(),

            cd_ratio=self.tag_ratio('CD'),
            dt_ratio=self.tag_ratio('DT'),

            jj_ratio=self.tag_ratio('JJ'),
            jjr_ratio=self.tag_ratio('JJR'),
            jjs_ratio=self.tag_ratio('JJS'),

            nn_ratio=self.tag_ratio('NN'),
            nns_ratio=self.tag_ratio('NNS'),
            nnp_ratio=self.tag_ratio('NNP'),
            nnps_ratio=self.tag_ratio('NNPS'),

            rb_ratio=self.tag_ratio('RB'),
            rbr_ratio=self.tag_ratio('RBR'),
            rbs_ratio=self.tag_ratio('RBS'),

            vb_ratio=self.tag_ratio('VB'),
            vbd_ratio=self.tag_ratio('VBD'),
            vbg_ratio=self.tag_ratio('VBG'),
            vbn_ratio=self.tag_ratio('VBN'),
            vbp_ratio=self.tag_ratio('VBP'),
            vbz_ratio=self.tag_ratio('VBZ'),

            **(tags or {}),

        )


@attr.s
class TrainingCorpus:

    path = attr.ib()

    def paths(self):
        """Generate training XML paths.
        """
        yield from scan_paths(self.path, '\.xml')
