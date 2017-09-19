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


def _find_sub_list(sublist, full_list):
    """
    Args:
        - sublist is a list of words that are supposed to be found in
          the full list.
        - full list is a list of words that is supposed to be searched
          in.
    Returns:
        - List of tuples with the form
            (first_index_of_occurence, last_index_of_occurence)

    This function finds all occurences of sublist in the full_list.
    """
    # this is the output list
    results = []
    sublist_len = len(sublist)
    # loop over all ind if the word in full_list[ind] matches the first
    # word of the sublist
    for ind in (i for i, word in enumerate(full_list)
                if word == sublist[0]):
        # check that the complete sublist is matched
        if full_list[ind:ind+sublist_len] == sublist:
            # then append this to the results
            results.append((ind, ind+sublist_len-1))
    return results


def _contract_sentences(expansions, sent_lst):
    """
    Args:
        - expansions is a dictionary containing  the corresponding
          contractions to the expanded words
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
    # first find the indices of the sentences that contain contractions
    contains_contractibles = []
    key_list = list(expansions.keys())
    for i, sent in enumerate(sent_lst):
        # check whether any expansion is present then add the index
        # it has a True for every expansion that is present
        expansion_bool = [expansion in ' '.join(sent) for expansion
                          in key_list]
        if any(expansion_bool):
            # convert the boolean list to a list of indices
            expansion_idx = [i for i, boolean in enumerate(expansion_bool)
                             if boolean]
            # add the index of the relevant sentences together with the
            # indices for the relevant replacements to the
            # contains_contractibles list
            contains_contractibles.append([i, expansion_idx])

    for i, expansion_idx in contains_contractibles:
        # the sentence to be evaluated
        sent = sent_lst[i]
        # the list of relevant expansions for the sentence as found
        # earlier
        relevant_exp = [key_list[i] for i in expansion_idx]
        for expansion in relevant_exp:
            # first split the contraction up into a list of the same
            # length as the expanded string
            if len(expansion.split()) in [2, 3]:
                # if you contract three or two words,
                # just split at apostrophes
                contraction = expansions[expansion].split("'")
                assert len(contraction) == len(expansion.split())
                # add the apostrophes again
                contraction[1] = "'" + contraction[1]
                if len(contraction) == 3:
                    contraction[2] = "'" + contraction[2]
            else:
                # this case is only entered when there is only one word
                # input. So assert that this is the case.
                assert len(expansion) == 1
                # this is a completely pathological case, since
                # ambiguous 1-word replacements are not in the common
                # list of replacements from wikipedia. But since one can
                # openly expand contractions.yaml it is checked.
                contraction = expansions[expansion]
            # find where the sublist occurs
            occurences = _find_sub_list(expansion.split(), sent)
            # loop over all first indices of occurences
            for occurence in occurences:
                first_index = occurence[0]
                contr_sent = sent[:first_index] + contraction
                contr_sent += sent[first_index+len(contraction):]
                yield (first_index,
                       sent[first_index:first_index+len(contraction)],
                       contr_sent)


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
    with open("contractions.yaml", "r") as stream:
        # load the dictionary containing all the contractions
        contractions = yaml.load(stream)

    # invert the dictionary for quicker finding of contractions
    expansions = dict()
    for key, value in contractions.items():
        if len(value) == 1:
            continue
        for expansion in value:
            if expansion in expansions:
                print("WARNING: As an expansion to {}, {} is replaced with"
                      " {}.".format(expansion,
                                    expansions[expansion],
                                    key))
            expansions[expansion] = key

    output_dict = dict()
    model = utils.load_stanford("pos")
    ambiguity_counter = 0
    for tuple_rslt in _contract_sentences(expansions, sent_lst):
        # pos tag the sentence
        pos_sent = model.tag(tuple_rslt[2])
        # extract the pos tags on the contracted part
        contr_pos = tuple(pos_sent[tuple_rslt[0]:(tuple_rslt[0] +
                                                  len(tuple_rslt[1]))])
        # write a dictionary entry connecting the (words, pos) of the
        # contraction to the expanded part
        word = ' '.join(tuple_rslt[1])
        if contr_pos not in output_dict:
            output_dict[contr_pos] = dict()
            output_dict[contr_pos][word] = 1
            # keep track of the progress
            print("\n\n ---- \n\n")
            pprint.pprint(output_dict)
            print("Ambiguity counter is {}.".format(ambiguity_counter))
            print("\n\n ---- \n\n")
        elif word in output_dict[contr_pos].keys():
            # check whether the entry is already there
            output_dict[contr_pos][word] += 1
            continue
        else:
            # if the combination of pos tags with words already occured
            # once then a list has to be made. Ideally this case doesn't
            # occur
            ambiguity_counter += 1
            output_dict[contr_pos][word] = 1
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
