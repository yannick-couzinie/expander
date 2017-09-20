#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" General utilities file """

__author__ = "Yannick Couzinié"


# standard library imports
import glob
import os
# third party library imports
import nltk


def load_stanford(model,
                  model_name=None,
                  dirname=None):
    """
    Args:
        model - either "pos" or "ner" for pos-tagging or named entity
                recognition.
        model_name - Name of the model to be used, if none is supplied,
                     the recommended standard is loaded.
        dirname - Directory name where the model is located, if none is
                  supplied it is assumed to be in ./stanford_models.
    Returns:
        An object of Stanford(POS/NER)Tagger
    Raises:
        LookupError if the model is not found.

    Load the Stanford module specified by model.
    For this you have to download the model from:

        https://nlp.stanford.edu/software/stanford-postagger-2017-06-09.zip
        https://nlp.stanford.edu/software/stanford-ner-2017-06-09.zip

    respectively and unzip the containers into the stanford_model
    sub-directory of this model or alternatively in the specified
    dirname.
    """
    if model == 'pos':
        sub_dir = "models"
        jar_name = "stanford-postagger.jar"
        if model_name is None:
            model_name = "english-bidirectional-distsim.tagger"
    elif model == 'ner':
        sub_dir = "classifiers"
        jar_name = "stanford-ner.jar"
        # the model name can be adapted to use the 4class or 7class
        # model for recognition. The 3 class model has been deemed the
        # most stable one for now.
        if model_name is None:
            model_name = "english.all.3class.distsim.crf.ser.gz"
    else:
        raise ValueError("Illegal model name in call to load_stanford(), "
                         "use 'pos' or 'ner'.")

    if dirname is None:
        # set model dir to ./asset/models
        current_dir = os.path.dirname(os.path.realpath(__file__))
        model_dir = os.path.join(current_dir, "stanford_models")
    else:
        model_dir = dirname
    # glob for the class recursively in model_dir
    glob_dir = os.path.join(model_dir,
                            "**",
                            jar_name)
    classes = glob.glob(glob_dir,
                        recursive=True)

    if len(classes) > 1:
        # only have one stanford postagger version at any time
        raise LookupError("Multiple {} versions found, please only have one"
                          " version downloaded at any time.".format(model))
    # point model_dir to the models directory in the stanford pos
    # directory
    model_dir = os.path.dirname(classes[0])
    model_dir = os.path.join(model_dir, sub_dir)

    if not os.path.exists(model_dir):
        raise LookupError("The model directory could not be found.")
    # set the environment variables so that nltk can find the models
    os.environ["CLASSPATH"] = classes[0]
    os.environ["STANFORD_MODELS"] = model_dir

    # load the model
    if model == 'pos':
        stanford_model = nltk.tag.StanfordPOSTagger(model_name)
    elif model == 'ner':
        stanford_model = nltk.tag.StanfordNERTagger(model_name)
    return stanford_model


def conv_2_word_pos(stanford_model, sent_list, is_split):
    """
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

    Converts a sentence list to a list of lists, where the lists contain
    (word, pos_tag) tuples using the provided stanford_model.
    """
    output = []
    if not is_split:
        for sent in sent_list:
            tmp = nltk.word_tokenize(sent)
            for i, word in enumerate(tmp):
                j = 0
                # This while loop breaks once there is no apostrophe
                # left anymore.
                while "'" in word[1:-1]:
                    tmp2 = []
                    # search for ' in the middle of the word indicating
                    # that the splitting is not correct. An example is:
                    #   Who'd've -> Who'd, 've
                    # so we need to check and split up further.
                    tmp2 = tmp[:i+j]
                    # if this is not the first apostrophe, take care to
                    # add the apostrophe again
                    if j:
                        tmp2.append("'" + word.split("'", 1)[0])
                    else:
                        tmp2.append(word.split("'", 1)[0])
                    tmp2.append("'" + word.split("'", 1)[1])
                    word = word.split("'", 1)[1]
                    tmp2 += tmp[i+j+1:]
                    tmp = tmp2
                    j += 1
            output.append(tmp)
    else:
        output = sent_list
    output = [stanford_model.tag(e) for e in output]
    return output
