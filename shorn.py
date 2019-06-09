#!/usr/bin/env python3
"""
This program optimizes my personal workflow at 
developing software and is built on top of git.
"""

import sys, os, subprocess, re, traceback, importlib.util, datetime

class management:
	def __init__(self):
		self.version = 1.11
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
			"update":[
				"update()",
				'Checks if a new version is available on github and updates the local binary.'
			],
			"install":[
				"install()",
				'Installs one of the optional modules to your local environment.'
			],
			"version":[
				"printVersion()",
				'Prints the currently installed version of shorn.'
			]

		}

	def help(self):
		print('Usage: shorn [parameter]\nAvailable parameter:')
		print('\n'.join([ '   {}  -  {}'.format(keys, values[1]) for keys, values in self.args.items()]))
		sys.exit()

	def init(self):
		print('Start initializing new repository.')
		self.__shell__('git init')
		if not os.path.isdir('.shorn'):
			print('Creating .shorn directory for testing and executing.')
			self.__shell__('mkdir .shorn') 	# put tools for building, testing in .shorn
		self.__shell__('touch .shorn/exec.sh')
		print('Created exec.sh.')
		self.__shell__('chmod -R 770 .shorn')
		self.commit()				# create master-branch by first commit
		print('Adding dev branch.')
		self.__shell__('git branch dev')
		self.__shell__('git checkout dev')
		print('Configuring merge tools.')
		self.__shell__('git config merge.tool vimdiff')
		self.__shell__('git config merge.conflictstyle diff3')
		self.__shell__('git config mergetool.prompt false')
		self.__executeModules__()

	def tryCurrent(self):
		if self.commit() in [b'0\n', None]:
			shorn_lst = os.listdir('.shorn') 
			if shorn_lst:
				if not open('.shorn/exec.sh', 'r').readlines():
					print('WARNING: .shorn/exec.sh is empty, testing is not possible.')
				[self.__shell__('./.shorn/' + subtool) for subtool in shorn_lst]
			if self.__ask__('Restore commit?'):
				self.restore()
		self.__executeModules__()

	def commit(self):
		print('Commiting all changes.')
		self.__shell__('git add -A')
		commitMessage = 'minor changes'
		try:
			if self.opt_arg:
				commitMessage = self.opt_arg
		except:
			print('Using default commit-message.')
		try:
			self.__shell__('git commit -m \'{}\''.format(commitMessage))
			return self.__shell__('echo $?')
		except Exception as err:
			print('  commit: {}'.format(err))
			if 'returned non-zero exit status 1.' in str(err):
				print('commit: Nothing new to try or commit.')
		self.__executeModules__()

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
		self.__executeModules__()

	def pull(self):
		self.commit()
		print('Pulling from origin.')
		self.__shell__('git checkout master')
		branches = self.__shell__('git branch').strip().split('\n')
		del branches[[i for i, val in enumerate(branches) if '*' in val][0]]	# delete branch marked with '*' (active branch)
		for branch in branches:
			self.__shell__('git pull origin {}'.format(branch))
			self.commit()
		self.__shell__('git pull origin master')
		self.commit()
		print('Switching to branch dev.')
		self.__shell__('git checkout dev')
		self.__executeModules__()
	
	def sync(self):
		# handle syncType
		try:
			syncType = sys.argv[2]
		except:
			syncType = 'all'
		# commit message handling with sys args
		try:
			self.opt_arg = sys.argv[3]
		except:
			if syncType not in ['all', 'dev', 'altdev']:
				self.opt_arg = syncType
				syncType = 'all'
		self.commit()
		currentBranch = self.__getCurrentBranch__()
		branches = self.__shell__('git branch').strip().split('\n')
		del branches[[i for i, val in enumerate(branches) if '*' in val][0]]	# delete branch marked with '*' (active branch)
		if syncType == 'all':
			print('Merging all branches to the current state.')
			self.__mergeBranches__(branches, currentBranch)
		elif syncType == 'dev':
			print('Merging all development branches.')
			branches = [branch for branch in branches if 'dev' in branch]
			self.__mergeBranches__(branches, currentBranch)
		elif syncType == 'altdev':
			branchName = 'dev' + datetime.datetime.now().strftime("%Y-%m-%d_%H.%M")
			self.__shell__('git branch {}'.format(branchName))
			self.__shell__('git checkout {}'.format(branchName))
		else:
			print('Entered invalid sync method.\nUsage: shorn sync <all|dev|altdev>\n  all - commit and push all branches\n  dev - commit and push all dev branches\n  altdev - commit changes in dev branch and create forked dev branch')
		print('Pushing all altered branches to origin.')
		self.__shell__('git push --all origin')
		print('Switched back to branch dev.')
		self.__shell__('git checkout dev')
		self.__executeModules__()

	def __mergeBranches__(self, branches, currentBranch):
		for branch in branches:
			branch = branch.strip()
			print('  Doing checkout and merge for branch {}'.format(branch))
			self.__shell__('git checkout {}'.format(branch))
			self.__shell__('git merge {}'.format(currentBranch))

	def __getCurrentBranch__(self):
		return self.__shell__('git status').split('\n')[0].strip().split(' ')[-1]

	def clean(self):
		if self.__ask__('Clean up .shorn, .git and .orig-files?'):
			self.__shell__('rm -rf .shorn .git *.orig')

	def parse(self, argv):
		try:
			parameter = argv[0]
		except:
			self.help()
		if parameter not in self.args: 
			# check if it's an additional module parameter
			try:
				additionalCommandsPath = '/usr/lib/shorn/new'
				for filename in os.listdir(additionalCommandsPath):
					filename = os.path.join(additionalCommandsPath, filename)
					expectedMethodStr = 'def {}('.format(parameter)
					with open(filename) as moduleContent:
						for line in moduleContent.readlines():
							if expectedMethodStr in line:
								return self.__importAndExecuteModule__(filename, parameter)
			except:
				pass
			self.help()
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
			quotes = [n for n, val in enumerate(cmd.split(' ')) if '\'' in val]
			if len(quotes) == 1:
				quotes.append(quotes[0]) 	# fixes the problem that there is only one number when bothe quotes are in the same place of the cmd.split(' ') list
			newMsg = ' '.join(splittedCmd[quotes[0] : quotes[1] + 1])
			del splittedCmd[quotes[0] : quotes[1] + 1]
			splittedCmd.insert(quotes[0], newMsg)
		ps = subprocess.Popen(splittedCmd, **opts)
		stdout, stderr = ps.communicate()
		if stderr:
			err = self.manageGitErr(stderr)
			if err:
				print('Error occurred in __shell__:\n $ {}\n{}'.format(
					''.join(cmd), 
					''.join([' >> {}\n'.format(line) for line in err.split('\n')])
					).strip()
				)
			return err
		return stdout.decode('utf-8').strip()

	def manageGitErr(self, err):
		'''
		Returns empty string if allowed git error message
		else returns the utf-8 and stripped error.
		'''
		allowedGitErrors = [
			b'Cloning into \'shorn\'...', 
			b'Everything up-to-date',
			b'Already on',
			b'To https://github.com/zoerbd/shorn',
			b'Switched to branch',
			b'From https://github.com/zoerbd/shorn',
		]
		if not any(allowedGitErr in err for allowedGitErr in allowedGitErrors):
			return err.decode('utf-8').strip()
		return ''

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
							print('Installing new version...')
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
		supportedMethods = []
		for method in methods:
			availableModules = os.listdir(os.path.join('/tmp/shorn/modules', method))
			if newModule + '.py' in availableModules:
				supportedMethods.append(method)

		# Available methods for modules in supportedMethods, if empty -> module not found
		if supportedMethods:
			print('Installing module...')
			for method in supportedMethods:
				self.__shell__('sudo mkdir -p {}'.format(os.path.join('/usr/lib/shorn', method)))
				self.__shell__('sudo cp {} /usr/lib/shorn/{}'.format(os.path.join('/tmp/shorn/modules', method, newModule + '.py'), method))
			return
		# pray to god that you don't have to tshoot this
		print('Requested module not found.\nThe following are available: {}'.format(
			''.join(['\n {} '.format(module) 
				for module in [entry.replace('.py', '') 
					for entry in list(set(sum(
						[ os.listdir(filename) for filename in [ os.path.join('/tmp/shorn/modules', method) for method in methods ] ], []
					)))
				]
			])
		))
		
	def __fetchRepo__(self):
		if os.path.isdir('/tmp/shorn/'):
			self.__shell__('rm -rf /tmp/shorn')
		self.__shell__('git clone https://github.com/zoerbd/shorn', '/tmp')
	
	def __executeModules__(self):
		parent = traceback.extract_stack(None, 2)[0][2]
		try:
			for modulePath in os.listdir(os.path.join('/usr/lib/shorn', parent)):
				modulePath = os.path.join('/usr/lib/shorn', parent, modulePath)
				self.__importAndExecuteModule__(modulePath)	
		except:
			pass

	def __importAndExecuteModule__(self, modulePath, parameter=None): #='main'):
		# execute imported function
		if parameter:
			executable = os.path.basename(modulePath)
			sys.path.append(modulePath.replace(executable, ''))
			i = importlib.import_module(executable.replace('.py', ''))
			return eval('i.{}()'.format(parameter))
		with open(modulePath) as moduleContent:
			print('Will proceed executing the installed {} module.'.format(os.path.basename(modulePath)))
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
