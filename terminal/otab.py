import os
import curses
import json
import math

class Song:
    def __init__(self, file):
        self.file = file
        self.text = file.read()
        self.format = "text"
        if self.text.startswith("otab-json"):
            self.format = "json"
            self.text = self.text[9:-1]
            self.obj = json.loads(self.text)

def main(scr):
    curses.curs_set(False)
    curses.noecho()
    curses.start_color()
    curses.use_default_colors()
    curses.typeahead(-1)

    state = "list"
    list_scroll = 0
    list_selected = 0
    list_width = 64
    tab_scroll = -1
    hasrunonce = False
    refresh = True

    while True:
        if not hasrunonce or refresh:
            songs = os.listdir("tabs")
            song = loadSong(songs[list_selected])
            refresh = False
        currentx = 0
        listWin = None
        if curses.COLS > list_width or state == "list":
            currentx = min(list_width, curses.COLS)
            listWin = draw_list(scr, curses.LINES - 2, currentx, 1, 2, songs, list_scroll, list_selected, state == "list")

            splitter = curses.newwin(curses.LINES, 5, 0, currentx)
            splitter.vline(0, 2, "|", curses.LINES)
            splitter.refresh()
            currentx += 5


        tabWin = draw_tab(scr, curses.LINES, curses.COLS - currentx, 0, currentx, song, tab_scroll, state == "tab")
        scr.refresh()

        if hasrunonce:
            key = scr.getkey()
            if key == "q":
                break
            if key == "+":
                list_width = max(1, list_width + 1)
            if key == "-":
                list_width = max(1, list_width - 1)
            if state == "list":
                list_scroll, list_selected, state, refresh = key_list(key, list_scroll, list_selected, list_width, curses.LINES, state, len(songs))
            elif state == "tab":
                tab_scroll, state = key_tab(key, tab_scroll, state)
        hasrunonce = True

def key_tab(key, scroll, state):
    if key == "KEY_LEFT":
        state = "list"
        scroll = -1
    if key == "KEY_UP":
        scroll -= 1
    if key == "KEY_DOWN":
        scroll += 1
    return scroll, state

def draw_tab(scr, height, width, begin_y, begin_x, song, scroll, active):
    if width > 8:
        win = curses.newwin(height, width, begin_y, begin_x)

        if song.format == "text":
            strings = song.text.split("\n")
            for s in range(0, height):
                if -1 < s + scroll < len(strings):
                    win.addstr(s, 0, strings[s + scroll])

        if song.format == "json":
            line = 0

            line = printifinside(win, song.obj["title"], scroll, line, height, False)
            line = printifinside(win, song.obj["artist"] + " - " + song.obj["album"], scroll, line, height, True)
            line = printifinside(win, "Type: " + song.obj["type"] + " - Tabber: " + song.obj["tabber"], scroll, line, height, True) + 3

            for s in song.obj["sectionOrder"]:
                section = song.obj["sections"][s]
                if section["type"] == "lyrics":
                    for l in section["lyrics"]:
                        if isinsidescreen(scroll, line, height):
                            for c in l["c"]:
                                if c[1] < width:
                                    win.addstr(line - scroll, c[1], c[0])
                        line += 1
                        if isinsidescreen(scroll, line, height):
                            win.addstr(line - scroll, 0, l["l"], curses.A_DIM)
                        line += 2
                line += 2
                if section["type"] == "chords":
                    if isinsidescreen(scroll, line, height):
                        win.addstr(line - scroll, 0, section["prefix"], curses.A_DIM)
                        for c in section["chords"]:
                            win.addstr(" " + c + " ")
                        win.addstr(section["suffix"], curses.A_DIM)
                    line += 5



                if section["type"] == "tab":
                    col = 0
                    for tso in section["sectionOrder"]:
                        for f in range(0, section["barsize"]):
                            if col == 0:
                                printfinger(win, line, 0, section["tuning"], scroll, height)
                                printfinger(win, line, 1, ["||"] * len(section["tuning"]), scroll, height)
                                col = 3
                            exists = None
                            for t in section["sections"][tso]:
                                if exists == None and t[0] == f:
                                    exists = t
                                    pass
                            if exists:
                                printfinger(win, line, col, exists[1 : section["barsize"] + 1], scroll, height)
                            else:
                                printfinger(win, line, col, ["-"] * len(section["tuning"]), scroll, height)
                            col += 1
                        printfinger(win, line, col, ["|"] * len(section["tuning"]), scroll, height)
                        col += 1
                        if col + section["barsize"] + 1 > width - 4:
                            line += 5
                            col = 0
                            pass
                    line += 5


                if section["type"] == "text":
                    for text in section["text"]:
                        line = printifinside(win, text, scroll, line, height, True)
                    line += 5
        win.refresh()
        return win
    return None

def printfinger(win, line, x, a, scroll, height):
    add_y = 0
    for s in a:
        if isinsidescreen(scroll, line + add_y, height):
            if s != "-":
                win.addstr(line - scroll + add_y, x, s)
            else:
                win.addstr(line - scroll + add_y, x, s, curses.A_DIM)
        add_y += 1
    pass

def printifinside(win, text, scroll, line, height, dimmed):
    if isinsidescreen(scroll, line, height):
        if dimmed:
            win.addstr(line - scroll, 0, text, curses.A_DIM)
        else:
            win.addstr(line - scroll, 0, text)

    return line + 1

def isinsidescreen(scroll, line, height):
    return scroll <= line < scroll + height

def key_list(key, list_scroll, list_selected, width, height, state, songslen):
    refresh = False
    if key == "KEY_RIGHT":
        state = "tab"
    if key == "KEY_UP":
        list_selected -= 1
        if list_selected == -1:
            list_selected = songslen - 1
            if curses.LINES < songslen:
                list_scroll = songslen - curses.LINES
        if list_selected == list_scroll - 1:
            list_scroll -= 1
        lyrics_scroll = 0
        refresh = True
    if key == "KEY_DOWN":
        list_selected += 1
        if list_selected == songslen:
            list_selected = 0
            list_scroll = 0
        if list_selected == list_scroll + curses.LINES:
            list_scroll += 1
        refresh = True

    return list_scroll, list_selected, state, refresh

def draw_list(scr, height, width, begin_y, begin_x, songs, scroll, selected, active):
    win = curses.newwin(height, width, begin_y, begin_x)

    for l in range(0, min(height, len(songs))):
        songIndex = l + scroll
        songName = songs[songIndex][0:-5].replace("_", " ") + width * " "
        if not active:
            win.addnstr(l, 0, songName, width - 1, curses.A_DIM)
        else:
            if songIndex == selected:
                win.addnstr(l, 0, songName, width - 1, curses.A_REVERSE)
            else:
                win.addnstr(l, 0, songName, width - 1)

    win.refresh()
    return win

def loadSong(filename):
    song = Song(open("tabs/" + filename, "r"))

    return song

if len(os.listdir("tabs")) == 0:
    print("No tabs found in directory")

curses.wrapper(main)
