
import os
require date, task, taskgroup

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
		
		self.__periodic()

	def __periodic(self):
		while self.__lastrun < self.__date.date:
			self.__lastrun += Date.oneday
			name = Date.convert(self.__lastrun)
			group = self.group(name)
			for task in self.group("Periodic").task_list():
				temp = task.iteration(self.__lastrun,group)
				if temp: group.task_add(temp)
			self.update(name,group)

	def __serialize(self,taskgroup):
		return "".join("\t"+task.raw()+"\n" for task in taskgroup.task_list(True))

	def __extract(self,position):
		self.__file.seek(position[0])
		return self.__file.read(position[1]-position[0])

	def save(self):

		# create the temporary file
		index = 1
		while index:
			tempname = self.__name+"."+str(index)
			if os.path.exists(tempname): index += 1
			else: break
		tempfile = open(tempname,"w")

		# special groups first
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

		# individual dates
		for name in sorted( set(self.__updated.keys()+self.__position.keys()), reverse=True):
			if name in self.__updated: data = self.__serialize(self.__updated[name])
			else: data = self.__extract(self.__position[name])
			if data: tempfile.write(name+"\n"+data)

		# save today's date
		tempfile.write("# "+self.__date.str())

		# replace the original with the temporary file
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