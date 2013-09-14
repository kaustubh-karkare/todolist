
import datetime, re

class Date:

	relative = {
		"yesterday": -1,
		"today": 0,
		"tomorrow": 1,
	}

	regexp = re.compile("\d{4}-\d{2}-\d{2}")
	format = "%Y-%m-%d"

	def __init__(self,today=None):

		self.date = datetime.date.today()
		self.__1day = datetime.timedelta(1)
		self.__relative = {}

		if today is None:
			pass
		elif today in self.relative:
			self.date += self.relative[today]*self.__1day
		elif self.regexp.match(today):
			datetime.date(*map(int,today.split("-")))

		for word in self.relative:
			temp = self.date + self.relative[word] * self.__1day
			self.__relative[word] = temp.strftime(self.format)
			self.__setattr__(word, self.__relative[word])

	def __valid(self,x):
		return x in self.relative or self.regexp.match(x) is not None

	def translate(self,x):
		if x in self.__relative: return self.__relative[x]
		elif self.regexp.match(x): return x

exports["Date"] = Date