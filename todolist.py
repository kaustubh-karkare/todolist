#!/usr/bin/python

import argparse, copy, datetime, itertools, prettytable, re, readline, os, sys

class Tags:

	longterm = "longterm".split()
	periodic = "everyday weekday weekend monday tuesday wednesday thrusday friday saturday sunday".split()
	status = "done partial failed".split()
	random = "hidden"
	all = list(itertools.chain(longterm, periodic, status, random))

class TaskList:

	dateformat = "%Y-%m-%d"
	# Today's Date as a String
	today = datetime.date.today().strftime(dateformat)
	# Special Groups
	special = { "Longterm": Tags.longterm, "Periodic": Tags.periodic }
	# Group Heading Pattern
	re_date = re.compile("^[0-9]{4}-[0-9]{2}-[0-9]{2}|"+"|".join(special.keys())+"$")

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
			self.data = self.parse( f.read() )
			f.close()
		else:
			# raise Exception("Data File does not exist!");
			self.data = {}

	def filesave(self):
		i = 0
		while True: # do
			name = self.name+"."+str(i)
			if not os.path.exists(name): break # while
			else: i = i+1
		f = open(name,"w");
		f.write(self.serialize(self.data))
		f.close()
		if os.path.isfile(self.name):
			os.unlink(self.name)
		os.rename(name,self.name)
	
	def parse(self, rawdata):
		self.data = {}
		group = self.today
		for line in rawdata.split("\n"):
			if line.strip()=="": continue
			date = self.re_date.match(line)
			if date!=None: group = date.group()
			elif line.startswith("\t"):
				Task( self.get(group), line[1:] )
		return self.data

	def serialize(self,data):
		keys = sorted(data.keys())[::-1]
		rawdata = "\n".join([data[name].serialize() for name in keys if not data[name].empty()])
		return rawdata

class TaskGroup:

	def __init__(self,tlist,name):
		self.list = tlist
		self.name = name
		self.data = []

	def tag(self,tag):
		return filter(lambda x: tag in x.tag, self.data)

	def add(self,task):
		self.data.append(task)

	def get(self,index,remove=False):
		if isinstance(index,Task):
			if index not in self.data: return None
			i = self.data.index(index)
			if not remove: return i
			else:
				self.data.pop(i)
				return i
		else:
			index = int(index)
			if index<=0 or index>len(self.data):
				raise ValueError("Invalid Index")
			return self.data.pop(index-1) if remove else self.data[index-1]
	def delete(self,index):
		temp = self.get(index,True)
		if len(self.data)==0:
			self.list.delete(self)
		return temp

	def tabulate(self):
		p = 1 if self.name=="Periodic" else 0
		f = ["ID","Task","Tags","Frequency" if p else "Status"]
		t = prettytable.PrettyTable(f, padding_width=1)
		for i in f: t.align[i] = "l"
		for index, task in enumerate(filter(lambda x: "#hidden" not in x.tags, self.data)):
			if p: status = ", ".join( filter(lambda x: x in Tags.periodic, map(lambda x: x[1:], task.tags)) )
			else: status = next((x for x in Tags.status if "#"+x in task.tags),"pending")
			tags = ", ".join( filter(lambda x: x not in Tags.all, map(lambda x: x[1:], task.tags)) )
			t.add_row([index+1 ,task.text, tags, status ])
		return "\n"+t.get_string()+"\n"

	def __iter__(self):
		self.index = 0

	def next(self):
		if self.index <= len(self.data):
			temp = self.data[self.index]
			self.index = self.index + 1
			return temp
		else: del self.index
	
	def empty(self):
		return len(self.data)==0

	def serialize(self):
		return self.name+"\n"+"\n".join(["\t"+task.raw for task in self.data])

class Task:

	re_ws = re.compile("\s+")
	re_tag = re.compile("\\#[^ ]+")
	re_date = re.compile("\\#date\\=[0-9]{4}-[0-9]{2}-[0-9]{2}")

	def __init__(self, group, raw):
		self.group = group
		self.group.add(self)
		self.update(raw)

	def update(self,raw):
		self.raw = raw

		self.tags = map(str.lower, self.re_tag.findall(self.raw))
		self.text = self.re_tag.sub("",self.raw)
		self.text = self.re_ws.sub(" ",self.text).strip()

		tlist = self.group.list

		flag = False # is this a special group
		for key in TaskList.special:
			if flag: break
			for val in TaskList.special[key]:
				if flag: break
				if "#"+val.lower() in self.tags:
					flag = True
					if self.group.name!=key:
						self.group.delete(self)
						self.group = tlist.get(key)
						self.group.add(self)

		# if this is a general task but with date specified
		if not flag:
			temp = filter(lambda x: self.re_date.match(x), self.tags)
			group = temp[-1][6:] if len(temp)>0 else self.group.name
			if group in TaskList.special: group = TaskList.today
			if group!=self.group.name:
				self.group.delete(self)
				self.group = tlist.get(group)
				self.group.add(self)

		# remove all date tags
		self.raw = self.re_date.sub("",self.raw)
		self.raw = self.re_ws.sub(" ",self.raw).strip()
		self.tags = filter(lambda x: not self.re_date.match(x), self.tags)

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
		elif data in "today tomorrow yesterday".split():
			x = datetime.date.today()
			if data=="yesterday": x -= datetime.timedelta(1)
			elif data=="tomorrow": x += datetime.timedelta(1)
			return x.strftime(TaskList.dateformat)
		elif TaskList.re_date.match(data): return data
		else: return None
	@classmethod
	def process(self,args):
		if not args.x: # no arguments
			args.action = "list"
			args.group = TaskList.today
		elif not args.y: # one argument
			args.action = self.action(args.x)
			args.group = TaskList.today
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
		Task(g,prompt("Create Task: "))
		if confirm("Are you sure you want to create this task?"): l.filesave()
		else: g = _g
	elif args.action=="edit":
		t = g.get(prompt("Select Task ID for Modification: "))
		t.update(prompt("Update Task: ",t.raw))
		if confirm("Are you sure you want to update this task?"): l.filesave()
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
