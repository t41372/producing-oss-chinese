# Building the Book

This document describes how to build the HTML and PDF versions of the book from the XML sources.

## Dependencies

The build process requires the following tools to be installed:

- `make`
- `sed`
- `xsltproc`
- `fop`

On a Debian-based system, you can install them with:

```
sudo apt-get update
sudo apt-get install make sed libxml2-utils fop
```

## Build Process

The main `Makefile` in the root directory is used to build the book.

To build all language versions, run:

```
make all
```

To build a specific language version (e.g., Chinese), run:

```
make zh
```

The build process will generate the output files in the corresponding language directory (e.g., `book/zh/`).
