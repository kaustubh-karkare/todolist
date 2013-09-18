
require date

periodic = { # function arguments: datetime.date instance
	"everyday": lambda date: True,
	"weekdays": lambda date: date.weekday()<5,
	"weekends": lambda date: date.weekday()>4,
}
for index,name in enumerate("monday tuesday wednesday thursday friday saturday sunday".split()):
	periodic[name] = (lambda x: lambda date: date.weekday()==x)(index)

status = "failed impossible done".split()

prefix = "+"
prefixlen = len(prefix)

def istagstr(str): return len(str)>0 and len(str.split())==1
def istag(tag): return tag.startswith(prefix) and istagstr(tag[prefixlen:])

# end of tag related declarations

class Task:

	def __init__(self,raw,group,date):
		self.__date = date
		self.group = group
		self.update(raw)

	def update(self,raw):
		self.__raw = []
		self.__tags = []

		for word in raw.split():
			if not istag(word):
				self.__raw.append(word)
			else:
				tag = word.lower()[prefixlen:]
				index = tag.find("=")
				if index==-1:
					name = tag
					value = None
				else:
					name = tag[:index]
					value = tag[index:]
				start = prefix+name+(value or "")
				if any(word.startswith(start) for word in self.__raw if istag(word)):
					continue
				elif name=="deadline":
					if value=="none":
						self.__raw.append(prefix+tag)
						self.__tags.append(tag)
						continue
					date = self.__date.translate(value)
					if date:
						date = prefix+"deadline="+date
						self.__raw.append(prefix+date)
						self.__tags.append(date)
				else:
					self.__raw.append(prefix+tag)
					self.__tags.append(tag)

		self.__raw = " ".join(self.__raw)

	def __eq__(self,other): return isinstance(other,self.__class__) and self.__raw==other.__raw
	def __ne__(self,other): return not self.__eq__(other)
	def __hash__(self): return self.__raw.__hash__()
	def __repr__(self): return self.__raw
	def __contains__(self,word):
		suffix = "" if len(filter(lambda tag: tag in status, self.__tags))!=0 \
			else " "+prefix+"pending"
		return isinstance(word,str) and word.lower() in self.__raw.lower()+suffix

	def raw(self): return self.__raw

	table_heading = "Date Task Tags Periodicity Deadline Status".title().split()

	def table_fields(self):
		groupname = self.group.name if self.group else ""
		text = " ".join(word for word in self.__raw.split() if not istag(word))
		tags = ", ".join(tag for tag in self.__tags if tag not in status and \
			tag not in periodic and not tag.startswith("deadline="))
		freq = ", ".join([tag for tag in self.__tags if tag in periodic])
		deadline = next(("No Limit" if tag[9:]=="none" else tag[9:] \
			for tag in self.__tags if tag.startswith("deadline=")),"")
		# if not deadline and groupname not in self.sg: deadline = "(same-day)"
		stat = self.status().title()
		return [groupname, text, tags, freq, deadline, stat]

	sg = "periodic".split() # special group names

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

	def status(self):
		result = next((tag for tag in self.__tags if tag in status),None)
		if result: return result
		deadline = next((tag[9:] for tag in self.__tags if tag.startswith("deadline=")),None)
		if deadline: deadline = deadline!="none" and Date.deconvert(deadline)
		else: deadline = self.group and Date.regexp.match(self.group.name) and Date.deconvert(self.group.name)
		if not deadline or self.__date.date<=deadline: return "pending"
		return "failed"

	def carryover(self):
		if any(i in status for i in self.__tags): return
		for tag in self.__tags:
			if tag.startswith("deadline=") and ( tag[9:]=="none" or \
				Date.regexp.match(tag[9:]) and self.__date.date<Date.deconvert(tag[9:]) ):
				return True

	def periodic(self,group):
		if not self.group or self.group.name!="periodic": return
		tags = filter(lambda tag: tag in periodic, self.__tags)
		if not any(periodic[name](self.__date.date) for name in tags): return
		temp = [tag for tag in self.__raw.split() \
			if not istag(tag) or tag[prefixlen:] not in status]
		return self.__class__( " ".join(temp), group, self.__date )

exports["Task"] = Task