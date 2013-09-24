
import fcntl, math, os, struct, termios, textwrap

# https://gist.github.com/jtriley/1108174
def __get_terminal_size_linux():
	def ioctl_GWINSZ(fd):
		try:
			cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
			return cr
		except:
			pass
	cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
	if not cr:
		try:
			fd = os.open(os.ctermid(), os.O_RDONLY)
			cr = ioctl_GWINSZ(fd)
			os.close(fd)
		except:
			pass
	if not cr:
		try:
			cr = (os.environ["LINES"], os.environ["COLUMNS"])
		except:
			return None
	return int(cr[1]), int(cr[0])

terminal = __get_terminal_size_linux()

vc, hc, jc, pd, nl = "|-+ \n"

def prettytable(rows,header=None,footer=None):
	if len(rows)==0: return

	width = [-1]*min(len(row) for row in rows)
	lword = [-1]*len(width) # largest word
	for row in rows:
		for j, col in enumerate(row):
			width[j] = max(width[j],len(col))
			lword[j] = max(lword[j], max(len(word) for word in col.split(" ")) )

	if terminal:
		x = sum([i+3 for i in width])+1 - terminal[0] # table width - console width
		if x>0:
			y = [i for i in range(len(lword)) if lword[i]<width[i]] # columns to be resized
			z = int(math.ceil(float(x)/len(y))) # difference in width
			for i in y: width[i] -= z

	result = ""
	line = (jc)+(jc).join(hc*(i+2) for i in width)+(jc)+nl
	for i, row in enumerate(rows):
		if i<2: result+=line
		data = list(enumerate( textwrap.wrap(col,width[j]) for j, col in enumerate(row) ))
		for k in range(max(len(k) for j,k in data)):
			for j, col in data:
				ck = col[k] if k<len(col) else ""
				result+=vc+pd+"{0:<{1}}".format(ck,width[j])+pd
			result+=vc+nl
	result+=line

	if header or footer:
		def pad(data):
			x = len(line)-5-len(data)
			y = vc + pd + " "*(x/2) + data + " "*(x-x/2) + pd + vc + nl
			return y
		if header: result = line + pad(header) + result
		if footer: result = result + pad(footer) + line

	return result

exports["prettytable"] = prettytable