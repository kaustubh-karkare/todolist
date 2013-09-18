
import os, sys, textwrap

text = ["""\
Command Line To-Do-List Manager
\n\
Usage: ./"""+os.path.basename(sys.argv[0])+""" [-h] [-H] [-f <filepath>] [data ...]
""", """\
Positional Arguments (data)
	The first argument is expected to be an Operation*. (default=list)
	The next argument is expected to be a TaskGroup*. (default=today)
	In case of add-operation, the remaining arguments should be the new task.
	In all other cases, the remaining arguments are task-group filters.
	Note: In case of task-group filters, normal words are treated are considered
		positive filters (match required), while those that start with the tilde 
		character ("~") are considered negative (mismatch required). To match the
		actual "~" symbol at the start of the word, use the "~~" prefix.
	Warning: You may need to escape certain characters, if your shell has
		reserved its normal form for a special purpose.
\n\
Optional Arguments
	-h, --help
		Show this help message and exit.
	-f <filepath>, --file <filepath> (default="./todolist.txt")
		The properly formatted text-file to be used as the data-source.
\n\
Operation & TaskGroup Options
	Operations = list | add | done | failed | edit | move | delete
	TaskGroup = Either a specific date in the format YYYY-MM-DD, or
		today | tomorrow | thisweek | yesterday | lastweek | nextweek |
		thismonth | lastmonth | nextmonth | YYYY-MM | YYYY | forever |
		future | past | periodic
	Note: You will need to specify an exact date (and not a range) while
		adding new tasks. By default, tasks are added to the group
		corresponding to the current date.
	Note: Weeks are assumed to start from a Monday and end on a Sunday.
\n\
Tags (special and otherwise)
	Basics
		Tasks can include tags, which are basically string without whitespace,
		and prefixed with the plus (+) symbol. While you may create your own
		tags, certain tags have special meanings as explained below.
		Note that tags cannot be repeated.
	Status Tags
		These tags are used to indicate the current status of a task:
		+done | +failed | +impossible (lack of a status tag => +pending)
	Tasks with deadlines
		Tasks with a +deadline=<taskgroup> tag, if pending, are carried forward
		from the previous day to the current day. The <taskgroup> must refer
		a specific date, with the exception of the string "none", which just
		means that there is no stop-date for the carry-forwards.
	Periodic Tasks
		Tasks in the "periodic" taskgroup are automatically added to the group
		corresponding to the current date based on the following special tags:
		+everyday | +weekday | +weekend | +monday | +tuesday | ... | +sunday
		Note that Periodic Tags have a special meaning only if the containing
		task in the special "periodic" group.
\n\
Usage Examples (not comprehensive)
	$ alias todo='"""+__file__+"""'
	$ todo add Catch the damn mouse. \+essential
	$ todo list today
	$ todo edit mouse # append " +food"
	$ todo list food
	$ todo done catch
	$ todo add 2013-09-15 Make plans for World Domination.
	$ todo list 2013-09
	$ todo add periodic Stare creepily at human. \+thursday
\n\
File (data-source)
	The format of file being used as the data-source has kept extremely simple
	so that it can be easily read and manually modified is necessary.
	(1) Lines with no indenting declare a TaskGroup, which must be a specific
		date (format=YYYY-MM-DD) or a special group ("Periodic").
	(2) Once a TaskGroup has been declared, the following lines specify the
		actual task (with tags). A single horizontal tab is used as indentation.
	(3) The last line of the file starts with a hash (#), followed by a space,
		and finally the last script run date (format=YYYY-MM-DD).
	Any deviations from the above specified rules will result in an error.
	Warning: Do not change the last line of the file! Doing so may result in
		unexpected, unwanted & irreversible changes and inconsistencies!
\n\
Created by: Kaustubh Karkare
"""]

def merge(*a):
	temp = (textwrap.dedent(j) for i,j in enumerate(text) if i in a)
	return "\n".join(temp).replace("	"," "*4)

class help:
	basic = merge(0)
	full = merge(0,1)

exports["help"] = help