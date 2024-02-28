# Bootstrap

Bootstraps ansible-related configurations to ensure password-free connection and improved security.

Can pick either of the following to bootstrap.

- `ansible`: Creates ansible user which locks to controller host and the key that exists in `~/.ssh/`. Also installs `sudo` with no password for ansible user.
- `regular`: Deploys key to specified user. Should be `sudo` user.
- `router`: Specific role for VyOS router.
