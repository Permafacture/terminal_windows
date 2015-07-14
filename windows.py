import curses
from curses import COLOR_GREEN,COLOR_RED, COLOR_CYAN,COLOR_BLACK
from curses import KEY_UP, KEY_DOWN
from curses import A_REVERSE
from curses import textpad
from collections import OrderedDict, namedtuple


#Just to make things explicit, use this for Menu callbacks
MenuTuple = namedtuple("MenuTuple",('title','callback'))

#Can't trust curses to find TAB, ENTER, etc
KEY_ENTER = 10

class Window(object):
    '''Basic Window object draw a border for itself and can write 
    colored strings into itself'''

    def __init__(self,position=(0,0),size=(40,5),title=None,
                 palette = COLOR_GREEN,
                 border=True):
      '''
      position -> upper left corner: (x,y)
      size -> (width,height)
      title -> words to put in upper left corner
      palette -> integer corisponding to a curses color pair (0,1,2,3,etc)
      '''
      self._pos = position
      self._size = size
      self.title = title
      self.palette = palette
      self._border = border
      self._win = curses.newwin(size[1],size[0],
                                 position[1],position[0])
      self.draw_border()
      self.dirty = True


    def _addstr(self,x,y,string,effect=None,palette=None):
        '''Draw a string starting at (x,y) with an optional  
        color and effect, like curses.A_REVERSE'''
        #bitwise or color with effect to get both
        effect = effect or 0
        if palette is None:
          color = curses.color_pair(self.palette) | effect
        else:
          color = curses.color_pair(palette) | effect
        self._win.addstr(x,y,string,color)

    def draw_border(self,palette=None):
        if self._border:
          self._win.border()
        if self.title:
          self._addstr(0,2,self.title[:self._size[0]-3],curses.A_REVERSE,palette)
        self.dirty = True
        
    def update(self):
        '''update buffer if changed but don't output it.
        must still call refresh on this window or the main
        screen to update the display'''
        if self.dirty:
          self._win.noutrefresh()
          self.dirty = False

    def clear(self):
        win = self._win
        width, height = self._size
        for i in xrange(height):
          win.addstr(i,0,' '*(width-2))
        self.dirty = True


class StringWindow(Window):
    '''A subclass of Window that knows how to manage strings,
    including scrolling and line wrapping'''

    def __init__(self,*args,**kwargs):
        super(StringWindow,self).__init__(*args,**kwargs)
        self._strings=[]

    def add_str(self,string,palette=None,effect=None):
        '''Add a string with optional color and effect to the list
        to be rendered'''
        #I'd rather mangle strings only on render
        #rather than store mangled data (less useful)
        self._strings.append((string,(palette,effect)))
        self.dirty = True

    def render_strings(self):
        width, height = self._size
        width -= 2  #for border
        height -= 2
        strings_and_colors= self._strings[-height:]
        frame = []

        #break list of strings up into line wrapped pieces
        for string, color in strings_and_colors:
          old = 0
          piece = string[old:old+width]
          while piece:
            frame.append((piece.ljust(width),color))
            old += width
            piece = string[old:old+width]        
        for i,(string,color) in enumerate(frame[-height:]):
          palette,effect = color
          try:
            #awkward iterating backwards through two containers 
            # of different sizes...
            self._addstr(i+1,1,string,palette=palette, effect=effect)
          except IndexError:
            pass

    def update(self):
        if self.dirty:
          self.render_strings()
          self._win.noutrefresh()
          self.dirty = False


class EditorWindow(Window):
    '''Window that contains a readlines enabled text editing pad with 
    emacs like bindings.  Actual editable area is width-2, height-2 
    smaller than given size to leave room for the border.'''

    def __init__(self,*args,**kwargs):
        '''Takes same args and kwargs as Window, plus a callback.
        The callback is a function that gets called with the string 
        in the editor window as it's only argument.
       '''
        try:
          callback = kwargs.pop('callback')
        except KeyError:
          callback = (lambda x: None)

        super(EditorWindow,self).__init__(*args,**kwargs)
        self.init_editor()
        self.callback = callback or (lambda x: x)

    def init_editor(self):
        self.input_window = Window([x+1 for x in self._pos],[x-2 for x in self._size],
                                   title=None,border=False)
        self.input_window._win.keypad(1)
        self.editor = textpad.Textbox(self.input_window._win)

    def update(self):
        super(EditorWindow,self).update()
        self.input_window.update()

    def process_key(self,key):
        if key == KEY_ENTER:
          string = self.editor.gather()
          string = ''.join(x for x in string if x != "\n")
          if string:
            self.callback(string)
            self.init_editor()
        else:
          if self.editor.do_command(key):
            self.input_window._win.refresh() #needed to hold curson in window

class MenuWindow(StringWindow):
    '''String window that has a cursor for selecting lines and which
    executes callbacks when lines are selected.'''

    def __init__(self,*args,**kwargs):
        '''Takes same args and kwargs as String Window.
        Be sure to use set_menu or this window won't do
        anything'''
        super(MenuWindow,self).__init__(*args,**kwargs)
        self.menu_list = list()
        self.rebuild_menu()
        self.cursor = 0

    def rebuild_menu(self):
        self._strings = [(s.title,(None,None)) for s in self.menu_list]
        self.dirty=True

    def set_menu(self,new_menu):
        '''takes a list of MenuTuples and creates the menu from them
        MenuTuple.title is the name that displays on the menu
        MenuTuple.callback is a tuple of (callback_func, arg_1, ..., arg_n)
        the callback is called with it's arguments when the menu item is 
        selected'''
        self.menu_list = new_menu
        self.rebuild_menu()
    
    def move_cursor(self,delta):
        strings = self._strings
        old_i = self.cursor
        new_i = old_i + delta
        #make sure cursor is not less than 0 or more than the number of options
        new_i = sorted( (0, new_i, len(strings)-1) )[1]
        self.cursor = new_i

        #get rid of formatting on old line
        strings[old_i] = (strings[old_i][0],(None,None))
        strings[new_i] = (strings[new_i][0],(None,A_REVERSE))
        self.dirty=True

    def process_key(self,key):
        if key == KEY_UP:
          self.move_cursor(-1)
        elif key == KEY_DOWN:
          self.move_cursor(1)
        elif key == KEY_ENTER:
          title,callback = self.menu_list[self.cursor]
          callback[0](*callback[1:])
