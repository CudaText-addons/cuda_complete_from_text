import os
from cudatext import *
import cudax_lib as appx

fn_config = os.path.join(app_path(APP_DIR_SETTINGS), 'plugins.ini')
section = 'complete_from_text'
prefix = 'text'
nonwords = ''

def bool_to_str(v): return '1' if v else '0'
def str_to_bool(s): return s=='1'

# '-' here is none-lexer
option_lexers = ini_read(fn_config, section, 'lexers', '-,ini files,markdown,restructuredtext,properties')
option_min_len = int(ini_read(fn_config, section, 'min_len', '3'))
option_case_sens = str_to_bool(ini_read(fn_config, section, 'case_sens', '1'))
option_no_cmt = str_to_bool(ini_read(fn_config, section, 'no_comments', '1'))
option_no_str = str_to_bool(ini_read(fn_config, section, 'no_strings', '1'))

def isword(s):

    return s not in ' \t'+nonwords


def is_text_with_begin(s, begin):

    if option_case_sens:
        return s.startswith(begin)
    else:
        return s.upper().startswith(begin.upper())


def get_words_list(ed):

    if option_no_cmt and option_no_str:
        ops = 'T6'
    elif option_no_cmt:
        ops = 'T4'
    elif option_no_str:
        ops = 'T5'
    else:
        ops = ''

    res = ed.action(EDACTION_FIND_ALL, 
        r'\b[a-z_]\w{' + str(option_min_len-1) + r',}\b',
        'r' + ops
        ) or []
    
    l = [ed.get_text_substr(*r) for r in res]

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

        words = get_words_list(ed_self)
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


    def config(self):
        
        ini_write(fn_config, section, 'lexers', option_lexers)
        ini_write(fn_config, section, 'min_len', str(option_min_len))
        ini_write(fn_config, section, 'case_sens', bool_to_str(option_case_sens))
        ini_write(fn_config, section, 'no_comments', bool_to_str(option_no_cmt))
        ini_write(fn_config, section, 'no_strings', bool_to_str(option_no_str))
        file_open(fn_config)
