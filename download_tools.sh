#!/bin/bash
wget -r -np -nH --cut-dirs=3 -R "index.html*" "https://svn.red-bean.com/repos/producingoss/trunk/tools/"
