#!/usr/bin/env python3
"""
This program optimizes my personal workflow at 
developing software and is build on top of git.
"""

import sys, os, subprocess

class management:
	def __init__(self):
		self.args = {
			"init" : "init()",
			"try" : "try_current()",
			"commit" : "commit()",
			"restore" : "restore_last()",
			"sync":"sync()",
			"clean":"clean()",
			"pack":"pack()",
			"backup" : "backup()"

		}

	def help(self):
		print('Usage: shorn [parameter]\nAvailable parameter:')
		print(str([ keys for keys, values in self.args.items()]).replace('[', '').replace(']', ''))
		sys.exit()

	def init(self):
		os.system('git init')
		if not os.path.isdir('.shorn'):
			print('init: Creating .shorn directory for testing and executing.')
			os.system('mkdir .shorn') 	# put tools for building, testing in .shorn
		os.system('touch .shorn/exec.sh')
		print('init: Created or recreated exec.sh.')
		os.system('chmod -R 770 .shorn')
		self.commit()				# create master-branch by first commit
		os.system('git branch dev')
		os.system('git checkout dev')
		os.system('git config merge.tool vimdiff')
		os.system('git config merge.conflictstyle diff3')
		os.system('git config mergetool.prompt false')

	def try_current(self):
		if self.commit() in [b'0\n', None]:
			shorn_lst = os.listdir('.shorn') 
			if shorn_lst:
				if not open('.shorn/exec.sh', 'r').readlines():
					print('WARNING: .shorn/exec.sh is empty, testing is not possible.')
				[os.system('./.shorn/' + subtool) for subtool in shorn_lst]
			if self.__ask__('Restore commit?') in ['y', 'Y']:
				self.restore_last()

	def commit(self):
		os.system('git add -A')
		try:
			subprocess.check_output('git commit -m \'shorn commit\'', shell = True)
			return subprocess.check_output('echo $?', shell = True)
		except Exception as err:
			if 'returned non-zero exit status 1.' in str(err):
				print('commit: Nothing new to try or commit.')
			else:
				print('commit: Error occured: {}'.format(err))

	def restore_last(self):
		try:
			gitLogOutput = subprocess.check_output('git log ', shell=True).decode('utf-8').split('\n')
			commitHashes =  [item.replace(' ', '').replace('commit', '')
						for j, item in enumerate(gitLogOutput) 
						if 'commit' in item and not 'shorn' in item]
			# peter 
			commits = [[item.replace('Date', '').replace(':', '') for item in gitLogOutput 
					if item.replace(' ', '').replace('commit', '') not in commitHashes and not 'shorn' in item
					and not 'Author' in item and item], 
					commitHashes]
			if len(commits[0]) != len(commits[1]):
				print('restore: FATAL - number of dates and number of corresponding hashes is unequal\nExiting')
				sys.exit()
			for j, commit in enumerate(commits[0]):
				try:
					commit = commit.split(' ')[2:-1][1:] 
					commit[3] = commit[3][0:2] + ':' + commit[3][2:4] + ':' + commit[3][4:]
					commit = ' '.join(commit)
				except:
					#print('commit var: {}\nError:{}'.format(commit, err))
					continue	
				if self.__ask__('Restore commit from {}?'.format(commit)) in ['y', 'Y']:
					subprocess.check_output('git checkout {} .'.format(commits[1][j]), shell=True)
					return
		except Exception as err:
			print('restore: Error occurred: {}'.format(err))
			try:
				if self.__ask__('Want to start mergetool/cleaning?') in ['y', 'Y']:
					os.system('git mergetool')
					os.system('rm *.orig')
					os.system('git clean -f')
			except Exception as err:
				print('restore: Caught that exception for you while trying to resolve merge-conflict: {}'.format(err))	
		self.commit()	
	
	def backup(self):
		try:
			if self.opt_arg:
				if self.opt_arg in ['check', 'c', '1']:
					os.system('sudo /opt/check_backup.sh')
		except:
			os.system('sudo ls > /dev/null') 		#get shell asking for password before starting sudo command in bg
			subprocess.Popen(['sudo', '/opt/do_backup.sh'], stdout = subprocess.PIPE)
		self.commit()
		os.system('git push origin {}'.format(subprocess.check_output('git status', shell = True).decode('utf-8').split('\n')[0].split(' ')[-1]))

	def sync(self):
		self.commit()
		current_branch = subprocess.check_output('git status', shell = True).decode('utf-8').split('\n')[0].split(' ')[-1]
		os.system('git checkout master')
		os.system('git merge dev')
		self.commit()
		os.system('git checkout {}'.format(current_branch))
		os.system('git push origin {}'.format(current_branch))

	def clean(self):
		if self.__ask__('Clean up .shorn, .git and .orig-files?') in ['y', 'Y']:
			os.system('rm -rf .shorn .git *.orig')

	def parse(self, argv):
		try:
			parameter = argv[0]
		except:
			self.help()
		if parameter not in self.args: self.help()
		if len(argv) > 1: 
			self.opt_arg = argv[1]
		eval('self.' + self.args[parameter])
	
	def pack(self):
		if subprocess.check_output('whoami', shell=True).decode('utf-8').replace('\n', '').replace(
' ', '') != 'root':
			print('pack: Execute pack as root!\nExiting!')
			sys.exit()
		dir_name = subprocess.check_output('pwd', shell = True).decode('utf-8')#.split('/')[-1]
		dir_name = dir_name.split('/')[-1].replace('\n', '')
		os.system('sudo rm -rf /package')
		os.system('sudo cp -R ../{} /package'.format(dir_name))
		[os.system('sudo rm -rf /package/{}'.format(files)) for files in ['.git', '.shorn', '.cache', '*old*', '*.orig', '.vscode']]

		# some particular things for dreamworld-project
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

	def __ask__(self, question):
		return subprocess.check_output('read -s -n 1 -p "{} [y|n]\n" a && echo $a'.format(question), shell = True).decode('utf-8').replace('\n', '')


if __name__ == '__main__':
	# command to (build and) execute
	if os.path.exists('.shorn/exec.sh') == True:
		management().parse(sys.argv[1:]) 
	else:
		print('init: .shorn/exec.sh does not exist or is not accessible')
		management().parse(sys.argv[1:])

