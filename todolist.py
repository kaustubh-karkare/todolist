#!/usr/bin/python

import argparse, copy, datetime, itertools, prettytable, re, readline, os, sys

class TaskList:

	dateformat = "%Y-%m-%d"
	today = datetime.date.today().strftime(dateformat)
	special = "Longterm Periodic".split()
	re_date = re.compile("^[0-9]{4}-[0-9]{2}-[0-9]{2}|"+"|".join(special)+"$")

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
		if not os.path.isfile(self.name):
			raise Exception("Data File does not exist!");
		f = open(self.name,"r")
		self.data = self.parse( f.read() )
		f.close()

	def filesave(self):
		i = 0
		while True: # do
			name = self.name+"."+str(i)
			if not os.path.exists(name): break # while
			else: i = i+1
		f = open(name,"w");
		f.write(self.serialize(self.data))
		f.close()
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
		temp = list(itertools.takewhile(lambda x: x in self.special, keys))
		keys = sorted(temp, key = lambda x: self.special.index(x) ) + keys[len(temp):]
		rawdata = "\n".join([data[name].serialize() for name in keys if not data[name].empty()])+"\n"
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
		f = ["ID","Task","Tags","Status"]
		t = prettytable.PrettyTable(f, padding_width=1)
		for i in f: t.align[i] = "l"
		for index, task in enumerate(self.data):
			if task.opt["comment"]: continue
			t.add_row([index+1 ,task.text, ", ".join(map(lambda x: x[1:], task.tag)), task.opt["status"] ])
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

	re_tag = re.compile("\\#[^ ]+")
	re_opt = re.compile("\\$([a-z]+)\\=([^ ]+) ?")
	re_opt_date = re.compile("\\$date\\=[^ ]+ ?")
	default_options = {
		"status": "pending",
		"date": TaskList.today,
		"longterm": None,
		"periodic": None,
		"comment": None
	}

	def __init__(self, group, raw):
		self.group = group
		self.group.add(self)
		self.update(raw)

	def update(self,raw):
		self.raw = raw

		self.tag = self.re_tag.findall(self.raw) # extract task tags
		if self.group.name in TaskList.special: pos = [(self.group.name.lower(),True)]
		else: pos = [("date",self.group.name)]
		self.opt = dict(self.default_options, **dict( pos +
			[ (item[0],None if item[1] in ("0","False","No","None") else item[1])
				for item in self.re_opt.findall(self.raw) if item[0] in self.default_options ]
			))
		# remove all tags & options before tabulation
		self.text = raw
		self.text = self.re_tag.sub("",self.text)
		self.text = self.re_opt.sub("",self.text)
		# ensure that the task is part of the appropriate group
		gn = self.group.name
		tlist = self.group.list
		for key in TaskList.special:
			if self.opt[key.lower()] is not None:
				if self.group.name!=key:
					self.group.delete(self)
					self.group = tlist.get(key)
					self.group.add(self)
				break
		else:
			if self.opt["date"]!=self.group.name:
				self.group.delete(self)
				self.group = tlist.get(self.opt["date"])
				self.group.add(self)
		self.raw = self.re_opt_date.sub("",self.raw)

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
