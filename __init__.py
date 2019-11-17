import re
from cudatext import *
import cudax_lib as appx

# '-' here is none-lexer
option_lexers = '-,ini files,markdown,restructuredtext,properties'
option_min_len = 3
option_case_sens = False
prefix = 'word'
nonwords = ''

def isword(s):

    return s not in ' \t'+nonwords


def is_text_with_begin(s, begin):

    if option_case_sens:
        return s.startswith(begin)
    else:
        return s.upper().startswith(begin.upper())


def get_words_list():

    text = ed.get_text_all()
    pattern = '[ \t\n'+re.escape(nonwords)+']+'
    l = re.split(pattern, text)
    l = [s for s in l if len(s)>=option_min_len]

    if not l: return
    l = sorted(list(set(l)))
    return l


def get_word(x, y):

    if not 0<=y<ed.get_line_count():
        return
    s = ed.get_text_line(y)
    if not 0<x<=len(s):
        return

    x0 = x
    while (x0>0) and isword(s[x0-1]):
        x0-=1
    text1 = s[x0:x]

    x0 = x
    while (x0<len(s)) and isword(s[x0]):
        x0+=1
    text2 = s[x:x0]

    return (text1, text2)


class Command:

    def on_complete(self, ed_self):

        carets = ed.get_carets()
        if len(carets)!=1: return
        x0, y0, x1, y1 = carets[0]
        if y1>=0: return #don't allow selection

        lex = ed.get_prop(PROP_LEXER_FILE, '')
        if lex is None: return
        if lex=='': lex='-'
        allow = ','+lex.lower()+',' in ','+option_lexers.lower()+','
        if not allow: return

        global nonwords
        nonwords = appx.get_opt('nonword_chars',
          '''-+*=/\()[]{}<>"'.,:;~?!@#$%^&|`…''',
          appx.CONFIG_LEV_ALL)

        words = get_words_list()
        if not words: return
        word = get_word(x0, y0)
        if not word: return
        word1, word2 = word

        words = [prefix+'|'+w for w in words
                 if is_text_with_begin(w, word1)
                 and w!=word1
                 and w!=(word1+word2)
                 ]
        #print('word:', word)
        #print('list:', words)

        ed.complete('\n'.join(words), len(word1), len(word2))
        return True
