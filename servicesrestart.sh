#!/bin/bash
systemctl restart reciever
systemctl restart sender
systemctl status reciever
systemctl status sender

