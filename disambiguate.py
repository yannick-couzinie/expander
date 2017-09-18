#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains the necessary functions to load  a text-corpus from
NLTK, contract all possible sentences, applying POS-tags to the
contracted sentences and compare that with the original text.
The information about which contraction+pos-tag pair gets expanded to
which full form will be saved in a dictionary for use in expander.py
"""

__author__ = "Yannick Couzinié"

# standard library imports
import pprint
import yaml
# third-party library imports
import nltk
# local library imports
import utils


def _check_ambiguous_contractions(expanded_words):
    """
    Args:
        - expanded_words is a list of 1, 2 or 3 words which is checked for
          existing contractions.
    Returns:
        - either the contraction if there is one, or None.

    Use the contractions.yaml to check whether therer are ambiguous
    contractions to make in the provided words.
    Only ambiguous ones are checked since the non-ambiguous once should
    not be handled with POS-tags but directly.
    """
    with open("contractions.yaml", "r") as stream:
        # load the dictionary containing all the contractions
        contractions = yaml.load(stream)

    for key, value in contractions.items():
        if len(value) == 1:
            # ignore the non-ambiguous case
            continue
        elif expanded_words in value:
            # else check whether the words are an expansoin
            # and if they are return the contraction split up into
            # single words
            if len(expanded_words.split()) in [2, 3]:
                # if you contract three or two words,
                # just split at apostrophes
                tmp = key.split("'")
                assert len(tmp) == len(expanded_words.split())
                # add the apostrophes again
                tmp[1] = "'" + tmp[1]
                if len(tmp) == 3:
                    tmp[2] = "'" + tmp[2]
            else:
                # this case is only entered when there is only one word
                # input. So assert that this is the case.
                assert len(expanded_words) == 1
                # this is a completely pathological case, since
                # ambiguous 1-word replacements are not in the common
                # list of replacements from wikipedia. But since one can
                # openly expand contractions.yaml it is checked.
                tmp = key
            return tmp
    return None


def _contract_sentences(sent_lst):
    """
    Args:
        - sent_lst is a list of sentences, which is itself a list of
          words, i.e. [["I", "am", "blue"], [...]].
    Returns:
        - yields tuples of the form
              (index of first word that was replaced,
              list of words that were replaced,
              contracted sentence).
          The above example would then give
              (0, ["I", "am"], ["I", "'m", "blue"])
          Note that uncontractible sentences are not added to the
          output.
          Since yield is used, iterate over the results. Otherwise it
          takes too much time.

    This function checks a list of sentences for whether they can be
    contracted. It starts with the first two words, then the first three
    and then goes on to the second+third, then the second+third+fourth
    and so on.
    """
    for sent in sent_lst:
        for j, word in enumerate(sent):
            # join the relevant three words
            try:
                check_word = ' '.join([word, sent[j+1], sent[j+2]])
            except IndexError:
                # this happens if we are amongst the last two words
                check_word = None
            # check whether they are in the dictionary
            contraction = _check_ambiguous_contractions(check_word)
            if contraction is None:
                # check for two words in three words didn't give
                # anything
                try:
                    check_word = ' '.join([word, sent[j+1]])
                except IndexError:
                    # if word is the last word
                    check_word = None
                contraction = _check_ambiguous_contractions(check_word)
            if contraction is None:
                # and lastly the one word case
                check_word = word
                contraction = _check_ambiguous_contractions(check_word)
            if contraction is None:
                # if it is still None there are no contractions to be
                # done.
                continue
            contr_sent = sent[:j] + contraction
            contr_sent += sent[j+len(contraction):]
            yield (j, sent[j:j+len(contraction)], contr_sent)


def write_dictionary(sent_lst):
    """
    Args:
        - sent-lst a list of sentences which themselves are lists of the
          single words.
    Returns:
        - None, but writes a disambiguations.yaml file with disambiguations
          for the ambiguous contractions in contractions.yaml.

    Using the provided list of sentences, contract them and pos-tag them.
    Using the pos-tags it is then possible to classify which
    (contraction, pos-tag) combinations get expanded to which ambiguous
    long form.
    """
    output_dict = dict()
    model = utils.load_stanford("pos")
    ambiguity_counter = 0
    for tuple_rslt in _contract_sentences(sent_lst):
        # pos tag the sentence
        pos_sent = model.tag(tuple_rslt[2])
        # extract the pos tags on the contracted part
        contr_pos = tuple(pos_sent[tuple_rslt[0]:(tuple_rslt[0] +
                                                  len(tuple_rslt[1]))])
        # write a dictionary entry connecting the (words, pos) of the
        # contraction to the expanded part
        if contr_pos not in output_dict:
            output_dict[contr_pos] = [' '.join(tuple_rslt[1])]
            # keep track of the progress
            print("\n\n ---- \n\n")
            pprint.pprint(output_dict)
            print("Ambiguity counter is {}.".format(ambiguity_counter))
            print("\n\n ---- \n\n")
        elif ' '.join(tuple_rslt[1]) in output_dict[contr_pos]:
            # check whether the entry is already there
            continue
        else:
            # if the combination of pos tags with words already occured
            # once then a list has to be made. Ideally this case doesn't
            # occur
            ambiguity_counter += 1
            output_dict[contr_pos] += [' '.join(tuple_rslt[1])]
            print("\n\n ---- \n\n")
            print("AMBIGUITY ADDED!")
            pprint.pprint(output_dict)
            print("Ambiguity counter is {}.".format(ambiguity_counter))
            print("\n\n ---- \n\n")
    with open("disambiguations.yaml", "w") as stream:
        yaml.dump(output_dict, stream)


if __name__ == '__main__':
    # if you call this function directly just build the disambiguation
    # dictionary.
    SENT_LST = nltk.corpus.brown.sents()
    write_dictionary(SENT_LST)
