
__metaclass__ = type

from ansible.plugins.action import ActionBase
#from ansible.utils.display import Display

import json

#display = Display()

def _fail(ret, msg):
	ret['failed'] = True
	ret['msg'] = msg
	return ret

class ActionModule(ActionBase):
	def run(self, tmp=None, task_vars=None):
		# task_vars: all variables for a task, including playbook variables
		# module_args: arguments for the module itself
		super(ActionModule, self).run(tmp, task_vars)
		module_args = self._task.args.copy()
		check_mode = self._play_context.check_mode

		hostvars = task_vars['hostvars']

		ret = dict(changed=False)

		if 'method' not in module_args:
			return _fail(ret, "Require method argument")
		if 'key' not in module_args:
			return _fail(ret, "Require key argument")
		if 'data' not in module_args:
			return _fail(ret, "Require data argument")
		if not isinstance(module_args['data'], str):
			return _fail(ret, "Require data argument to be a str")
		url = module_args.get('url', f"https://{task_vars['ansible_host']}")

		uri_return = self._execute_module(
			module_name='ansible.builtin.uri',
			module_args=dict(
				method='POST',
				url=f"{url}/{module_args['method']}",
				validate_certs=False,
				return_content=True,
				body_format='form-urlencoded',
				body=dict(
					key=module_args['key'],
					data=module_args['data'])),
			task_vars=task_vars, tmp=tmp)

		if 'skipped' in uri_return and uri_return['skipped']:
			ret['skipped'] = True
			return ret

		if uri_return['status'] == -1:
			return _fail(ret, uri_return['msg'])

		result = json.loads(uri_return['content'])
		if not result['success']:
			return _fail(ret, result['error'])

		data = result['data']

		if data is not None:
			ret['response'] = data

		ret['changed'] = True
		ret['status'] = uri_return['status']

		return ret

