import os
import re
from cudatext import *
import cudax_lib as appx

fn_config = os.path.join(app_path(APP_DIR_SETTINGS), 'plugins.ini')
section = 'complete_from_text'
PREFIX_TEXT = 'text'
PREFIX_VAR = 'var'
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

    return (',*,' in ','+option_lexers+',') or (','+(lex or '-').lower()+',' in ','+option_lexers.lower()+',')


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
        else:
            break

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

    regex = r'[%s]{%d,}' % (cls, option_min_len)
    #print('regex:', repr(regex))
    return regex

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


def _read_acp_file(sfile):

    with open(sfile, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    return lines

def get_acp_words(word1, word2):

    sfile = os.path.join(app_path(APP_DIR_DATA), 'autocomplete', ed.get_prop(PROP_LEXER_CARET, '') + '.acp')
    if os.path.isfile(sfile):
        acp_lines = _read_acp_file(sfile)
    else:
        sfile = os.path.join(app_path(APP_DIR_DATA), 'autocomplete', ed.get_prop(PROP_LEXER_CARET, '') + '_.acp')
        if os.path.isfile(sfile):
            acp_lines = _read_acp_file(sfile)
        else:
            return [], set()

    target_word = word1+word2

    if len(acp_lines) > 0  and  acp_lines[0].startswith('#chars'):
        del acp_lines[0]

    acp_words = []
    words = set()
    fstr = '{}|{}|{}'+chr(9)+'{}'
    for line in acp_lines:
        line = line.rstrip()
        if not line:
            continue

        # using '#chars'
        #m = re.match('^([^\s]+)\s([\w'+ word_chars +']+)([^|]*)\|?(.*)?$', line) # ^Prefix Word Args Descr?
        m = re.match('^([^\s]+)\s([^(| ]+)([^|]*)\|?(.*)?$', line) # ^Prefix Word Args Descr?
        if not m:
            continue

        # avoid 'm[index]' to support old Python 3.4
        pre, word, args, descr = m.group(1), m.group(2).rstrip(), m.group(3), m.group(4) or ''

        if len(word) < option_min_len:
            continue
        if is_text_with_begin(word, word1)  and  word != word1  and  word != target_word:
            word = word.replace('%20', ' ')
            acp_words.append(fstr.format(pre, word, args, descr))
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

        word = get_word(x0, y0)

        if not word: return
        word1, word2 = word
        if not word1: return # to fix https://github.com/Alexey-T/CudaText/issues/3175

        words = []

        regex = get_regex(nonwords)

        #find word list from needed editors
        for e in get_editors(ed_self, lex):
            words += get_words_list(e, regex)

        if option_what_editors==1 or option_what_editors==2:
            words_by_tabs = []
            tab_titles = []
            for e in get_editors(ed_self, lex):
                words_by_tabs.append(get_words_list(e, regex))
                tab_titles.append(Editor.get_prop(e, PROP_TAB_TITLE))

        def search_tab(w):
            if option_what_editors==1 or option_what_editors==2:
                tabs_found = []
                for i,words_by_tabs_ in enumerate(words_by_tabs):
                    for wbt in words_by_tabs_:
                        if wbt == w:
                            tabs_found.append(i)
                if len(tabs_found) > 0:
                    tabs_titles = '|'
                    for tf in tabs_found:
                        tabs_titles += tab_titles[tf] + ' '
                    return tabs_titles
                return ''
            else:
                return ''

        #exclude numbers
        words = [w for w in words if not w.isdigit()]
        if words:
            words = sorted(list(set(words)))

        acp_words,acp_set = get_acp_words(word1, word2)  if option_use_acp else  ([],set())

        if not words and not acp_words:
            return

        def get_prefix(w):
            if w.startswith('$'):
                return PREFIX_VAR
            else:
                return PREFIX_TEXT

        words = [get_prefix(w)+'|'+w+search_tab(w) for w in words
                 if (is_text_with_begin(w, word1) or is_text_with_begin(w, '$'+word1))
                 and w not in acp_set # do not repeat words from acp
                 and w!=word1
                 and w!=(word1+word2)
                 ]
        #print('word:', word)
        #print('list:', words)

        ed_self.complete('\n'.join(words+acp_words), len(word1), len(word2))
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
