#!/usr/bin/python

import datetime, re, os

class TaskFile:
	def __init__(self,datafile):
		self.name = datafile
		if not os.path.isfile(self.name):
			raise Exception("Data File does not exist!");
		f = open(self.name,"r")
		self.data = TaskFile.parse( f.read() )
		f.close()
	def save(self):
		i = 0
		while True: # do
			name = self.name+"."+str(i)
			if not os.path.exists(name): break # while
			else: i = i+1
		f = open(name,"w");
		f.write(TaskFile.serialize(self.data))
		f.close()
		os.unlink(self.name)
		os.rename(name,self.name)
	
	@staticmethod
	def parse(rawdata):
		re_date = re.compile("^[0-9]{4}-[0-9]{2}-[0-9]{2}|Longterm|Periodic$")
		data, group = {}, datetime.date.today().strftime("%Y-%m-%d")
		for line in rawdata.split("\n"):
			if line.strip() is "": continue
			date = re_date.match(line)
			if date is not None: group = date.group()
			elif line.startswith("\t"):
				if group not in data: data[group] = []
				data[group].append(line[1:])
		return data
	@staticmethod
	def serialize(data):
		keys = sorted(data.keys())[::-1]
		if len(keys)>1 and keys[0] is "Periodic" and keys[1] is "Longterm": keys[0], keys[1] = keys[1], keys[0]
		rawdata = "\n".join([name+"\n"+"\n".join(["\t"+task for task in data[name]]) for name in keys])+"\n"
		#print "Serialized:", repr(rawdata)
		return rawdata

x = TaskFile("todolist.txt")
x.save()
