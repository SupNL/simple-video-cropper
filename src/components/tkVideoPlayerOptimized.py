import ffmpeg
import pims
from pathlib import Path
from time import time, sleep
from numpy import arange as nparange
from cv2 import VideoCapture, CAP_PROP_FPS, CAP_PROP_FRAME_COUNT, CAP_PROP_FRAME_HEIGHT, CAP_PROP_FRAME_WIDTH
from pygame.mixer import music, init as init_mixer
import pygame.mixer
from tkinter import messagebox, filedialog, Frame, Spinbox, StringVar, Toplevel, Button, Label, BOTTOM, TOP, LEFT, RIGHT
from imageio import get_reader
from PIL import Image, ImageTk

AUDIO_PREVIEW_FILENAME = "audio_output_preview.mp3"
VIDEO_PREVIEW_FILENAME = "video_output_preview.mp4"

FILE_TYPES = [
    ('MP4', '*.mp4'),
    ('AVI', '*.avi'),
    ('MKV', '*.mkv'),
    ('MOV', '*.mov'),
    ('WVM', '*.wmv'),
]

class VideoPlayer(Frame):
    FRAME_CUTOFF = 3
    def __init__(self, root):
        pygame.mixer.pre_init(44100, -16, 1, 1024)
        pygame.mixer.init()
        Frame.__init__(self, root)

        bottomFrame = Frame(root)
        range_validation = bottomFrame.register(self.validate)
        bottomFrame.pack(side=BOTTOM)
        frame = Frame(root)
        frame.pack(side=BOTTOM)

        topFrame = Frame(root)
        topFrame.pack(side=BOTTOM)
    
        leftButtonContainer = Frame(topFrame)
        rightButtonContainer = Frame(topFrame)
        leftButtonContainer.pack(side=LEFT)
        rightButtonContainer.pack(side=RIGHT)

        self.buttons = []

        self.buttons.append(Button(frame, text='Play', height=2, bg='#cfdbaf', command=self._resume, state="disabled"))
        self.buttons.append(Button(frame, text='Pause', height=2, bg='#cfdbaf',  command=self._pause, state="disabled"))
        self.buttons.append(Button(frame, text='From beginning', height=2, bg='#cfdbaf',  command=self._restart, state="disabled"))
        self.buttons.append(Button(frame, text='Open...', height=2, bg='#cfdbaf',  command=self._open_video))
        self.buttons.append(Button(frame, text='Export...', height=2, bg='#cfdbaf',  command=self._export_video, state="disabled"))

        self.buttons.append(Button(leftButtonContainer, text='Back Frame', height=1, bg='#cfdbaf',  command=self.retract_left_bar, state="disabled"))
        self.buttons.append(Button(leftButtonContainer, text='Adv. Frame', height=1, bg='#cfdbaf',  command=self.advance_left_bar, state="disabled"))
        
        self.buttons.append(Button(rightButtonContainer, text='Back Frame', height=1, bg='#cfdbaf',  command=self.retract_right_bar, state="disabled"))
        self.buttons.append(Button(rightButtonContainer, text='Adv. Frame', height=1, bg='#cfdbaf',  command=self.advance_right_bar, state="disabled"))
        
        Label(leftButtonContainer, text="Left cut").pack(side=TOP)
        Label(rightButtonContainer, text="Right cut").pack(side=TOP)

        for i, button in enumerate(self.buttons):
            if i == 3:
                Frame(frame, width=150, height=80).pack(side=LEFT)
            if i == 7:
                Frame(topFrame, width=200, height=50).pack(side=LEFT)
            Frame(frame, width=20).pack(side=LEFT)
            button.pack(side=LEFT)
        
        Label(bottomFrame, text="Compression (CRF) value, higher values = higher compression (worse quality)\nRecommended quality = 16 to 20 (minimum value is 0, maximum value is 51)\nThis is only used when exporting the video").pack(side=TOP)
        Label(bottomFrame, height=1).pack(side=BOTTOM)
        self.crf_value = StringVar(root, 20)
        self.spinbox = Spinbox(bottomFrame, from_ = 0, to = 52, textvariable=self.crf_value)
        self.spinbox.pack(side=BOTTOM)
        self.spinbox.config(validate="key", validatecommand=(range_validation, '%P'))
        self.spinbox.bind("<KeyRelease>", self.verify_padding_zero)
       
        self.frame_offset = 0
        self.seconds_offset = 0
        self.duration = 1

        self.my_label = Label(root)
        self.my_label.pack(side=TOP)

        self.pause_video = True
        self.restart = False
        self.current_frame = 0

        self.imgMem = []

        self.my_label.after(200, self.loop)

    def retract_right_bar(self):
        slider = self.master.children["!slider"]
        self._pause()

        seconds = self.convert_to_seconds(slider.getHighestBarValue())
        offset = round(self.fps * seconds * VideoPlayer.FRAME_CUTOFF) - 1
        if offset < 0:
            return
        
        current_second = offset / VideoPlayer.FRAME_CUTOFF * (1 / self.fps)
        
        if slider.setRightBarValue(current_second):
            slider.setPlayBarValue(current_second)
            self.frame_offset = offset
            self.seconds_offset = seconds
            try:
                self.apply_frame(self.frame_offset)
            except:
                pass
            self.update()

    def advance_right_bar(self):
        slider = self.master.children["!slider"]
        self._pause()

        seconds = self.convert_to_seconds(slider.getHighestBarValue())
        offset = round(self.fps * seconds * VideoPlayer.FRAME_CUTOFF) + 1
        
        current_second = offset / VideoPlayer.FRAME_CUTOFF * (1 / self.fps)
        
        if slider.setRightBarValue(current_second):
            slider.setPlayBarValue(current_second)
            self.frame_offset = offset
            self.seconds_offset = seconds
            try:
                self.apply_frame(self.frame_offset)
            except:
                pass
            self.update()

    def retract_left_bar(self):
        slider = self.master.children["!slider"]
        self._pause()

        seconds = self.convert_to_seconds(slider.getLowestBarValue())
        offset = round(self.fps * seconds * VideoPlayer.FRAME_CUTOFF) - 1
        if offset < 0:
            return
        
        current_second = offset / VideoPlayer.FRAME_CUTOFF * (1 / self.fps)
        
        if slider.setLeftBarValue(current_second):
            slider.setPlayBarValue(current_second)
            self.frame_offset = offset
            self.seconds_offset = seconds
            try:
                self.apply_frame(self.frame_offset)
            except:
                pass
            self.update()

    def advance_left_bar(self):
        slider = self.master.children["!slider"]
        self._pause()

        seconds = self.convert_to_seconds(slider.getLowestBarValue())
        offset = round(self.fps * seconds * VideoPlayer.FRAME_CUTOFF) + 1
        
        current_second = offset / VideoPlayer.FRAME_CUTOFF * (1 / self.fps)
        
        if slider.setLeftBarValue(current_second):
            slider.setPlayBarValue(current_second)
            self.frame_offset = offset
            self.seconds_offset = seconds
            try:
                self.apply_frame(self.frame_offset)
            except:
                pass
            self.update()
        

    def verify_padding_zero(self, event):
        value = self.crf_value.get()
        if len(value) == 0:
            self.crf_value.set("0")
        elif len(value) > 1 and value[0] == "0":
            value = value.replace('0', '')
            self.crf_value.set(value)

    def validate(self, user_input):
        if user_input.isdigit():
            minval = int(self.spinbox.config('from')[4])
            maxval = int(self.spinbox.config('to')[4])

            if int(user_input) not in range(minval, maxval):
                return False

            return True
        elif len(user_input) == 0:
            return True
        return False
        
    def create_loading_message(self, message):
        loading = Toplevel(self)
        loading.geometry("+%d+%d" % (self.master.winfo_x(), self.master.winfo_y()))
        loading.transient()
        loading.title("Loading...")
        Label(loading, text=message).pack()
        self.update()
        return loading

    def apply_frame(self, frame_index):
        self.my_label.config(image=self.process_image(self.imageList[frame_index]))
        self.my_label.update()

    def video_frame_generator(self):
        t0 = time()
        print("Loading frames...")
        self.imageList = []

        self.imageList = pims.Video(VIDEO_PREVIEW_FILENAME)
        
        t1 = time()
        print(f"Frames loaded. Total: {len(self.imageList)}")
        print(f"Time taken: {t1 - t0}s")

    def _open_video(self):
        self.pause_video = True
        music.pause()
        video = filedialog.askopenfile(mode = 'r', filetypes=FILE_TYPES)
        if video is not None:
            music.unload()
            loading = self.create_loading_message("Loading your video, please wait.")
            self.original_filename = video.name
            self.video = get_reader(self.original_filename)

            t0 = time()
            print("Generating audio preview")
            try:
                ffmpeg.input(self.original_filename).output(AUDIO_PREVIEW_FILENAME, ar=44100).overwrite_output().run(capture_stderr=True)
                print(f"Audio preview generation successful.\nTime taken: {time()-t0}s.")

                self.cap = VideoCapture(self.original_filename)
                height = self.cap.get(CAP_PROP_FRAME_HEIGHT)
                width = self.cap.get(CAP_PROP_FRAME_WIDTH)
                self.cap.release()

                if height > 480:
                    aspect_ratio = width / height
                    width = 480 * aspect_ratio
                    if width % 2 != 0:
                        width += 1
                    height = 480

                t0 = time()
                print("Compressing preview video")
                ffmpeg.input(self.original_filename).filter('scale', width, height).output(VIDEO_PREVIEW_FILENAME,vcodec="libx264", crf=30, preset="ultrafast").overwrite_output().run(capture_stderr=True)
                print(f"Compression successful.\nTime taken: {time()-t0}s.")
            except ffmpeg.Error as e:
                error_list = e.stderr.decode('utf-8').split("\n")
                error_list.pop()
                print(e.stderr.decode('utf-8'))
                messagebox.showerror("Error", "Error loading the video.\n" + error_list[-1] + "\nCheck console for more information.")
                loading.destroy()
                return
            except FileNotFoundError as e:
                print(e.message)
                messagebox.showerror("Error", "File not found.\nMost likely you do not have FFMPEG downloaded.\nCheck console for more information.")
                loading.destroy()
                return
            except Exception as e:
                print(e.message)
                messagebox.showerror("Error", "Unknown error.\nCheck console for more information.")
                loading.destroy()
                return

            self.cap = VideoCapture(VIDEO_PREVIEW_FILENAME)
            self.fps = self.cap.get(CAP_PROP_FPS) / VideoPlayer.FRAME_CUTOFF
            frame_count = int(self.cap.get(CAP_PROP_FRAME_COUNT))
            self.seconds = (frame_count / self.fps)
            self.cap.release()
            
            music.unload()
            music.load(AUDIO_PREVIEW_FILENAME)

            self.duration = self.seconds / VideoPlayer.FRAME_CUTOFF

            slider = self.master.children["!slider"]
            slider.max_val = self.duration
            slider.resetBars()
            slider.update()

            self.video_frame_generator()
            self.get_movie_frame = self.preview_video()

            self.frame_offset = 0
            self.seconds_offset = 0
            self.apply_frame(self.current_frame)

            for but in self.buttons:
                but["state"] = "normal"

            loading.destroy()
            self.update()

    def _export_video(self):
        self.pause_video = True
        music.pause()
        filename = filedialog.asksaveasfilename(filetypes=FILE_TYPES, defaultextension=Path(self.original_filename).suffix)
        if filename != "":
            loading = self.create_loading_message("Exporting your video, please wait.")
            print(f"Trying to export to {filename}")
            print(f"Compressing with CRF value of {self.crf_value.get()}")
            slider = self.master.children["!slider"]
            timer1 = slider.getLowestBarValue()
            timer2 = slider.getHighestBarValue()
            try:
                ffmpeg.input(self.original_filename).output(filename, ss=timer1, vcodec="libx264", crf=int(self.crf_value.get()), preset="superfast", acodec="copy", to=timer2, avoid_negative_ts="make_zero").overwrite_output().run(capture_stderr=True)
                
                loading.destroy()
                messagebox.showinfo("Complete", "Video succesfully exported")
            except ffmpeg.Error as e:
                error_list = e.stderr.decode('utf-8').split("\n")
                error_list.pop()
                messagebox.showerror("Error", "Error exporting the video.\n" + error_list[-1] + "\nCheck console for more information.")
                print(e.stderr.decode('utf-8'))
            except FileNotFoundError as e:
                print(e.message)
                messagebox.showerror("Error", "File not found.\nMost likely you do not have FFMPEG downloaded.\nCheck console for more information.")
                return
            except Exception as e:
                print(e.message)
                messagebox.showerror("Error", "Unknown error.\nCheck console for more information.")
                return
            

    def convert_to_seconds(self, time_str):
        values = time_str.split(':')
        seconds = 0.0
        seconds += float(values[0]) * 60 * 60
        seconds += float(values[1]) * 60
        seconds += float(values[2])
        return seconds


    def set_offset(self, time_str : str):
        self.pause_video = True
        music.pause()
        
        seconds = self.convert_to_seconds(time_str)

        self.seconds_offset = seconds
        self.frame_offset = round(self.fps * seconds * VideoPlayer.FRAME_CUTOFF)
        self.current_frame = 0

        try:
            self.apply_frame(self.current_frame + self.frame_offset)
        except IndexError:
            pass

    def update_play_slider(self, seconds):
        slider = self.master.children["!slider"]
        slider.setPlayBarValue(seconds)

    def _restart(self):
        slider = self.master.children["!slider"]
        slider.setPlayBarValue(self.convert_to_seconds(slider.getLowestBarValue()))
        self.set_offset(slider.getLowestBarValue())
        self.restart = True
        self.pause_video = False
        music.rewind()
        music.play(start=self.seconds_offset)


    def _pause(self):
        if not self.pause_video:
            self.pause_video = True
            music.pause()
            slider = self.master.children["!slider"]
            self.set_offset(slider.getPlayBarValue())

    
    def _resume(self):
        if self.pause_video:
            # should start from the green play
            self.restart = True
            self.pause_video = False
            music.rewind()
            music.play(start=self.seconds_offset)

    def process_image(self, image):
        image = Image.fromarray(image)
        image.thumbnail((800, 800), Image.ANTIALIAS)
        image = ImageTk.PhotoImage(image)
        self.imgMem.append(image)
        if len(self.imgMem) > 1:
            self.imgMem.pop(0)
        return image

    def loop(self):
        if self.restart:
            self.get_movie_frame = self.preview_video()
            self.restart = False
        if not self.pause_video:
            try:
                self.current_frame = next(self.get_movie_frame)
                current_second = (self.current_frame + self.frame_offset) / VideoPlayer.FRAME_CUTOFF * (1 / self.fps)
                self.update_play_slider(current_second)
                self.apply_frame(self.current_frame + self.frame_offset)
            except StopIteration:
                music.stop()
                self._pause()
            except IndexError:
                music.stop()
                self.current_frame -= 1
                self._pause()
        self.my_label.after(10, self.loop)

    def preview_video(self):
        t0 = time()
        for frame, t in enumerate(nparange(1.0 / self.fps, self.seconds - 0.001, 1.0 / self.fps)):
            t1 = time()
            sleep(max(0, t - (t1 - t0)))

            yield frame * VideoPlayer.FRAME_CUTOFF

