
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

		self.__file = open(self.__name,"r")
		self.__position = {}
		self.reset()

		self.__file.seek(0,2)
		end = self.__file.tell()
		self.__file.seek(0)

		groupname = None
		number = 0
		def error(msg):
			raise Exception(self.__name+":"+str(number)+" # "+msg)

		while True:
			line, number = self.__file.readline().rstrip(), number+1
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
			elif line in Task.sg or Date.regexp.match(line):
				if line in self.__position: error("Repeated Group")
				else: groupname, self.__position[line] = line, [self.__file.tell()]*2
			else: error("Unexpected Pattern")
		
		self.__periodic()

	def __periodic(self):
		while self.__lastrun < self.__date.date:
			self.__lastrun += Date.oneday
			name = Date.convert(self.__lastrun)
			group = self.group(name)
			for task in self.group("Periodic").task_list():
				temp = task.iteration(self.__lastrun)
				if temp: group.task_add(temp)
			self.update(name,group)

	def reset(self):
		self.__updated = {}
		self.__deleted = {}

	def update(self,name,group):
		self.__updated[name] = group
		if name in self.__deleted:
			del self.__deleted[name]

	def delete(self,name,group=None):
		self.__deleted[name] = group
		if name in self.__updated:
			del self.__updated[name]

	def __serialize(self,taskgroup):
		return "".join("\t"+str(task)+"\n" for task in taskgroup.task_list())

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
			if name in self.__deleted:
				continue
			elif name in self.__updated:
				data = self.__serialize(self.__updated[name])
				del self.__updated[name]
			elif name in self.__position:
				data = self.__extract(self.__position[name])
				del self.__position[name]
			else: continue
			if data: tempfile.write(name+"\n"+data)

		# individual dates
		for name in sorted( set(self.__updated.keys()+self.__position.keys()), reverse=True):
			if name in self.__deleted: continue # or not Date.regexp.match(name)
			elif name in self.__updated: data = self.__serialize(self.__updated[name])
			else: data = self.__extract(self.__position[name])
			if data: tempfile.write(name+"\n"+data)

		# save today's date
		tempfile.write("# "+self.__date.today)

		# replace the original with the temporary file
		self.__file.close()
		tempfile.close()
		os.unlink(self.__name)
		os.rename(tempname,self.__name)

	def group(self,name):
		if name in self.__updated:
			return self.__updated[name]
		elif name in self.__deleted:
			return TaskGroup()
		elif name in self.__position:
			return TaskGroup( Task(line[1:]) for line in \
				self.__extract(self.__position[name]).split("\n") \
				if line.strip()!="" )
		elif name in Task.sg or Date.regexp.match(name):
			return TaskGroup()

	def select(self,name,words,date):
		if name.title() in Task.sg:
			return self.group(name.title()).select(words)
		temp = date.translate(name)
		if temp is not None:
			return self.group(temp).select(words)

		if name in daterange:
			temp = [ self.group(current).select(words) \
				for current in self.__position.keys() if current not in Task.sg \
				and daterange[name]( date.date, date.deconvert(current) ) ]
			return reduce(lambda x,y: x+y, temp) if len(temp) else TaskGroup()
		
		return TaskGroup()

exports["TaskFile"] = TaskFile