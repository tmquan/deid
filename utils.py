import html
from itertools import zip_longest
from typing import List, Any, Callable, Tuple, Union
Token = str
TokenList = List[Token]

import difflib
import pandas as pd
import os 
import re
import spacy
# Check if 'en_core_web_sm' model is installed
if not spacy.util.is_package('en_core_web_sm'):
    # Install 'en_core_web_sm' model
    spacy.cli.download('en_core_web_sm')

# Load the pre-trained spaCy model
nlp = spacy.load('en_core_web_sm')

def read_files(
    folders: List = [], # Path to the data
    formats: Union[List, str] = "csv", # Text or csv
    columns: Union[List, str] = "text"
):
    parsed_list = []
    
    if isinstance(formats, str):
        formats = [formats]

    if isinstance(columns, str):
        columns = [columns]

    for folder in folders:
        for root, dirs, files in os.walk(folder):
            for file in sorted(files):
                file_path = os.path.join(root, file)
                file_format = file_path.split(".")[-1]
                
                if file_format in formats:
                    if file_format == "csv":
                        df = pd.read_csv(file_path)
                        for column in columns:
                            if column in df.columns:
                                parsed_list.extend(df[column].astype(str).tolist())
                    elif file_format == "txt":
                        with open(file_path, 'r') as f:
                            content = f.read()
                            parsed_list.append(content)

    return parsed_list


def deidentify_spacy(text):
    doc = nlp(text)
    for entity in doc.ents:
        # print(entity.label_)
        # if entity.label_ in ['PERSON', 'DATE', 'CARDINAL', 'ORG', 'FAC', 'EMAIL']:
        text = text.replace(entity.text, '<REDACTED>')
    return text


whitespace = re.compile('\s+')
end_sentence = re.compile('[.!?]\s+')


def tokenize(s: str) -> TokenList:
    '''Split a string into tokens'''
    return whitespace.split(s)


def untokenize(ts: TokenList) -> str:
    '''Join a list of tokens into a string'''
    return ' '.join(ts)


def sentencize(s: str) -> TokenList:
    '''Split a string into a list of sentences'''
    return end_sentence.split(s)


def unsentencise(ts: TokenList) -> str:
    '''Join a list of sentences into a string'''
    return '. '.join(ts)


def html_unsentencise(ts: TokenList) -> str:
    '''Joing a list of sentences into HTML for display'''
    return ''.join(f'<p>{t}</p>' for t in ts)


# def mark_text(text: str) -> str:
#     return f'<span style="color: red;">{text}</span>'


# def mark_span(text: TokenList) -> TokenList:
#     return [mark_text(token) for token in text]


def mark_span(text: TokenList) -> TokenList:
    if len(text) > 0:
        text[0] = '<span style="background: #69E2FB;">' + text[0]
        text[-1] += '</span>'
    return text


def markup_diff(a: TokenList, b: TokenList,
                mark: Callable[TokenList, TokenList] = mark_span,
                default_mark: Callable[TokenList, TokenList] = lambda x: x,
                isjunk: Union[None, Callable[[Token], bool]] = None) -> Tuple[TokenList, TokenList]:
    """Returns a and b with any differences processed by mark

    Junk is ignored by the differ
    """
    seqmatcher = difflib.SequenceMatcher(
        isjunk=isjunk, a=a, b=b, autojunk=True)
    out_a, out_b = [], []
    for tag, a0, a1, b0, b1 in seqmatcher.get_opcodes():
        markup = default_mark if tag == 'equal' else mark
        out_a += markup(a[a0:a1])
        out_b += markup(b[b0:b1])
    assert len(out_a) == len(a)
    assert len(out_b) == len(b)
    return out_a, out_b



def align_seqs(a: TokenList, b: TokenList, fill: Token = '') -> Tuple[TokenList, TokenList]:
    out_a, out_b = [], []
    seqmatcher = difflib.SequenceMatcher(a=a, b=b, autojunk=True)
    for tag, a0, a1, b0, b1 in seqmatcher.get_opcodes():
        delta = (a1 - a0) - (b1 - b0)
        out_a += a[a0:a1] + [fill] * max(-delta, 0)
        out_b += b[b0:b1] + [fill] * max(delta, 0)
    assert len(out_a) == len(out_b)
    return out_a, out_b


def html_sidebyside(a, b):
    # Set the panel display
    out = '<div style="display: grid;grid-template-columns: 1fr 1fr;grid-gap: 20px;">'
    # There's some CSS in Jupyter notebooks that makes the first pair unalign. This is a workaround
    out += '<p></p><p></p>'
    for left, right in zip_longest(a, b, fillvalue=''):    
        out += f'<p>{left}</p>'
        out += f'<p>{right}</p>'
    out += '</div>'
    return out


def html_diffs(a, b):
    a = html.escape(a)
    b = html.escape(b)

    out_a, out_b = [], []
    for sent_a, sent_b in zip(*align_seqs(sentencize(a), sentencize(b))):
        mark_a, mark_b = markup_diff(tokenize(sent_a), tokenize(sent_b))
        out_a.append(untokenize(mark_a))
        out_b.append(untokenize(mark_b))

    return html_sidebyside(out_a, out_b)

def show_diffs(a, b):
    display(HTML(html_diffs(a,b)))