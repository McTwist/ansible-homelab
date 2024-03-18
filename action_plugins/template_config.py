# Action for template validating configs
#
# Will template the source file and validate the whole instance
# before restoring if failed. If anything fails, it will try to
# restore to previous state to avoid breaking the system.
# In detail, it will do the following:
# 1. Backup current file, if it exists.
# 2. Template source file onto destination.
# 3. Validate config by running a command.
#    Note that it does not take in any argument.
# 4. Remove backup.
# 5. If anything fails, it will restore from backup and remove it.
#
# Note: May need some more checks if anything fails.

__metaclass__ = type

from ansible.plugins.action import ActionBase

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

		if 'dest' not in module_args:
			return _fail(ret, "Require dest argument")
		if 'validate' not in module_args:
			return _fail(ret, "Require validate argument")

		if not check_mode:
			# Note: Not the best name, but it will always be removed anyway
			bak_file = f"{module_args['dest']}.bak~"
			backup_return = self._execute_module(
				module_name='ansible.builtin.copy',
				module_args=dict(
					src=module_args['dest'],
					dest=bak_file,
					remote_src=True),
				task_vars=task_vars, tmp=tmp)

		self._task.args.pop('validate')

		template_return = self._shared_loader_obj.action_loader.get("ansible.builtin.template",
			self._task, self._connection, self._play_context, self._loader,
			self._templar, self._shared_loader_obj).run(tmp, task_vars)

		if template_return.get('failed'):
			if not check_mode and not backup_return.get('failed'):
				self._restore_config(tmp, task_vars, bak_file, module_args['dest'])
			return template_return

		if not check_mode:
			result = self._low_level_execute_command(module_args['validate'], sudoable=True)

			if result['rc'] != 0:
				if not backup_return.get('failed'):
					self._restore_config(tmp, task_vars, bak_file, module_args['dest'])
				else:
					self._execute_module(
						module_name='ansible.builtin.file',
						module_args=dict(
							path=module_args['dest'],
							state='absent'
						),
						task_vars=task_vars, tmp=tmp)
				return result

			if not backup_return.get('failed'):
				self._remove_backup(tmp, task_vars, bak_file)

		ret['changed'] = template_return.get('changed', False)

		return ret

	def _restore_config(self, tmp, task_vars, bak_file, dest):
		# Note: Ignore if it succeeded or not
		self._execute_module(
			module_name='ansible.builtin.copy',
			module_args=dict(
				src=bak_file,
				dest=dest,
				remote_src=True),
			task_vars=task_vars, tmp=tmp)
		self._remove_backup(tmp, task_vars, bak_file)

	def _remove_backup(self, tmp, task_vars, bak_file):
		self._execute_module(
			module_name='ansible.builtin.file',
			module_args=dict(
				path=bak_file,
				state='absent'
			),
			task_vars=task_vars, tmp=tmp)
