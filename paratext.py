

from textblob import TextBlob
from cached_property import cached_property
from bs4 import BeautifulSoup


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

        text = '\n'.join(lines[i1:i2])

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
