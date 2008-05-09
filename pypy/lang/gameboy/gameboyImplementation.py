#!/usr/bin/env python 

import pyglet
pyglet.options['audio'] = ('openal', 'silent')
        
from pyglet        import window
from pyglet        import media
from pyglet        import image
from pyglet.window import key

from pypy.lang.gameboy.gameboy import *
from pypy.lang.gameboy.joypad import JoypadDriver
from pypy.lang.gameboy.video  import VideoDriver
from pypy.lang.gameboy.sound  import SoundDriver


# GAMEBOY ----------------------------------------------------------------------

class GameBoyImplementation(GameBoy):
    
    def __init__(self):
        self.create_window()
        GameBoy.__init__(self)
        self.mainLoop()
        
    def create_window(self):
        self.win = window.Window()
        self.win.set_caption("PyBoy a GameBoy (TM)")
        
    def create_drivers(self):
        self.clock = Clock()
        self.joypad_driver = JoypadDriverImplementation(self.win)
        self.video_driver  = VideoDriverImplementation(self.win)
        self.sound_driver  = SoundDriverImplementation()
        
    def mainLoop(self):
        while not self.win.has_exit: 
           pass
        
# VIDEO DRIVER -----------------------------------------------------------------

class VideoDriverImplementation(VideoDriver):
    
    def __init__(self, win):
        VideoDriver.__init__(self)
        self.win = win
        self.win.on_resize = self.on_resize
        self.set_window_size()
        self.create_image_buffer()

    def create_image_buffer(self):
        self.buffers = image.get_buffer_manager()
        self.image_buffer = self.buffers.get_color_buffer()
        
    def on_resize(self, width, height):
        pass
    
    def set_window_size(self):
        self.win.set_size(self.width, self.height)
        
    def update_display(self):
        self.image_buffer.blit(0, 0)
        self.win.flip()
        
        
# JOYPAD DRIVER ----------------------------------------------------------------

class JoypadDriverImplementation(JoypadDriver):
    
    def __init__(self, win):
        JoypadDriver.__init__(self)
        self.create_button_key_codes()
        self.win = win
        self.create_listeners()
        
    def create_button_key_codes(self):
        self.button_key_codes = {key.UP : (self.button_up),
                              key.RIGHT : (self.button_right), 
                              key.DOWN  : (self.button_down), 
                              key.LEFT  : (self.button_left), 
                              key.ENTER : (self.button_start),
                              key.SPACE : (self.button_select),
                              key.A     : (self.button_a), 
                              key.B     : (self.button_b)}
        
    def create_listeners(self):
        self.win.on_key_press = self.on_key_press
        self.win.on_key_release = self.on_key_press
        
    def on_key_press(symbol, modifiers): 
        pressButtonFunction = self.get_button_handler(symbol, modifiers)
        if pressButtonFunction != None:
            pressButtonFunction(True)
    
    def on_key_release(symbol, modifiers): 
        pressButtonFunction = self.get_button_handler(symbol, modifiers)
        if pressButtonFunction != None:
            pressButtonFunction(False)
            
    def get_button_handler(self, symbol, modifiers):
        if symbol in self.button_key_codes:
            if len(self.button_key_codes[symbol]) == 1 or\
                    self.button_key_codes[symbol][1] ==  modifiers:
                return self.button_key_codes[symbol][0]
        return None
        
        
# SOUND DRIVER -----------------------------------------------------------------

class SoundDriverImplementation(SoundDriver):
    
    def __init__(self):
        SoundDriver.__init__(self)
        self.create_sound_driver()
        self.enabled = True
        self.sampleRate = 44100
        self.channelCount = 2
        self.bitsPerSample = 8

    def create_sound_driver(self):
        pass
    
    def start(self):
        pass
        
    def stop(self):
        pass
    
    def write(self, buffer, length):
        pass
    
    
# ==============================================================================

if __name__ == '__main__':
    entry_point()



def entry_point(args):
    gameboy = GameBoyImplementation()


# _____ Define and setup target ___

def target(*args):
    return entry_point, None
