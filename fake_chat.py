import curses
from curses import COLOR_WHITE,COLOR_GREEN,COLOR_RED, COLOR_CYAN,COLOR_BLACK, COLOR_MAGENTA
from time import sleep

from windows import Window, StringWindow, EditorWindow, MenuWindow, MenuTuple

from itertools import cycle

from random import randint
from time import time, sleep

KEY_TAB = 9


TITLE_ACTIVE = 2
TITLE_INACTIVE = 3
MENU_MESSAGE = 4
BASIC = 0

class FakeChatWindow(StringWindow):

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
    main_border = Window((0,0),(maxx, maxy),"Main Window",TITLE_INACTIVE)
    display_output = FakeChatWindow((1,1),(splitx-1,splity-1),"Chat",TITLE_INACTIVE)
    menu_window = MenuWindow((splitx,1),((maxx-splitx-1),maxy-2),"Menu",TITLE_INACTIVE)
    editor_window = EditorWindow((1,splity),(splitx-1,maxy-splity-1), "Text Edit", palette=TITLE_INACTIVE,
                             callback=display_output.add_str)

    menu_actions = [MenuTuple("Say 'Hi'",(display_output.add_str,"Hello from the Menu",MENU_MESSAGE)),
                    MenuTuple("Say something else",(display_output.add_str,"From the Menu, Hello!",MENU_MESSAGE)),
                    MenuTuple("I Prefer Cyan",(curses.init_pair,TITLE_INACTIVE,COLOR_CYAN,COLOR_BLACK)),
                    MenuTuple("I Prefer Green",(curses.init_pair,TITLE_INACTIVE,COLOR_GREEN,COLOR_BLACK)),
                    MenuTuple("I Prefer Plain",(curses.init_pair,TITLE_INACTIVE,COLOR_WHITE,COLOR_BLACK)),
                    ]
 
    menu_window.set_menu(menu_actions)

    windows = [main_border, display_output, menu_window, editor_window]
    input_windows = cycle([menu_window,editor_window])
    active_window = input_windows.next()
    active_window.draw_border(TITLE_ACTIVE)

    while True:
      key = stdscr.getch()
      if key == curses.ERR:
          dirtied = 0
          for win in windows:
            dirtied += win.dirty
            win.update()
          #if dirtied:
          stdscr.refresh()
          sleep(.1) #don't be burnin up the CPU, yo.
      elif key == KEY_TAB:
          active_window.draw_border() #uses window default
          active_window = input_windows.next()
          active_window.draw_border(TITLE_ACTIVE)
          
      else:
        #input_window.process_key(key)
        active_window.process_key(key)
try:
  #stolen from https://docs.python.org/2/howto/curses.html
  stdscr = curses.initscr()
  curses.start_color()
  curses.noecho()
  curses.cbreak()
  stdscr.nodelay(1)
  stdscr.keypad(1)
  curses.init_pair(1, COLOR_GREEN, COLOR_BLACK)
  curses.init_pair(2, COLOR_RED, COLOR_BLACK)
  curses.init_pair(3, COLOR_WHITE, COLOR_BLACK)
  curses.init_pair(4, COLOR_MAGENTA, COLOR_BLACK)
  run()

except Exception:
  curses.nocbreak(); stdscr.keypad(0); curses.echo();curses.endwin()
  raise
finally:
  curses.nocbreak(); stdscr.keypad(0); curses.echo();curses.endwin()
  print "\nThis terminal can%s display color\n" % ["'t",""][curses.has_colors()]
