
import argparse, os, readline, sys
require date, taskfile, helptext

__dir__ = os.path.join(*os.path.split(__file__)[:-1]) \
	if os.path.basename(__file__)!=__file__ else "."

# Command Line Argument Validation

operations = "list add edit delete move pending done failed".split()
def date(x): return Date("today") # development only

ap = argparse.ArgumentParser(description="A Command Line ToDoList Manager", add_help=False)
ap.add_argument("data", nargs="*", default=[])
ap.add_argument("-h","--help", action="store_true", default=False)
ap.add_argument("-f","--file", default="./todolist.txt")
ap.add_argument("--date", type=date, default="today")
ap.add_argument("--nosave", action="store_true", default=False)

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

	args = ap.parse_args(sys.argv[1:])

	if args.help:
		print helptext
		sys.exit(0)

	taskfile = TaskFile(args.file,args.date)

	if len(args.data) and args.data[0] in operations:
		operation = args.data[0]
		args.data.pop(0)
	else: operation = "list"

	if operation=="add":
		if len(args.data)==0:
			raise Exception("Empty Task")
		group = taskfile.group(args.data[0])
		line = " ".join(args.data[1:])
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
				print group.tabulate(date=args.date, index=True)
				while True:
					index = prompt("Select Task by Index: ")
					try: task = tasks[int(index)]
					except ValueError, IndexError: continue
					break
			del tasks

	if operation=="list":

		print group.tabulate(date=args.date)

	elif operation=="add":

		if line=="": raise Exception("Empty Task")
		
		task = Task(line,group,args.date)
		group.task_add(task)
		print group.tabulate(date=args.date)

		today = taskfile.group("today")
		task = task.periodic(args.date)
		if task:
			today.task_add(temp)
			taskfile.update(today)

	else:

		if operation in ("edit","delete","move"):
			print TaskGroup([task]).tabulate(date=args.date)

		if operation=="edit":
			while True:
				line = prompt("Edit Task: ",str(task))
				if line!="": break
			task.update(line,args.date)
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
			task.tag_remove("failed",args.date)
			task.tag_add("done",args.date)
			taskfile.update(task.group)

		elif operation=="failed":
			task.tag_remove("done",args.date)
			task.tag_add("failed",args.date)
			taskfile.update(task.group)

		elif operation=="pending":
			task.tag_remove("done",args.date)
			task.tag_remove("failed",args.date)

		else: raise Exception("Unknown Action")

		if operation!="delete":
			print TaskGroup([task]).tabulate(date=args.date)
	
	if args.nosave:
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

exports["main"] = __main