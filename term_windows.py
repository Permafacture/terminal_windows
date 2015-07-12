import curses
from curses import COLOR_GREEN,COLOR_RED, COLOR_CYAN,COLOR_BLACK
from curses import textpad
from time import sleep
#stolen from https://docs.python.org/2/howto/curses.html
stdscr = curses.initscr()
curses.start_color()
curses.noecho()
curses.cbreak()
stdscr.nodelay(1)
stdscr.keypad(1)

curses.init_pair(COLOR_GREEN,COLOR_GREEN,COLOR_BLACK)
curses.init_pair(COLOR_RED,  COLOR_RED  , COLOR_BLACK)
curses.init_pair(COLOR_CYAN, COLOR_CYAN , COLOR_BLACK)


KEY_ENTER = 10 #why do I have to do this?

class Window(object):

    def __init__(self,position=(0,0),size=(40,5),title=None,
                 palette = COLOR_GREEN,
                 border=True):
      self._pos = position
      self._size = size
      self.title = title
      self.palette = palette
      self._border = border
      self._strings = []
      self._win = curses.newwin(size[1],size[0],
                                 position[1],position[0])
      self.draw_border()
      self.dirty = True


    def _addstr(self,x,y,string,effect=0):
        #bitwise or with effect like A_REVERSE to get both
        color = curses.color_pair(self.palette) | effect
        self._win.addstr(x,y,string,color)

    def draw_border(self):
        if self._border:
          self._win.border()
        if self.title:
          self._addstr(0,2,self.title[:self._size[0]-3],curses.A_REVERSE)

    def update(self):
        if self.dirty:
          self.render_strings()
          self._win.noutrefresh()
          self.dirty = False

    def clear(self):
        win = self._win
        width, height = self._size
        for i in xrange(height):
          win.addstr(i,0,' '*(width-2))
        self.dirty = True

    def render_strings(self):
        #TODO padd with spaces
        width, height = self._size
        width -= 2  #for border
        height -= 2
        strings = self._strings[-height:]
        frame = []
        for string in strings:
          old = 0
          piece = string[old:old+width]
          while piece:
            frame.append(piece.ljust(width))
            old += width
            piece = string[old:old+width]        
        for i in range(height)[::-1]:
          try:
            #awkward iterating backwards through two containers 
            # of different sizes...
            self._addstr(i+1,1,frame[i])
          except IndexError:
            pass

class StringWindow(Window):

    def add_str(self,string):
        #I'd rather mangle strings only on render
        #rather than store mangled data (less useful)
        self._strings.append(string)
        self.dirty = True

class CharWindow(Window):

    def add_chr(self,char):
      pass

def run():
    maxy,maxx = stdscr.getmaxyx()
    
    display_windows = [Window((0,0),(maxx, maxy),"Main Window",COLOR_GREEN),
                       StringWindow((45,3),(40,10),"Text"),
                       StringWindow((3,3),(40,10),"What you wrote") ]
    display_windows[1].add_str("Am I the muffin man? I am the muffin man.  The muffin man I am! you booger. ")
    display_windows[1].add_str("I am a banana")
   
    input_border = Window((50,40),(60,10),"input") 
    input_window = Window((51,41),(58,8),None,COLOR_CYAN,False)
    input_window._win.keypad(1)
    editor = textpad.Textbox(input_window._win)
    display_windows.extend((input_border,input_window))

    while True:
      key = stdscr.getch()
      if key == curses.ERR:
          dirtied = 0
          for win in display_windows:
            dirtied += win.dirty
            win.update()
          if dirtied:
            stdscr.refresh()
          sleep(.1) #don't be burnin up the CPU, yo.
      else:
        #editor.edit()
        if key == KEY_ENTER:
          string = editor.gather()
          string = ''.join(x for x in string if x != "\n")
          display_windows[2].add_str(string)
          display_windows.remove(input_window)
          input_window = Window((51,41),(58,8),None,COLOR_CYAN,False)
          editor = textpad.Textbox(input_window._win)
          display_windows.append(input_window)

        else:
          #TODO show cursor, try not touching other windows every ERR
          if editor.do_command(key):
            input_window._win.refresh()

try:
  run()
except Exception:
  curses.nocbreak(); stdscr.keypad(0); curses.echo();curses.endwin()
  raise
finally:
  curses.nocbreak(); stdscr.keypad(0); curses.echo();curses.endwin()
  print "\nThis terminal can%s display color\n" % ["'t",""][curses.has_colors()]
