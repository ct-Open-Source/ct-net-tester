#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pygame
from gui import gui
from net import net
from config import config
from subprocess import call

class nettester:

    def __init__(self):
        # are we running
        self._running = False
    
    @staticmethod
    def cleanup():
        # end the created objects
        gui.quit()
        exit()
    
    # set the running state of the programm and start the internal loop
    def execute(self):
        self._running = self.init()
        while self._running:
            self.loop()
        # clean up end end
        self.cleanup()

    def init(self):
        # load the config file
        self.nettester_config = config()
        # initialize the gui
        self.nettester_gui = gui(
            self.nettester_config.config["resolution"],
            self.nettester_config.config["fg_color"],
            self.nettester_config.config["bg_color"],
            self.nettester_config.config["font_size_correction"],
            self.nettester_config.config["show_mouse_cursor"],
            )
        # initialize the networking
        self.nettester_net = net()
        # create the buttons
        self.create_buttons()
        self.switch_to_wired()
        return True

    # insert buttons into the gui
    def create_buttons(self):
        self.nettester_gui.titlebar_buttons.extend(
            [{
                "command": self.toggle_menu,
                "text": "Menü",
            }]
        )

        self.nettester_gui.menu_buttons.extend(
        [{
            "command": self.switch_to_wireless,
            "icon": "wireless.png",
            "text": "Wireless",
        },
        {
            "command": self.switch_to_wired,
            "icon": "wired.png",
            "text": "Wired",
        },
        {
            "command": self.shutdown,
            "icon": "shutdown.png",
            "text": "Shutdown",
        },
        {
            "command": self.check_net,
            "icon": "internet.png",
            "text": "Check Internet",
        },
        {
            "command": self.scan_wifi,
            "icon": "search.png",
            "text": "Wifi-Scan",
        },
        {
            "command": self.custom_command,
            "icon": "custom.png",
            "text": "Custom Command",
        }]
        )

        self.nettester_gui.paging_buttons[0]["command"] = self.page_up
        self.nettester_gui.paging_buttons[1]["command"] = self.page_down

    # the main loop
    def loop(self):
        # process all events since the last cycle
        self.process_events()
        # update the display
        self.nettester_gui.update_display()
        # call the guis tick to limit the framerate
        self.nettester_gui.tick()

    # process the pygame events
    def process_events(self):
        # walk all events received from the gui
        for event in self.nettester_gui.get_events():
            # if the event is any type of quit request end the programm
            if event.type == pygame.QUIT:
                self._running = False

            # resize the window if its requested
            elif event.type == pygame.VIDEORESIZE:
                self.nettester_gui.window_size = event.size
                self.nettester_gui.display_resize()
            
            # evaluate keypresses
            elif event.type == pygame.KEYDOWN:
                # exit on Escape
                if event.key == pygame.K_ESCAPE:
                    self._running = False
                # switch to fullscreen on F11
                elif event.key == pygame.K_F11:
                    self.nettester_gui.fullscreen = not self.nettester_gui.fullscreen
                    self.nettester_gui.display_resize()

            # evaluate all presses of the left mousebutton
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # make sure the programm doesn't crash if there are no buttons
                # yet
                if len(self.nettester_gui.titlebar_buttons) > 0:
                    self.check_buttonclick(event.pos,self.nettester_gui.titlebar_buttons)
                # menu buttons should only be clickable when the menu is open.
                # if its closed the paging_buttons should be clickable
                if self.nettester_gui.menu_open:
                    if len(self.nettester_gui.menu_buttons) > 0:
                        self.check_buttonclick(event.pos,self.nettester_gui.menu_buttons)
                else:
                    if len(self.nettester_gui.paging_buttons) > 0:
                        self.check_buttonclick(event.pos,self.nettester_gui.paging_buttons)

    # check the given buttons if their boundaries are a match to the mouse position
    def check_buttonclick(self, pos, button_list):
        for button in button_list:
            # if they are execute their given function
            if "bounds" in button and button["bounds"].collidepoint(pos):
                button["command"]()
                break
    
    # switch to the wireless interface and update the display accordingly
    def switch_to_wireless(self):
        self.nettester_net.switch_to_wireless()
        self.nettester_gui.interface_text = self.nettester_net.current_interface
        self.nettester_gui.set_text(self.nettester_net.get_interface_info())

    # switch to the wired interface and update the display accordingly
    def switch_to_wired(self):
        self.nettester_net.switch_to_wired()
        self.nettester_gui.interface_text = self.nettester_net.current_interface
        self.nettester_gui.set_text(self.nettester_net.get_interface_info())
    
    # show the last results of the wifi scan
    def scan_wifi(self):
        # update the display
        self.nettester_gui.interface_text = "WiFi-Scan"
        # hide the menu
        self.toggle_menu()
        # this is set to false if the user opens the menu again or the scan completes
        self.wifi_scan_in_progress = True
        # wait for the results
        while self.wifi_scan_in_progress:
            # try to get the scan data
            scan_data = self.nettester_net.get_wifi_scan()
            # if there are scan data show them and exit the loop
            if scan_data != None:
                self.nettester_gui.set_text(scan_data)
                self.wifi_scan_in_progress = False
                break
            else:
                # if there are no scan data show yet show a please wait notification
                text = []
                text.append("Bitte warten")
                self.nettester_gui.set_text(text)
                # update the interface although the main loop is blocked. this is easier than maintaining a proper loop management
                self.loop()
        self.nettester_net.wifi_scanner_thread.join(30)

    # show the results of the net scan
    def check_net(self):
        # update the display
        self.nettester_gui.interface_text = "Netztest"
        # hide the menu
        self.toggle_menu()
        # this is set to false if the user opens the menu again or the scan completes
        self.check_net_in_progress = True
        # get the remotes from the config file
        remotes = self.nettester_config.config["online_test_remote"].split(',')
        # start the check thread 
        self.nettester_net.net_checker(remotes)
        # wait for the results
        while self.check_net_in_progress:
            # try to get the scan data
            scan_data = self.nettester_net.get_net_status()
            # if there are scan data show them and exit the loop
            if scan_data != None:
                self.nettester_gui.set_text(scan_data)
                self.check_net_in_progress = False
                break
            else:
                # if there are no scan data show yet show a please wait notification
                text = []
                text.append("Bitte warten")
                self.nettester_gui.set_text(text)
                # update the interface although the main loop is blocked. this is easier than maintaining a proper loop management
                self.loop()
        self.nettester_net.check_net_thread.join(30)

    # show the results of the custom command
    def custom_command(self):
        # update the display
        self.nettester_gui.interface_text = "Eigener Befehl"
        # hide the menu
        self.toggle_menu()
        # this is set to false if the user opens the menu again or the command completes
        self.custom_command_in_progress = True
        # get the command from the config file
        command = self.nettester_config.config["custom_command"]
        # start the command thread 
        self.nettester_net.custom_command(command)
        # wait for the results
        while self.custom_command_in_progress:
            # try to get the scan data
            command_result = self.nettester_net.get_custom_command_status()
            # if there are scan data show them and exit the loop
            if command_result != None:
                self.nettester_gui.set_text(command_result)
                self.check_net_in_progress = False
                break
            else:
                # if there are no results show yet show a please wait notification
                text = []
                text.append("Bitte warten")
                self.nettester_gui.set_text(text)
                # update the interface although the main loop is blocked. this is easier than maintaining a proper loop management
                self.loop()
        self.nettester_net.custom_command_thread.join(30)

    # scroll the page down 
    def page_down(self):
        self.nettester_gui.scroll_textbox(False)

    # scroll the page up 
    def page_up(self):
        self.nettester_gui.scroll_textbox(True)
    
    # toggle the menu
    def toggle_menu(self):
        self.nettester_gui.menu_open = not self.nettester_gui.menu_open
        # stop the running background tasks
        self.wifi_scan_in_progress = False
        self.check_net_in_progress = False
        self.custom_command_in_progress = False

    # exit the programm and say bye
    def shutdown(self):
        self.nettester_gui.interface_text = "Auf Wiedersehen"
        call(["sudo", "poweroff"])
        self._running = False
        
if __name__ == "__main__":
    application = nettester()
    application.execute()
