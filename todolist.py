#!/usr/bin/python2
def define(scope):
	def actual(exports):
		scope.update(exports)
	return actual
define = define(vars())
import argparse, textwrap, datetime, sys, re, readline, os
def exports():
	exports = {}
	vc, hc, jc, pd, nl = "|-+ \n"
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
			elif isinstance(today,datetime.date):
				self.date = today
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
	periodic = { # function arguments: datetime.date instance
		"everyday": lambda date: True,
		"weekdays": lambda date: date.weekday()<5,
		"weekends": lambda date: date.weekday()>4,
	}
	for index,name in enumerate("monday tuesday wednesday thursday friday saturday sunday".split()):
		periodic[name] = (lambda x: lambda date: date.weekday()==x)(index)
	status = "failed impossible done".split()
	prefix = "+"
	prefixlen = len(prefix)
	def istagstr(str): return len(str)>0 and len(str.split())==1
	def istag(tag): return tag.startswith(prefix) and istagstr(tag[prefixlen:])
	class Task:
		def __init__(self,raw,group,date):
			self.__date = date
			self.group = group
			self.update(raw)
		def update(self,raw):
			self.__raw = raw
			self.__tags = [tag.lower()[prefixlen:] for tag in self.__raw.split() if istag(tag)]
			temp = []
			i = prefixlen+9 # len(prefix+"deadline=")
			for tag in self.__raw.split():
				if not istag(tag): temp.append(tag)
				elif tag[prefixlen:] in self.__tags:
					if tag[prefixlen:].startswith("deadline="):
						date = tag[i:]
						if date=="none":
							temp.append(tag)
							continue
						date = self.__date.translate(date)
						self.__tags.remove(tag[prefixlen:])
						if date:
							date = tag[:i]+date
							temp.append(date)
							self.__tags.append(date[prefixlen:])
					else: temp.append(tag)
			self.__raw = " ".join(temp)
		def __eq__(self,other): return isinstance(other,self.__class__) and self.__raw==other.__raw
		def __ne__(self,other): return not self.__eq__(other)
		def __hash__(self): return self.__raw.__hash__()
		def __repr__(self): return self.__raw
		def __contains__(self,word):
			suffix = "" if len(filter(lambda tag: tag in status, self.__tags))!=0 \
				else " "+prefix+"pending"
			return isinstance(word,str) and word.lower() in self.__raw.lower()+suffix
		def raw(self): return self.__raw
		table_heading = "Date Task Tags Periodicity Deadline Status".title().split()
		def table_fields(self):
			groupname = self.group.name if self.group else ""
			text = " ".join(word for word in self.__raw.split() if not istag(word))
			tags = ", ".join(tag for tag in self.__tags if tag not in status and \
				tag not in periodic and not tag.startswith("deadline="))
			freq = ", ".join([tag for tag in self.__tags if tag in periodic])
			deadline = next(("No Limit" if tag[9:]=="none" else tag[9:] \
				for tag in self.__tags if tag.startswith("deadline=")),"")
			stat = self.status().title()
			return [groupname, text, tags, freq, deadline, stat]
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
		def status(self):
			result = next((tag for tag in self.__tags if tag in status),None)
			if result: return result
			deadline = next((tag[9:] for tag in self.__tags if tag.startswith("deadline=")),None)
			if deadline: deadline = deadline!="none" and Date.deconvert(deadline)
			else: deadline = self.group and Date.regexp.match(self.group.name) and Date.deconvert(self.group.name)
			if not deadline or self.__date.date<=deadline: return "pending"
			return "failed"
		def carryover(self):
			if any(i in status for i in self.__tags): return
			for tag in self.__tags:
				if tag.startswith("deadline=") and ( tag[9:]=="none" or \
					Date.regexp.match(tag[9:]) and self.__date.date<Date.deconvert(tag[9:]) ):
					return True
		def periodic(self,group):
			if not self.group or self.group.name!="periodic": return
			tags = filter(lambda tag: tag in periodic, self.__tags)
			if not any(periodic[name](self.__date.date) for name in tags): return
			temp = [tag for tag in self.__raw.split() \
				if not istag(tag) or tag[prefixlen:] not in status]
			return self.__class__( " ".join(temp), group, self.__date )
	exports["Task"] = Task
	return exports
define(exports())
def exports():
	exports = {}
	class TaskGroup:
		def __init__(self,tasks,name=""):
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
				self.__tasks.sort(key=lambda x: x.raw().lower())
				self.__tasks.sort(key=lambda x: x.group and x.group.name, reverse=True)
		def task_remove(self,task):
			if isinstance(task,Task) and task in self.__tasks:
				self.__tasks.remove(task)
		def tabulate(self, index=False, heading=None):
			data = [Task.table_heading]
			data.extend( task.table_fields() for task in self.task_list() )
			if index:
				for i,row in enumerate(data):
					data[i] = ["Index" if i==0 else str(i-1)]+data[i]
			result, prefix = prettytable(data), ""
			if heading:
				x = result.find("\n")-len(heading)
				prefix = "="*(x/2-1)+" "+heading+" "+"="*(x-x/2-1)+"\n"
			return prefix+result+"\n"
		def select(self,words):
			words = [word for word in words if word!=""]
			if len(words)==0: return self.__class__( self.__tasks )
			tasks = []
			for task in self.__tasks:
				check = 1
				for word in words:
					if not word.startswith("~"): check &= word in task
					elif word.startswith("~~"): check &= word[1:] in task
					else: check &= word[1:] not in task
				if check: tasks.append(task)
			return self.__class__( tasks )
	exports["TaskGroup"] = TaskGroup
	return exports
define(exports())
def exports():
	exports = {}
	relative = {
		"forever": lambda ref, now: True,
		"thisweek": lambda ref, now: Date.weekdiff(ref,now)==0,
		"nextweek": lambda ref, now: Date.weekdiff(ref,now)==1,
		"lastweek": lambda ref, now: Date.weekdiff(ref,now)==-1,
		"thismonth": lambda ref, now: Date.monthdiff(ref,now)==0,
		"nextmonth": lambda ref, now: Date.monthdiff(ref,now)==1,
		"lastmonth": lambda ref, now: Date.monthdiff(ref,now)==-1,
		"future": lambda ref, now: ref<now,
		"past": lambda ref, now: ref>now,
	}
	absolute = {
		"month": lambda ref, now: map(int,ref.split("-"))==[now.year,now.month],
		"year": lambda ref, now: int(ref)==now.year
	}
	absolute["month"].regexp = re.compile("^\d{4}-\d{2}$")
	absolute["year"].regexp = re.compile("^\d{4}$")
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
						self.__lastrun = Date(temp)
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
			if self.__lastrun.date==self.__date.date: return
			group = self.group(self.__lastrun.str())
			carry = []
			for task in group.task_list():
				temp = task.carryover()
				if not temp: continue
				carry.append(task)
				group.task_remove(task)
			self.update(group)
			while self.__lastrun.date < self.__date.date:
				self.__lastrun = Date(self.__lastrun.date+Date.oneday)
				group = self.group(self.__lastrun.str())
				for task in carry:
					group.task_add(task)
					task.group = group
				carry = []
				if self.__lastrun.date < self.__date.date:
					for task in group.task_list():
						temp = task.carryover()
						if not temp: continue
						group.task_remove(task)
						carry.append(task)
				for task in self.group("periodic").task_list():
					temp = task.periodic(group)
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
						group.task_add(Task(line[1:],group,self.__date))
				return group
			elif name in Task.sg or Date.regexp.match(name):
				return TaskGroup([],name)
		def __select(self,words,condition):
			temp = [ self.group(current).select(words).task_list() \
				for current in self.__position.keys() \
				if current not in Task.sg and condition(current) ]
			return TaskGroup(task for sublist in temp for task in sublist)
		def select(self,name,words):
			name = name.lower()
			if name in relative:
				return self.__select(words, lambda current: \
					relative[name]( self.__date.date, Date.deconvert(current) ) )
			for key in absolute:
				if absolute[key].regexp.match(name):
					return self.__select(words, lambda current: \
						absolute[key]( name, Date.deconvert(current) ) )
			group = self.group(name)
			return group and group.select(words)
	exports["TaskFile"] = TaskFile
	return exports
define(exports())
def exports():
	exports = {}
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
	return exports
define(exports())
def exports():
	exports = {}
	__dir__ = os.path.join(*os.path.split(__file__)[:-1]) \
		if os.path.basename(__file__)!=__file__ else "."
	operations = "list add edit delete move done failed help".split()
	ap = argparse.ArgumentParser(description="A Command Line ToDoList Manager", add_help=False)
	ap.add_argument("data", nargs="*", default=[])
	ap.add_argument("-h","--help", action="store_true", default=False)
	ap.add_argument("-f","--file", default="./todolist.txt")
	ap.add_argument("-n","--nosave", action="store_true", default=False)
	ap.add_argument("-d","--date", type=Date, default="today")
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
	return exports
define(exports())

if "main" in dir() and "__call__" in dir(main): main()

