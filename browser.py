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
        if self.tokens == None: return

        if self.scroll < self.document.height - HEIGHT:
            self.scroll += SCROLL_STEP
        self._draw()

    def _scrollup(self, event):
        if self.tokens == None: return

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
        if self.tokens == None: return

        self._fill_canvas_layout()
        self._draw()

    def _draw(self):
        self.canvas.delete("all")
        for cmd in self.canvas_layout:
            if cmd.top > self.scroll + HEIGHT: continue
            if cmd.bottom < self.scroll: continue
            cmd.execute(self.scroll, self.canvas)

        # page_coordinates = self.layout_info['page-coordinates']
        # print(page_coordinates)
        # for x, y, c, f in page_coordinates:
        #     if y > self.scroll + HEIGHT: continue
        #     if y + VSTEP < self.scroll: continue
        #     self.canvas.create_text(x, y - self.scroll, text=c, font=f, anchor='nw')

    def _fill_canvas_layout(self):
        self.document = DocumentLayout(self.tokens)
        self.document.layout()
        self.canvas_layout = []
        self.document.paint(self.canvas_layout)
        


class DocumentLayout:
    """
    Represents the root layout object in the tree.
    Yes, there is another copy of this layout node in the layout tree.
    """
    def __init__(self, node):
        self.node = node # should be the "html" element
        self.parent = None
        self.children = [] # layout object children

    def layout(self):
        """
        Build a layout tree recursively (from html tree)
        """
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height + 2 * VSTEP

        #self.display_dict = {'page-coordinates': child.display_list}
    
    def paint(self, display_list):
        self.children[0].paint(display_list)

class BlockLayout:
    """
    Represents individual layout object in the tree. 
    """
    def __init__(self, node, parent, previous) -> None:
        self.node = node
        self.parent = parent
        self.previous = previous # previous layout object under the same parent (siblings)
        self.children = []

    def __repr__(self) -> str:
        return repr(self.node) + ": " \
            + "x: " + repr(self.x) + ", "\
            + "y: " + repr(self.y) + ", "\
            + "width: " + repr(self.width) + ", "\
            + "height: " + repr(self.height)
    
    def layout(self):
        previous = None
        for html_child in self.node.children:
            mode = layout_mode(html_child)
            if mode == "block":
                child = BlockLayout(html_child, self, previous)
            else:
                child = InlineLayout(html_child, self, previous)
            previous = child
            self.children.append(child)
        
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous is None:
            self.y = self.parent.y
        else:
            self.y = self.previous.y + self.previous.height

        for child in self.children:
            child.layout()

        self.height = sum([child.height for child in self.children])

        #print(self.node, self.children)

    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)

class InlineLayout:
    def __init__(self, node, parent, previous) -> None:
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def __repr__(self):
        return repr(self.node) + ": " \
            + "x: " + repr(self.x) + ", "\
            + "y: " + repr(self.y) + ", "\
            + "width: " + repr(self.width) + ", "\
            + "height: " + repr(self.height)

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous is None:
            self.y = self.parent.y
        else:
            self.y = self.previous.y + self.previous.height

        self.cursor_x = 0 # relative to self.x
        self.cursor_y = 0 # relative to self.y
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.display_list = []
        self.buffer_line = []
        self._recurse(self.node)  
        self._flush_buffer_line()
        self.height = self.cursor_y

    def paint(self, display_list):
        if isinstance(self.node, Element) and self.node == "pre":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, "gray")
            display_list.append(rect)

        for x, y, word, font in self.display_list:
            display_list.append(DrawText(x, y, word, font))


    def _process_text(self, token):
        """
        Process the text line by line. After recursively applying 
        """
        font = get_font(self.size, self.weight, self.style)
        for word in token.text.split():
            w = font.measure(text=word)
            if self.cursor_x + w > self.width:
                self._flush_buffer_line()

            #self.display_list.append((self.cursor_x, self.cursor_y, word, font))
            self.buffer_line.append((self.cursor_x, word, font))
            self.cursor_x += w + font.measure(text=" ")

    def _recurse(self, tree):
        if isinstance(tree, Text):
            self._process_text(tree)
        else:
            #print(tree.tag, tree.children)
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

        for rel_x, word, font in self.buffer_line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        
        self.cursor_x = 0
        self.buffer_line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]

def layout_mode(node):
    if isinstance(node, Text):
        return "inline"
    elif node.children:
        if any([isinstance(child, Element) and \
                child.tag in BLOCK_ELEMENTS
                for child in node.children]):
            return "block"
        else:
            return "inline"
    else:
        return "block"
        
def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)

class DrawText:
    def __init__(self, x1, y1, text, font) -> None:
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.bottom = y1 + font.metrics("linespace")

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left, self.top - scroll,
            text=self.text,
            font=self.font,
            anchor='nw',
        )

class DrawRect:
    def __init__(self, x1, y1, x2, y2, color) -> None:
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color
    
    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left, self.top - scroll,
            self.right, self.bottom - scroll,
            width=0,
            fill=self.color,
        )

if __name__ == "__main__":
    browser = Browser()
    tkinter.mainloop()




