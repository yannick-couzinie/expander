#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Class for expanding contractions in english text. """

__author__ = "Yannick Couzinié"

# standard library imports
import yaml
# third party library imports
import nltk
# local imports
import utils


def expand_contractions(stanford_model, sent_list, is_split=True):
    """
    This method uses the StanfordPOSTagger tags to identify contractions in
    the sentence and expand them sensibly. Some examples are:
        "I'm" -> "I am"
        "It's difficult" -> "It is difficult"
    The difficulty is that sometimes "'s" is not an indicator of a
    contraction but a possessive pronoun like
        "It's legs were shaking"
    which should not be expanded. The stanford tagger tags this as
    "POSS" for possessive which makes it easy to identify these cases.
    Furthermore, a difficulty lies in the fact that the expansion is not
    unique. Without context we have for example the following:
        "I'll" -> "I will" or "I shall"

    Args:
        stanford_model - object of StanfordPOSTagger, as returned by
                         load_stanford_pos.
        sent_list - list of sentences which are split up by word.
                    For the splitting use nltk.word_tokenize.
        is_split - boolean to track whether splitting has to be done
                   or not. If it has to be done provide sentences as
                   single strings.

    Returns:
        sent_list with expanded contractions.
    """
    tuple_list = utils.conv_2_word_pos(stanford_model,
                                       sent_list,
                                       is_split=is_split)

    with open("contractions.yaml", "r") as stream:
        contractions = yaml.load(stream)

    for i, sent in enumerate(tuple_list):
        # look at all the sentences in the list
        for j, word_pos_tuple in enumerate(sent):
            word = word_pos_tuple[0]
            pos = word_pos_tuple[1]
            # check that it is a contraction
            # an example of this would be "'m"
            if word[0] == "'":
                # if it is a contraction we need to combine all the
                # contractions. Since our dictionary knows "I'm" and not
                # "'m".
                # Else just do nothing.
                if sent[j+1][0][0] == "'":
                    # if the next word is also a contraction combine all
                    # three, three is the maximum possible.
                    word = ''.join([sent[j-1][0], sent[j][0],
                                    sent[j+1][0]])
                else:
                    # otherwise join only two words
                    word = ''.join([sent[j-1][0], sent[j][0]])

                if pos != 'POS':  # for possessive
                    if word.lower() in contractions:
                        # split the string to be inserted up
                        replace = contractions[word.lower()][0]
                        replace = nltk.word_tokenize(replace)
                        # we need to check whether the first letter is
                        # upper case for the replacement.
                        if word[0].isupper():
                            replace[0] = replace[0].capitalize()
                    elif word in contractions:
                        # split the string to be inserted up
                        replace = contractions[word][0]
                        replace = nltk.word_tokenize(replace)
                    else:
                        replace = None

                    # replace the word part in the word_pos_tuples with
                    # the expanded word.
                    if len(replace) == 2:
                        tuple_list[i][j-1] = (replace[0],
                                              tuple_list[i][j-1][1])
                        tuple_list[i][j] = (replace[1],
                                            tuple_list[i][j][1])

                    elif len(replace) == 3:
                        tuple_list[i][j-1] = (replace[0],
                                              tuple_list[i][j-1][1])
                        tuple_list[i][j] = (replace[1],
                                            tuple_list[i][j][1])
                        tuple_list[i][j+1] = (replace[2],
                                              tuple_list[i][j+1][1])
                    elif replace is None:
                        pass
                    else:
                        raise RuntimeError("This should never happen.")
    return tuple_list


if __name__ == '__main__':
    TEST_CASES = [
        "I'm a bad person",  # 'm -> am
        "It's not what you think",  # 's -> is
        "It's his cat anyway",  # 's -> is
        "It's a man's world",  # 's -> is and 's possessive
        "Catherine's been thinking about it",  # 's -> has
        "It'll be done",  # 'll -> will
        "Who'd've thought!",  # 'd -> would, 've -> have
        "She said she'd go.",  # she'd -> she would
        "She said she'd gone.",  # she'd -> had
        ]
    # use nltk to split the strings into words
    MODEL = utils.load_stanford_pos()
    # get the list oif pos_tags
    EXPANDED_LIST = expand_contractions(MODEL, TEST_CASES, is_split=False)
    for SENT in EXPANDED_LIST:
        print(SENT)
