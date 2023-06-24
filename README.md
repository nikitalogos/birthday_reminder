# Birthday Reminder

## File format

File format is very simple:
1. Each line is a record with two fields: `date` and `title` separated by whitespace
2. text after `#` is considered a comment and is ignored
3. empty lines are ignored
4. whitespace before and after `date` and `title` is ignored

Example:
```sh
# this is a comment
2000-01-01 John Doe # this is also a comment
  2000-01-02 Jane      # leading/trailing tabs/spaces are ignored
  
2000-01-03 # error, title is missing
Alex # error, date is missing
```


## Install CLI

### Linux

#### Install

1. Put this directory to the place where all your programs live. Do not move it after installation or links will break!
2. Enter the directory `cd birthday_reminder`
3. Run `make install`. What it does:
   1. installs packages `python3.11` and `python3.911-venv` 
      1. (if you want to use it with different version of python, you can edit `Makefile`. However, it may not work with older versions of python
   2. creates virtual environment `venv` in directory `birthday_reminder`
   3. creates executable `/usr/local/bin/birthday-reminder` that runs code from the current repository
4. Restart your shell to make autocompletion work
5. Run `birthday-reminder --help`

#### Install for development

```sh
make install_git_pre_commit_hook
make install
```

> Developer note: `make install` installs package in editable mode, so you can edit code and `birthday-reminder` will use the updated version

#### Uninstall

1. Remove python3.11 if you do not need it (which is unlikely) - `sudo apt-get uninstall python3.11 python3.11-venv`
2. Run `make uninstall`