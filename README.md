This is the expander module with it's main feature the function
`expand_contractions` in `expand.py`. It uses an object of the
`StanfordPOSTagger` class from `nltk` to POS-tag input sentences and
decide accordingly which expansion to use.

To be able to run the code you need to download a Stanford POS-tagger
model. You can download the basic english tagger on the official
homepage at `https://nlp.stanford.edu/software/tagger.shtml`. Extract
the zip-file into the subdirectory `stanford_models` of this module.
Alternatively you can supply the path to the model in the call to
`load_stanford_pos`.

To see example output run `expand.py` directly using `python expand.py`.
You can supply your own directory to the call of `load_stanford_pos`
here. In this you can also see how to use this module.

There are a few assumptions being made about the input english language
to do these expansions:
    - Apostrophes in the middle of a lexical item (i.e. *usually*
          sequences of characters surrounded by spaces and/or delimited 
          by punctuation) are signs for contraction and will be dealt
          with as such.
    - The input sentence is grammatically correct.

Notable drawbacks are:
    - The nature of using POS-taggers is of course, that they are
          not perfect. The best is being done to make correct
          expansions, but errors will happen. Especially since
          expansions are not unambiguous.

Remaining TODOS:
    - Disambiguate replacements where the list has multiple elements!
    - Is it possible to replace only using the contraction part and not
      the part in front of that? In an attempt to handle names.
    - Include a test case when this is run as __main__, correctly
      asserting that the right results come out.
