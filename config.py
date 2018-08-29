#!/usr/bin/python
# -*- coding: utf-8 -*-
import configparser

class config:
    def __init__(self):
        self._parser = configparser.ConfigParser()
        self.config = ""
        self._load_config()

    def _load_config(self):
        try:
            # load the configuration file and load the nettester segment 
            self._parser.read('nettester.conf')
            if "nettester" in self._parser:
                self.config = self._parser['nettester']
        except Exception as exc:
            # return the error and exit
            print("Loading the configuration file failed")
            print(exc)
            exit()
