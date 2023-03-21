from transfer.transferutil import *
from response.response import *
from util import *
import tkinter, tkinter.font

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 20

FONTS_CACHE = {}
def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS_CACHE:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS_CACHE[key] = font
    return FONTS_CACHE[key]

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.window.configure(background="light grey")
        self.window.title("Awesome Browser")
        self.window.bind("<Down>", self._scrolldown)
        self.window.bind("<Up>", self._scrollup)
        self.window.bind("<Button-4>", self._mousewheel)
        self.window.bind("<Button-5>", self._mousewheel)

        self.searchFrame = tkinter.Frame(self.window, background="grey")
        self.searchFrame.pack(fill=tkinter.X, expand=tkinter.NO)
        
        self.searchLabel = tkinter.Label(self.searchFrame, text="Enter URL", background="grey")
        self.searchLabel.pack(side=tkinter.LEFT)

        self.searchText = tkinter.StringVar()
        self.entry = tkinter.Entry(self.searchFrame, textvariable=self.searchText)
        self.entry.pack(side=tkinter.LEFT, fill=tkinter.X, expand=tkinter.YES)
        
        self.searchButton = tkinter.Button(self.searchFrame, text="Search",\
                                           command=lambda : [self._fetch_and_get(), self._print_text_on_canvas()])
        self.searchButton.pack(side=tkinter.LEFT)

        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack(fill=tkinter.BOTH, expand=tkinter.YES)
        self.canvas.bind("<Configure>", self._canvas_resize)

        self.scroll = 0
        self.tokens = None

    def _scrolldown(self, event):
        if self.scroll < self.layout_info['max-scroll']:
            self.scroll += SCROLL_STEP
        self._draw()

    def _scrollup(self, event):
        self.scroll -= SCROLL_STEP
        if self.scroll < 0:
            self.scroll = 0
        self._draw()

    def _canvas_resize(self, event):
        global WIDTH, HEIGHT

        WIDTH, HEIGHT = event.width, event.height
        self._print_text_on_canvas()

    def _mousewheel(self, event):
        if event.num == 4:
            self._scrollup(event)
        elif event.num == 5:
            self._scrolldown(event)
    
    def _fetch_and_get(self):
        url = self.searchText.get()
        if url == "":
            return
        
        response = get(url)

        if isinstance(response, HTTPResponse):
            self.tokens = HTMLParser(response.get_raw_body()).parse()
        else:
            self.tokens = response.get_raw_body()

    def _print_text_on_canvas(self):
        self.layout_info = self._canvas_layout_info()
        self._draw()

    def _draw(self):
        self.canvas.delete("all")
        page_coordinates = self.layout_info['page-coordinates']
        for x, y, c, f in page_coordinates:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=f, anchor='nw')

    def _canvas_layout_info(self):
        self.document = DocumentLayout(self.tokens)
        self.document.layout()
        return self.document.get_layout_info()


class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.children = []

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        child.layout()

        self.display_dict = {'page-coordinates': child.display_list,\
                'max-scroll': child.cursor_y - HEIGHT}

    def get_layout_info(self):
        return self.display_dict


class BlockLayout:
    def __init__(self, node, parent, previous) -> None:
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
    
    def layout(self):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.buffer_line = []

        if self.node:
            self._recurse(self.node)
        
        self._flush_buffer_line()

    def _process_text(self, token):
        font = get_font(self.size, self.weight, self.style)
        for word in token.text.split():
            w = font.measure(text=word)
            if self.cursor_x + w > WIDTH - HSTEP:
                self._flush_buffer_line()

            #self.display_list.append((self.cursor_x, self.cursor_y, word, font))
            self.buffer_line.append((self.cursor_x, word, font))
            self.cursor_x += w + font.measure(text=" ")

    def _recurse(self, tree):
        if isinstance(tree, Text):
            self._process_text(tree)
        else:
            print(tree.tag, tree.children)
            self._open_tag(tree.tag)
            for child in tree.children:
                self._recurse(child)
            self._close_tag(tree.tag)

    def _open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self._flush_buffer_line()
        elif tag == "p":
            self._flush_buffer_line()
            self.cursor_y += VSTEP  

    def _close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4        

    def _flush_buffer_line(self):
        if not self.buffer_line: return
        metrics = [font.metrics() for x, word, font in self.buffer_line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.buffer_line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        
        self.cursor_x = HSTEP
        self.buffer_line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent



if __name__ == "__main__":
    browser = Browser()
    tkinter.mainloop()




