![Python versions](https://img.shields.io/badge/Python-3.14-blue)
![OS support](https://img.shields.io/badge/OS-Windows_Linux_macOS-red)
![Tool version](https://img.shields.io/badge/Version-0.4.4-green)

# AoCLI
Manage Advent of Code puzzles.

## Installation
The program is intended to be installed as an [uv](https://docs.astral.sh/uv/) tool:
```bash
uv tool install git+https://github.com/the-sh4d0w/tools#subdirectory=aocli
```

## Updating
Updates are also done through uv (⚠be warned, this will reset the config):
```bash
uv tool upgrade aocli
```

## Authentication with Advent of Code
The tool needs to authenticate itself with the Advent of Code to perform some of its functionality
(`setup` and `submit`). This is handled through an authentication token expected in the file `session.cookie` in the directory the tool is executed in (the path can be changed in the config).
The auth token can be retrieved by logging into the website and copying the value of the cookie
`session`.

I would suggest putting the path to the `session.cookie` file in your `.gitignore` so you can't
accidentally commit it to a (public) repository. Anyone who has the auth token can (for the year
or so it is valid) access your Advent of Code account. Also, please feel free to review the source
code before using the tool, if you don't want to trust me blindly.
