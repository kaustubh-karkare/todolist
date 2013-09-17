#!/usr/bin/python
def define(scope):
	def actual(exports):
		scope.update(exports)
	return actual
define = define(vars())
import argparse, datetime, sys, re, readline, os
def exports():
	exports = {}
	periodic = { # function arguments: datetime.date instance
		"everyday": lambda date: True,
		"weekdays": lambda date: date.weekday()<5,
		"weekends": lambda date: date.weekday()>4,
	}
	for index,name in enumerate("monday tuesday wednesday thursday friday saturday sunday".split()):
		periodic[name] = (lambda x: lambda date: date.weekday()==x)(index)
	status = "failed done".split()
	prefix = "#"
	prefixlen = len(prefix)
	def istagstr(str): return len(str)>0 and len(str.split())==1
	def istag(tag): return tag.startswith(prefix) and istagstr(tag[prefixlen:])
	class Task:
		def __init__(self,raw,group):
			self.update(raw)
			self.group = group
		def update(self,raw):
			self.__raw = raw
			self.__tags = [tag.lower() for tag in self.__raw.split() if istag(tag)]
			self.__tags = [tag[prefixlen:] for tag in self.__tags]
			temp = len(self.__tags)
			if "essential" in self.__tags:
				self.__tags = [i for i in self.__tags if i not in periodic and not i.startswith("deadline=")]
			if len(self.__tags)<temp:
				temp = [i for i in self.__raw.split() \
					if not istag(i) or i[prefixlen:] in self.__tags]
				self.__raw = " ".join(temp)
		def __eq__(self,other): return isinstance(other,self.__class__) and self.__raw==other.__raw
		def __ne__(self,other): return not self.__eq__(other)
		def __hash__(self): return self.__raw.__hash__()
		def __contains__(self,word): return isinstance(word,str) and word.lower() in self.__raw.lower()
		def __repr__(self): return self.__raw
		def raw(self): return self.__raw
		table_heading = "Date Task Tags Periodicity Deadline Status".title().split()
		def table_fields(self):
			text = " ".join(word for word in self.__raw.split() if not istag(word))
			tags = ", ".join(tag for tag in self.__tags if tag not in status and \
				tag not in periodic and not tag.startswith("deadline=") and tag!="essential")
			freq = ", ".join([tag for tag in self.__tags if tag in periodic])
			dead = next((tag[9:] for tag in self.__tags if tag.startswith("deadline=")), \
				"No Limit" if "essential" in self.__tags else "")
			stat = next((tag for tag in self.__tags if tag in status), "pending").title()
			return [self.group.name, text, tags, freq, dead, stat]
		sg = "periodic".split() # special group names
		def tag_add(self,tag):
			if istagstr(tag) and tag not in self.__tags:
				self.update( " ".join(self.__raw.split()+[prefix+tag]) )
				return True
			return False
		def tag_check(self,tag):
			return tag in self.__tags
		def tag_remove(self,tag):
			if istagstr(tag) and tag in self.__tags:
				tag = prefix + tag # eliminates recomputation
				temp = [i for i in self.__raw.split() if i!=tag]
				self.update( " ".join(temp) )
				return True
			return False
		def carryover(self,date):
			if any(i in status for i in self.__tags): return
			for tag in self.__tags:
				if tag=="essential" \
					or tag.startswith("deadline=") \
					and Date.regexp.match(tag[9:]) \
					and date<Date.deconvert(tag[9:]):
					return True
		def periodic(self,date,group):
			tags = filter(lambda tag: tag in periodic, self.__tags)
			if not any(periodic[name](date) for name in tags): return
			temp = [tag for tag in self.__raw.split() \
				if not istag(tag) or tag[prefixlen:] not in status and not tag.startswith("deadline=")]
			return self.__class__( " ".join(temp), group )
			return self.__class__( self.__raw, None )
	exports["Task"] = Task
	return exports
define(exports())
def exports():
	exports = {}
	vc = "|"
	hc = "-"
	jc = "+"
	pd = " "
	nl = "\n"
	def prettytable(rows):
		if len(rows)==0: return
		width = [-1]*min(len(row) for row in rows)
		for row in rows:
			for j, col in enumerate(row):
				width[j] = max(width[j],len(col))
		result = ""
		line = (jc)+(jc).join(hc*(i+2) for i in width)+(jc)+nl
		for i, row in enumerate(rows):
			if i<2: result+=line
			for j, col in enumerate(row):
				result+=vc+pd+"{0:<{1}}".format(col,width[j])+pd
			result+=vc+nl
		result+=line[:-1]
		return result
	exports["prettytable"] = prettytable
	return exports
define(exports())
def exports():
	exports = {}
	class TaskGroup:
		def __init__(self,tasks=[],name=""):
			self.name = name
			self.__tasks = []
			for task in tasks:
				self.task_add(task)
		def __repr__(self):
			return self.__tasks.__repr__()
		def task_list(self,unhide=False):
			return [task for task in self.__tasks if unhide or not task.tag_check("hidden")]
		def task_add(self,task):
			if isinstance(task,Task) and not any(t==task for t in self.__tasks):
				self.__tasks.append(task)
		def task_remove(self,task):
			if isinstance(task,Task) and task in self.__tasks:
				self.__tasks.remove(task)
		def tabulate(self,heading=None,index=False):
			data = [ (["Index"] if index else [])+Task.table_heading ]
			for i, task in enumerate(self.task_list()):
				data.append( ([i] if index else [])+task.table_fields() )
			result, prefix = prettytable(data), ""
			if heading:
				x = result.find("\n")-len(heading)
				prefix = "="*(x/2-1)+" "+heading+" "+"="*(x-x/2-1)+"\n"
			return prefix+result+"\n"
		def select(self,words):
			return self.__class__( self.__tasks if len(words)==0 else \
				[task for task in self.__tasks if all(word in task for word in words)] )
	exports["TaskGroup"] = TaskGroup
	return exports
define(exports())
def exports():
	exports = {}
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
	return exports
define(exports())
def exports():
	exports = {}
	class Date:
		relative = {
			"yesterday": -1,
			"today": 0,
			"tomorrow": 1,
		}
		regexp = re.compile("\d{4}-\d{2}-\d{2}")
		oneday = datetime.timedelta(1)
		def __init__(self,today=None):
			self.date = datetime.date.today()
			self.__relative = {}
			if today is None:
				pass
			elif today in self.relative:
				self.date += self.relative[today]*self.oneday
			elif self.regexp.match(today):
				self.date = self.deconvert(today)
			else: raise Exception("Invalid Date")
			self.__str = self.convert(self.date)
			for word in self.relative:
				temp = self.date + self.relative[word] * self.oneday
				self.__relative[word] = self.convert(temp)
		def str(self): return self.__str
		def translate(self,word):
			if word in self.__relative: return self.__relative[word]
			elif self.regexp.match(word): return word
		@staticmethod
		def convert(obj):
			return obj.strftime("%Y-%m-%d")
		@staticmethod
		def deconvert(word):
			return datetime.date(*map(int,word.split("-")))
		@staticmethod
		def weekdiff(d1,d2):
			m1 = d1 - datetime.timedelta(days=d1.weekday())
			m2 = d2 - datetime.timedelta(days=d2.weekday())
			return (m2-m1).days/7
		@staticmethod
		def monthdiff(d1,d2):
			return (d2.year*12+d2.month)-(d1.year*12+d1.month)
	exports["Date"] = Date
	return exports
define(exports())
def exports():
	exports = {}
	daterange = {
		"forever": lambda ref, now: True,
		"thisweek": lambda ref, now: Date.weekdiff(ref,now)==0,
		"nextweek": lambda ref, now: Date.weekdiff(ref,now)==1,
		"lastweek": lambda ref, now: Date.weekdiff(ref,now)==-1,
		"thismonth": lambda ref, now: Date.monthdiff(ref,now)==0,
		"nextmonth": lambda ref, now: Date.monthdiff(ref,now)==1,
		"lastmonth": lambda ref, now: Date.monthdiff(ref,now)==-1,
	}
	class TaskFile:
		def __init__(self,name,date):
			self.__name = name
			self.__date = date
			self.load()
		def load(self):
			if not os.path.isfile(self.__name):
				tempfile = open(self.__name,"w")
				tempfile.write("# "+self.__date.str())
				tempfile.close()
			self.__file = open(self.__name,"r")
			self.__position = {}
			self.__updated = {}
			self.__file.seek(0,2)
			end = self.__file.tell()
			self.__file.seek(0)
			groupname = None
			number = 0
			def error(msg):
				raise Exception(self.__name+":"+str(number)+" # "+msg)
			while True:
				line = self.__file.readline().rstrip()
				number, line2 = number+1, line.lower()
				if self.__file.tell()==end: # last line
					temp = line[2:12]
					if line.startswith("#") and Date.regexp.match(temp):
						self.__lastrun = Date.deconvert(temp)
						break
					else: error("Premature File Termination")
				elif line.startswith("\t"):
					if len(line)>len(line.lstrip())+1: error("Excessive Indentation")
					elif not groupname: error("Unexpected Task")
					else: self.__position[groupname][1] = self.__file.tell()
				elif line2 in Task.sg or Date.regexp.match(line):
					if line in self.__position: error("Repeated Group")
					else: groupname, self.__position[line2] = line2, [self.__file.tell()]*2
				else: error("Unexpected Pattern")
			self.__process()
		def __process(self):
			if self.__lastrun==self.__date.date: return
			name = Date.convert(self.__lastrun)
			group = self.group(name)
			carry = []
			for task in group.task_list():
				temp = task.carryover(self.__lastrun)
				if not temp: continue
				carry.append(task)
				group.task_remove(task)
			self.update(group)
			while self.__lastrun < self.__date.date:
				self.__lastrun += Date.oneday
				name = Date.convert(self.__lastrun)
				group = self.group(name)
				for task in carry:
					group.task_add(task)
					task.group = group
				carry = []
				if self.__lastrun < self.__date.date:
					for task in group.task_list():
						temp = task.carryover(self.__lastrun)
						if not temp: continue
						group.task_remove(task)
						carry.append(task)
				for task in self.group("periodic").task_list():
					temp = task.periodic(self.__lastrun,group)
					if temp: group.task_add(temp)
				self.update(group)
		def __serialize(self,taskgroup):
			return "".join("\t"+task.raw()+"\n" for task in taskgroup.task_list(True))
		def __extract(self,position):
			self.__file.seek(position[0])
			return self.__file.read(position[1]-position[0])
		def save(self):
			index = 1
			while index:
				tempname = self.__name+"."+str(index)
				if os.path.exists(tempname): index += 1
				else: break
			tempfile = open(tempname,"w")
			for name in Task.sg:
				if name in self.__updated:
					data = self.__serialize(self.__updated[name])
					del self.__updated[name]
					if name in self.__position:
						del self.__position[name]
				elif name in self.__position:
					data = self.__extract(self.__position[name])
					del self.__position[name]
				else: continue
				if data: tempfile.write(name.title()+"\n"+data)
			for name in sorted( set(self.__updated.keys()+self.__position.keys()), reverse=True):
				if name in self.__updated: data = self.__serialize(self.__updated[name])
				else: data = self.__extract(self.__position[name])
				if data: tempfile.write(name+"\n"+data)
			tempfile.write("# "+self.__date.str())
			self.__file.close()
			tempfile.close()
			os.unlink(self.__name)
			os.rename(tempname,self.__name)
		def update(self,group):
			if not isinstance(group,TaskGroup): return
			self.__updated[group.name] = group
		def group(self,name):
			name = self.__date.translate(name) or name.lower()
			if name in self.__updated:
				return self.__updated[name]
			elif name in self.__position:
				group = TaskGroup([],name)
				for line in self.__extract(self.__position[name]).split("\n"):
					if line.strip()!="":
						group.task_add(Task(line[1:],group))
				return group
			elif name in Task.sg or Date.regexp.match(name):
				return TaskGroup([],name)
			else: raise Exception("Invalid Group")
		def select(self,name,words):
			name = name.lower()
			if name in daterange:
				temp = [ self.group(current).select(words).task_list() \
					for current in self.__position.keys() if current not in Task.sg \
					and daterange[name]( self.__date.date, self.__date.deconvert(current) ) ]
				return TaskGroup(task for sublist in temp for task in sublist)
			return self.group(name).select(words)
	exports["TaskFile"] = TaskFile
	return exports
define(exports())
def exports():
	exports = {}
	__dir__ = os.path.join(*os.path.split(__file__)[:-1]) \
		if os.path.basename(__file__)!=__file__ else "."
	actions = "list add edit delete move pending done failed".split()
	argerror = argparse.ArgumentTypeError
	def action(z):
		(x, y) = z.split(":",1) if ":" in z else (z, None)
		if x in actions: return (x, y or "today")
		else: raise Exception("Unknown Action")
	ap = argparse.ArgumentParser(description="A Command Line ToDoList Manager", add_help=False)
	ap.add_argument("action", nargs="?", type=action, default="list")
	ap.add_argument("data", nargs="*")
	ap.add_argument("-h","--help", action="store_true", default=False)
	ap.add_argument("-f","--file", default="./todolist.txt")
	ap.add_argument("--date", type=Date, default="today")
	ap.add_argument("--nosave", action="store_true", default=False)
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
			print task.group.tabulate(name)			
		else:
			task = __select(taskfile, name, args.data)
			if action in ("edit","delete","move"):
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
					try: group = taskfile.group(name)
					except: continue
					break
				__relocate(taskfile,task,group.name)
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
		if args.nosave:
			pass
		elif action=="list":
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
	return exports
define(exports())

if "main" in dir() and "__call__" in dir(main): main()

