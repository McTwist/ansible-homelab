# PHP-FPM

Installs and configures php-fpm modules. 

# Action plugins

- `php_facts`: Gathers all running domains and php versions.

# Filter plugins

- `get_php_modules`: Prepates all php modules from config and applies default values for each php verion.
- `diff_config`: Remove dictionaries from a list which contain the disctionaries that is going to be removed contained in the fields.
  - `remove`: List of dictionaries to remove.
  - `fields`: Fields to compare with.
