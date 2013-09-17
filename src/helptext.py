
helptext = [
	"A Command Line ToDoList Manager",
	"\nUsage: todolist.py [-h] [-f <filepath>] [action] [data]",
	"\nPositional Arguments:",
	"	action (default=\"list:today\") = [(<operation>)[:<taskgroup>]]",
	"		<operation> = list | add | done | failed | pending | edit | move | delete",
	"		<taskgroup> = This can be either a date, a range or a special category.",
	"	data = [<word>*]",
	"		In case of the add-operation, this is the task string itself (including tags).",
	"		In all other cases, the words are used as task filters for the selected group.",
	"\nOptional Arguments:",
	"	-h, --help",
	"		Show this help message and exit.",
	"	-f <filepath>, --file <filepath> (default=\"./todolist.txt\")",
	"		The properly formatted text-file to be used as the data-source.",
	"\nCreated by: Kaustubh Karkare\n"
]
helptext = "\n".join(helptext).replace("\t"," "*4)
exports["helptext"] = helptext