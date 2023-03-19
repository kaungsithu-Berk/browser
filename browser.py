from transfer.transferutil import *
from response.response import *
from util import *
import tkinter, tkinter.font

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 20
FONTS_CACHE = {}

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
        self.canvas_width = WIDTH
        self.canvas_height = HEIGHT

        self.scroll = 0
        self.tokens = []

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
        self.canvas_width, self.canvas_height = event.width, event.height
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
            self.tokens = response.get_tags_and_texts()
        else:
            self.tokens = response.get_raw_body()

    def _print_text_on_canvas(self):
        self.layout_info = self._canvas_layout_info()
        self._draw()

    def _draw(self):
        self.canvas.delete("all")
        page_coordinates = self.layout_info['page-coordinates']
        for x, y, c, f in page_coordinates:
            if y > self.scroll + self.canvas_height: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=f, anchor='nw')

    def _canvas_layout_info(self):
        return Layout(self.tokens, self.canvas_width, self.canvas_height).get_layout_info()

        
        # for word in text.split():
        #     w = self.bi_times.measure(text=word)
        #     if cursor_x + w > self.canvas_width - HSTEP:
        #         cursor_y += self.bi_times.metrics("linespace") * 1.25
        #         cursor_x = HSTEP
        #     display_list.append((cursor_x, cursor_y, word))
        #     cursor_x += w + self.bi_times.measure(text=" ")
        # print("ended layout calculation")
    
        # return {'page-coordinates': display_list,\
        #         'max-scroll': cursor_y - self.canvas_height}

class Layout:
    def __init__(self, tokens, canvas_width, canvas_height) -> None:
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.buffer_line = []

        print("Processing Started")
        for token in tokens:
            self._process_token(token)
        
        self._flush_buffer_line()
        print("Processing Ended")

    def get_layout_info(self):
        return {'page-coordinates': self.display_list,\
                'max-scroll': self.cursor_y - self.canvas_height}

    def _process_token(self, token):

        if isinstance(token, Text):
            self._process_text(token)
        elif token.tag == "i":
            self.style = "italic"
        elif token.tag == "/i":
            self.style = "roman"
        elif token.tag == "b":
            self.weight = "bold"
        elif token.tag == "/b":
            self.weight = "normal"
        elif token.tag == "small":
            self.size -= 2
        elif token.tag == "/small":
            self.size += 2
        elif token.tag == "big":
            self.size += 4
        elif token.tag == "/big":
            self.size -= 4
        elif token.tag == "br":
            self._flush_buffer_line()
        elif token.tag == "p":
            self._flush_buffer_line()
            self.cursor_y += VSTEP


    def _process_text(self, token):
        font = get_font(self.size, self.weight, self.style)
        for word in token.text.split():
            w = font.measure(text=word)
            if self.cursor_x + w > self.canvas_width - HSTEP:
                self._flush_buffer_line()

            #self.display_list.append((self.cursor_x, self.cursor_y, word, font))
            self.buffer_line.append((self.cursor_x, word, font))
            self.cursor_x += w + font.measure(text=" ")
            

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


def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS_CACHE:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS_CACHE[key] = font
    return FONTS_CACHE[key]



if __name__ == "__main__":
    browser = Browser()
    tkinter.mainloop()

    # while(True):
    #     url = input("Enter url: ")
    #     if url == "exit":
    #         break
        
    #     print(get(url).get_raw_body())




