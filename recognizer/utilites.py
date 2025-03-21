import pygame, os, sys
pygame.mixer.init() 



def resource_path(relative_path):
    """ Get absolute path to resource, works for development and PyInstaller EXE """
    if getattr(sys, 'frozen', False):  # If running as compiled EXE
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def sound(path: str):
    try:
        sound = pygame.mixer.Sound(path)
        sound.play()
    except Exception as e:
        print(f"Error playing sound: {e}")


def camera():
    sound(resource_path('data/assets/camera_effect.mp3'))

def wrong():
    sound(resource_path('data/assets/wrong.mp3'))

def correct():
    sound(resource_path('data/assets/correct.mp3'))
