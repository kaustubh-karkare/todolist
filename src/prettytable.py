
vc, hc, jc, pd, nl = "|-+ \n"

def prettytable(rows):
	if len(rows)==0: return

	width = [-1]*min(len(row) for row in rows)
	for row in rows:
		for j, col in enumerate(row):
			width[j] = max(width[j],len(col))

	result = ""
	line = (jc)+(jc).join(hc*(i+2) for i in width)+(jc)+nl
	for i, row in enumerate(rows):
		if i<2: result+=line
		for j, col in enumerate(row):
			result+=vc+pd+"{0:<{1}}".format(col,width[j])+pd
		result+=vc+nl
	result+=line[:-1]

	return result

exports["prettytable"] = prettytable