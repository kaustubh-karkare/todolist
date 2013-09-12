#!/usr/bin/python

import re, os

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
		lines = rawdata.split("\n")
		index, total = 0, len(lines)
		re_date = re.compile("^[0-9]{4}-[0-9]{2}-[0-9]{2}|Longterm|Periodic$")
		data = {}
		while index<total :
			line = lines[index]
			index = index + 1
			if line.strip() is "": continue
			date = re_date.match(line)
			if date is not None:
				group = data[date.group()] = []
				# print "Group", date.group()
				while index<total :
					line = lines[index]
					if not line.startswith("\t") and line.strip() is not "": break
					# print "Task", line[1:]
					index = index + 1
					if line.strip() is "": continue
					group.append(line[1:])
				continue
			raise Exception("Invalid Group!",line)
		return data
	@staticmethod
	def serialize(data):
		keys = sorted(data.keys())[::-1]
		if len(keys)>1 and keys[0] is "Periodic" and keys[1] is "Longterm": keys[0], keys[1] = keys[1], keys[0]
		rawdata = "\n".join([name+"\n"+"\n".join(["\t"+task for task in data[name]]) for name in keys])+"\n"
		# print "Serialized:", repr(rawdata)
		return rawdata

x = TaskFile("todolist.txt")
x.save()
