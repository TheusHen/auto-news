import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import feedparser
import threading
import time
import sys
import re
import json
import os
from html import unescape

RSS_FEEDS = [
    "https://g1.globo.com/dynamo/rss2.xml",
    "https://g1.globo.com/brasil/rss2.xml",
    "https://g1.globo.com/mundo/rss2.xml",
    "https://g1.globo.com/economia/rss2.xml",
    "https://forbes.com.br/feed/",
    "https://www.forbes.com/most-popular/feed/",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "http://feeds.reuters.com/reuters/topNews",
    "http://feeds.feedburner.com/TechCrunch/",
    "https://feeds.ign.com/ign/all"
]

CONFIG_FILE = os.path.expanduser("~/.news_overlay_config.json")
IMG_RE = re.compile(r'<img\s+[^>]*src="([^"]+)"', re.IGNORECASE)

def clean_html(text):
    text = unescape(text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def fetch_news():
    news = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                summary = entry.summary if 'summary' in entry else entry.get('description', "")
                summary = clean_html(summary)
                news.append({
                    "title": clean_html(entry.title),
                    "summary": summary,
                    "link": entry.link if 'link' in entry else "",
                    "source": feed.feed.title if 'title' in feed.feed else url,
                })
        except Exception:
            continue
    news.sort(key=lambda x: x.get("title", ""))
    return news

class NewsOverlay(tk.Tk):
    def __init__(self, news):
        super().__init__()
        self.news = news
        self.current = 0
        self.title('')
        self.overrideredirect(True)
        self.attributes('-alpha', 0.97)
        self.configure(bg="#232323")
        self.withdraw()

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        width = max(380, min(690, int(sw * 0.36)))
        height = max(380, min(690, int(sh * 0.35)))

        pos = self.load_position(sw, sh, width, height)
        self.geometry(f"{width}x{height}+{pos['x']}+{pos['y']}")
        self._size = (width, height)
        self._screen = (sw, sh)

        try:
            self.attributes("-topmost", False)
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            ctypes.windll.user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001)
        except Exception:
            pass

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.lbl_title = tk.Label(
            self, text='', font=("Segoe UI", 21, "bold"),
            fg="#fff", bg="#232323", anchor='w', wraplength=width-35, justify="left"
        )
        self.lbl_title.grid(sticky="ew", padx=18, pady=(15,0), row=0, column=0)

        self.lbl_source = tk.Label(
            self, text='', font=("Segoe UI", 11),
            fg="#bbbbbb", bg="#232323", anchor='w'
        )
        self.lbl_source.grid(sticky="ew", padx=18, pady=(0,5), row=1, column=0)

        self.text = ScrolledText(
            self, font=("Segoe UI", 13), wrap="word", fg="#ececec", bg="#232323",
            insertbackground="#fff", relief="flat", height=7, bd=0
        )
        self.text.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0,7))
        self.text.configure(state="disabled")

        self.lbl_link = tk.Label(
            self, text='', font=("Segoe UI", 10, "underline"),
            fg="#40a9ff", bg="#232323", cursor="hand2"
        )
        self.lbl_link.grid(sticky="ew", padx=18, pady=(0,7), row=3, column=0)
        self.lbl_link.bind("<Button-1>", self.open_link)

        self.arrow = tk.Label(
            self, text='↓', font=("Segoe UI", 36), fg="#666", bg="#232323", cursor="hand2"
        )
        self.arrow.grid(row=4, column=0, pady=(0,0))
        self.arrow.bind("<Button-1>", self.next_news)

        self.bind("<Down>", self.next_news)
        self.bind("<MouseWheel>", self.scroll_text)
        self.text.bind("<MouseWheel>", self.scroll_text)
        self.bind("<Button-4>", self.scroll_text)
        self.bind("<Button-5>", self.scroll_text)
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<Escape>", lambda e: self.on_exit())
        self.arrow.bind("<ButtonPress-1>", self.start_move)
        self.arrow.bind("<B1-Motion>", self.do_move)
        self.arrow.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<Configure>", self.on_resize)

        self._drag_data = None
        self.after(500, self.deiconify)

        self.animating = False
        self.show_news(0)
        self.focus_force()

    def show_news(self, idx):
        if idx < 0 or idx >= len(self.news): return
        self.current = idx
        item = self.news[idx]
        self.lbl_title.config(text=item['title'])
        self.lbl_source.config(text=f"{item.get('source','')}")
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", item['summary'])
        self.text.config(state="disabled")
        self.lbl_link.config(text=item['link'])
        self.lbl_link.bind("<Button-1>", self.open_link)
        self.start_fade()

    def start_fade(self):
        if self.animating: return
        self.animating = True
        for i in range(7, 14):
            self.after(i*14, lambda a=i: self.attributes("-alpha", a/14))
        self.after(210, lambda: setattr(self, 'animating', False))

    def next_news(self, event=None):
        next_idx = (self.current + 1) % len(self.news)
        self.show_news(next_idx)

    def scroll_text(self, event):
        if event.delta:
            self.text.yview_scroll(int(-1*(event.delta/120)), "units")
        elif event.num == 4:
            self.text.yview_scroll(-3, "units")
        elif event.num == 5:
            self.text.yview_scroll(3, "units")
        return "break"

    def open_link(self, event):
        import webbrowser
        webbrowser.open(self.news[self.current]['link'])

    def start_move(self, event):
        self._drag_data = (event.x_root, event.y_root, self.winfo_x(), self.winfo_y())

    def do_move(self, event):
        if self._drag_data:
            dx = event.x_root - self._drag_data[0]
            dy = event.y_root - self._drag_data[1]
            nx = self._drag_data[2] + dx
            ny = self._drag_data[3] + dy
            nx = max(0, min(self._screen[0] - self._size[0], nx))
            ny = max(0, min(self._screen[1] - self._size[1], ny))
            self.geometry(f"+{nx}+{ny}")

    def stop_move(self, event):
        self._drag_data = None
        self.save_position()

    def on_resize(self, event):
        if (event.width, event.height) != self._size:
            self._size = (event.width, event.height)
            self._screen = (self.winfo_screenwidth(), self.winfo_screenheight())
            self.lbl_title.config(wraplength=event.width-35)
            self.save_position()

    def save_position(self):
        try:
            pos = {'x': self.winfo_x(), 'y': self.winfo_y(), 'width': self._size[0], 'height': self._size[1]}
            with open(CONFIG_FILE, 'w') as f:
                json.dump(pos, f)
        except Exception:
            pass

    def load_position(self, sw, sh, width, height):
        try:
            with open(CONFIG_FILE, 'r') as f:
                pos = json.load(f)
            x = min(max(pos.get('x', sw-width-30), 0), sw-width)
            y = min(max(pos.get('y', sh-height-60), 0), sh-height)
            return {'x': x, 'y': y}
        except Exception:
            return {'x': sw-width-30, 'y': sh-height-60}

    def on_exit(self):
        self.save_position()
        self.destroy()

def main():
    news_result = []
    def fetch_and_start():
        nonlocal news_result
        news_result = fetch_news()
        if not news_result:
            print("No news found.")
            sys.exit(1)
        app = NewsOverlay(news_result)
        app.mainloop()
    threading.Thread(target=fetch_and_start).start()

if __name__ == "__main__":
    main()