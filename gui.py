#!/usr/bin/python
# -*- coding: utf-8 -*-
import pygame
import os
import math
import datetime
from time import time
from aspect_scale import aspect_scale

class gui:
    def __init__(self, display_resolution, fg_color, bg_color,
                 scale_correction, cursor_visible):
        # a fullscreen switch for debugging purposes
        self.fullscreen = True
        # the display resolution as a tuple
        self.display_size = (int(display_resolution.split(',')[0]), int(display_resolution.split(',')[0]))
        # colors for foreground and background
        self.fg_color = self.string_to_color(fg_color)
        self.bg_color = self.string_to_color(bg_color)
        # the window size if the program is not set for fullscreen
        self.window_size = (640,480)
        # should the mouse cursor be visible?
        self.cursor_visible = True if cursor_visible == "1" else False
        # correction factor for text elements
        self.scale_correction = float(scale_correction)
        self._textbox_text = ""
        # size of the menubuttons will be calculated but should not be bigger than 200
        self.max_menu_icon_size= 200
        #variables for resource files
        self.resource_path = "res"
        self.logo_image = "logo.png"
        self.basefont = "freemono.ttf"
        # defines the font size threshold for antialiasing
        self.alias_threshold = 15
        self.font_antialiased = True
        # lists of buttons 
        self.titlebar_buttons = []
        self.menu_buttons = []
        # predefine the paging buttons since we know that there should be two
        self.paging_buttons = [
            {
                "text": "Up",
            },
            {
                "text": "Down",
            }
        ]
        # the menu should be closed at first
        self.menu_open = True
        # start the gui
        pygame.init()
        self.init()

    # initialize the display surface
    def display_init(self):
        # try to create a surface and check if it fails
        try:
            # fullscreen is the default
            if self.fullscreen:
                # create a hardware accelerated fullscreen surface
                self.display_surface = pygame.display.set_mode(self.display_size,
                                        pygame.FULLSCREEN | pygame.HWSURFACE |
                                        pygame.DOUBLEBUF)
            # alternatively try a windowed surface
            else:
                self.display_surface = pygame.display.set_mode(self.window_size,
                                                               pygame.RESIZABLE
                                                              |pygame.DOUBLEBUF)
        except Exception as exc:
            print(exc)
            print("Display initialization failed. This program needs a running X-Server.")
            exit()
            
        
        # get definitive size of the surface independend from what was
        # requested.
        self.display_size = self.display_surface.get_size()
    
    # return all pygame events
    def get_events(self):
        return pygame.event.get()

    # Tick the internal pygame clock to limit the framerate to 60fps
    def tick(self):
        pygame.time.Clock().tick(60)

    # set the window caption and the icon
    def set_window_details(self):
        pygame.display.set_caption("c't Net-Tester")
        icon = pygame.image.load(os.path.join(self.resource_path,self.logo_image))
        icon = aspect_scale(icon, (64,64))
        pygame.display.set_icon(icon)

    def calculate_sizes(self):
        # calculate the sizes of displayed elements based on the available
        # display resolution.
        # the size of the titlebar is an essential measurement and determines
        # most other measurements
        self.titlebar_font_size = math.floor((self.display_size[0] / 20)
                                      * self.scale_correction)
        self.text_font_size = math.floor(self.titlebar_font_size * 0.8)
                                
        self.titlebar_size = self.display_size[0], int(self.titlebar_font_size * 1.5)
        # textbox can be as wide as the screen but must leave space for the
        # titlebar 
        self.textbox_size = self.display_size[0], self.display_size[1] - self.titlebar_size[1]
        self.textbox_position = self.menu_position = (0,self.titlebar_size[1])
        
        #the upper half of the textbox is the up button and the lower the down
        #button to scroll text. their bounds can now be calculated
        paging_button_height = math.floor(self.textbox_size[1] / 2) # half of the textbox height
        
        self.paging_buttons[0]["bounds"] = pygame.Rect(
            self.textbox_position[0], # absolute left of the textbox
            self.textbox_position[1], # absolute top of the textbox
            self.textbox_size[0], # absolute right of the textbox
            paging_button_height
        )

        self.paging_buttons[1]["bounds"] = pygame.Rect(
            self.textbox_position[0],
            self.textbox_position[1] + paging_button_height, # top + half the height
            self.textbox_size[0],
            paging_button_height
        )

        # We want three buttons in a row and two rows of buttons, evenly spaced
        self.menu_button_size = int(math.floor((self.textbox_size[0] / 3) * 0.9))
        self.menu_button_padding = int((self.textbox_size[0] - (3 * self.menu_button_size)) / 4)
        self.menu_icon_size = int(self.menu_button_size * 0.9)

        # icons should look good, so don't oversize them 
        if self.menu_icon_size > self.max_menu_icon_size:
            self.menu_icon_size = self.max_menu_icon_size

    def create_fonts(self):
        # create a font object for titlebar and textbox text
        self.titlebar_font = pygame.font.Font(os.path.join(self.resource_path,self.basefont),self.titlebar_font_size)
        self.text_font = pygame.font.Font(os.path.join(self.resource_path,self.basefont),self.text_font_size)
        # enable or disable font antialiasing
        if self.text_font_size < self.alias_threshold:
            self.font_antialiased = False

    # show splash screen to better the user experience
    def show_splash_screen(self):
        # create a surface from the image file
        splash_logo = pygame.image.load(os.path.join(self.resource_path,self.logo_image))

        # calculate size and position of the logo to 75% of the screen size and
        # put it at 12.5%,12.5% of the screen to center it.
        splash_logo_size = (int(self.display_size[0] * 0.85),
                            int(self.display_size[1] * 0.85))
        
        splash_logo_position = (int(self.display_size[0] * 0.0725),
                            int(self.display_size[1] * 0.0725))
        
        # scale the logo according to its aspect
        splash_logo = aspect_scale(splash_logo, splash_logo_size)

        # blit it onto the surface and flip the display
        self.display_surface.blit(splash_logo,splash_logo_position)
        pygame.display.flip()

    def render_titlebar(self):
        # create an empty surface for the titlebar
        surface = pygame.Surface(self.titlebar_size,pygame.SRCALPHA, 32)
        # titlebars position will always be 0,0
        position = (0,0)
        
        # calculate border for titlebar
        line_start = (0, self.titlebar_size[1]-1)
        line_end = (self.titlebar_size[0], self.titlebar_size[1]-1)
        line_width = int(math.ceil(self.titlebar_size[1] / 100))
        # paint the bottom border
        pygame.draw.line(surface, self.fg_color, line_start, line_end, line_width)

        # calculate the text position
        text_pos_y = int(self.titlebar_size[1] / 6)

        # get current time
        time = str(datetime.datetime.now().strftime("%H:%M:%S"))
        # create the text_surface
        time_text_surface = self.titlebar_font.render(time,
                                  self.font_antialiased,
                                  self.fg_color)
        # calculate the text position
        time_text_surface_length = time_text_surface.get_rect()[2]
        time_text_pos_x = self.titlebar_size[0] - time_text_surface_length

        # blit it to the titlebar surface
        surface.blit(time_text_surface, (time_text_pos_x,text_pos_y))
        # the first button should be at 0
        button_pos_x = 0
        # iterate through all buttons
        for button in self.titlebar_buttons:
            # create a surface with the button text
            button_surface = self.titlebar_font.render(button["text"],
                                                self.font_antialiased,
                                                self.fg_color)
            # paint it onto the titlebar surface
            surface.blit(button_surface, (button_pos_x,text_pos_y))
            # get the size of the button surfqace
            button_size = button_surface.get_size()
            # calculate the clickable bounds
            button["bounds"] = pygame.Rect(
                button_pos_x,
                0,
                button_pos_x + button_size[0],
                0 + button_size[1] + (text_pos_y * 2),
            )
            # calculate the start and end position of the decorative button
            # divider line
            line_start = (button_size[0], 0)
            line_end = (button_size[0], button_size[1] + (text_pos_y * 2))
            # draw the line
            pygame.draw.line(surface, self.fg_color, line_start, line_end, line_width)
            # add the button size with some padding to the button position
            button_pos_x += (button_size[0]*1.1)
        
        # create the text of the interface text in the title
        interface_text_surface = self.titlebar_font.render(self.interface_text,
                                  self.font_antialiased,
                                  self.fg_color)
        # get the length of the surface
        interface_text_surface_length = interface_text_surface.get_rect()[2]
        # calculate the position of the interface text so it is centered
        interface_text_pos_x = (self.titlebar_size[0] - interface_text_surface_length) / 2
        # paint it to the titlebar surface
        surface.blit(interface_text_surface, (interface_text_pos_x,text_pos_y))
        # return the titlebar and its position
        return surface, position

    def render_menu(self):
        # create an empty surface for the menu
        menu_surface = pygame.Surface(self.textbox_size,pygame.SRCALPHA, 32)
        # set the initial button position
        button_pos_x = button_pos_y = self.menu_button_padding
        # initialize the button counter
        button_count = 0
        # iterate the menu buttons
        for button in self.menu_buttons:
            # create an empty surface for this button
            button_surface = pygame.Surface((self.menu_button_size,
                                            self.menu_button_size))
            # create a rect for the button background
            border_rect = (0,0) + (self.menu_button_size,
                                   self.menu_button_size)
            # paint the background
            pygame.draw.rect(button_surface, self.fg_color, border_rect, 0)

            # load the button icon
            icon = pygame.image.load(os.path.join(self.resource_path,button["icon"]))
            # scale the icon
            icon = pygame.transform.smoothscale(icon, (self.menu_icon_size,
                                                       self.menu_icon_size))
            # calculate the icon position so it is centered
            icon_pos = (self.menu_button_size / 2) - (self.menu_icon_size / 2)
            
            # paint the icon onto the button surface
            button_surface.blit(icon, (icon_pos, icon_pos))

            # paint the button onto the icon surface
            menu_surface.blit(button_surface, (button_pos_x, button_pos_y))
            
            # calculate the clickable bounds
            button["bounds"] = pygame.Rect(
                self.menu_position[0] + button_pos_x,
                self.menu_position[1] + button_pos_y,
                self.menu_button_size,
                self.menu_button_size,
            )

            # add the button size with some padding to the button position
            button_pos_x += self.menu_button_size + self.menu_button_padding
            # increment the button counter
            button_count += 1
            # wrap around if the button counter has reached 3
            if button_count == 3:
                button_pos_x = self.menu_button_padding
                button_pos_y += self.menu_button_size + self.menu_button_padding

        # return the titlebar and its position
        return menu_surface, self.menu_position


    # reinitialize display and recalculate all relevant sizes
    def display_resize(self):
        self.display_init()
        self.calculate_sizes()
        self.create_fonts()

    # initialize display and recalculate all relevant sizes create fonts and
    # show a splash screen to 'entertain' the user while waiting
    def init(self):
        self.set_window_details()
        self.display_init()
        self.show_splash_screen()
        self.calculate_sizes()
        self.create_fonts()
    
    # refresh the display
    def update_display(self):
        # paint the background color
        self.display_surface.fill(self.bg_color)
        # create a list of all known surfaces
        element_surfaces = []
        # append the titlebar to the surfaces
        element_surfaces.append(self.render_titlebar())
        # if the menu is open render the menu, otherwise show the textbox
        if (self.menu_open):
            element_surfaces.append(self.render_menu())
        else:
            element_surfaces.append(self.render_textbox())
        # paint all surfaces
        self.compose_image(element_surfaces)
    
    # assemble all surfaces and paint them onto the screen
    def compose_image(self, surfaces):
        # iterate all surfaces and paint them
        self.display_surface.blits(surfaces)
        # flip the screen for a refreh
        pygame.display.flip()
    
    # end
    def quit():
        # cleanly deactivate the pygame instance
        pygame.quit()

    def set_text(self, text):
            # update the textbox contents and reset the page so that a refresh will paint the first page
            self._textbox_text = text
            self.textbox_current_page = 0

    # render the textbox contents as surfaces. split lines if they are too long
    def render_textbox(self):
        # create a surface for the textbox
        surface = pygame.Surface(self.textbox_size,pygame.SRCALPHA, 32)
        # render an M as a measurement for the width of the characters. only works for monospaced fonts
        em_width = self.text_font.size("M")[0]
        # get the line height
        line_height = self.text_font.get_linesize()
        
        # calculate the available space in characters horizontally and vertically
        char_count_v = math.floor((self.textbox_size[0]) / em_width)
        char_count_h = math.floor((self.textbox_size[1]) / line_height)
        # how many pages do we need to display the entire text
        self.pages = math.floor(len(self._textbox_text) / char_count_h)

        # calculate at which line the text should start
        start_line = char_count_h * self.textbox_current_page
        
        # this stores the y-coordinates of the current line
        current_text_pos = 0
        # relative lines inside the page 
        line_count = 0
        for line_num, line in enumerate(self._textbox_text):
            # skip all lines that don't need to be rendered
            if(line_num < start_line):
                continue
            # start wrapping the line if it's too long for the display
            if len(line) >= char_count_v:
                # this stores the x-coordinates of the character to be drawn and char_counter stores the amount of characters already drawn
                char_pos = char_counter = 0
                # walk all characters
                for char in line:
                    # create an emptpy surface for this character.
                    char_surf = self.text_font.render(char, self.font_antialiased, self.fg_color)
                    # paint the character onto the surface
                    surface.blit(char_surf, (char_pos, current_text_pos))
                    # move the position one char right
                    char_pos = char_pos + em_width
                    # increment the amount of written characters
                    char_counter +=1
                    # if the line is full add a wrapping sign
                    if char_counter == (char_count_v - 1):
                        # create a surface for the wrapping char
                        char_surf = self.text_font.render("⏎", self.font_antialiased, self.fg_color)
                        # paint the character onto the surface
                        surface.blit(char_surf, (char_pos, current_text_pos))
                        # increment the line position one line
                        current_text_pos += line_height
                        # flip the wrap sign for the next line 
                        char_surf = pygame.transform.flip(char_surf, 1, 0)
                        # paint the character onto the surface at x-pos 0
                        surface.blit(char_surf, (0, current_text_pos))
                        # set the character position and counter to 1 char
                        char_pos = 1
                        char_pos = em_width
                        # increase the line counter
                        line_count +=1
            # if the line fits just paint it as a surface
            else:
                # create an emptpy surface for this line.
                text_surf = self.text_font.render(line, self.font_antialiased, self.fg_color)
                # paint the line onto the surface
                surface.blit(text_surf, (0, current_text_pos))
            # increase the line position and counter because we painted at least one line
            current_text_pos = current_text_pos + line_height
            line_count +=1
            # break out of the for loop when the screen is full
            if line_count == char_count_h:
                break
        # return the painted surface and it's position
        return surface, self.textbox_position
    
    # trigger a page scroll inside the textbox
    def scroll_textbox(self,direction = False):
        # True equals up, False equals down
        if direction:
            self.textbox_current_page -= 1
        else:
            self.textbox_current_page += 1
        # There is no page -1
        if self.textbox_current_page < 0:
            self.textbox_current_page = 0
        # There is a limit to the pages
        if self.textbox_current_page > self.pages:
            self.textbox_current_page = self.pages
            
    # convert a given comma seperated string to a color object
    def string_to_color(self,string):
        # split the string into a list
        list = string.split(',')
        # create color from the list indices
        color = pygame.Color(
            int(list[0]),
            int(list[1]),
            int(list[2])
            )
        # return the created color object
        return color

if __name__ == "__main__":
    print("This module cannot be called directly.")
