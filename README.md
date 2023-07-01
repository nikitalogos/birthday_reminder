# Birthday Reminder

## About

...

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
02-03 Alex # date can be specified without year
  
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

## Configure

1. you can modify all params in file `main_config.yaml`
   1. File `main_config.yaml` is created during installation. It has detailed description of all params.
2. you can also pass these params as command line arguments. CLI arguments have higher priority than config file. 
   1. If you want, you can specify a custom config file location with CLI argument `--config-file`
3. However, I don't recommend to use CLI arguments, because they are not as intuitive as YAML syntax.

## Authorize in Google Calendar API

...

## Usage

1. You can add birthdays to the `Birthdays.txt` file, which is created during installation. 
   1. You can specify a custom file location by editing parameter `input_file` in `main_config.yaml`
2. To check if file is valid, run `birthday-reminder validate`
3. To show birthdays from file, run `birthday-reminder show next` - this will show birthdays sorted by number of days to the next birthday.
   1. The other sort options are:
      1. `show date` - sorted by month and day
      2. `show year` - sorted by year of birth (dates without known year will show up in the end)
4. To show birthdays from Google Calendar, run `birthday-reminder gshow next`.
   1. To run this command, you first need to authorize in Google Calendar. (See the previous section for details)
5. To show diff between file and Google Calendar, run `birthday-reminder diff`
6. To upload birthdays from file to Google Calendar, run `birthday-reminder upload`
   1. This command first will show `diff` between file and Google Calendar, explain what changes it's going to make and ask for confirmation
   2. Upload supports optional flags: 
      1. `-y` / `--yes` - do not ask for confirmation
      2. `-f` / `--force` - delete all events in Google Calendar and upload all events from file

> **Note:** 
> 1. `birthday-reminder` will create a new calendar in your Google Calendar called `Birthday Reminder` (you can change this name in `main_config.yaml`).
> 2. It will not modify any events from other calendars. 
> 3. Calendar created by `birthday-reminder` is not intended to be edited manually from Google Calendar web interface. 
> 4. The only thing you can do in web interface is change the color of the calendar (unfortunately, it's not possible to change the color via API).
> 5. If you want to edit events, you should edit `Birthdays.txt` file and run `birthday-reminder upload` again.
