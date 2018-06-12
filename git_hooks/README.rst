Git hooks
=========

This folder is intended to store git hooks.

To use repository git hooks, you have two options:

* **Change your hook path to apply all the hooks located at this folder:**

  .. code-block:: bash

     git config core.hooksPath git_hooks

  .. note::

   ``core.hooksPath`` is added only at 2.9.0 version of git, so please update git version or use symlinks

* **Take the specific hook and create a sym link in *githooks* to the specific hook:**

  .. code-block:: bash

     ln -s git_hooks/pre-commit .git/hooks


Hooks can be muted with --no-verify option:  ``git commit --no-verify``

* ``pre-commit`` hook automatically fixes the following PEP8 rules:

  * E101 - Reindent all lines.
  * E11  - Fix indentation. (not include E112 and E113)
  * E121 - Fix indentation to be a multiple of four.
  * E122 - Add absent indentation for hanging indentation.
  * E123 - Align closing bracket to match opening bracket.
  * E124 - Align closing bracket to match visual indentation.
  * E125 - Indent to distinguish line from next logical line.
  * E126 - Fix over-indented hanging indentation.
  * E127 - Fix visual indentation.
  * E128 - Fix visual indentation.
  * E20  - Remove extraneous whitespace.
  * E211 - Remove extraneous whitespace.
  * E22  - Fix extraneous whitespace around keywords.
  * E224 - Remove extraneous whitespace around operator.
  * E226 - Fix missing whitespace around arithmetic operator.
  * E227 - Fix missing whitespace around bitwise/shift operator.
  * E228 - Fix missing whitespace around modulo operator.
  * E231 - Add missing whitespace.
  * E241 - Fix extraneous whitespace around keywords.
  * E242 - Remove extraneous whitespace around operator.
  * E251 - Remove whitespace around parameter '=' sign.
  * E252 - Missing whitespace around parameter equals.
  * E26  - Fix spacing after comment hash for inline comments.
  * E265 - Fix spacing after comment hash for block comments.
  * E27  - Fix extraneous whitespace around keywords.
  * E301 - Add missing blank line.
  * E302 - Add missing 2 blank lines.
  * E303 - Remove extra blank lines.
  * E304 - Remove blank line following function decorator.
  * E306 - Expected 1 blank line before a nested definition
  * E401 - Put imports on separate lines.
  * E501 - Try to make lines fit within --max-line-length characters.
  * E502 - Remove extraneous escape of newline.
  * E701 - Put colon-separated compound statement on separate lines.
  * E70  - Put semicolon-separated compound statement on separate lines.
  * E721 - Use "isinstance()" instead of comparing types directly.
  * E722 - Fix bare except.
  * W291 - Remove trailing whitespace.
  * W292 - Add a single newline at the end of the file.
  * W293 - Remove trailing whitespace on blank line.
  * W391 - Remove trailing blank lines.
  * W601 - Use "in" rather than "has_key()".
  * W602 - Fix deprecated form of raising exception.
  * W603 - Use "!=" instead of "<>"
  * W604 - Use "repr()" instead of backticks.

  More information can be found in the official `autopep8 repository <https://github.com/hhatto/autopep8>`_
