#!/bin/sh

PYTHON=`cat ${0%/*}/.pypath`
export PYTHONPATH=${0%/*}/..

$PYTHON $@
