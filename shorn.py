#!/usr/bin/env python3
"""
This program optimizes my personal workflow at 
developing software and is built on top of git.
"""

import sys, os, subprocess, re, traceback

class management:
	def __init__(self):
		self.version = 0.5
		self.args = {
			"init" : [
				"init()",
				'Initialize a new shorn/git repository.'
			],
			"try" : [
				"tryCurrent()",
				'Commits changes and executes test script (.shorn/exec.sh).'
			],
			"commit" : [
				"commit()",
				'Adds and commits all changes in the current branch.'
			],
			"restore" : [
				"restore()",
				'Lists all commits and restores the desired commit.'
			],
			"sync":[
				"sync()",
				'Commits through master and dev branch all changes and pushs to origin.'
			],
			"clean":[
				"clean()",
				'Deletes .shorn .git *.orig.'
			],
			"pull":[
				"pull()",
				'Pulls and commits all changes from origin.'
			],
			"version":[
				"printVersion()",
				'Prints the currently installed version of shorn.'
			],
			"update":[
				"update()",
				'Looks on github if a new version is commited and updates the local binary.'
			],
			"install":[
				"install()",
				'Install one of the optional modules to your local environment.'
			]
		}

	def help(self):
		print('Usage: shorn [parameter]\nAvailable parameter:')
		print('\n'.join([ '   {}  -  {}'.format(keys, values[1]) for keys, values in self.args.items()]))
		sys.exit()

	def init(self):
		self.__shell__('git init')
		if not os.path.isdir('.shorn'):
			print('init: Creating .shorn directory for testing and executing.')
			self.__shell__('mkdir .shorn') 	# put tools for building, testing in .shorn
		self.__shell__('touch .shorn/exec.sh')
		print('init: Created or recreated exec.sh.')
		self.__shell__('chmod -R 770 .shorn')
		self.commit()				# create master-branch by first commit
		self.__shell__('git branch dev')
		self.__shell__('git checkout dev')
		self.__shell__('git config merge.tool vimdiff')
		self.__shell__('git config merge.conflictstyle diff3')
		self.__shell__('git config mergetool.prompt false')

	def tryCurrent(self):
		if self.commit() in [b'0\n', None]:
			shorn_lst = os.listdir('.shorn') 
			if shorn_lst:
				if not open('.shorn/exec.sh', 'r').readlines():
					print('WARNING: .shorn/exec.sh is empty, testing is not possible.')
				[self.__shell__('./.shorn/' + subtool) for subtool in shorn_lst]
			if self.__ask__('Restore commit?'):
				self.restore()

	def commit(self):
		self.__shell__('git add -A')
		commitMessage = 'minor changes'
		try:
			if self.opt_arg:
				commitMessage = self.opt_arg
		except:
			print('Using default commit-message')
		try:
			self.__shell__('git commit -m \'{}\''.format(commitMessage))
			return self.__shell__('echo $?')
		except Exception as err:
			print(err)
			if 'returned non-zero exit status 1.' in str(err):
				print('commit: Nothing new to try or commit.')
			else:
				print('commit: Error occured: {}'.format(err))

	def restore(self):
		try:
			gitLogOutput = self.__shell__('git log').split('\n')
			
			# define regex-patterns
			regexMessages = re.compile(r'^\s+(.+\s*)*')
			regexDates = re.compile(r'(Date:)((\s*\w*)*(:\d{2}:\d{2}\s\d*))')
			regexHashes = re.compile(r'(commit)\s([a-z0-9]{28,30})')		# not sure about len of hashes
	
			commitMessages, commitHashes, commitDates = [], [], []
			for line in gitLogOutput:
				commitMessages.append([match.group(0).strip() for match in regexMessages.finditer(line)])
				commitMessages = [''.join(item) for item in commitMessages if item]
			
				commitHashes.append([ match.group(2) for match in regexHashes.finditer(line) ])
				commitHashes = [''.join(item) for item in commitHashes if item]

				commitDates.append([ match.group(2).strip() for match in regexDates.finditer(line) ])
				commitDates = [''.join(item) for item in commitDates if item]

			commits = [commitDates, commitHashes]
			if len(commits[0]) != len(commits[1]) or len(commits[1]) != len(commitMessages):
				print('restore: FATAL - number of dates and corresponding hashes and/or messages is unequal\nExiting')
				print('len(commits[0]): {}'.format(len(commits[0])))
				print('len(commits[1]): {}'.format(len(commits[1])))
				print('len(commitMessages): {}'.format(len(commitMessages)))
				if self.__ask__('Output content of lists?'):
					print('commits[0]: {}'.format(commits[0]))
					print('commits[1]: {}'.format(commits[1]))
					print('commitMessages: {}'.format(commitMessages))
				sys.exit()
			for j, commit in enumerate(commits[0]):
				print('{}: Restore commit{}from {}?'.format(j+1, [' \'' + commitMessages[j].strip() + '\' ' if 'minor changes' not in commitMessages[j] else ' ' for i in range(1)][0],  commit))
			try:
				num = int(input('Number to restore: '))
			except:
				print('restore: Invalid input.\nAborting...')
				sys.exit()
			if num <= len(commits[0]):
				restoreCommit = commits[1][num-1]
				print('Restoring commit \'{}\''.format(restoreCommit))
				self.__shell__('git checkout {} .'.format(restoreCommit))
				return
		except Exception as err:
			print('restore: Error occurred: {}'.format(err))
			raise
			try:
				if self.__ask__('Want to start mergetool/cleaning?'):
					self.__shell__('git mergetool')
					self.__shell__('rm *.orig')
					self.__shell__('git clean -f')
			except Exception as err:
				print('restore: Caught that exception for you while trying to resolve merge-conflict: {}'.format(err))	
		self.commit()	

	def pull(self):
		self.commit()
		current_branch = self.__getCurrentBranch__()
		if current_branch != 'master':
			self.__shell__('git pull origin {}'.format(current_branch))
			self.commit()
		self.__shell__('git pull origin master')
		self.commit()
	
	def sync(self):
		self.commit()
		current_branch = self.__getCurrentBranch__()
		self.__shell__('git push origin {}'.format(current_branch))
		self.__shell__('git checkout master')
		self.__shell__('git merge {}'.format(current_branch))
		self.commit()
		self.__shell__('git push origin master'.format(current_branch))
		self.__shell__('git checkout {}'.format(current_branch))

	def __getCurrentBranch__(self):
		return self.__shell__('git status').split('\n')[0].strip()

	def clean(self):
		if self.__ask__('Clean up .shorn, .git and .orig-files?'):
			self.__shell__('rm -rf .shorn .git *.orig')

	def parse(self, argv):
		try:
			parameter = argv[0]
		except:
			self.help()
		if parameter not in self.args: self.help()
		if len(argv) > 1: 
			self.opt_arg = argv[1]
		eval('self.' + self.args[parameter][0])

	def __ask__(self, question):
		return self.__shell__('read -s -n 1 -p "{} [y|n]\n" a && echo $a'.format(question)) in ['y', 'Y']
	
	def __shell__(self, cmd, cwd=os.getcwd()):
		opts = {
			'stdout': subprocess.PIPE,
			'stderr': subprocess.PIPE,
			'cwd': cwd
		}
		splittedCmd = cmd.split(' ')
		# make sure that commit messages are executed correctly (format message into one place in list, not white-space seperated)
		if cmd.find('\'') != -1:
			quotes = [n for n, val in enumerate(cmd.split(' ')) if val.find('\'') != -1]
			newMsg = ' '.join(splittedCmd[quotes[0] : quotes[1] + 1])
			del splittedCmd[quotes[0] : quotes[1] + 1]
			splittedCmd.insert(quotes[0], newMsg)
		print(splittedCmd)
		ps = subprocess.Popen(splittedCmd, **opts)
		stdout, stderr = ps.communicate()
		if stderr and not b'Cloning into \'shorn\'...' in stderr:
			err = stderr.decode('utf-8').strip()
			print('Error occurred in __shell__:\n $ {}\n{}'.format(
				''.join(cmd), 
				''.join([' >> {}\n'.format(line) for line in err.split('\n')])
				).strip()
			)
			return err
		return stdout.decode('utf-8').strip()

	def printVersion(self):
		print(self.version)
	
	def update(self):
		print('Checking for update...')
		self.__fetchRepo__()
		with open('/tmp/shorn/shorn.py') as newBin:
			for line in newBin.readlines():
				try:
					if 'self.version' in line:
						if self.version < float(line[line.find('=')+1:].strip()):
							print('Install new version...')
							shornPath = self.__shell__('which shorn')
							self.__shell__('sudo cp {} {}'.format('/tmp/shorn/shorn.py', shornPath))
							self.__shell__('sudo chmod a+x {}'.format(shornPath))
							whoami = self.__shell__('whoami')
							self.__shell__('sudo chown {} {}'.format(whoami, shornPath))
							print('Installed new binary!')
						else:
							print('The installed version is up to date!')
						break
				except:
					print('Was unable to detect the current version.\nAre you sure self.version is implemented?')
	
	def install(self):
		if not os.path.isdir('/usr/lib/shorn/'):
			print('Creating module directory at /usr/lib/shorn.')
			self.__shell__('sudo mkdir /usr/lib/shorn')
		self.__fetchRepo__()

		try:
			newModule = sys.argv[2]
		except:
			print('Please specify a module you would like to install.\nUsage: shorn install <modulename>')
			sys.exit(-1)
		methods = os.listdir('/tmp/shorn/modules')
		modules = [{method: os.listdir(os.path.join('/tmp/shorn/modules', method))} for method in methods]
		print(modules)

		# if module in dict, install
		try:
			for method in modules[newModule]:
				self.__shell__('sudo cp {} /usr/lib/shorn/'.format(os.path.join('/tmp/shorn/modules', method)))
		except:
			print('Requested module not found.\nThe following are available: {}'.format(''.join(['\n {} '.format(module) for module in modules.keys()])))
		
	def __fetchRepo__(self):
		if os.path.isdir('/tmp/shorn/'):
			self.__shell__('rm -rf /tmp/shorn')
		self.__shell__('git clone https://github.com/zoerbd/shorn', '/tmp')
	
	def __executeModules__(self):
		parent = traceback.extract_stack(None, 2)[0][2]
		for modulePath in os.listdir(os.path.join('/usr/lib/shorn'), parent):
			with open(modulePath) as moduleContent:
				[ eval(line) for line in moduleContent.readlines() ]

if __name__ == '__main__':
	# command to (build and) execute
	if os.path.exists('.shorn/exec.sh'):
		management().parse(sys.argv[1:]) 
	else:
		try:
			if sys.argv[1] not in ['version', 'init', 'help', 'update', 'install']:
				print('init: .shorn/exec.sh does not exist or is not accessible')
		except IndexError:
			sys.argv.append('help')
		management().parse(sys.argv[1:])
