import logging
from textwrap import dedent
from typing import Dict, List, Set

import openai

from voc_builder.models import WordSample

logger = logging.getLogger()

# The prompt being used to make word
prompt_tmpl = dedent(
    '''
I will give you a sentence and a list of words called "known-words" which is divided
by ",", please find out the most uncommon word in the sentence(the word must not in "known-words"),
get the simplified Chinese meaning of that word, the pronunciation of that word
and translate the whole sentence into simplified Chinese.

Your answer should be separated into 4 different lines, each line's content is as below:

- word: {{word}}
- pronunciation: {{pronunciation}}
- meaning: {{chinese_meaning_of_word}}
- translated: {{translated_sentence}}

The answer should have no extra content.

known-words: {known_words}

The sentence is:

{text}
'''
)


def query_openai(text: str, known_words: Set[str]) -> str:
    """Query OpenAI to get the translation results.

    :return: Well formatted string contains word and meaning
    """
    content = prompt_tmpl.format(text=text, known_words=','.join(known_words))
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": content},
        ],
    )
    logger.debug('Completion API returns: %s', completion)
    return completion.choices[0].message.content.strip()


def parse_openai_reply(reply_text: str, orig_text: str) -> WordSample:
    """Parse the OpenAI reply into WorkSample

    :param reply_text: Formatted text
    :param orig_text: The original text which needs translation
    :return: WordSample object
    :raise: ValueError when the given reply text can not be parsed
    """
    # Get the key value pairs from text first
    kv_pairs: Dict[str, str] = {}
    for line in reply_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            kv_pairs[key.strip(' -').lower()] = value.strip()

    # The reply may use non-standard keys sometimes, define a list of possible keys to handle
    # these situations.
    #   {field_name}: {list_of_possible_keys}
    possible_field_index: Dict[str, List[str]] = {
        'word': ['word', 'uncommon word'],
        'word_meaning': ['meaning'],
        'pronunciation': ['pronunciation'],
        'translated_text': ['translated'],
    }
    required_fields = set(possible_field_index.keys())

    # Build a fields dict for making the WordSample object
    fields: Dict[str, str] = {}
    for field, keys in possible_field_index.items():
        for k in keys:
            field_value = kv_pairs.get(k)
            if field_value:
                fields[field] = field_value
                break

    # All fields must be provided
    if set(fields.keys()) != required_fields:
        raise ValueError('Reply text "%s" is invalid' % reply_text)

    # The word was surrounded by {} sometimes, remove
    fields['word'] = fields['word'].strip('{}').lower()
    return WordSample(orig_text=orig_text, **fields)
