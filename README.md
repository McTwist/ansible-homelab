# Ansible collection for homelab

This repository contains roles, playbooks and configs that I have gathered over the course of some time since I started using Ansible. It is meant as a backup and a learning tool for other ansible-devs, but *not* a "the-best-tutorial", but only as a gateway on how one could tackle various issues. Some of it can be taken out of context, while others are specifically designed for my own network infrastructure and cannot be used as-is. It may change in the future drastically when I find a better way to deal with things.

This readme is meant to explain each section of the collection, what it does and how one could use it. I try to keep this file up to date, but occasionally may forget.

**If there are any suggestions or questions on how to use anything, please create an issue.** There are some sort of documentation, but as this is used for personal projects there are close to no need to add any documentations.

## Root

Usually you put all your playbooks in a specific folder and redefine the root from there if necessary. I decided to ignore that put the playbooks in the root folder for now. This might change later on, but it works for the amount of playbooks I currently have.

For config there is `ansible.cfg` which will modify some of the default behaviors and add specific include directories for certain structures.

### Playbooks

- [apcupsd](apcupsd.yml): Install and configure apcupsd.
- [bootstrap](bootstrap.yml): Connect and set up the host specified. Interactive.
- [emby](emby.yml): Install and configure Emby.
- [komga](komga.yml): Install and configure Komga.
- [network](network.yml): Configure network services like DHCP, DNS and Prometheus. Has tags to specify which type of service to update. Uses VyOS and PiHole. Variables used are specified in host variables.
- [rustdesk](rustdesk.yml): Install Rustdesk ID and Relay services.
- [syncthing](syncthing.yml): Install and configure Syncthing Discovery and Relay services.
- [update](update.yml): Updates each host.
- [web](web.yml): Install web stack with users, domains, and php. Will keep all data, but make sure that the state is actually used is only running.

## Inventory

One or more set of files defining groups of hosts. My structure is regarding on what they can do, having both `vm` and `ct` reside in `servers`, but also put more groups in `servers` if needed. This split up makes it easier to define certain . On top of this are groups of service defined, to make running playbooks easier for those type of services and specific variables for them.

- `servers` Main group for all servers.
  - `router` All routers that you can connect to. Although, this is mostly for listing and not used in any playbook per say, as some routers do not even support python.
  - `node` All servers which has dedicated hardware, including PVE and SoC boards.
  - `vm` All hosts that are within a virtual machine.
  - `ct` All hosts that are within a container. These containers are LXC and are connected to differently.
- `ignored` Special group which ignores a list of hosts that are decommissioned, disabled, not used or incompatible with Ansible.

## Group vars

Certain groups requires specific variables. `ct` for instance requires LXC connection. For certain services, DNS entries could be placed here for easier access. Some groups are reserved to allow certain variables to be specifically used for their structure, like `ct`. Make sure to separate each CT with the host they reside in.

Some variables are specifically required to use some of the playbooks.

- `controller_host`: The host which will control all other hosts, specifically where a playbook is called from.

## Host vars

Each host has its [own unique name](https://mnx.io/blog/a-proper-server-naming-scheme/), and therefore its own config file or folder. Due to how Ansible replaces config keys for each host, most configs will be placed here, even if it is duplicate from other hosts with similar services.

Besides known ansible variables, there exist some more host specific variables that should be added to each host.

- `dhcp_ipv4`: The IPv4 for the host, used to reserve DHCP.
- `dhcp_mac`: The MAC-address for the host, used to reserve DHCP.

For a `ct`, you also need to specify additional variables.

- `lxc_host`: The vmid of the container.

## Action plugins

- `template_config`: Like `template`, but a modified validation where it will insert the config into the current system and validate the whole system instead of that single config file.
  - All arguments is the same as `template`, with some minor changes.
  - `dest`: The destination file to write to. Will be backed up before written to.
  - `validate`: A binary which validates the whole system. Does not require a config file as input.
- `verify_hosts`: Verify variables over several hosts. Paths are dot(`.`)-delimited names, excluding lists, and allows wildcard(`*`) for any name.
  - `unique_value`: A list with paths, excluding lists, to make sure the value is unique over each host.
  - `value_format`: A dictionary with keys as path and value as regular expressions, to check if the values follows the expression.

## Filter plugins

- `chunks`: Splits a list into chunks of size `count`.
  - `count`: The amount of items to include in each chunk list.
- `expand_dict`: Expands a list into list of dictionaries.
  - `field`: The name of the field to move each item to.
- `flatten_dict`: Flatten a dict by traversing into a child and apply all parent fields.
  - `to`: Path to flatten dictionary to.
  - `fields`: List of paths which values should be combines into.

## Roles

A list containing all roles with a brief explanation of what they do.

- [apcupsd](roles/apcupsd): Set up apcupsd and optionally [vmctrl](../vmctrl).
- [apache2](roles/apache2): Set up apache with domains.
- [bootstrap](roles/bootstrap): Configure host to connect to.
- [emby](roles/emby): Set up Emby with config.
- [goacccess](roles/goacccess): Set up goaccess for statistics for apache.
- [komga](roles/komga): Set up Komga with config.
- [mysql](roles/mysql): Set up MariaDB with databases, users and permissions.
- [php-fpm](roles/php-fpm): Set up PHP-FPM with specific versions and modules.
- [pihole](roles/pihole): Set up PiHole with unbound and adlists.
- [prometheus](roles/prometheus): Set up prometheus hosts.
- [proxy](roles/proxy): Set up proxy for web serviecs.
- [router](roles/router): Set up a router with DHCP, NAT and firewall.
- [rustdesk](roles/rustdesk): Set up Rustdesk ID and Relay services.
- [sshd](roles/sshd): Configure sshd.
- [syncthing](roles/syncthing): Set up Syncthing Discovery and Relay services.
- [update](roles/update): Updates hosts with newest packages.
- [vyos](roles/vyos): Set up a VyOS instance with DHCP, NAT and firewall.
