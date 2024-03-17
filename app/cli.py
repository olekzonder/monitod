import curses
from monitor import Group, Value
class CLI:
    def __init__(self, importer):
        self.importer = importer
        self.importer.activate_all()
        self.tabs = []
        self.selected_tab = None
        self.current_tab = 0
        self.scroll_position = 0

    def run(self):
        curses.wrapper(self._main)

    def update_tabs(self):
        if self.selected_tab == None:
            self.tabs = [self._create_tab(group.name, group) for group in self.importer.read_all()]
        else:
            self.selected_tab = self.importer[self.tabs[self.current_tab]['title'].lower()].read()

    def display_tabs(self, stdscr):
        y = 2
        for i, tab in enumerate(self.tabs):
            attr = curses.A_REVERSE if i == self.current_tab else curses.A_NORMAL
            stdscr.addstr(tab['title'], attr)
            stdscr.addstr(" ")
        self.content = self.gather(self.tabs[self.current_tab]['content'])
        for i, value in enumerate(self.content[self.scroll_position:self.height+self.scroll_position-1]):
            stdscr.addstr(i+1,0,value['value'],value['attr'])
    
    def gather(self,group,depth=0):
        result = []
        for item in group:
            if isinstance(item,Value):
                result.append({'value':f"{item.name.replace('_',' ').title()}: {item.value} {item.unit}", 'attr':curses.A_NORMAL})
            else:
                attr = curses.A_UNDERLINE if depth==0 else curses.A_BOLD
                result.append({"value":item.name.replace('_',' ').title(), 'attr' : attr})
                result.extend(self.gather(item,depth=depth+1))
        return result

    def _create_tab(self, title, group):
        return {'title': title.upper(), 'content': group}

    def _main(self, stdscr):
        curses.noecho()
        stdscr.nodelay(1)
        curses.curs_set(0)
        stdscr.scrollok(True)
        curses.use_default_colors()
        stdscr.timeout(1000)
        while True:
            stdscr.clear()
            self.height, self.width = stdscr.getmaxyx()
            if self.height < 10 or self.width < 50:
                stdscr.addstr("Not enough size!")
                continue
            self.update_tabs()
            stdscr.refresh()
            self.display_tabs(stdscr)
            self.selected_tab = self.tabs[self.current_tab]
            key = stdscr.getch()
            if key == curses.KEY_LEFT:
                self.scroll_position = 0
                self.current_tab = (self.current_tab - 1) % len(self.tabs)
            elif key == curses.KEY_RIGHT:
                self.scroll_position = 0
                self.current_tab = (self.current_tab + 1) % len(self.tabs)
            elif key == curses.KEY_DOWN:
                if len(self.content) < self.height or self.scroll_position+self.height == len(self.content)+1:
                    pass
                else:
                    self.scroll_position = min(len(self.content),self.scroll_position+1)
                pass
            elif key == curses.KEY_UP:
                if len(self.content) < self.height:
                    pass
                else:
                    self.scroll_position = max(0,self.scroll_position-1)
                pass
            elif key == ord('q'):
                break