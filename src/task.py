
periodic = { # function arguments: datetime.date instance
	"everyday": lambda date: True,
	"weekdays": lambda date: date.weekday()<5,
	"weekends": lambda date: date.weekday()>4,
}
for index,name in enumerate("monday tuesday wednesday thursday friday saturday sunday".split()):
	periodic[name] = (lambda x: lambda date: date.weekday()==x)(index)

essential = "essential"
status = "failed done".split()

prefix = "#"
prefixlen = len(prefix)

def istagstr(str): return len(str)>0 and len(str.split())==1
def istag(tag): return tag.startswith(prefix) and istagstr(tag[prefixlen:])

# end of tag related declarations

class Task:

	def __init__(self,raw,group):
		self.update(raw)
		self.group = group

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
	def __hash__(self): return self.__raw.__hash__()
	def __contains__(self,word): return isinstance(word,str) and word.lower() in self.__raw.lower()
	def __repr__(self): return self.__raw

	def raw(self): return self.__raw

	table_heading = "Date Task Tags Status".title().split()

	def table_fields(self):
		text = " ".join(word for word in self.__raw.split() if not istag(word))
		tags = ", ".join(tag for tag in self.__tags if tag not in status)
		stat = next((tag for tag in self.__tags if tag in status), "pending").title()
		return [self.group.name, text, tags, stat]

	sg = "essential periodic".split() # special group names

	def groupname(self):
		if essential in self.__tags: return "essential"
		elif any([i in self.__tags for i in periodic]): return "periodic"

	def tag_add(self,tag):
		if istagstr(tag) and tag not in self.__tags:
			self.update( " ".join(self.__raw.split()+[prefix+tag]) )
			return True
		return False

	def tag_check(self,tag):
		return tag in self.__tags

	def tag_remove(self,tag):
		if istagstr(tag) and tag in self.__tags:
			tag = prefix + tag # eliminates recomputation
			temp = [i for i in self.__raw.split() if i!=tag]
			self.update( " ".join(temp) )
			return True
		return False

	def iteration(self,date,group):
		tags = filter(lambda tag: tag in periodic, self.__tags)
		if not any(periodic[name](date) for name in tags): return
		temp = [i for i in self.__raw.split() \
			if not istag(i) or i[prefixlen:] not in tags]
		return self.__class__( " ".join(temp), group )

exports["Task"] = Task