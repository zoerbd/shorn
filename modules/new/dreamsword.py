# pack method right here
# def pack(self):
if self.__shell__('whoami') != 'root':
	print('pack: Execute pack as root!\nExiting!')
	sys.exit()
dir_name = self.__shell__('pwd')
dir_name = dir_name.split('/')[-1].replace('\n', '')
self.__shell__('sudo rm -rf /package')
self.__shell__('sudo cp -R ../{} /package'.format(dir_name))
[self.__shell__('sudo rm -rf /package/{}'.format(files)) for files in ['.git', '.shorn', '.cache', '*old*', '*.orig', '.vscode']]

# dreamsword specifics
try:
	if self.opt_arg:
		if self.opt_arg in ['dw', 'dreamworld', 'cocoon']:
			[os.system('sudo rm -rf /package/{}'.format(files)) for files in ['typings', 'node_modules', '*.graphml', 'server-side', 'cordova', 'key', 'test.py', '*.log']]
			os.system('sudo mv /package/dist/assets/ /package/assets')
			os.system('sudo rm -rf /package/dist')
			os.system('sudo rm -rf /package/assets/svg /package/assets/concepts')

			#//////////// --> File editing
			items = [ 'src/' + item for item in os.listdir('src') if '.js' in item]	
			items = items + [ 'src/scenes/' + item for item in os.listdir('src/scenes') if '.js' in item]
			files = [open(item, 'r').readlines() for item in items]
			wfile = open('/package/index.js', 'w')
			for j, content in enumerate(files):
				for i, line in enumerate(content):
					# replace any invalid syntax for compiling
					if 'export' in line:
						line = line.replace('export', '')
					elif 'import' in line or '/**' in line:
						line = '\n'

					# warn when meet misc things
					for invalid_substr in ['window', '=>']:
						if invalid_substr in line:
							print('WARNING: \'{}\' in line {} of file \'{}\'.'.format(invalid_substr, i+1, items[j]))	
					wfile.write(line)
			wfile.close()

			index = open('/package/index.html', 'r').readlines()
			index_new = open('/package/index.html', 'w')
			[index_new.write('<script src=\"index.js\"></script>') if 'main.js' in item else index_new.write(item) for item in index]
			index_new.close()
			#//////////// --> File editing

except Exception as err:
	print('pack: Following error occurred while doing dreamworld specific things: {}'.format(err))

os.system('sudo rm -r /package/game* /package/package* /package/main.js /package/src > /dev/null 2<&1')
os.system('sudo zip -r -X {}.zip /package >> /dev/null'.format(dir_name))
os.system('sudo rm -R /package')
print('pack: Paste your code into this before compiling: https://babeljs.io/repl#?babili=false&browsers=&build=&builtIns=false&spec=false&loose=false&code_lz=Q&debug=false&forceAllTransforms=false&shippedProposals=false&circleciRepo=&evaluate=false&fileSize=false&timeTravel=false&sourceType=module&lineWrap=true&presets=es2015%2Creact%2Cstage-2&prettier=false&targets=&version=6.26.0&envVersion=')
print('pack: Replace window.load() as described and outcomment cordova.js-include in index.html and you are fine.')