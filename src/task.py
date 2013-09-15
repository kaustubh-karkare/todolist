
periodic = { # function arguments: datetime.date instance
	"everyday": lambda date: True,
	"weekdays": lambda date: date.weekday()<5,
	"weekends": lambda date: date.weekday()>4,
}
for index,name in enumerate("monday tuesday wednesday thursday friday saturday sunday".split()):
	periodic[name] = (lambda x: lambda date: date.weekday()==x)(index)

essential = "essential"
status = "done failed".split()

prefix = "#"
prefixlen = len(prefix)

def istagstr(str): return len(str)>0 and len(str.split())==1
def istag(tag): return tag.startswith(prefix) and istagstr(tag[prefixlen:])

# end of tag related declarations

class Task:

	def __init__(self,raw):
		self.update(raw)

	def update(self,raw):
		self.__raw = raw
		self.__tags = filter( istag, self.__raw.split() )
		self.__tags = [tag[prefixlen:] for tag in self.__tags]

		temp = len(self.__tags)
		if essential in self.__tags:
			self.__tags = [i for i in self.__tags if i not in periodic]
		elif any(i in periodic for i in self.__tags):
			self.__tags = [i for i in self.__tags if i not in status]
		elif any(i in status for i in self.__tags):
			if essential in self.__tags: self.__tags.remove(essential)
		if len(self.__tags)<temp:
			temp = [i for i in self.__raw.split() \
				if not istag(i) or i[prefixlen:] in self.__tags]
			self.__raw = " ".join(temp)

	def __eq__(self,other): return isinstance(other,self.__class__) and self.__raw==other.__raw
	def __ne__(self,other): return not self.__eq__(other)
	def __str__(self): return self.__raw
	def __contains__(self,word): return isinstance(word,str) and word.lower() in self.__raw.lower()

	def text(self):
		"Returns the task-string with all tags removed."
		return " ".join(word for word in self.__raw.split() if not istag(word))

	sg = ["Essential","Periodic"] # special group names

	def group(self,today):
		"Returns the group this task should be a part of."
		if essential in self.__tags: return sg[0]
		elif any([i in self.__tags for i in periodic]): return sg[1]
		else:
			gen = (i[5:] for i in self.__tags if i.startswith("date="))
			return next( gen, today )

	def tag_list(self):
		return self.__tags

	def tag_add(self,tag):
		if istagstr(tag) and tag not in self.__tags:
			self.update( " ".join(self.__raw.split()+[prefix+tag]) )
			return True
		return False

	def tag_delete(self,tag):
		if istagstr(tag) and tag in self.__tags:
			tag = prefix + tag # eliminates recomputation
			temp = [i for i in self.__raw.split() if i!=tag]
			self.update( " ".join(temp) )
			return True
		return False

	def iteration(self,date):
		tags = filter(lambda tag: tag in periodic, self.__tags)
		if not any(periodic[name](date) for name in tags): return
		temp = [i for i in self.__raw.split() \
			if not istag(i) or i[prefixlen:] not in tags]
		return self.__class__( " ".join(temp) )

exports["Task"] = Task

#!eof

def test():
	from datetime import date
	today = date.today()
	t = Task("Eat Breakfast.\t#everyday")
	if t.tags!=["everyday"]: return 1
	if t.text()!="Eat Breakfast.": return 2
	if t.group(today)!="Periodic": return 3
	t2 = t.iteration(today)
	if t2.text()!=t.text() or t2.tags==t.tags: return 4
	t.tag_add("essential")
	if "everyday" in t.tags: return 5
	t.tag_delete("essential")
	if t.group(today)!=today: return 6

if __name__ == "__main__": print test()
