from tkinter import Frame, Canvas, TOP
from components.tkVideoPlayerOptimized import VideoPlayer

# This modified version should have two sliders only, and each one cannot cross the other.
# The visual representation will be in time
class Slider(Frame):
    LINE_COLOR = "#476b6b"
    LINE_WIDTH = 8
    BAR_COLOR_OUTER = "#c2d6F6"
    BAR_COLOR_CIRCLE = "#22EE22"
    BAR_COLOR_INNER = "#FF0000"
    BAR_WIDTH_SIZE = 10
    BAR_HEIGHT_SIZE = 5
    DIGIT_PRECISION = '.1f' # for showing in the canvas

    # min and max val should be given in a float of seconds (seconds.ms)
    def __init__(self, master, width = 400, height = 100, min_val = 0, max_val = 1, show_value = True):
        Frame.__init__(self, master, height = height, width = width)
        self.master = master
        self.init_lis = [0, max_val, 0]
        self.max_val = max_val
        self.min_val = min_val
        self.show_value = show_value
        self.H = height
        self.W = width
        self.canv_H = self.H
        self.canv_W = self.W
        if not show_value:
            self.slider_y = self.canv_H/2 # y pos of the slider
        else:
            self.slider_y = self.canv_H*2/5
        self.slider_x = Slider.BAR_WIDTH_SIZE # x pos of the slider (left side)

        self.bars = []
        self.selected_idx = None # current selection bar index
        for value in self.init_lis:
            pos = (value-min_val)/(max_val-min_val)
            ids = []
            bar = {"Pos":pos, "Ids":ids, "Value":value}
            self.bars.append(bar)


        self.canv = Canvas(self, height = self.canv_H, width = self.canv_W)
        self.canv.pack(side=TOP)
        self.canv.bind("<Motion>", self._mouseMotion)
        self.canv.bind("<B1-Motion>", self._moveBar)
        self.canv.bind("<ButtonRelease-1>", self._releaseBar)

        self.__addTrack(self.slider_x, self.slider_y, self.canv_W-self.slider_x, self.slider_y)
        for i, bar in enumerate(self.bars):
            bar["Ids"] = self.__addBar(bar["Pos"], i)

    def convertPosToTimeStr(self, value):
        hours = "00"
        minutes = "00"
        if value > 60 * 60:
            hours = value // (60*60)
            value = value - (hours*60*60)
            hours = str(round(hours)).zfill(2)
        if value > 60:
            minutes = value // 60
            value = value - (minutes*60)
            minutes = str(round(minutes)).zfill(2)
        splitted = str(round(value, 3)).split('.')
        seconds = splitted[0]
        try:
            milli = splitted[1]
        except IndexError:
            milli = "0"
        str_time = f"{hours}:{minutes}:{seconds.zfill(2)}.{milli.ljust(3, '0')}"
        return str_time

    def getValues(self):
        values = [bar["Value"] for bar in self.bars]
        return sorted(values)

    def _mouseMotion(self, event):
        x = event.x; y = event.y
        selection = self.__checkSelection(x,y)
        if selection[0]:
            self.canv.config(cursor = "hand2")
            self.selected_idx = selection[1]
        else:
            self.canv.config(cursor = "")
            self.selected_idx = None

    def _releaseBar(self, event):
        if self.selected_idx in [0, 1, 2]:
            video : VideoPlayer = self.master.children["!videoplayer"]
            if len(video.imgMem) > 0:
                time_str = self.convertPosToTimeStr(self.bars[self.selected_idx]["Value"])
                video.set_offset(time_str)

    def _moveBar(self, event):
        # shit should pause whenever user touches it
        video : VideoPlayer = self.master.children["!videoplayer"]
        video._pause()

        x = event.x; y = event.y
        idx = self.selected_idx
        if idx == None:
            return False
        pos = self.__calcPos(x)
        if idx == 0 and pos > self.bars[1]["Pos"]:
            return False
        elif idx == 1 and pos < self.bars[0]["Pos"]:
            return False
        elif idx == 2 and (pos < self.bars[0]["Pos"] or pos > self.bars[1]["Pos"]):
            return False

        # move green bar along
        if idx == 0 and pos > self.bars[2]["Pos"]:
            self.__moveBar(2,pos)
        if idx == 1 and pos < self.bars[2]["Pos"]:
            self.__moveBar(2,pos)

        self.__moveBar(idx,pos)

    def __addTrack(self, startx, starty, endx, endy):
        id1 = self.canv.create_line(startx, starty, endx, endy, fill = Slider.LINE_COLOR, width = Slider.LINE_WIDTH)
        return id

    def fixTextPresentation(self, x):
        if x < 37:
            return 37
        if x > 762:
            return 762

        return x

    def __addBar(self, pos, idx=None):
        """@ pos: position of the bar, ranged from (0,1)"""
        if self.selected_idx is not None and idx is None:
            idx = self.selected_idx
        if pos < 0 or pos > 1:
            raise Exception("Pos error - Pos: "+str(pos))
        height = Slider.BAR_HEIGHT_SIZE
        width = Slider.BAR_WIDTH_SIZE
        L = self.canv_W - 2*self.slider_x
        if idx == 0:
            y = self.slider_y - 5
            y_value = y+Slider.BAR_WIDTH_SIZE-25
        elif idx == 1:
            y = self.slider_y + 5
            y_value = y+Slider.BAR_WIDTH_SIZE+5
        else:
            y = self.slider_y
            y_value = y+Slider.BAR_WIDTH_SIZE+10
        x = self.slider_x+pos*L
        if idx == 2:
            id_outer = self.canv.create_rectangle(x-4,y-height-8,x+4,y+height+8, fill = Slider.BAR_COLOR_CIRCLE, outline = "")
        else:
            id_outer = self.canv.create_rectangle(x-width,y-height,x+width,y+height, fill = Slider.BAR_COLOR_OUTER, outline = "")
            id_inner = self.canv.create_rectangle(x-1,y-height,x+1,y+height, fill = Slider.BAR_COLOR_INNER, outline = "")
        if self.show_value and idx != 2:
            value = pos*(self.max_val - self.min_val)+self.min_val
            x = self.fixTextPresentation(x)
            id_value = self.canv.create_text(x,y_value, text = self.convertPosToTimeStr(value))
            return [id_outer, id_inner, id_value]
        else:
            return [id_outer, -1, -1]

    def __moveBar(self, idx, pos, user=True):
        ids = self.bars[idx]["Ids"]
        for id in ids:
            self.canv.delete(id)
        self.bars[idx]["Ids"] = self.__addBar(pos, idx)
        self.bars[idx]["Pos"] = pos
        self.bars[idx]["Value"] = pos*(self.max_val - self.min_val)+self.min_val

    def __calcPos(self, x):
        """calculate position from x coordinate"""
        pos = (x - self.slider_x)/(self.canv_W-2*self.slider_x)
        if pos < 0:
            return 0
        elif pos > 1:
            return 1
        else:
            return pos

    def __checkSelection(self, x, y):
        """
        To check if the position is inside the bounding rectangle of a Bar
        Return [True, bar_index] or [False, None]
        """
        for idx in range(len(self.bars)):
            id = self.bars[idx]["Ids"][0]
            bbox = self.canv.bbox(id)
            if bbox[0] < x and bbox[2] > x and bbox[1] < y and bbox[3] > y:
                return [True, idx]
        return [False, None]

    def getLowestBarValue(self):
        return self.convertPosToTimeStr(self.bars[0]["Value"])

    def getHighestBarValue(self):
        return self.convertPosToTimeStr(self.bars[1]["Value"])

    def getPlayBarValue(self):
        return self.convertPosToTimeStr(self.bars[2]["Value"])

    def resetBars(self):
        self.__moveBar(0, 0, False)
        self.__moveBar(1, 1, False)
        self.__moveBar(2, 0, False)

    def setPlayBarValue(self, value):
        pos = value/(self.max_val - self.min_val)-self.min_val
        if pos <= self.bars[1]["Pos"]:
            self.__moveBar(2, pos, False)
        else:
            video : VideoPlayer = self.master.children["!videoplayer"]
            video._pause()

    def setLeftBarValue(self, value):
        pos = value/(self.max_val - self.min_val)-self.min_val
        if pos <= self.bars[1]["Pos"]:
            self.__moveBar(0, pos, False)
            return True
        return False

    def setRightBarValue(self, value):
        pos = value/(self.max_val - self.min_val)-self.min_val
        if pos >= self.bars[0]["Pos"] and pos <= 1:
            self.__moveBar(1, pos, False)
            return True
        return False