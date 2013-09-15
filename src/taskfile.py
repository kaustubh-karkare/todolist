
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

	def __init__(self,name):

		self.name = name
		self.load()

	def load(self):

		self.file = open(self.name,"r")
		self.position = {}

		number, groupname = 0, None
		def error(msg): raise Exception(self.name+":"+str(number)+" # "+msg)

		self.file.seek(0)
		while True:
			line, number = self.file.readline(), number+1
			if line=="": break # end of file
			line = line.rstrip()
			if line.startswith("\t"):
				if len(line)>len(line.lstrip())+1: error("Excessive Indentation")
				elif not groupname: error("Unexpected Task")
				else: self.position[groupname][1] = self.file.tell()
			elif line in Task.sg or Date.regexp.match(line):
				if line in self.position: error("Repeated Group")
				else: groupname, self.position[line] = line, [self.file.tell()]*2
			else: error("Unexpected Pattern")

	def __serialize(self,taskgroup):
		return "".join("\t"+str(task)+"\n" for task in taskgroup.task_list())

	def __extract(self,position):
		self.file.seek(position[0])
		return self.file.read(position[1]-position[0])

	def save(self,updated=[],deleted=[]):

		# create the temporary file
		index = 1
		while index:
			tempname = self.name+"."+str(index)
			if os.path.exists(tempname): index += 1
			else: break
		tempfile = open(tempname,"w")

		# convert argument lists into dicts
		updated = dict((group.name, group) for group in updated)
		deleted = dict((group.name, group) for group in deleted)

		# special groups first
		for name in Task.sg:
			if name in deleted:
				continue
			elif name in updated:
				data = self.__serialize(updated[name])
				del updated[name]
			elif name in self.position:
				data = self.__extract(self.position[name])
				del self.position[name]
			else: continue
			if data: tempfile.write(name+"\n"+data)

		# individual dates
		for name in sorted( set(updated.keys()+self.position.keys()), reverse=True):
			if name in deleted: continue # or not Date.regexp.match(name)
			elif name in updated: data = self.__serialize(updated[name])
			else: data = self.__extract(self.position[name])
			if data: tempfile.write(name+"\n"+data)

		# replace the original with the temporary file
		self.file.close()
		tempfile.close()
		os.unlink(self.name)
		os.rename(tempname,self.name)

	def group(self,name):
		if name in self.position:
			return TaskGroup( Task(line[1:]) for line in \
				self.__extract(self.position[name]).split("\n") \
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
				for current in self.position.keys() if current not in Task.sg \
				and daterange[name]( date.date, date.deconvert(current) ) ]
			return reduce(lambda x,y: x+y, temp) if len(temp) else TaskGroup()
		
		return TaskGroup()

exports["TaskFile"] = TaskFile