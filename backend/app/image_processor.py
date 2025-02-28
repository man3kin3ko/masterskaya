import os
from PIL import Image

class Processor:
    def __init__(
            self, 
            output_directory, 
            sizes=[(120,120), (720,720), (1600,1600)]
            ):
        self.output_directory = output_directory
        self.sizes = sizes

    def generate_thumbnails(self, orig_path):
        for i in self.sizes:
            image = Image.open(orig_path)
            image.thumbnail(i)

            print(os.getcwd())

            filename = os.path.split(orig_path)[1]
            ext =  os.path.splitext(orig_path)[1]
            dest = os.path.join(os.getcwd(), self.output_directory, f"{filename}_{i[0]}x{i[1]}.{ext}")
            print(dest)
            #image.save(dest)