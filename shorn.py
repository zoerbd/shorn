#!/usr/bin/env python3
"""
This program optimizes my personal workflow at 
developing software and is build on top of git.
"""

import sys, os, subprocess, re

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
			"backup" : "backup()",
			"pull":"pull()"
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
			if self.__ask__('Restore commit?'):
				self.restore_last()

	def commit(self):
		os.system('git add -A')
		commitMessage = 'shorn commit'
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

	def restore_last(self):
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
				print('{}: Restore commit{}from {}?'.format(j+1, [' \'' + commitMessages[j].strip() + '\' ' if 'shorn commit' not in commitMessages[j] else ' ' for i in range(1)][0],  commit))
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
					os.system('git mergetool')
					os.system('rm *.orig')
					os.system('git clean -f')
			except Exception as err:
				print('restore: Caught that exception for you while trying to resolve merge-conflict: {}'.format(err))	
		self.commit()	

	def pull(self):
		self.commit()
		current_branch = self.__getCurrentBranch__()
		if current_branch != 'master':
			os.system('git pull origin {}'.format(current_branch))
			self.commit()
		os.system('git pull origin master')
		self.commit()
	
	def backup(self):
		try:
			if self.opt_arg:
				if self.opt_arg in ['check', 'c', '1']:
					os.system('sudo /opt/check_backup.sh')
		except:
			os.system('sudo ls > /dev/null') 		#get shell asking for password before starting sudo command in bg
			self.__shell__('sudo /opt/do_backup.sh')
		self.commit()
		self.__shell__('git push origin {}'.format(self.__shell__('git status').split('\n')[0].split(' ')[-1]))

	def sync(self):
		self.commit()
		current_branch = self.__getCurrentBranch__()
		os.system('git push origin {}'.format(current_branch))
		os.system('git checkout master')
		os.system('git merge {}'.format(current_branch))
		self.commit()
		os.system('git push origin master'.format(current_branch))
		os.system('git checkout {}'.format(current_branch))

	def __getCurrentBranch__(self):
		return self.__shell__('git status').split('\n')[0].split(' ')[-1]

	def clean(self):
		if self.__ask__('Clean up .shorn, .git and .orig-files?'):
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
		if self.__shell__('whoami').strip() != 'root':
			print('pack: Execute pack as root!\nExiting!')
			sys.exit()
		dir_name = self.__shell__('pwd').strip()
		dir_name = dir_name.split('/')[-1].replace('\n', '')
		os.system('sudo rm -rf /package')
		os.system('sudo cp -R ../{} /package'.format(dir_name))
		[os.system('sudo rm -rf /package/{}'.format(files)) for files in ['.git', '.shorn', '.cache', '*old*', '*.orig', '.vscode']]

	def __ask__(self, question):
		return self.__shell__('read -s -n 1 -p "{} [y|n]\n" a && echo $a'.format(question)).strip() in ['y', 'Y']
	
	def __shell__(self, cmd):
		opts = {
			'stdout': subprocess.PIPE,
			'stderr': subprocess.PIPE
		}
		ps = subprocess.Popen(cmd.split(' '), **opts)
		stdout, stderr = ps.communicate()
		if stderr:
			return stderr.decode('utf-8')[:-1]
		return stdout.decode('utf-8')[:-1]


if __name__ == '__main__':
	# command to (build and) execute
	if os.path.exists('.shorn/exec.sh') == True:
		management().parse(sys.argv[1:]) 
	else:
		print('init: .shorn/exec.sh does not exist or is not accessible')
		management().parse(sys.argv[1:])

