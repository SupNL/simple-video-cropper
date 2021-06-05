from tkinter import Tk
from components.tkSliderWidget import Slider
from components.tkVideoPlayerOptimized import VideoPlayer

root = Tk()
video = VideoPlayer(root)

slider = Slider(root, width = 800, height = 100, min_val = 0, max_val = video.duration, show_value = True)
slider.pack()
root.title("Video cropper")

root.mainloop()

# print(slider.getValues())