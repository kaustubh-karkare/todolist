#!/usr/bin/python

import argparse, datetime, itertools, prettytable, re, os, sys

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
	def delete(self,index):
		if index<=0 or index>=len(self.data):
			raise IndexError("Invalid Index")
		return self.data.pop(index-1)

	def tabulate(self):
		f = ["ID","Task","Tags","Options"]
		t = prettytable.PrettyTable(f, padding_width=1)
		for i in f: t.align[i] = "l"
		for index, task in enumerate(self.data):
			t.add_row([index+1 ,task.text, ", ".join(map(lambda x: x[1:], task.tag)), task.opt])
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
		return self.name+"\n"+"\n".join(["\t"+task.text for task in self.data])

class Task:
	re_tag = re.compile("\\#[^ ]+")
	re_opt = re.compile("\\$[a-z]+(\\=[^ ]+)?")
	def __init__(self,text):
		self.text = text
		self.tag = self.re_tag.findall(self.text)
		self.opt = dict([ ((item[0],True) if len(item)==1 else item) for item in self.re_opt.findall(self.text)])


def ap_group(data):
	if data[0] in ("#",":"): return "#"+data[1:]
	elif data=="longterm": return "Longterm"
	elif data=="periodic": return "Periodic"
	elif data in "today tomorrow yesterday".split():
		x = datetime.date.today()
		if data=="yesterday": x -= datetime.timedelta(1)
		elif data=="tomorrow": x += datetime.timedelta(1)
		return x.strftime(TaskFile.dateformat)
	elif TaskFile.re_date.match(data): return data
	else: raise ValueError("Invalid Group")

def confirm(msg="Are you sure you wish to save this change? (yes/no) "):
	while True:
		x = raw_input(msg)
		if x=="yes": return True
		elif x=="no": return False

def main():

	ap = argparse.ArgumentParser(description="To Do List",epilog="Author: Kaustubh Karkare")
	ap.add_argument("--datafile", default="todolist.txt", help="Data File Path")
	ap.add_argument("action", nargs="?", default="list", choices="add delete edit list done failed partial".split())
	ap.add_argument("group", nargs="?", default=TaskFile.today, type=ap_group, help="Group selector.")
	ap.add_argument("data", nargs="?", default=1, type=int, help="Index within Group / Task String")
	args = ap.parse_args(sys.argv[1:])

	f = TaskFile(args.datafile)
	g = f.select(args.group)
	if args.action=="list":
		print g.tabulate()
	elif args.action=="add":
		t = Task(args.data)
		g.add(t)
		print g.tabulate()
		if confirm(): f.save()
	elif args.action=="delete":
		g.delete(args.data)
		print g.tabulate()
		if confirm(): f.save()
	else: print "argparse:", args

if __name__ == "__main__": main()
