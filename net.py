#!/usr/bin/python
# -*- coding: utf-8 -*-

import pyric
import pyric.pyw as pyw
import netifaces
from getmac import get_mac_address
from access_points import get_scanner
import threading
import time
from net_helper import *

class net:
    def __init__(self):
        # placeholders for the list of interfaces
        self.wireless_interfaces = []
        self.wired_interfaces = []
        # query all system interfaces
        self.get_interfaces()
        # set the selected interface to the first found wired interface
        self.current_interface = self.wired_interfaces[0]
        self.last_wired_interface= self.wired_interfaces[0]
        self.last_wireless_interface= self.wireless_interfaces[0]
        # start the automatic wifi scan as a thread
        self.wifi_scanner()
        # has the first wifi scan been completed?
        self.first_scan_complete = False

    # get all system interfaces
    def get_interfaces(self):
        # request list of interfaces from pyric
        all_interfaces = pyw.interfaces()
        
        #walk all interfaces
        for interface in all_interfaces:
            # check if the interface is loopback or virtual
            if get_mac_address(interface) != "00:00:00:00:00" and interface != "lo":
                # check if it's wireless or not
                if pyw.iswireless(interface):
                    self.wireless_interfaces.append(interface)
                else:
                    self.wired_interfaces.append(interface)

        # append a placeholder interaface for the empty lists
        if len(self.wireless_interfaces) == 0:
                    self.wireless_interfaces.append("None")
        if len(self.wired_interfaces) == 0:
                    self.wired_interfaces.append("None")
    
    # switch to next interface
    def iterate_interface(self, current_interface, interfaces, last_interface):
        # get index of last selected interface
        interface_index = interfaces.index(last_interface)
        # if the current interface is equal to the last interface increment it, so the next one will be selected
        if current_interface == last_interface:
            next_interface = interface_index + 1
        # otherwise return the last interface, so we will simply switch between wireless and wired
        else:
            return last_interface

        # reset the list, if the interface counter exceeds the number of interfaces
        # attn: here lies an of by one error, beacause we compare an index with a count
        if next_interface == len(interfaces):
            next_interface = 0
        
        # return the selected interface
        return interfaces[next_interface]

    # switch to the wired interfaces
    def switch_to_wired(self):
        # select the next interface
        interface = self.iterate_interface(self.current_interface, self.wired_interfaces,self.last_wired_interface)
        # set the current interface and last used interface accordingly
        self.current_interface = self.last_wired_interface = interface
        # request the interface information
        self.get_interface_info()

    def switch_to_wireless(self):
        # select the next interface
        interface = self.iterate_interface(self.current_interface, self.wireless_interfaces,self.last_wireless_interface)
        # set the current interface and last used interface accordingly
        self.current_interface = self.last_wireless_interface = interface
        # request the interface information
        self.get_interface_info()

    # get infos about the interface
    def get_interface_info(self):
        # try to get the information from the interface. it might fail, if the device disappears for some reason
        try:
            # get all the addresses from netifaces
            if_info = netifaces.ifaddresses(self.current_interface)
            
            # the first line will be the devices MAC
            text = ["MAC:  " + if_info[netifaces.AF_LINK][0]['addr']]
            
            # get all IPv4 Addresses, netmask and broadcast and append them to text
            if netifaces.AF_INET in if_info:
                for dataset in if_info[netifaces.AF_INET]:
                    text.append("")
                    if 'addr' in dataset:       text.append("IPv4: " +
                                                            str(dataset['addr']))
                    if 'netmask' in dataset:    text.append("  NM: " +
                                                            str(dataset['netmask']))
                    if 'broadcast' in dataset:  text.append("  BC: " +
                                                            str(dataset['broadcast']))

            # get all IPv6 Addresses, netmask and broadcast and append them to text
            if netifaces.AF_INET6 in if_info:
                for dataset in if_info[netifaces.AF_INET6]:
                    text.append("")
                    if 'addr' in dataset:       text.append("IPv6: " +
                                                            str(dataset['addr']))
                    if 'netmask' in dataset:    text.append("  NM: " +
                                                            str(dataset['netmask']))
                    if 'broadcast' in dataset:  text.append("  BC: " +
                                                            str(dataset['broadcast']))
        except Exception as exc:
            # add the cause for the error to text
            text = ["Not available:"]
            text.append(str(exc))

        # return the text to be displayed
        return text

    # convert the wifi scan result into text
    def get_wifi_scan(self):
        text = []
        # check if the first scan has been completed
        if self.first_scan_complete:
            # format every access points data into text
            for access_point in self.access_points:
                text.append("SSID:     " + access_point['ssid'])
                text.append("BSSID:    " + access_point['bssid'])
                text.append("Signal:   " + str(access_point['quality']))
                text.append("Security: " + access_point['security'])
                text.append(" ")
        else:
            # when the scan is incomplete return None
            text = None

        return text
    
    # start the wifi scanning thread
    def wifi_scanner(self):
        self.wifi_scanner_thread = threading.Thread(target=self._wifi_scanner)
        self.wifi_scanner_thread.start()

    # function for the wifi scannin that is in another thread. 
    # this is needed since the wifi scanner blocks the code execution and the programm will seemingly hang
    def _wifi_scanner(self):
        # reset the known access points
        self.access_points = []
        # walk through all known wireless interfaces to get complete coverage
        for interface in self.wireless_interfaces:
            # create a card instance to work with
            card = pyw.getcard(interface)
            # check if the card is still valid
            if pyw.validcard(card):
                # skip the card if it is hard blocked
                if pyw.isblocked(card)[1]:
                    continue
                else:
                    # try to unblock a softblock, put the card up and disable the powersave mode
                    try:
                        pyw.unblock(card)
                        pyw.up(card)
                        pyw.pwrsaveset(card, False)
                    except:
                        # ignore failures
                        pass
                    # start scanning 
                    wifi_scanner = get_scanner(interface)
                    # extend the access point list
                    self.access_points.extend(wifi_scanner.get_access_points())

        # the first scan has been completed 
        self.first_scan_complete = True

    # return the status
    def get_net_status(self):
        return self.net_status_results

    # start net status thread
    def net_checker(self, remotes):
        self.net_status_results = None
        self.check_net_thread = threading.Thread(target=self._net_checker, args=[remotes])
        self.check_net_thread.start()
    
    # check the network connection by resolving dns data and pinging hosts
    def _net_checker(self, remotes):
        text = []
        # walk all given remotes
        for remote in remotes:
            # try to check if it is a valid ipv4- or ipv6-address or a domainname
            try:
                if is_valid_ipv4_address(remote):
                    hostip = remote
                    pass
                elif is_valid_ipv6_address(remote):
                    hostip = remote
                    pass
                else:
                    hostip = get_ip_from_hostname(remote)
                    text.append(str(remote) + ": " + hostip)
            except:
                # if it's neither fail and skip this remote
                text.append(str(remote) + ": Gegenstelle ungültig")
                continue
            # ping the ip and evaluate the result
            if ping_host(hostip):
                text.append(str(remote) + ": erreichbar")
            else:
                text.append(str(remote) + ": NICHT erreichbar")
        self.net_status_results = text

    def get_custom_command_status(self):
        return self.custom_command_result

    # start custom command thread
    def custom_command(self, command):
        self.custom_command_result = None
        self.custom_command_thread = threading.Thread(target=self._custom_command, args=[command])
        self.custom_command_thread.start()
    
    # execute a given custom command and store its stdout
    def _custom_command(self, command):
        command = command.split(' ')
        text = []
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE)
            print(result)
            if result.returncode != 0: raise Exception('Programmausführung fehlgeschlagen')
            output = result.stdout.decode('utf-8').splitlines()
            text.extend(output)
        except:
            text.append("Programmausführung fehlgeschlagen")
        self.custom_command_result = text
