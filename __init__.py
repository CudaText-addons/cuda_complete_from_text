import os
import re
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
option_what_editors = int(ini_read(fn_config, section, 'what_editors', '0'))
option_max_lines = int(ini_read(fn_config, section, 'max_lines', '10000'))
option_use_acp = str_to_bool(ini_read(fn_config, section, 'use_acp', '1'))
option_case_split = str_to_bool(ini_read(fn_config, section, 'case_split', '0'))
option_underscore_split = str_to_bool(ini_read(fn_config, section, 'underscore_split', '0'))


def get_editors(ed, lexer):

    if option_what_editors==0:
        return [ed]
    elif option_what_editors==1:
        return [Editor(h) for h in ed_handles()]
    elif option_what_editors==2:
        res = []
        for h in ed_handles():
            e = Editor(h)
            if e.get_prop(PROP_LEXER_FILE)==lexer:
                res += [e]
        return res


def is_lexer_allowed(lex):

    return ','+(lex or '-').lower()+',' in ','+option_lexers.lower()+','


def isword(s):

    return s not in ' \t'+nonwords


def is_text_with_begin(s, begin):

    if option_case_split or option_underscore_split:
        if option_case_split  and  s[0] == begin[0]:
            searchwords = re.findall('.[^A-Z]*', begin)
            wordwords = re.findall('.[^A-Z]*', s)
            
            swl = len(searchwords)
            wwl = len(wordwords)
            if swl <= wwl:
                for i in range(swl):
                    if not wordwords[i].startswith(searchwords[i]):
                        break
                else:
                    return True
            
        if option_underscore_split:
            ss = s.strip('_') # ignore starting,ending underscores
            if '_' in ss:
                
                if not option_case_sens:
                    begin = begin.lower()
                    ss = ss.lower()

                wordwords = re.findall('[^_]+', ss) # PROP_LEX => [PROP, LEX]
                wwl = len(wordwords)
                bl = len(begin)
                    
                if bl <= wwl: # most common case, first chars of each word: PLF|PL|P => PROP_LEXER_FILE
                    for i in range(bl):
                        if begin[i] != wordwords[i][0]:
                            break
                    else:
                        return True
                            
                if spl_match(begin, wordwords):
                    return True
        
    if option_case_sens:
        return s.startswith(begin)
    else:
        return s.upper().startswith(begin.upper())


def spl_match(begin, words):
    '''returns True if 'begin' fits consecutively into 'words' (prefixes of 'words')'''
    
    word = words[0]
    common_len = 0
    for i in range(min(len(begin), len(word))):
        if begin[i] == word[i]:
            common_len = i+1
    
    if common_len > 0:
        if len(begin) == common_len: # last match success
            return True
        elif len(words) == 1: # last word - should be full prefix
            return False
            
        for i in range(common_len): # i: 0 and 1 for common_len=2 ->
            # ... on calling spl_match() 'begin' will always be non-empty - less than full match
            res = spl_match(begin[common_len-i:], words[1:])
            if res:
                return True
        
    return False


def get_regex(nonwords):
    '''main regex to find words, considering Cud option nonword_chars'''

    specials = '$%#-'

    cls = r'\w'
    for ch in specials:
        if ch not in nonwords:
            cls += '\\'+ch

    return r'\b[%s]{%d,}' % (cls, option_min_len)

def get_words_list(ed, regex):

    if ed.get_line_count() > option_max_lines:
        return []

    if option_no_cmt and option_no_str:
        ops = 'T6'
    elif option_no_cmt:
        ops = 'T4'
    elif option_no_str:
        ops = 'T5'
    else:
        ops = ''

    res = ed.action(EDACTION_FIND_ALL, regex, 'r'+ops) or []

    l = [ed.get_text_substr(*r) for r in res]
    l = list(set(l))
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

def get_acp_words(word1, word2):
    
    sfile = os.path.join(app_path(APP_DIR_DATA), 'autocomplete', ed.get_prop(PROP_LEXER_CARET, '') + '.acp')
    if os.path.isfile(sfile):
        with open(sfile, 'r') as f:
            acp_lines = f.readlines()
    else:
        return [],set()
    
    target_word = word1+word2
    
    if len(acp_lines) > 0  and  acp_lines[0].startswith('#chars'):
        del acp_lines[0]
    
    acp_words = []
    words = set()
    for line in acp_lines:
        line = line.rstrip()
        if not line:
            continue
        
        m = re.match('^([^\s]+)\s([^|]+)(\|.*)?$', line) # ^Prefix Word |Descr?
        if not m:
            continue
            
        pre,word,descr = m[1],m[2].rstrip(),m[3] or ''
        
        if len(word) < option_min_len:
            continue
        
        if is_text_with_begin(word, word1)  and  word != word1  and  word != target_word:
            acp_words.append('{}|{}{}'.format(pre,word,descr)) # descr has a |
            words.add(word)
                 
    return acp_words,words

class Command:

    def on_complete(self, ed_self):

        carets = ed_self.get_carets()
        if len(carets)!=1: return
        x0, y0, x1, y1 = carets[0]
        if y1>=0: return #don't allow selection

        lex = ed_self.get_prop(PROP_LEXER_FILE, '')
        if lex is None: return
        if not is_lexer_allowed(lex): return

        global nonwords
        nonwords = appx.get_opt(
            'nonword_chars',
            '''-+*=/\()[]{}<>"'.,:;~?!@#$%^&|`…''',
            appx.CONFIG_LEV_ALL,
            ed_self,
            lex)

        words = []
        regex = get_regex(nonwords)

        #find word list from needed editors
        for e in get_editors(ed_self, lex):
            words += get_words_list(e, regex)
        
        #exclude numbers
        words = [w for w in words if not w.isdigit()]
        if not words: return
        
        words = sorted(list(set(words)))
        #print('words', words)

        word = get_word(x0, y0)
        if not word: return
        word1, word2 = word
        if not word1: return # to fix https://github.com/Alexey-T/CudaText/issues/3175

        acp_words,acp_set = get_acp_words(word1, word2)  if option_use_acp else  ([],set())

        words = [prefix+'|'+w for w in words
                 if is_text_with_begin(w, word1)
                 and w not in acp_set # do not repeat words from acp
                 and w!=word1
                 and w!=(word1+word2)
                 ]
        #print('word:', word)
        #print('list:', words)

        ed_self.complete('\n'.join(acp_words+words), len(word1), len(word2))
        return True


    def config(self):

        ini_write(fn_config, section, 'lexers', option_lexers)
        ini_write(fn_config, section, 'min_len', str(option_min_len))
        ini_write(fn_config, section, 'case_sens', bool_to_str(option_case_sens))
        ini_write(fn_config, section, 'no_comments', bool_to_str(option_no_cmt))
        ini_write(fn_config, section, 'no_strings', bool_to_str(option_no_str))
        ini_write(fn_config, section, 'what_editors', str(option_what_editors))
        ini_write(fn_config, section, 'max_lines', str(option_max_lines))
        ini_write(fn_config, section, 'use_acp', bool_to_str(option_use_acp))
        ini_write(fn_config, section, 'case_split', bool_to_str(option_case_split))
        ini_write(fn_config, section, 'underscore_split', bool_to_str(option_underscore_split))
        file_open(fn_config)
