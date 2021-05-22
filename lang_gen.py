import coretools as rpgtools
import random
import table_process
import spacy.util
import sys

# TODO: Numbers and base system

VERBOSE = False

if not spacy.util.is_package('en_core_web_sm'):
    print('Downloading spaCy language model for POS tagger.',
          file=sys.stderr)
    import spacy.cli.download
    spacy.cli.download('en_core_web_sm')

import copy
import subject_verb_object_extract


def vbprint(*args):
    if VERBOSE:
        print(*args)


class Language:
    def __init__(self, word_generator, dictionary, sentence_order, existing_words, tenses):
        self.word_generator = word_generator
        self.dictionary = dictionary
        self.sentence_order = sentence_order.split()
        self.existing_words = existing_words
        self.tenses = tenses

    def make_new_word(self, definition, combine=False):
        definition = definition.lower()
        if not combine:
            exhaustion = 0
            while True:
                c = self.word_generator.table_fetch('word')
                if c not in self.existing_words:
                    self.existing_words.append(c)
                    self.dictionary[definition] = c
                    break
                if exhaustion > 30:  # Create "portmanteau" words when prior word combinations have been exhausted
                    c = self.word_generator.table_fetch('word')+self.word_generator.table_fetch('V')+self.word_generator.table_fetch('word')
                    if c not in self.existing_words:
                        self.existing_words.append(c)
                        self.dictionary[definition] = c
                        break
                exhaustion += 1
            return c
        else:  # Combine multiple words into portmanteau if using multi word definition
            c = ''
            definition = definition.split()
            for word in definition:
                try:
                    c += self.dictionary[word]
                except KeyError:
                    self.make_new_word(word)
            return c

    def get_word(self, word, mode='complex'):
        if mode == 'complex':
            word = self.process_word(word)
            finished_word = []
            for subword in word:
                raw_word = subword.lemma_
                tense = None
                vbprint('Attempting to translate:', subword)
                if subword.is_punct:
                    vbprint('Is punctuation, skipped')
                    finished_word.append(raw_word)
                    continue
                for data in str(subword.morph).split('|'):
                    if data.startswith('Tense'):
                        tense = data.split('=')[1]
                        vbprint(f'Tense detected: {tense}')
                try:
                    vbprint(self.dictionary[raw_word])
                    target = self.dictionary[raw_word]
                except KeyError:
                    vbprint('Making new word')
                    target = self.make_new_word(raw_word)
                vbprint('Raw translation result:', target)
                # Apply tense transformation if applicable
                if tense:
                    target = self.apply_tense(target, tense)
                    vbprint('Applied tense, became:', target)
                finished_word.append(target)
            return ' '.join(finished_word)
        elif mode == 'simple':
            word = word.lower()
            vbprint('Attempting to translate: ', word)
            try:
                vbprint(self.dictionary[word])
                return self.dictionary[word]
            except KeyError:
                vbprint('Making new word')
                return self.make_new_word(word)

    def expand_phrase(self, sentence):
        new_sentence = copy.deepcopy(self.sentence_order)
        vbprint(new_sentence)
        for group in sentence.keys():
            translated_group = []
            for word in sentence[group]:
                translated_group.append(self.get_word(word))
            for raw_group in new_sentence:
                if raw_group == group and translated_group:
                    new_sentence[new_sentence.index(raw_group)] = ' '.join(translated_group)
                    vbprint(new_sentence)
        # Checking for unused groups
        for group in new_sentence:
            if group in self.sentence_order:
                new_sentence.remove(group)
        return ' '.join(new_sentence)

    def clever_translate(self, target_phrase):
        tok = subject_verb_object_extract.nlp(target_phrase)
        svos = subject_verb_object_extract.findSVOs(tok)
        vbprint(svos)
        final_sentence = []
        words_used_up = []
        if svos:
            for phrase in svos:
                for word in phrase:
                    words_used_up += word.lower().split()
                ctree = {'(S)': '', '(V)': '', '(O)': ''}
                try:
                    # Try and construct svo tree
                    ctree['(S)'] = phrase[0].split()
                    ctree['(V)'] = phrase[1].split()
                    ctree['(O)'] = phrase[2].split()
                except IndexError:
                    pass
                partial_translation_result = self.expand_phrase(ctree)
                final_sentence.append(partial_translation_result)
        else:
            # If no subject verb objects found, just brute force translate the whole thing
            return self.brute_force_translate(target_phrase)
        # If there are unused words add them as riders to the end
        additions = []
        for word in target_phrase.split():
            if word.lower() not in words_used_up:
                additions.append(word)
        final_sentence = ' '.join(final_sentence)
        final_sentence += ' '+self.brute_force_translate(' '.join(additions))
        return final_sentence

    def brute_force_translate(self, phrase):
        new_phrase = []
        for word in phrase.split():
            new_phrase.append(self.get_word(word))
        return ' '.join(new_phrase)

    def process_word(self, word):
        return subject_verb_object_extract.nlp(word)

    def apply_tense(self, word, tense):
        try:
            transformation = self.tenses[tense]
            vbprint('Transformation type is:', transformation)
            # (W) = Word before (Add the tense word before the actual word)
            if transformation == '(W)':
                return self.get_word(tense, mode='simple')+' '+word
            # (W) = Word rider after (Add the tense word after the actual word)
            elif transformation == '(R)':
                return word+' '+self.get_word(tense, mode='simple')
            # (P) = Word prefix (Add the tense word to the actual word)
            elif transformation == '(P)':
                return self.get_word(tense, mode='simple')+word
            # (P) = Word suffix (Add the tense word to the actual word)
            elif transformation == '(S)':
                return word+self.get_word(tense, mode='simple')

        except KeyError:
            # If no transformation for that tense can be found simply return the word
            vbprint(f'No transformation for {tense} tense found')
            return word


def make_word_struct(ruleset, init_state='v'):
    curr_state = init_state
    for _ in range(max(rpgtools.roll(f'2d2-1'), 1)):
        for rule in ruleset:
            if rule in curr_state:
                curr_state = curr_state.replace(rule, random.choice(ruleset[rule]), 1)
    return curr_state


def make_wordgen(raw_lang_data, rules):
    word_gen = {'word': [], 'V': [], 'C': []}
    for _ in range(6):
        word_gen['word'].append(make_word_struct(rules).replace('v', '[@V]').replace('c', '[@C]'))
    word_gen['V'] += raw_lang_data.table_fetch('V', rpgtools.roll('2d3'), repeat=False, concat=False)
    word_gen['C'] += raw_lang_data.table_fetch('C', rpgtools.roll('6d6'), concat=False)
    word_gen = table_process.Table(init_data=word_gen)
    return word_gen


def make_language(base_words, raw_lang_data):
    syllable_rules = {'v': raw_lang_data.data['v'], 'c': raw_lang_data.data['c']}
    tenses = {'Past': raw_lang_data.table_fetch('TenseTransformations'),
              'Future': raw_lang_data.table_fetch('TenseTransformations')}
    wordList = table_process.Table(base_words)
    dictionary = {}
    existing_words = []
    myWordGen = make_wordgen(raw_lang_data, syllable_rules)
    for char in ['n', 'v', 'a', 'p']:  # Nouns Verbs Adjectives Pronouns
        candidates = wordList.data[char]
        for cand in candidates:
            while True:
                c = myWordGen.table_fetch('word')
                if c not in existing_words:
                    existing_words.append(c)
                    break
            dictionary[cand.lower()] = c
    sentence_order = raw_lang_data.table_fetch('SentenceOrder')
    return Language(myWordGen, dictionary, sentence_order, existing_words, tenses)


if __name__ == '__main__':
    NewLang = make_language('text/common_words.txt', table_process.Table('text/lang_struct.txt'))
    while True:
        src = input()
        print(NewLang.clever_translate(src))
