
require date

periodic = { # function arguments: datetime.date instance
	"everyday": lambda date: True,
	"weekdays": lambda date: date.weekday()<5,
	"weekends": lambda date: date.weekday()>4,
}
for index,name in enumerate("monday tuesday wednesday thursday friday saturday sunday".split()):
	periodic[name] = (lambda x: lambda date: date.weekday()==x)(index)

status = "failed done".split()

prefix = "#"
prefixlen = len(prefix)

def istagstr(str): return len(str)>0 and len(str.split())==1
def istag(tag): return tag.startswith(prefix) and istagstr(tag[prefixlen:])

# end of tag related declarations

class Task:

	def __init__(self,raw,group,date):
		self.update(raw,date)
		self.group = group

	def update(self,raw,date):
		self.__raw = raw
		self.__tags = [tag.lower() for tag in self.__raw.split() if istag(tag)]
		self.__tags = [tag[prefixlen:] for tag in self.__tags]

		temp = len(self.__tags)
		if "essential" in self.__tags or any(tag in periodic for tag in self.__tags):
			self.__tags = [i for i in self.__tags if not i.startswith("deadline=")]
		
		temp = []
		for tag in self.__raw.split():
			if not istag(tag): temp.append(tag)
			elif tag[prefixlen:] in self.__tags:
				if tag[prefixlen:].startswith("deadline="):
					x = date.translate(tag[prefixlen+9:])
					self.__tags.remove(tag[prefixlen:])
					if x:
						x = tag[:prefixlen+9]+x
						temp.append(x)
						self.__tags.append(x[prefixlen:])
				else: temp.append(tag)
		self.__raw = " ".join(temp)

	def __eq__(self,other): return isinstance(other,self.__class__) and self.__raw==other.__raw
	def __ne__(self,other): return not self.__eq__(other)
	def __hash__(self): return self.__raw.__hash__()
	def __contains__(self,word): return isinstance(word,str) and word.lower() in self.__raw.lower()
	def __repr__(self): return self.__raw

	def raw(self): return self.__raw

	table_heading = "Date Task Tags Periodicity Deadline Status".title().split()

	def table_fields(self,date):
		text = " ".join(word for word in self.__raw.split() if not istag(word))
		tags = ", ".join(tag for tag in self.__tags if tag not in status and \
			tag not in periodic and not tag.startswith("deadline=") and tag!="essential")
		freq = ", ".join([tag for tag in self.__tags if tag in periodic])
		dead = next((tag[9:] for tag in self.__tags if tag.startswith("deadline=")), \
			"No Limit" if "essential" in self.__tags else "")
		stat = self.status(date).title()
		return [self.group.name if self.group else "", text, tags, freq, dead, stat]

	sg = "periodic".split() # special group names

	def tag_add(self,tag,date):
		if istagstr(tag) and tag not in self.__tags:
			self.update( " ".join(self.__raw.split()+[prefix+tag]), date )
			return True
		return False

	def tag_check(self,tag):
		return tag in self.__tags

	def tag_remove(self,tag,date):
		if istagstr(tag) and tag in self.__tags:
			tag = prefix + tag # eliminates recomputation
			temp = [i for i in self.__raw.split() if i!=tag]
			self.update( " ".join(temp), date )
			return True
		return False

	def status(self,date):
		result = next((tag for tag in self.__tags if tag in status),None)
		if result: return result
		if "essential" in self.__tags: return "pending"
		deadline = next((tag[9:] for tag in self.__tags if tag.startswith("deadline=")),None)
		deadline = deadline and Date.deconvert(deadline) \
			or self.group and Date.regexp.match(self.group.name) and Date.deconvert(self.group.name)
		if not deadline or date.date<=deadline: return "pending"
		return "failed"

	def carryover(self,date):
		if any(i in status for i in self.__tags): return
		for tag in self.__tags:
			if tag=="essential" \
				or tag.startswith("deadline=") \
				and Date.regexp.match(tag[9:]) \
				and date.date<Date.deconvert(tag[9:]):
				return True

	def periodic(self,date,group):
		if not self.group or self.group.name!="periodic": return
		tags = filter(lambda tag: tag in periodic, self.__tags)
		if not any(periodic[name](date.date) for name in tags): return
		temp = [tag for tag in self.__raw.split() \
			if not istag(tag) or tag[prefixlen:] not in status and not tag.startswith("deadline=")]
		return self.__class__( " ".join(temp), group )

exports["Task"] = Task