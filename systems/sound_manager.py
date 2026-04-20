import pygame
import os

class SoundManager:
    """Manages audio playback and loading. Gracefully handles missing files."""
    
    def __init__(self, assets_dir):
        self.assets_dir = assets_dir
        self.audio_dir = os.path.join(assets_dir, "audio")
        self.sounds = {}
        
        # Ensure audio directory exists
        if not os.path.exists(self.audio_dir):
            try:
                os.makedirs(self.audio_dir)
            except Exception as e:
                print(f"Warning: Could not create audio directory: {e}")

        # Initialize mixer if not already initialized
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"Warning: Could not initialize pygame.mixer: {e}")

    def _get_path(self, filename):
        return os.path.join(self.audio_dir, filename)

    def load_sound(self, name, filename):
        """Loads a sound effect. Fails silently if file is missing."""
        if not pygame.mixer.get_init():
            return
            
        path = self._get_path(filename)
        if os.path.exists(path):
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Warning: Failed to load sound {filename}: {e}")
        else:
            print(f"Notice: Sound file {filename} not found at {path}. Playback will be silent.")

    def play_sound(self, name, volume=1.0):
        """Plays a loaded sound effect."""
        if name in self.sounds:
            self.sounds[name].set_volume(volume)
            self.sounds[name].play()

    def play_music(self, filename, volume=0.5, loops=-1):
        """Plays background music."""
        if not pygame.mixer.get_init():
            return
            
        path = self._get_path(filename)
        if os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(loops)
            except Exception as e:
                print(f"Warning: Failed to play music {filename}: {e}")
        else:
            print(f"Notice: Music file {filename} not found at {path}. Playback will be silent.")

    def stop_music(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

# Create a global instance, will be initialized later in main
sound_manager = None
