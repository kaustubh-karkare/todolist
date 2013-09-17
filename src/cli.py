
import argparse, os, readline, sys
require date, taskfile

__dir__ = os.path.join(*os.path.split(__file__)[:-1]) \
	if os.path.basename(__file__)!=__file__ else "."

# Command Line Argument Validation

actions = "list add edit delete move pending done failed".split()
argerror = argparse.ArgumentTypeError
def action(z):
	(x, y) = z.split(":",1) if ":" in z else (z, None)
	if x in actions: return (x, y or "today")
	else: raise Exception("Unknown Action")

ap = argparse.ArgumentParser(description="A Command Line ToDoList Manager", add_help=False)
ap.add_argument("action", nargs="?", type=action, default="list")
ap.add_argument("data", nargs="*")
ap.add_argument("-f","--file", default="./todolist.txt")
ap.add_argument("-d","--date", type=Date, default="today")
ap.add_argument("-h","--help", action="store_true", default=False)

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

# User Interaction Functions

def confirm(msg="Are you sure?"):
	while True:
		x = raw_input(msg+" (yes/no) ")
		if x=="yes": return True
		elif x=="no": return False
def prompt(prompt, prefill=""):
	readline.set_startup_hook(lambda: readline.insert_text(prefill))
	try: return raw_input(prompt)
	finally: readline.set_startup_hook()

# Convenience Functions

def __relocate(taskfile,task,name):
	if task.group:
		task.group.task_remove(task)
		taskfile.update(task.group)
	name = task.groupname() or name
	taskgroup = taskfile.group(name)
	if not taskgroup: return False
	taskgroup.task_add(task)
	task.group = taskgroup
	taskfile.update(taskgroup)
	return True

def __select(taskfile,name,data):
	taskgroup = taskfile.select(name,data)
	tasks = taskgroup.task_list()
	if len(tasks)==0:
		raise Exception("No Matching Task")
	if len(tasks)==1:
		return tasks[0]
	else:
		print taskgroup.tabulate(" ".join(data),True)
		while True:
			index = prompt("Select Task by Index: ")
			try: task = tasks[int(index)]
			except ValueError, IndexError: continue
			return task

def __main():

	print

	args = ap.parse_args(sys.argv[1:])
	if args.help:
		print helptext
		sys.exit(0)

	taskfile = TaskFile(args.file,args.date)
	action, name = args.action
	line = " ".join(args.data)
	
	if action=="list":
		taskgroup = taskfile.select(name, args.data)
		print taskgroup.tabulate(line)

	elif action=="add":
		if line=="": raise Exception("Empty Task")
		
		task = Task(line,None)
		name = args.date.translate(name) or name
		if not __relocate(taskfile,task,name):
			raise Exception("Invalid Date")
		print taskgroup.tabulate(name)			

	else:

		task = __select(taskfile, name, args.data)
		print TaskGroup([task]).tabulate()

		if action=="edit":
			while True:
				line = prompt("Edit Task: ",str(task))
				if line!="": break
			task.update(line)
			name = args.date.translate(task.group.name) or args.date.str()
			__relocate(taskfile,task,name)

		elif action=="delete":
			task.group.task_remove(task)
			taskfile.update(task.group)

		elif action=="move":
			while True:
				name = prompt("Enter Destination Date: ")
				try: name = Date(name).str()
				except: continue
				break
			__relocate(taskfile,task,name)

		elif action=="done":
			task.tag_remove("failed")
			task.tag_add("done")
			taskfile.update(task.group)

		elif action=="failed":
			task.tag_remove("done")
			task.tag_add("failed")
			taskfile.update(task.group)

		elif action=="pending":
			task.tag_remove("done")
			task.tag_remove("failed")

		else: raise Exception("Unknown Action")

		if action!="delete":
			print TaskGroup([task]).tabulate()
	
	if action!="list" and confirm():
		taskfile.save()
		print "Saved changes to file."
		print

def main():
	try:
		__main()
	except KeyboardInterrupt:
		print "^SIGINT\n"
		sys.exit(1)
	except Exception as e:
		print "Error:", e.message, "\n"

exports["main"] = main