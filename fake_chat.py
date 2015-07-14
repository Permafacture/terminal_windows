import curses
from curses import COLOR_WHITE,COLOR_GREEN,COLOR_RED, COLOR_CYAN,COLOR_BLACK, COLOR_MAGENTA
from time import sleep

from windows import Window, StringWindow, EditorWindow, MenuWindow, MenuTuple

from itertools import cycle

from random import randint
from time import time, sleep

#can't rely on curses to find tab, enter, etc.
KEY_TAB = 9


#name some colors (foreground/background pairs)
#actually defined later through curses.init_pair
BASIC = 0  #not editable
TITLE_ACTIVE = 1
TITLE_INACTIVE = 2
MENU_MESSAGE = 3

class FakeChatWindow(StringWindow):
    '''String Window that just spews out some words at random times'''

    def __init__(self,*args,**kwargs):

        super(FakeChatWindow,self).__init__(*args,**kwargs)
        self.next_time = time() + randint(1,4)
        self.things_to_say = self.fake_chat_gen()

    def fake_chat_gen(self):
        intro = [
          "This is a fake chat program",
          "Press TAB to switch between windows",
          "When you type in the editor, this window is still responsive",
          "I could be getting information from a socket rather than a dumb loop!",
          "Press CTRL+C to quit.",
          "So, uh, have fun and all."]

        annoying = cycle(["this is the song that never ends","It goes on and on my FRIEND!",
                            "Some people started singing it not knowing what it was.",
                            "and then they kept on singing it for-ever just because"])

        for s in intro:
          yield s
        for s in annoying:
          yield s


    def update(self):
        now = time()
        if now > self.next_time:
          self.next_time = now+randint(1,5)
          self.add_str(self.things_to_say.next(),palette=BASIC)
        super(FakeChatWindow,self).update()

          
def run():

    #Manual tiling
    maxy,maxx = stdscr.getmaxyx()
    splity = int(maxy*.8)
    splitx = int(maxx*.8)

    #initialize windows
    #specify Upper left corner, size, title, color scheme and border/no-border
    main_border = Window((0,0),(maxx, maxy),"Main Window",TITLE_INACTIVE)
    display_output = FakeChatWindow((1,1),(splitx-1,splity-1),"Chat",TITLE_INACTIVE)
    menu_window = MenuWindow((splitx,1),((maxx-splitx-1),maxy-2),"Menu",TITLE_INACTIVE)
    editor_window = EditorWindow((1,splity),(splitx-1,maxy-splity-1), "Text Edit", palette=TITLE_INACTIVE,
                             callback=display_output.add_str)

    #Set menu options with corrisponding callbacks
    menu_actions = [MenuTuple("Say 'Hi'",(display_output.add_str,"Hello from the Menu",MENU_MESSAGE)),
                    MenuTuple("Say something else",(display_output.add_str,"From the Menu, Hello!",MENU_MESSAGE)),
                    MenuTuple("I Prefer Cyan",(curses.init_pair,TITLE_INACTIVE,COLOR_CYAN,COLOR_BLACK)),
                    MenuTuple("I Prefer Green",(curses.init_pair,TITLE_INACTIVE,COLOR_GREEN,COLOR_BLACK)),
                    MenuTuple("I Prefer Plain",(curses.init_pair,TITLE_INACTIVE,COLOR_WHITE,COLOR_BLACK)),
                    ]
    menu_window.set_menu(menu_actions)

    #Put all the windows in a list so they can be updated together
    windows = [main_border, display_output, menu_window, editor_window]

    #create input window cycling
    # an input window must have a process_key(key) method
    input_windows = cycle([menu_window,editor_window])
    active_window = input_windows.next()
    active_window.draw_border(TITLE_ACTIVE)


    #Main Program loop.  CTRL+C to break it.
    while True:
      #asynchronously try to get the key the user pressed
      key = stdscr.getch()
      if key == curses.ERR:
          #no key was pressed.  Do house-keeping
          dirtied = 0
          for win in windows:
            dirtied += win.dirty
            win.update()
          #if dirtied:
          stdscr.refresh()
          sleep(.1) #don't be burnin up the CPU, yo.
      elif key == KEY_TAB:
          #cycle input window
          active_window.draw_border() #uses window default
          active_window = input_windows.next()
          active_window.draw_border(TITLE_ACTIVE)
          
      else:
        #every other key gets processed by the active input window
        active_window.process_key(key)

#Set up screen.  Try/except to make sure the terminal gets put back
#  together no matter what happens
try:
  #https://docs.python.org/2/howto/curses.html
  stdscr = curses.initscr()
  curses.start_color()
  curses.noecho()  #let input windows handle drawing characters to the screen
  curses.cbreak()  #enable key press asynch
  stdscr.nodelay(1)  #enable immediate time out (don't wait for keys at all)
  stdscr.keypad(1)  #enable enter, tab, and other keys

  #Set initial palette
  curses.init_pair(TITLE_ACTIVE, COLOR_RED, COLOR_BLACK)
  curses.init_pair(TITLE_INACTIVE, COLOR_WHITE, COLOR_BLACK)
  curses.init_pair(MENU_MESSAGE, COLOR_MAGENTA, COLOR_BLACK)

  #run while wrapped in this try/except
  run()

except Exception:
  #put the terminal back in it's normal mode before raising the error
  curses.nocbreak(); stdscr.keypad(0); curses.echo();curses.endwin()
  raise

finally:
  curses.nocbreak(); stdscr.keypad(0); curses.echo();curses.endwin()
  print "\nThis terminal can%s display color\n" % ["'t",""][curses.has_colors()]
