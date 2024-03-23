
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display
from os.path import basename
import re

display = Display()

def _fail(ret, msg):
	ret['failed'] = True
	ret['msg'] = msg
	return ret

class ActionModule(ActionBase):

	TRANSFERS_FILES = True

	def run(self, tmp=None, task_vars=None):
		# task_vars: all variables for a task, including playbook variables
		# module_args: arguments for the module itself
		super(ActionModule, self).run(tmp, task_vars)
		module_args = self._task.args.copy()
		check_mode = self._play_context.check_mode

		ret = dict(changed=False)

		if 'repo' not in module_args:
			return _fail(ret, "Require repo argument")
		if 'dest' not in module_args:
			return _fail(ret, "Require dest argument")
		repo = module_args['repo']
		if 'tag' in module_args and module_args['tag'] != 'latest':
			api = f"https://api.github.com/repos/{repo}/releases/tags/{module_args['tag']}"
		else:
			api = f"https://api.github.com/repos/{repo}/releases/latest"
		dest = module_args['dest']

		self._task.args = dict(
			url=api,
			return_content=True)

		self._play_context.check_mode = False
		json_response = self._shared_loader_obj.action_loader.get("ansible.builtin.uri",
			self._task, self._connection, self._play_context, self._loader,
			self._templar, self._shared_loader_obj).run(tmp, task_vars)
		self._play_context.check_mode = check_mode

		if 'failed' in json_response:
			return _fail(ret, json_response['msg'])

		content = json_response['json']

		download = self.get_github_download(content, module_args.get('regex'))

		if download is None:
			return _fail(ret, "Failed to get download link")

		download, name = download

		if dest[-1] == "/":
			dest += basename(download)

		args = module_args.copy()
		if 'checksum_file' in args:
			args.pop('checksum_file')
		if 'regex' in args:
			args.pop('regex')
		if 'tag' in args:
			args.pop('tag')
		args.pop('repo')
		args['url'] = download

		if 'checksum_file' in module_args:
			algo, file = module_args['checksum_file'].split(':', 1)
			checksum = self.get_github_download(content, file)
			if checksum is not None:
				args['checksum'] = f"{algo}:{checksum[0]}"
			else:
				display.warning(f"Checksum file {file} dows not exist")

		url_response = self._execute_module(
			module_name='ansible.builtin.get_url',
			module_args=args,
			task_vars=task_vars, tmp=tmp)

		if 'failed' in url_response:
			return _fail(ret, url_response['msg'])

		ret['changed'] = url_response['changed']
		ret['msg'] = url_response['msg']
		ret['dest'] = dest
		ret['tag'] = content['tag_name']
		ret['name'] = name
		ret['checksum_dest'] = url_response['checksum_dest']
		ret['checksum_src'] = url_response['checksum_src']

		return ret

	def get_github_download(self, json, regex=None):
		if 'assets' not in json:
			return None
		if regex:
			r = re.compile(regex)
			for dl in json['assets']:
				if r.search(dl['name']) is not None:
					return dl['browser_download_url'], dl['name']
		return json['tarball_url'], json['name']
