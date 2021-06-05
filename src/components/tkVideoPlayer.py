import ffmpeg
import pims
from os import access
from time import process_time, time, sleep
from numpy import arange as nparange
from cv2 import VideoCapture, CAP_PROP_FPS, CAP_PROP_FRAME_COUNT
from pygame.mixer import music
# from moviepy.editor import VideoFileClip
from PIL import Image, ImageTk
from tkinter import messagebox, filedialog, Frame, Toplevel, Button, Label, BOTTOM, TOP
from imageio import get_reader

class VideoPlayer(Frame):
    FRAME_CUTOFF = 9
    def __init__(self, root):
        Frame.__init__(self, root)

        frame = Frame(self).pack(side=BOTTOM)

        self.buttons = []

        self.buttons.append(Button(frame, text='Play', command=self._resume, state="disabled"))
        self.buttons.append(Button(frame, text='Pause', command=self._pause, state="disabled"))
        self.buttons.append(Button(frame, text='From beginning', command=self._restart, state="disabled"))
        self.buttons.append(Button(frame, text='Open...', command=self._open_video))
        self.buttons.append(Button(frame, text='Export...', command=self._export_video, state="disabled"))

        for button in self.buttons:
            button.pack(side=BOTTOM)

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

    def create_loading_message(self, message):
        loading = Toplevel(self)
        loading.geometry("+%d+%d" % (self.master.winfo_x(), self.master.winfo_y()))
        loading.transient()
        loading.title("Loading...")
        Label(loading, text=message).pack()
        self.update()
        return loading

    def video_frame_generator(self):
        t0 = time()
        print("Loading frames...")
        self.imageList = []

        self.imageList = pims.Video(self.original_filename)

        # i = 0
        # while(cap.isOpened()):
        #     ret, frame = cap.read()
        #     if ret == False: 
        #         break
        #     self.imageList.append(frame)
        #     i+=1

        # for i, image in enumerate(self.video.iter_data()):
        #     if i % VideoPlayer.FRAME_CUTOFF == 0:
        #         self.imageList.append(image)
        
        t1 = time()
        print(f"Frames loaded. Total: {len(self.imageList)}")
        print(f"Time taken: {t1 - t0}s")

            

    def _open_video(self):
        self.pause_video = True
        video = filedialog.askopenfile(mode = 'r', filetypes=[('MP4', '*.mp4'),('AVI', '*.avi')])
        if video is not None:
            loading = self.create_loading_message("Loading your video, please wait.")
            self.original_filename = video.name
            self.video = get_reader(self.original_filename)
            temp_video = VideoFileClip(self.original_filename)

            music.unload()
            temp_video.audio.write_audiofile("audio_output_preview.mp3")
            music.load("audio_output_preview.mp3")

            cap = VideoCapture(self.original_filename)
            self.fps = cap.get(CAP_PROP_FPS) / VideoPlayer.FRAME_CUTOFF
            frame_count = int(cap.get(CAP_PROP_FRAME_COUNT))
            self.seconds = (frame_count / self.fps)

            self.duration = self.seconds / VideoPlayer.FRAME_CUTOFF

            slider = self.master.children["!slider"]
            slider.max_val = self.duration
            slider.resetBars()
            slider.update()

            self.video_frame_generator()
            self.get_movie_frame = self.preview_video()

            self.frame_offset = 0
            self.seconds_offset = 0
            current_image = self.process_image(self.imageList[self.current_frame])
            self.my_label.config(image=current_image)
            self.update()

            for but in self.buttons:
                but["state"] = "normal"

            loading.destroy()
            self.update()

    def _export_video(self):
        self.pause_video = True
        music.pause()
        filename = filedialog.asksaveasfilename(filetypes=[("MP4", "*.mp4")], defaultextension=".mp4")
        if filename != "":
            loading = self.create_loading_message("Exporting your video, please wait.")
            print(f"Trying to export to {filename}")
            slider = self.master.children["!slider"]
            timer1 = slider.getLowestBarValue()
            timer2 = slider.getHighestBarValue()
            try:
                ffmpeg.input(self.original_filename).output(filename, ss=timer1, vcodec="libx264", crf=20, acodec="copy", to=timer2, avoid_negative_ts="make_zero").overwrite_output().run(capture_stderr=True)
                
                loading.destroy()
                messagebox.showinfo("Complete", "Video succesfully exported")
            except ffmpeg.Error as e:
                error_list = e.stderr.decode('utf-8').split("\n")
                error_list.pop()
                messagebox.showerror("Error", "Error exporting the video.\n" + error_list[-1] + "\nFor more information, check the console.")
                print(e.stderr.decode('utf-8'))
                
            
                

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

        try:
            access_frame = self.imageList[self.current_frame + self.frame_offset]
            current_image = self.process_image(access_frame)
            self.my_label.config(image=current_image)
            self.update()
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
                current_frame = next(self.get_movie_frame)
                current_second = (current_frame / VideoPlayer.FRAME_CUTOFF + self.frame_offset / VideoPlayer.FRAME_CUTOFF) * (1 / self.fps)
                self.update_play_slider(current_second)
                access_frame = self.imageList[current_frame + self.frame_offset]
                current_image = self.process_image(access_frame)
                self.my_label.config(image=current_image)
                self.my_label.update()
            except StopIteration:
                music.stop()
                self._pause()
            except IndexError:
                music.stop()
                current_frame -= 1
                self._pause()
        self.my_label.after(10, self.loop)

    def preview_video(self):
        t0 = time()
        for frame, t in enumerate(nparange(1.0 / self.fps, self.seconds - 0.001, 1.0 / self.fps)):
            t1 = time()
            sleep(max(0, t - (t1 - t0)))

            yield frame * VideoPlayer.FRAME_CUTOFF

