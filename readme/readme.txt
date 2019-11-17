plugin for CudaText.
handles auto-complete command (Ctrl+Space). gives completion listbox with 
words from current document, which start with the current word (under caret). 
e.g. if you typed "ri", it may give "riddle", "righter" etc.

plugin has options in the config file, call menu item
"Options / Settings-pligins / Complete From Text": 

- lexers list (for which to work), specify none-lexer as '-'
- minimal word length (words of smaller length won't show in list)
- case-sensitive

plugin respects CudaText option "nonword_chars", so for example it can find
names with $ (if $ is added to "nonword_chars").


Author: Alexey Torgashin (CudaText)
License: MIT
