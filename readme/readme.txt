Plugin for CudaText.
Handles auto-completion command (default hotkey: Ctrl+Space).
Gives completion listbox with words from current document, starting with the current word (under caret).
E.g. if you typed "op", it may show words "operations", "opinion", "option" etc.
Plugin cannot work with multi-carets. 

Plugin has options in the config file, call menu item "Options / Settings-pligins / Complete From Text".
Options are: 

- 'lexers': comma-separated lexer names, ie for which lexers to work; specify none-lexer as '-'.
- 'min_len': minimal word length, words of smaller length will be ignored.
- 'max_lines': if document has bigger count of lines, ignore this document.    
- 'case_sens': case-sensitive; words starting with 'A' will be ignored when you typed 'a'.
- 'no_comments': ignore words inside "syntax comments" (lexer specific).
- 'no_strings': ignore words inside "syntax strings" (lexer specific).
- 'what_editors': which documents (ie UI tabs) to read to get words. Values:
    0: only current document.
    1: all opened documents.
    2: all opened documents with the same lexer.

Plugin supports CudaText option "nonword_chars", so for example words with '$' can be added,
if option is configured so.


Author: Alexey Torgashin (CudaText)
License: MIT
