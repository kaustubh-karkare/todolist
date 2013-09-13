#!/usr/bin/python

import argparse, copy, datetime, itertools, prettytable, re, readline, os, sys

class TaskFile:
	dateformat = "%Y-%m-%d"
	today = datetime.date.today().strftime(dateformat)
	re_date = re.compile("^[0-9]{4}-[0-9]{2}-[0-9]{2}|Longterm|Periodic$")

	def __init__(self,datafile):
		self.name = datafile
		self.load()

	def load(self):
		if not os.path.isfile(self.name):
			raise Exception("Data File does not exist!");
		f = open(self.name,"r")
		self.data = self.parse( f.read() )
		f.close()
	def save(self):
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
	def select(self,query):
		if query.startswith("#"):
			result = TaskGroup(query)
			temp = map( lambda group: group.tag(query), self.data.values() )
			for task in itertools.chain(*temp): result.add(task)
		elif query in self.data: result = self.data[query]
		else: result = self.data[query] = TaskGroup(query)
		return result
	
	def parse(self, rawdata):
		data, group = {}, self.today
		for line in rawdata.split("\n"):
			if line.strip()=="": continue
			date = self.re_date.match(line)
			if date!=None: group = date.group()
			elif line.startswith("\t"):
				if group not in data: data[group] = TaskGroup(group)
				data[group].add(Task(line[1:]))
		return data
	def serialize(self,data):
		keys = sorted(data.keys())[::-1]
		if len(keys)>1 and keys[0]=="Periodic" and keys[1]=="Longterm": keys[0], keys[1] = keys[1], keys[0]
		rawdata = "\n".join([data[name].serialize() for name in keys if not data[name].empty()])+"\n"
		return rawdata

class TaskGroup:
	def __init__(self,name):
		self.name = name
		self.data = []
	def tag(self,tag):
		return filter(lambda x: tag in x.tag, self.data)

	def add(self,task):
		self.data.append(task)
	def get(self,index,remove=False):
		if isinstance(index,Task):
			i = self.data.index(index)
			if not remove: return i
			self.data.pop(i)
			return i
		else:
			index = int(index)
			if index<=0 or index>len(self.data):
				raise ValueError("Invalid Index")
				return self.data.pop(index-1) if remove else self.data[index-1]
	def delete(self,index): return self.get(index,True)

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
	re_opt = re.compile("\\$([a-z]+)(?:\\=([^ ]+))?")
	re_ws = re.compile("\s+")
	default_options = {
		"status": "pending",
		"date": TaskFile.today,
		"longterm": None,
		"repeat": None,
		"comment": None
	}

	def __init__(self,raw):
		self.update(raw)
	def update(self,raw):
		self.raw = raw
		self.tag = self.re_tag.findall(self.raw)
		self.opt = dict(self.default_options, **dict([
			(item[0],True) if len(item)==1 else item
				for item in self.re_opt.findall(self.raw)
			if item[0] in self.default_options] ))

		self.text = raw
		self.text = self.re_tag.sub("",self.text)
		self.text = self.re_opt.sub("",self.text)
		self.text = self.re_ws.sub(" ",self.text)

def relocate(f,g,t):
	pass

# Command-Line Option Validators (clov)

class clov:
	@staticmethod
	def action(data):
		if data in "add delete edit list done failed partial".split(): return data;
		else: return None
	@staticmethod
	def group(data):
		if data[0].startswith(("#",":"),0): return "#"+data[1:]
		elif data=="longterm": return "Longterm"
		elif data=="periodic": return "Periodic"
		elif data in "today tomorrow yesterday".split():
			x = datetime.date.today()
			if data=="yesterday": x -= datetime.timedelta(1)
			elif data=="tomorrow": x += datetime.timedelta(1)
			return x.strftime(TaskFile.dateformat)
		elif TaskFile.re_date.match(data): return data
		else: return None
	@classmethod
	def process(self,args):
		if not args.x: # no arguments
			args.action = "list"
			args.group = TaskFile.today
		elif not args.y: # one argument
			args.action = self.action(args.x)
			args.group = TaskFile.today
			if not args.action:
				args.action = "list"
				args.group = self.group(args.x)
			if not args.group: return None
		else: # two arguments
			args.action = clov_action(args.x)
			if args.action: args.group = clov_group(args.y)
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

	f = TaskFile(args.datafile)
	g = f.select(args.group)
	_g = copy.deepcopy(g)
	if args.action!="list": print g.tabulate()
	if args.action=="list": pass
	elif args.action=="add":
		g.add(Task(prompt("Create Task: ")))
		if confirm("Are you sure you want to create this task?"): f.save()
		else: g = _g
	elif args.action=="edit":
		t = g.get(prompt("Select Task ID for Modification: "))
		t.update(prompt("Update Task: ",t.raw))
		relocate(f,g,t) # ensure that the task is part of the appropriate group
		if confirm("Are you sure you want to update this task?"): f.save()
		else: g = _g
	elif args.action=="delete":
		g.delete(prompt("Select Task ID for Deletion: "))
		if confirm("Are you sure you want to delete this task?"): f.save()
		else: g = _g
	else: print "argparse:", args
	print g.tabulate()

if __name__ == "__main__": main()
