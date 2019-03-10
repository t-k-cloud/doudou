import os, os.path, time, json
from whoosh import index
from whoosh import highlight
from whoosh.fields import Schema, TEXT, STORED, ID
from whoosh.qparser import MultifieldParser
from jieba.analyse import ChineseAnalyzer
from http.server import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process

import pdfminer.settings
pdfminer.settings.STRICT = False
import pdfminer.high_level

index_dir = 'indexdir'
page_len = 15
port = 19986

srch_root = '/home/tk/master-tree/incr'
#srch_root = './test'

reset_index = False

schema = Schema(
	fileid=ID(unique=True),
	filepath=TEXT(stored=True, analyzer=ChineseAnalyzer()),
	document=TEXT(stored=True, analyzer=ChineseAnalyzer()),
	moditime=STORED
)

def files_under(root):
	for dirpath, dirnames, filenames in os.walk(root):
		for f_name in filenames:
			yield os.path.join(dirpath, f_name)

def get_index():
	global reset_index
	if not os.path.exists(index_dir):
		os.mkdir(index_dir)
		reset_index = False
		return index.create_in(index_dir, schema)
	if reset_index:
		reset_index = False
		return index.create_in(index_dir, schema)
	else:
		return index.open_dir(index_dir)

def index_txt_file(writer, path):
	mtime = os.path.getmtime(path)
	with open(path, 'rb') as fh:
		binary = fh.read()
		possible_enc = ['utf-8', 'gb2312']
		content = ''
		for guess in possible_enc:
			is_right = True
			try:
				content = binary.decode(guess)
			except:
				is_right = False
			if is_right:
				break
			elif guess == possible_enc[-1]:
				print('Cannot decode', path)
				return
		writer.add_document(
			fileid=path,
			filepath=path,
			document=content,
			moditime=mtime
		)

def index_file_name(writer, path):
	mtime = os.path.getmtime(path)
	writer.add_document(
		fileid=path,
		filepath=path,
		document='',
		moditime=mtime
	)

def index_pdf_file(writer, path):
	out = open('tmp.txt', 'w', encoding='utf-8')
	params = pdfminer.layout.LAParams()
	with open(path, 'rb') as fh:
		pdfminer.high_level.extract_text_to_fp(fh, out, laparams=params)
	out.close()
	# now index the text output
	mtime = os.path.getmtime(path)
	with open('./tmp.txt', encoding='utf-8') as fh:
		content = fh.read()
		writer.add_document(
			fileid=path,
			filepath=path,
			document=content,
			moditime=mtime
		)

def incremental_index():
	global srch_root
	ix = get_index()
	writer = ix.writer()
	indexed_paths = set()
	# scan for file updates or deletions
	with ix.searcher() as se:
		for fields in se.all_stored_fields():
			path = fields['filepath']
			if not os.path.exists(path):
				writer.delete_by_term('fileid', path)
				print('[deletion detected]', path)
			else:
				indexed_time = fields['moditime']
				modified_time = os.path.getmtime(path)
				if modified_time > indexed_time:
					print('[update detected]', path)
					writer.delete_by_term('fileid', path)
				else:
					print('[unchanged]', path)
					indexed_paths.add(path)
	# re-index everyfile that is "new" to whoosh
	for path in files_under(srch_root):
		try:
			os.stat(path)
		except:
			print('[err open]', path)
			continue
		if path not in indexed_paths:
			ext = path.split('.')[-1].lower()
			if ext in ['c', 'cpp', 'dll', 'info', 'h', 'sys', 'bin', 'hex']:
				continue
			print('[indexing %s] %s' % (ext, path))
			if ext == 'pdf':
				index_pdf_file(writer, path)
			elif ext == 'txt':
				index_txt_file(writer, path)
			else:
				index_file_name(writer, path)
	writer.commit()

def indexing_forever():
	while True:
		incremental_index()
		time.sleep(1)

def search(query, page):
	ix = index.open_dir(index_dir)
	res = dict()
	with ix.searcher() as se:
		q = MultifieldParser([
			"filepath", "document"
			], schema=ix.schema).parse(query)
		p = se.search_page(q, page, pagelen=page_len)
		fg = highlight.ContextFragmenter(
			maxchars=200, surround=100, charlimit=100000
		)
		p.results.fragmenter = fg
		res['cur_page'] = p.results.pagenum
		res['tot_page'] = p.results.pagecount
		res['list'] = list()
		for hit in p:
			t = time.localtime(hit['moditime'])
			timestr = time.strftime('%Y-%m-%d %H:%M:%S', t)
			res['list'].append({
				"path": hit['filepath'],
				"time": timestr,
				"path_highlight": hit.highlights('filepath'),
				"highlight": hit.highlights('document')
			})
	return res

def doudouHandleReq(req):
	global reset_index
	print(req)
	if req['type'] == 'reset':
		print('Reset index in the next cycle.')
		reset_index = True
		return
	elif req['type'] == 'search':
		return json.dumps(search(req['q'], req['p']))

class doudouHandler(BaseHTTPRequestHandler):
	def do_POST(self):
		content_len = int(self.headers['Content-Length'])
		raw_req = self.data_string = self.rfile.read(content_len)
		response = doudouHandleReq(json.loads(raw_req.decode('utf-8')))
		self.send_response(200)
		self.end_headers()
		self.wfile.write(response.encode('utf-8'))

# try:
# 	print("Runing indexd in background ...")
# 	indexd = Process(target=indexing_forever)
# 	indexd.start()
# 	print("Listening on port " + str(port))
# 	server = HTTPServer(('', port), doudouHandler)
# 	server.serve_forever()
# except KeyboardInterrupt:
# 	print('\n\n')
# 	print('Close the server...')
# 	indexd.terminate()
# 	server.socket.close()

indexing_forever()
