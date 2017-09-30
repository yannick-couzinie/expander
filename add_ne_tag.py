"""
Short module that should be run in case you didn't run disambiguate.py
with NER on but still want to use the NER tags. It will use all entries
that begin with he, she or it and replace the it with <NE> and then write
the new dictionary disambiguations_with_ner.yaml.

Note: This will delete the original yaml file.
"""


import yaml

with open("disambiguations.yaml", "r") as stream:
    INP_DICT = yaml.load(stream)

OUT_DICT = INP_DICT.copy()
for key, value in INP_DICT.items():
    if key[0][0] == 'he' or key[0][0] == 'she' or key[0][0] == 'it':
        preposition = key[0][0]
        # this is a bad work-around to get the tuple to actually be a
        # single element as a tuple and not automatically converted to a
        # list.
        new_key = ['placeholder']
        new_key[0] = ("<NE>", key[0][1])
        new_key += key[1:]
        new_key = tuple(new_key)

        OUT_DICT[new_key] = {subkey.replace(preposition, '<NE>'): subvalue
                             for subkey, subvalue in value.items()}

with open("disambiguations.yaml", "w") as stream:
    yaml.dump(OUT_DICT, stream)
