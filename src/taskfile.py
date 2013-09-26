
import datetime, os, re
require date, task, taskgroup

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
	"tillnow": lambda ref, now: ref>=now,
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

		if self.__lastrun.date>=self.__date.date: return

		today = self.__date
		self.__date = self.__lastrun
		del self.__lastrun

		# get list of incomplete tasks with deadlines
		group = self.group(self.__date.str())
		carry = []
		for task in group.task_list():
			temp = task.carryover()
			if not temp: continue
			carry.append(task)
			group.task_remove(task)
		self.update(group)

		while self.__date.date < today.date:

			# get the current group and add carried over tasks
			self.__date.update(self.__date.date+Date.oneday)
			group = self.group(self.__date.str())
			for task in carry:
				group.task_add(task)
				task.group = group
			carry = []

			# for all periodic groups, add if applicable
			for task in self.group("periodic").task_list():
				temp = task.periodic(group)
				if temp: group.task_add(temp)

			for task in self.group("birthdays").task_list():
				temp = task.birthday(group)
				if temp: group.task_add(temp)

			# for all iterations except the last, calculate carry
			if self.__date.date < today.date:
				for task in group.task_list():
					temp = task.carryover()
					if not temp: continue
					group.task_remove(task)
					carry.append(task)

			self.update(group)

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
					group.task_add(Task(line[1:],group,self.__date))
			return group
		elif name in Task.sg or Date.regexp.match(name):
			return TaskGroup([],name)
		# else: raise Exception("Invalid Group")

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