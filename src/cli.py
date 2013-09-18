
import argparse, os, readline, sys
require date, taskfile, help

__dir__ = os.path.join(*os.path.split(__file__)[:-1]) \
	if os.path.basename(__file__)!=__file__ else "."

# Command Line Argument Validation

operations = "list add edit delete move done failed help".split()

ap = argparse.ArgumentParser(description="A Command Line ToDoList Manager", add_help=False)
ap.add_argument("data", nargs="*", default=[])
ap.add_argument("-h","--help", action="store_true", default=False)
ap.add_argument("-f","--file", default="./todolist.txt")
ap.add_argument("-n","--nosave", action="store_true", default=False)
ap.add_argument("-d","--date", type=Date, default="today")

# User Interaction Functions

def confirm(msg="Are you sure?"):
	while True:
		x = raw_input(msg+" (yes/no) ")
		if x=="yes": return True
		elif x=="no": return False
	print
def prompt(prompt, prefill=""):
	readline.set_startup_hook(lambda: readline.insert_text(prefill))
	try:
		data = raw_input(prompt)
		print
		return data
	finally: readline.set_startup_hook()

# Convenience Functions

def __relocate(taskfile,task,name):
	if task.group:
		task.group.task_remove(task)
		taskfile.update(task.group)
	taskgroup = taskfile.group(name)
	if not taskgroup: return False
	taskgroup.task_add(task)
	task.group = taskgroup
	taskfile.update(taskgroup)
	return True

def __main():

	print

	args, unknown = ap.parse_known_args()

	if len(unknown)>0:
		print help.basic
		sys.exit(0)

	if len(args.data) and args.data[0] in operations:
		operation = args.data[0]
		args.data.pop(0)
	else: operation = "list"

	if args.help or operation=="help":
		print help.full
		sys.exit(0)

	realdate = args.date.date==datetime.date.today()
	taskfile = TaskFile(args.file,args.date)

	if operation=="add":

		if len(args.data)>0:
			group = taskfile.group(args.data[0])
			if group: args.data.pop(0)
			else: group = taskfile.group("today")
		else: group = taskfile.group("today")

		if len(args.data)>0:
			line = " ".join(args.data)
		else:
			while True:
				line = prompt("Add Task: ")
				if line.strip()!="": break

		task = Task(line,group,args.date)
		group.task_add(task)
		taskfile.update(group)
		print group.tabulate()

		today = taskfile.group("today")
		task = task.periodic(today)
		if task:
			today.task_add(temp)
			taskfile.update(today)

	else:

		if len(args.data)==0:
			group = taskfile.group("today")
		else:
			group = taskfile.select(args.data[0], args.data[1:])
			if not group:
				group = taskfile.select("today", args.data)
		if operation!="list":
			tasks = group.task_list()
			if len(tasks)==0:
				raise Exception("No Matching Task")
			elif len(tasks)==1:
				task = tasks[0]
			else:
				print group.tabulate(True)
				while True:
					index = prompt("Select Task by Index: ")
					try: task = tasks[int(index)]
					except ValueError, IndexError: continue
					break
			del tasks

		if operation not in ("list", "done", "failed"):
			print TaskGroup([task]).tabulate()

		if operation=="list":
			print group.tabulate()

		elif operation=="edit":
			while True:
				line = prompt("Edit Task: ",str(task))
				if line!="": break
			task.update(line)
			taskfile.update(task.group)

		elif operation=="delete":
			task.group.task_remove(task)
			taskfile.update(task.group)

		elif operation=="move":
			while True:
				name = prompt("Enter Destination Date: ")
				try: group = taskfile.group(name)
				except: continue
				break
			__relocate(taskfile,task,group.name)

		elif operation=="done":
			task.tag_remove("failed")
			task.tag_remove("impossible")
			task.tag_add("done")
			taskfile.update(task.group)

		elif operation=="failed":
			task.tag_add("failed")
			task.tag_remove("impossible")
			task.tag_remove("done")
			taskfile.update(task.group)

		if operation not in ("list","delete"):
			print TaskGroup([task]).tabulate()
	
	if args.nosave or not realdate:
		pass
	elif operation=="list":
		taskfile.save()
	elif confirm():
		taskfile.save()
		print "Saved updates to file."
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