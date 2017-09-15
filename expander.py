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


def _extract_contractions(sent):
    """
    Based on the POS-tags and the existence of an apostrophe or not,
    extract the existing contractions.

    Args:
        sent - a single sentence split up into (word, pos) tuples.
    Returns:
        List with the indices in the sentence where the contraction
        starts.
        Or None if no contractions are in the sentence.
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


def _extract_replacements(idx_lst, sent, contractions):
    """
    Based on the idx_lst and the contractions dictionary, give a list of
    replacements which shall be performed on the words in sent.

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
        Examples are:
            ([0,1], ["I", "'m"], ["I", "am"])
            ([0,1], ["She", "'s"], [["She", "is"], ["She", "has"]])
    """
    output = []
    for i, index in enumerate(idx_lst):
        # check whether the next word also starts with an apostrophe,
        # an example for this is "Who'd've"
        triple = False  # flag for keeping track of triple contraction
        if i+1 < len(idx_lst) and idx_lst[i+1] == idx_lst[i]+1:
            tmp = ''.join([sent[index-1][0],
                           sent[index][0],
                           sent[index+1][0]])
            triple = True
        # check whether the previous word was already a contraction, in
        # that case the previous loop iteration should have taken care
        # of it, so just continue.
        elif i > 0 and idx_lst[i-1] == idx_lst[i]-1:
            continue
        # else it is just a single apostrophe contraction, so just join
        # the current with the previous word, e.g.
        #       ["I", "'m"] -> "I'm"
        else:
            tmp = ''.join([sent[index-1][0],
                           sent[index][0]])

        # if the contracted string is one of the known contractions,
        # extract the suggested expansions.
        # Note that however many expansions there are tmp2 is a list!
        if tmp in contractions:
            tmp2 = contractions[tmp]
        # the dictionary only contains non-capitalized replacements,
        # check for capitalization
        elif tmp.lower() in contractions:
            if tmp[0].isupper():
                # capitalize the replacement in this case
                tmp2 = [a.capitalize() for a in
                        contractions[tmp.lower()]]
        else:
            print("WARNING: Unknown replacement: ", tmp)

        # separate the phrases into their respective words again.
        tmp2 = [nltk.word_tokenize(a) for a in tmp2]
        if triple:
            tmp = [sent[index-1][0],
                   sent[index][0],
                   sent[index+1][0]]
            index_range = [index-1, index, index+1]
        else:
            tmp = [sent[index-1][0],
                   sent[index][0]]
            index_range = [index-1, index]
        output.append((index_range, tmp, tmp2))
    return output


def _remove_pos_tags(sent):
    """
    Convert a list of (word, pos) tuples back to a list of only words.

    Args:
        sent - list of (word, pos) tuples
    Returns:
        A list of only lexical items.
    """
    output = []
    for word_pos in sent:
        output.append(word_pos[0])
    return output


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

        # evaluate the needed replacements
        replacement_lst = _extract_replacements(idx_lst,
                                                sent,
                                                contractions)
        for rplc_tuple in replacement_lst:
            # if the replacement is unambiguous, do it.
            if len(rplc_tuple[2]) == 1:
                tmp = _remove_pos_tags(sent)
                for i, index in enumerate(rplc_tuple[0]):
                    tmp[index] = rplc_tuple[2][0][i]
                output.append(tmp)
            else:
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
        ]
    # use nltk to split the strings into words
    MODEL = utils.load_stanford_pos()
    # get the list oif pos_tags
    EXPANDED_LIST = expand_contractions(MODEL, TEST_CASES, is_split=False)
    for SENT in EXPANDED_LIST:
        print(SENT)
