#!/bin/bash
#
# lib/stx-nfv
# Functions to control the configuration and operation of the **network function virtualization** service

# check for service enabled
if is_service_enabled stx-nfv; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
	# Perform installation of service source
	echo_summary "Installing stx-nfv"
        install_nfv

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
	# Configure after the other layer 1 and 2 services have been configured
	echo_summary "Configuring stx-nfv"
	:
    fi
    if [[ "$1" == "unstack" ]]; then
	:
    fi

    if [[ "$1" == "clean" ]]; then
	echo_summary "Clean stx-nfv"
	clean_nfv
    fi
fi
