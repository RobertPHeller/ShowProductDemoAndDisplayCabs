#!/bin/bash
dir=`dirname $0`
rm *P?.pdf
$dir/ShowProductDemoAndDisplayCabs.py
qpdf --empty --pages *P?.pdf -- ShowProductDemoAndDisplayCabs.pdf

