# Pymdown-Embedly
Embedly card support for Python Markdown.

## Install

```sh
$ pip install pymdown-embedly
```

or

```sh
$ pip install .
```

## Usage

in mkdocs.

```yml title="mkdocs.yml"
markdown_extensions:
  - embedly
```

in cli.

```sh
$ python -m markdown -x embedly -x input.md > output.html
```
