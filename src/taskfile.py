
import os
require date, task

class TaskFile:

	def __init__(self,name):

		self.name = name
		self.file = open(self.name,"r")
		self.position = {}

		self.scan()

	def scan(self):

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

	def save(self,updated=[],deleted=[]):

		index = 1
		while index:
			tempname = self.name+"."+str(index)
			if os.path.exists(tempname): index += 1
			else: break
		tempfile = open(tempname,"w")

		updated = dict((group.name, group) for group in updated)
		deleted = dict((group.name, group) for group in deleted)

		def serialize(taskgroup):
			return "".join("\t"+task.raw+"\n" for task in taskgroup.tasks)
		def transfer(position):
			self.file.seek(position[0])
			return self.file.read(position[1]-position[0])

		# special groups first
		for name in Task.sg:
			if name in deleted:
				continue
			elif name in updated:
				data = serialize(updated[name])
				del updated[name]
			elif name in self.position:
				data = transfer(self.position[name])
				del self.position[name]
			else: continue
			tempfile.write(name+"\n"+data)

		# individual dates
		for name in sorted( set(updated.keys()+self.position.keys()), reverse=True):
			if name in deleted: continue # or not Date.regexp.match(name)
			elif name in updated: data = serialize(updated[name])
			else: data = transfer(self.position[name])
			tempfile.write(name+"\n"+data)

		tempfile.close()
		os.unlink(self.name)
		os.rename(tempname,self.name)

exports["TaskFile"] = TaskFile