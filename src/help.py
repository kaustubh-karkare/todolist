
import os,sys

text = [
	"A Command Line ToDoList Manager",
	"\nUsage: ./"+os.path.basename(sys.argv[0])+" [-h] [-H] [-f <filepath>] [data ...]",
], [
	"Positional Arguments (data)",
	"	The first argument is expected to be an Operation*. (default=list)",
	"	The next argument is expected to be a TaskGroup*. (default=today)",
	"	In case of add-operation, the remaining arguments should be the new task.",
	"	In all other cases, the remaining arguments are task-group filters.",
], [
	"Optional Arguments",
	"	-h, --help",
	"		Show the basic help message and exit.",
	"	-H, --help2",
	"		Show the extended help message and exit.",
	"	-f <filepath>, --file <filepath> (default=\"./todolist.txt\")",
	"		The properly formatted text-file to be used as the data-source.",
], [
	"Operation & TaskGroup Options",
	"	Operations = list | add | done | failed | edit | move | delete",
	"	TaskGroup = Either a specific date in the format YYYY-MM-DD, or",
	"		today | tomorrow | thisweek | yesterday | lastweek | nextweek",
	"		thismonth | lastmonth | nextmonth | forever | periodic",
	"	Note: Weeks are assumed to start from a Monday and end on a Sunday.",
], [
	"Tags (special and otherwise)",
	"	Basics",
	"		Tasks can include tags, which are basically string without whitespace,",
	"		and prefixed with the hash (#) symbol. While you may create your own",
	"		tags, certain tags have special meanings as explained below.",
	"	Status Tags",
	"		These tags are used to indicate the current status of a task:",
	"		#done | #failed | #impossible (lack of a status tag => #pending)",
	"	Essential Tasks",
	"		Tasks tagged #essential are carried forward from the previous day",
	"		to the current day, if they have not yet been done or failed.",
	"	Tasks with deadlines",
	"		These are similar to #essential tasks, but are not carried forward",
	"		beyond the specified date. To add a deadline to a task, add the tag:",
	"		#deadline=<taskgroup> (requires reference to a specific date)",
	"	Periodic Tasks",
	"		Tasks in the \"periodic\" taskgroup are automatically added to the group",
	"		corresponding to the current date based on the following special tags:",
	"		#everyday | #weekday | #weekend | #monday | #tuesday | ... | #sunday",
	"	Note: Periodic Tags have a special meaning only if the containing task",
	"		in the special \"periodic\" group.",
], [
	"File (data-source)",
	"	The format of file being used as the data-source has kept extremely simple",
	"	so that it can be easily read and manually modified is necessary.",
	"	(1) Lines with no indenting declare a TaskGroup, which must be a specific",
	"		date (format=YYYY-MM-DD) or a special group (\"Periodic\").",
	"	(2) Once a TaskGroup has been declared, the following lines specify the",
	"		actual task (with tags). A single horizontal tab is used as indentation.",
	"	(3) The last line of the file starts with a hash (#), followed by a space,",
	"		and finally the last script run date (format=YYYY-MM-DD).",
	"	Any deviations from the above specified rules will result in an error.",
	"	Warning: Do not change the last line of the file! Doing so may result in",
	"		unexpected, unwanted & irreversible changes and inconsistencies!",
], [
	"Created by: Kaustubh Karkare\n"
]

def merge(*a):
	temp = ("\n".join(j) for i,j in enumerate(text) if i in a)
	return "\n\n".join(temp).replace("	"," "*4)

class help:
	basic = merge(0,1,2,6)
	extended = merge(0,1,2,3,4,5,6)

exports["help"] = help