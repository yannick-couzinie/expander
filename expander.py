#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Module for expanding contractions in english text. """

__author__ = "Yannick Couzinié"

# standard library imports
import itertools
import operator
import yaml
# third party library imports
import nltk
# local imports
import utils


def _extract_contractions(sent):
    """
    Args:
        sent - a single sentence split up into (word, pos) tuples.
    Returns:
        List with the indices in the sentence where the contraction
        starts.
        Or None if no contractions are in the sentence.

    Based on the POS-tags and the existence of an apostrophe or not,
    extract the existing contractions.
    """
    idx_lst = []
    for i, word_pos in enumerate(sent):
        # If the word in the word_pos tuple begins with an apostrophe,
        # add the index to idx_list.
        if word_pos[0][0] == "'":
            if word_pos[1] != 'POS':
                # a case we can immediately dismiss is possessive
                # pronouns like "Peter's house", in which the apostrophe
                # denotes possession and not contraction.
                idx_lst.append(i)
    if idx_lst:
        # empty list is false so use that, otherwise give no return.
        return idx_lst


def _consecutive_sub_list(int_list):
    """
    Args:
        - int_list is a list whose consecutive sub-lists are yielded
          from this function.
    Yields:
        - The consecutive sub-lists

    This is basically an adaptation from
    https://docs.python.org/2.6/library/itertools.html#examples for
    Python 3.
    """
    # we group the items by using the lambda-function for the key which
    # checks whether the next element and the current element is one
    # apart. If it it is exactly one, the list of items that are 1 apart
    # are grouped.
    # The map with the itemgetter then maps the grouping to the actual
    # items and then we yield the sublists.
    for _, index in itertools.groupby(enumerate(int_list),
                                      lambda x: x[1]-x[0]):
        yield list(map(operator.itemgetter(1), index))


def _extract_replacements(idx_lst, sent, contractions):
    """
    Args:
        idx_lst - The list of indices for the position of contractions
                  in sent.
        sent - List of (word, pos) tuples.
        contractions - dictionary of contractions in the form of:
                            'contracted string' : 'list of possible
                                                   replacements'
    Returns:
        A list in the form of (tuples of (index of words to be replaced,
                                          word to be replaced,
                                          list of suggested replacements))
        Examples are: ([0,1], ["I", "'m"], ["I", "am"])
            ([0,1], ["She", "'s"], [["She", "is"], ["She", "has"]])

    Based on the idx_lst and the contractions dictionary, give a list of
    replacements which shall be performed on the words in sent.
    """
    # loop over all the consecutive parts
    for consecutive in _consecutive_sub_list(idx_lst):
        # add the one index prior to the first one for easier
        # replacements
        consecutive = [consecutive[0]-1] + consecutive
        # combine all the words that are expanded, i.e. one word
        # before the first apostrophe until the last one with an
        # apostrophe
        contr = [word_pos[0] for word_pos
                 in sent[consecutive[0]:consecutive[-1]+1]]
        # if the expanded string is one of the known contractions,
        # extract the suggested expansions.
        # Note that however many expansions there are, expanded is a list!
        if ''.join(contr) in contractions:
            expanded = contractions[''.join(contr)]
        # the dictionary only contains non-capitalized replacements,
        # check for capitalization
        elif ''.join(contr).lower() in contractions:
            if ''.join(contr)[0].isupper():
                # capitalize the replacement in this case
                expanded = [a.capitalize() for a in
                            contractions[''.join(contr).lower()]]
        else:
            # if the replacement is unknown skip to the next one
            print("WARNING: Unknown replacement: ", ''.join(contr))
            continue

        # separate the phrases into their respective words again.
        expanded = [nltk.word_tokenize(a) for a in expanded]
        yield (consecutive, contr, expanded)


def _remove_pos_tags(sent):
    """
    Args:
        sent - list of (word, pos) tuples
    Returns:
        A list of only lexical items.

    Convert a list of (word, pos) tuples back to a list of only words.
    """
    output = []
    for word_pos in sent:
        output.append(word_pos[0])
    return output


def expand_contractions(stanford_model, sent_list, is_split=True):
    """
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
    """
    tuple_list = utils.conv_2_word_pos(stanford_model,
                                       sent_list,
                                       is_split=is_split)

    with open("contractions.yaml", "r") as stream:
        # load the dictionary containing all the contractions
        contractions = yaml.load(stream)

    output = []
    # look at all the sentences in the list
    for sent in tuple_list:
        # get all the indices of the contractions
        idx_lst = _extract_contractions(sent)

        if idx_lst is None:
            # if there are no contractions, continue
            output.append(_remove_pos_tags(sent))
            continue

        # evaluate the needed replacements, and loop over them
        for rplc_tuple in _extract_replacements(idx_lst,
                                                sent,
                                                contractions):

            # if the replacement is unambiguous, do it.
            if len(rplc_tuple[2]) == 1:
                tmp = _remove_pos_tags(sent)
                for i, index in enumerate(rplc_tuple[0]):
                    tmp[index] = rplc_tuple[2][0][i]
                output.append(tmp)
            else:
                # else deal with the ambiguos case
                output.append(["AMBIGUOUS"] + _remove_pos_tags(sent))

    if not is_split:
        # join the sentences if they were joined in the beginning
        output = [' '.join(sent) for sent in output]
        # remove the space in front of the apostrophe, if it survived
        # the apostrophe cleansing.
        output = [sent.replace(" '", "'") for sent in output]
    return output


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
        "Y'all'd've a great time"  # wouldn't it be so cold!"
        # Y'all'd've -> You all would have, wouldn't -> would not
        ]
    # use nltk to split the strings into words
    MODEL = utils.load_stanford(model='pos')
    # get the list oif pos_tags
    EXPANDED_LIST = expand_contractions(MODEL, TEST_CASES, is_split=False)
    for SENT in EXPANDED_LIST:
        print(SENT)
