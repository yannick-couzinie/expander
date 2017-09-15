#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" General utilities file """

# standard library imports
import glob
import os
# third party library imports
import nltk


def load_stanford_pos(dirname=None,
                      model_name="english-bidirectional-distsim.tagger"):
    """
    Load the Stanford POS-tagging module. For this you have to download
    the model from:

        https://nlp.stanford.edu/software/stanford-postagger-2017-06-09.zip

    and make sure the file english-bidirectional-distsim.tagger is in
    the directory under dirname.
    Args:
        dirname - Directory name where the model is located, if none is
                  supplied it is assumed to be in ./stanford_models.
        model_name - Name of the model to be used, if none is supplied,
                     the standard stanford tagger is used.
    Returns:
        An object of StanfordPOSTagger, which can be used like
            st.tag('What is the airspeed of an unladen swallow ?'.split())
        to obtain an output
        [('What', 'WP'), ('is', 'VBZ'), ('the', 'DT'), ('airspeed', 'NN'),
         ('of', 'IN'), ('an', 'DT'), ('unladen', 'JJ'), ('swallow', 'VB'),
         ('?', '.')]
    Raises:
        LookupError if the model is not found.
    """
    if dirname is None:
        # set model dir to ./asset/models
        current_dir = os.path.dirname(os.path.realpath(__file__))
        model_dir = os.path.join(current_dir, "stanford_models")
    # glob for the class recursively in model_dir
    glob_dir = os.path.join(model_dir,
                            "**",
                            "stanford-postagger.jar")
    classes = glob.glob(glob_dir,
                        recursive=True)

    if len(classes) > 1:
        # only have one stanford postagger version at any time
        raise LookupError("Multiple PosTaggers found, please only have"
                          " one version downloaded at any time.")
    # point model_dir to the models directory in the stanford pos
    # directory
    model_dir = os.path.dirname(classes[0])
    model_dir = os.path.join(model_dir, "models")

    if not os.path.exists(model_dir):
        raise LookupError("The directory /asset/models/ does not"
                          " exist, make sure you create it and place"
                          " file english-bidirectional-distsim.tagger"
                          " in it. Alternatively, supply the directory"
                          " to loadStanfordPos() in which it is located.")
    # set the environment variables so that nltk can find the models
    os.environ["CLASSPATH"] = classes[0]
    os.environ["STANFORD_MODELS"] = model_dir

    # load the model
    stanford_model = nltk.tag.StanfordPOSTagger(model_name)
    return stanford_model


def conv_2_word_pos(stanford_model, sent_list, is_split):
    """
    Converts a sentence list to a list of lists, where the lists contain
    (word, pos_tag) tuples using the provided stanford_model.

    Args:
        stanford_model - object of StanfordPOSTagger, as returned by
                         load_stanford_pos.
        sent_list - List with sentences split up into list of singular words
                    e.g. [["I", "am", "sentence", "one"],
                          ["I", "am", "sentence", "two"]]
        is_split - if False then the input should be
                         ["I am sentence one",
                          "I am sentence two"]

    Returns:
           output - the same list of sentences, with each word replaced by
                     a (word, tag) tuple.
    """
    output = []
    if not is_split:
        for sent in sent_list:
            output.append(nltk.word_tokenize(sent))
    else:
        output = sent_list
    output = [stanford_model.tag(e) for e in output]
    return output
