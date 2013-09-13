#!/usr/bin/python

import argparse, copy, datetime, itertools, prettytable, re, readline, os, sys

class Tags:

	periodic = {
		"everyday": lambda x: True,
		"weekday": lambda x: x.weekday()<5,
		"weekend": lambda x: x.weekday()>4,
		"monday": lambda x: x.weekday()==0,
		"tuesday": lambda x: x.weekday()==1,
		"wednesday": lambda x: x.weekday()==2,
		"thursday": lambda x: x.weekday()==3,
		"friday": lambda x: x.weekday()==4,
		"saturday": lambda x: x.weekday()==5,
		"sunday": lambda x: x.weekday()==6,
	}

	status = "done partial failed".split()
	random = "hidden essential date".split()
	all = list(itertools.chain(periodic, status, random))

class Date:

	_dateformat = "%Y-%m-%d"
	_today = datetime.date.today()
	_1day = datetime.timedelta(1)

	today = _today.strftime(_dateformat)
	yesterday = (_today-_1day).strftime(_dateformat)
	tomorrow = (_today+_1day).strftime(_dateformat)

	pattern = "[0-9]{4}-[0-9]{2}-[0-9]{2}"
	recognized = "today yesterday tomorrow".split()

	@staticmethod
	def translate(data):
		if data=="today": return Date.today
		elif data=="yesterday": return Date.yesterday
		elif data=="tomorrow": return Date.tomorrow

class TaskList:

	# Special Groups
	special = { "Essential":["essential"], "Periodic": Tags.periodic }

	def __init__(self,datafile):
		self.name = datafile
		self.fileload()

	def get(self,group):
		if group not in self.data:
			self.data[group] = TaskGroup(self,group)
		return self.data[group]

	def delete(self,group):
		if group.name in self.data:
			del self.data[group.name]
		return group

	def select(self,query):
		if query.startswith("#"):
			result = TaskGroup(self,query)
			temp = map( lambda group: group.tag(query), self.data.values() )
			for task in itertools.chain(*temp): result.add(task)
		else: result = self.get(query)
		return result

	def fileload(self):
		if os.path.isfile(self.name):
			f = open(self.name,"r")
			self.raw = f.read()
			f.close()
		else:
			# raise Exception("Data File does not exist!");
			# TODO: Provide Warning at this point!
			self.raw = ""
		self.parse()

	def filesave(self):
		self.serialize()
		i = 0
		while True: # do
			name = self.name+"."+str(i)
			if not os.path.exists(name): break # while
			else: i = i+1
		f = open(name,"w");
		f.write(self.raw)
		f.close()
		if os.path.isfile(self.name):
			os.unlink(self.name)
		os.rename(name,self.name)
	
	# Group Heading Pattern
	re_date = re.compile("^"+Date.pattern+"|"+"|".join(special.keys())+"$")
	# Last Run Data
	re_last = re.compile("^# ("+Date.pattern+")$")

	def parse(self):
		self.data = {}
		group = Date.today
		lines = self.raw.split("\n")
		
		# check the last line to detect when this script was last run
		last = self.re_last.match(lines[-1])
		if last:
			lines.pop()
			self.lastrun = last.group(1)
		else:
			self.lastrun = Date.today
		
		# process the remaining lines
		for line in lines:
			if line.strip()=="": continue
			date = self.re_date.match(line)
			if date!=None: group = date.group()
			elif line.startswith("\t"):
				Task( self.get(group), line[1:] )

		# In case the last-run was yesterday or before, advance the date counter
		if "Periodic" in self.data:
			now = datetime.date(*map(int,self.lastrun.split("-")))
			while now < Date._today:
				now += Date._1day
				for task in self.get("Periodic"):
					task.iteration(now,self.get)

	def serialize(self):
		keys = sorted(self.data.keys())[::-1]
		# temp = list(itertools.takewhile(lambda x: x in TaskList.special, keys))
		rawdata = "\n".join( [self.data[name].serialize() for name in keys
			if not self.data[name].empty()] )
		self.raw = rawdata+"\n\n# "+Date.today

class TaskGroup:

	def __init__(self,tlist,name):
		self.list = tlist
		self.name = name
		self.data = []

	def tag(self,tag):
		return filter(lambda x: tag in x.tags(), self.data)

	def add(self,task):
		self.data.append(task)

	def get(self,data,remove=False):
		if isinstance(data,Task): # task -> index
			task = data
			if task not in self.data:
				raise Exception("TaskGroup.get.unknown-value-1")
			index = self.data.index(task)
			if not remove: return index
			else:
				self.data.pop(index)
				return index
		else: # index -> task
			index = int(data)
			if index<=0 or index>len(self.data):
				raise Exception("TaskGroup.get.unknown-value-2")
			return self.data.pop(index-1) if remove else self.data[index-1]

	def delete(self,index):
		temp = self.get(index,True)
		if len(self.data)==0:
			self.list.delete(self)
		return temp

	def tabulate(self):
		t = 1 if self.name=="Periodic" else 0
		fields = ["ID","Task","Tags",["Status","Frequency"][t]]
		table = prettytable.PrettyTable(fields, padding_width=1)
		for i in fields: table.align[i] = "l"
		index = 0
		for task in self:
			tags = task.tags()
			if "#hidden" in tags: continue
			else: index = index+1
			if t==1:
				temp = map(lambda x: x[1:], tags)
				temp = filter(lambda x: x in Tags.periodic, temp)
				data = ", ".join(temp)
			else:
				temp = (x for x in Tags.status if "#"+x in tags)
				data = next(temp, "pending") # first match
			temp = map(lambda x: x[1:], tags)
			temp = filter(lambda x: x not in Tags.all, temp)
			tags2 = ", ".join( temp )
			table.add_row([index ,task.text(), tags2, data ])
		return "\n"+table.get_string()+"\n"

	def __iter__(self):
		self.index = 0
		return self

	def next(self):
		if self.index < len(self.data):
			temp = self.data[self.index]
			self.index = self.index + 1
			return temp
		else:
			del self.index
			raise StopIteration
	
	def empty(self):
		return len(self.data)==0

	def serialize(self):
		return self.name+"\n"+"\n".join(["\t"+task.raw for task in self.data])

class Task:

	re_date = re.compile(Date.pattern+"|"+"|".join(Date.recognized))
	@classmethod
	def fn_tag(self,x): return x.startswith("#")
	@classmethod
	def fn_date(self,x): return self.fn_tag(x) and self.re_date.match(x[1:])
	@classmethod
	def fn_status(self,x): return self.fn_tag(x) and x[1:] in Tags.status
	@classmethod
	def fn_periodic(self,x): return self.fn_tag(x) and x[1:] in Tags.periodic

	def __init__(self, group, raw):
		self.group = group
		self.group.add(self)
		self.update(raw)

	def reject(self,fn):
		self.raw = " ".join(filter( lambda x: not fn(x), self.raw.split() ))

	def tags(self):
		return filter(self.fn_tag, self.raw.split())

	def text(self):
		return " ".join(filter(lambda x: not self.fn_tag(x), self.raw.split()))

	def tag_add(self,tag):
		if self.fn_tag(tag):
			self.raw = " ".join(self.raw.split()+[tag])

	def tag_del(self,tag):
		if self.fn_tag(tag):
			self.reject(lambda x: x==tag)

	def update(self,raw):
		self.raw = raw
		tlist = self.group.list # the tasklist which contains all groups
		flag = False # is this a special group
		tags = self.tags()
		for key in TaskList.special:
			if flag: break
			for val in TaskList.special[key]:
				if flag: break
				if "#"+val.lower() in tags:
					flag = True
					if self.group.name!=key:
						self.group.delete(self)
						self.group = tlist.get(key)
						self.group.add(self)

		# in case of essential tasks, discard all periodic tags
		if self.group.name=="Essential":
			self.reject(self.fn_periodic)

		# in case of periodic tasks, discard all status tags
		if self.group.name=="Periodic":
			self.reject(self.fn_status)

		# if this is a general task, ensure that the date is proper
		if not flag:
			temp = filter(self.fn_date, self.tags())
			group = temp[-1][6:] if len(temp)>0 else self.group.name
			if Date.translate(group): group = Date.translate(group)
			elif group in TaskList.special: group = Date.today
			if group!=self.group.name:
				self.group.delete(self)
				self.group = tlist.get(group)
				self.group.add(self)

		# in case of all tasks, remove all date tags (as they have been processed above)
		self.reject(self.fn_date)

	def iteration(self, now, group_get):
		temp = filter( self.fn_periodic, self.tags() )
		temp = map( lambda x: Tags.periodic[x[1:]](now), temp)
		if any(temp):
			# duplicate this task
			task = copy.deepcopy(self)
			# remove all periodic tags, since this is now a normal task
			task.reject(self.fn_periodic)
			# change the group
			group = now.strftime(Date._dateformat)
			task.group = group_get(group)
			task.group.add(task)
		

# Command-Line Option Validators (clov)

class clov:
	@staticmethod
	def action(data):
		if data in "add delete edit list done failed partial".split(): return data;
		else: return None
	@staticmethod
	def group(data):
		if data[0].startswith(("#",":"),0): return "#"+data[1:]
		elif data.title() in TaskList.special: return data.title()
		elif Date.translate(data): return Date.translate(data)
		elif TaskList.re_date.match(data): return data
		else: return None
	@classmethod
	def process(self,args):
		if not args.x: # no arguments
			args.action = "list"
			args.group = Date.today
		elif not args.y: # one argument
			args.action = self.action(args.x)
			args.group = Date.today
			if not args.action:
				args.action = "list"
				args.group = self.group(args.x)
			if not args.group: return None
		else: # two arguments
			args.action = clov.action(args.x)
			if args.action: args.group = clov.group(args.y)
			else:
				args.action = self.action(args.y)
				args.group = self.group(args.x)
			if not args.action or not args.group: return None
		return args

# User Interaction Functions

def confirm(msg="Are you sure you wish to save this change?"):
	while True:
		x = raw_input(msg+" (yes/no) ")
		if x=="yes": return True
		elif x=="no": return False

def prompt(prompt, prefill=""):
	readline.set_startup_hook(lambda: readline.insert_text(prefill))
	try: return raw_input(prompt)
	finally: readline.set_startup_hook()

def main():

	ap = argparse.ArgumentParser(description="To Do List",epilog="Author: Kaustubh Karkare")
	ap.add_argument("--datafile", default="todolist.txt", help="Data File Path")
	ap.add_argument("x", nargs="?", metavar="action", help="The Action to be performed.")
	ap.add_argument("y", nargs="?", metavar="group", help="The Group to which it must be applied.")
	args = ap.parse_args(sys.argv[1:])
	if not clov.process(args): raise Exception("Could not parse Command-Line Options.")

	l = TaskList(args.datafile)
	l.filesave()

	g = l.select(args.group)
	_g = copy.deepcopy(g)

	if args.action!="list": print g.tabulate()
	if args.action=="list": pass
	elif args.action=="add":
		t = Task(g,prompt("Create Task: "))
		if confirm("Are you sure you want to create this task?"):
			t.iteration(Date._today,l.get)
			l.filesave()
		else: g = _g
	elif args.action=="edit":
		t = g.get(prompt("Select Task ID for Modification: "))
		t.update(prompt("Update Task: ",t.raw))
		if confirm("Are you sure you want to update this task?"):
			l.filesave()
			t.iteration(Date._today,l.get)
			g = t.group
		else: g = _g
	elif args.action=="delete":
		g.delete(prompt("Select Task ID for Deletion: "))
		if confirm("Are you sure you want to delete this task?"): l.filesave()
		else: g = _g
	else: print "argparse:", args
	print g.tabulate()

if __name__ == "__main__":
	main()
	try: pass
	except Exception as e:
		print "Error:", e, "\n"
