Plugin for CudaText.
Handles auto-completion command (Ctrl+Space). Gives completion listbox with 
words from current document, which start with the current word (under caret). 
E.g. if you typed "op", it may show words "operations", "opinion" etc.

Plugin has options in the config file, call menu item
"Options / Settings-pligins / Complete From Text".
Options are: 

- 'lexers': comma-separated lexer names, ie for which lexers to work; specify none-lexer as '-'.
- 'min_len': minimal word length, words of smaller length will be ignored.
- 'case_sens': case-sensitive; words starting with 'A' will be ignored when you typed 'a'.
- 'no_comments': ignore words inside "syntax comments" (lexer specific).
- 'no_strings': ignore words inside "syntax strings" (lexer specific).
- 'what_editors': which editor-controls (ie UI tabs) to read to get words. Values:
    '0': only current editor.
    '1': all opened editors.
    '2': all editors with the same lexer.


Author: Alexey Torgashin (CudaText)
License: MIT
