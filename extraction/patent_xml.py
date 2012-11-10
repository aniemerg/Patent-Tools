

XMLFILE = "C:\\Users\\aarontropy\\Envs\\patenttools_env\\ipgb20120103.xml"

def read_file_in_sections(filename):
	f = open(filename, 'r')
	out_xml = ''

	while True:
		line = f.readline()

		if (line[0:5] == "<?xml" or not line) and len(out_xml) > 0:
			yield out_xml
			out_xml = ''

		if not line:
			break

		out_xml += line

	f.close()


for pat in read_file_in_sections(TXTFILE):
	print pat



