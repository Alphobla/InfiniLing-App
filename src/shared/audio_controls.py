"""
Shared audio controls component for both transcriber and gentexter modules
"""
from tkinter import Frame, Button, Label, DoubleVar
from tkinter import ttk
import os
from .styles import Colors, Fonts, Spacing

class AudioControls:
    """Professional audio controls with VLC support"""
    
    def __init__(self, parent_frame, audio_path=None):
        self.parent_frame = parent_frame
        self.audio_path = audio_path
        self.vlc_available = False
        self.audio_speed = 1.0
        self.audio_length = 1
        self._slider_dragging = False
        
        # Try to import VLC
        try:
            import vlc
            self.vlc = vlc
            self.vlc_available = True
        except ImportError:
            self.vlc = None
            self.vlc_available = False
        
        # Initialize VLC if available
        if self.vlc_available and self.audio_path and os.path.exists(self.audio_path):
            try:
                self.vlc_instance = self.vlc.Instance()
                self.vlc_player = self.vlc_instance.media_player_new()
                media = self.vlc_instance.media_new(self.audio_path)
                self.vlc_player.set_media(media)
            except Exception as e:
                print(f"VLC initialization failed: {e}")
                self.vlc_available = False
        
        self.setup_controls()
    
    def setup_controls(self):
        """Setup the audio control widgets"""
        # Clear existing widgets
        for widget in self.parent_frame.winfo_children():
            widget.destroy()

        # Configure grid for the main audio controls frame
        self.parent_frame.grid_columnconfigure(0, weight=1)
        
        if self.vlc_available and self.audio_path and os.path.exists(self.audio_path):
            # Playback controls row
            playback_frame = Frame(self.parent_frame, bg=Colors.LIGHT)
            playback_frame.grid(row=0, column=0, sticky='ew', pady=(0, Spacing.XS))
            
            self.play_btn = Button(playback_frame, text="▶ Play", command=self.play_audio,
                                   font=Fonts.BODY_BOLD, bg=Colors.BUTTON_PLAY, fg=Colors.WHITE, 
                                   relief='flat', bd=0, cursor='hand2')
            self.play_btn.pack(side='left', padx=Spacing.XS)
            
            self.pause_btn = Button(playback_frame, text="⏸ Pause", command=self.pause_audio,
                                    font=Fonts.BODY, bg=Colors.BUTTON_PAUSE, fg=Colors.WHITE, 
                                    relief='flat', bd=0, cursor='hand2')
            self.pause_btn.pack(side='left', padx=Spacing.XS)
            
            self.stop_btn = Button(playback_frame, text="⏹ Stop", command=self.stop_audio,
                                   font=Fonts.BODY, bg=Colors.BUTTON_STOP, fg=Colors.WHITE, 
                                   relief='flat', bd=0, cursor='hand2')
            self.stop_btn.pack(side='left', padx=Spacing.XS)
            
            Button(playback_frame, text="⏪ -4s", command=lambda: self.jump_audio(-4), 
                   font=Fonts.BODY, bg=Colors.BUTTON_JUMP, fg=Colors.WHITE, 
                   relief='flat', bd=0, cursor='hand2').pack(side='left', padx=Spacing.XS)
            
            Button(playback_frame, text="+4s ⏩", command=lambda: self.jump_audio(4), 
                   font=Fonts.BODY, bg=Colors.BUTTON_JUMP, fg=Colors.WHITE, 
                   relief='flat', bd=0, cursor='hand2').pack(side='left', padx=Spacing.XS)
            
            Button(playback_frame, text="🐌 -5%", command=lambda: self.change_speed(-0.05), 
                   font=Fonts.BODY, bg=Colors.BUTTON_SPEED, fg=Colors.WHITE, 
                   relief='flat', bd=0, cursor='hand2').pack(side='left', padx=2)
            
            Button(playback_frame, text="🐇 +5%", command=lambda: self.change_speed(0.05), 
                   font=Fonts.BODY, bg=Colors.BUTTON_SPEED, fg=Colors.WHITE, 
                   relief='flat', bd=0, cursor='hand2').pack(side='left', padx=2)
            
            # Progress bar row
            self.audio_progress = DoubleVar()

            # Add a custom style for a thicker progress bar
            style = ttk.Style(self.parent_frame)
            style.configure("Thick.Horizontal.TScale", sliderthickness=25)

            self.audio_progress_bar = ttk.Scale(
                self.parent_frame,
                variable=self.audio_progress,
                from_=0,
                to=100,
                orient='horizontal',
                command=self.slider_seek_update,
                style="Thick.Horizontal.TScale"
            )
            self.audio_progress_bar.grid(row=1, column=0, sticky='ew', padx=Spacing.XS, pady=(Spacing.XS, Spacing.XS))
            self.audio_progress_bar.bind('<ButtonRelease-1>', self.slider_seek_commit)
            self.audio_progress_bar.focus_set()

            # Add mouse wheel scrolling support
            def on_scroll(event):
                if hasattr(self, 'audio_progress'):
                    current = self.audio_progress.get()
                    delta = 2 if event.delta > 0 else -2
                    new_value = max(0, min(100, current + delta))
                    self.audio_progress.set(new_value)
                    self.slider_seek_commit()
            
            self.audio_progress_bar.bind('<MouseWheel>', on_scroll)
            self.audio_progress_bar.bind('<Button-4>', lambda e: on_scroll(type('', (), {'delta': 120})))
            self.audio_progress_bar.bind('<Button-5>', lambda e: on_scroll(type('', (), {'delta': -120})))

            self.update_audio_progress()
        else:
            Label(self.parent_frame, text="No audio file available or VLC not installed.",
                  font=Fonts.BODY, bg=Colors.LIGHT, fg=Colors.DANGER).pack(pady=Spacing.SM)

    def play_audio(self):
        """Play the audio"""
        if hasattr(self, 'vlc_player'):
            self.vlc_player.play()
            self.vlc_player.set_rate(self.audio_speed)
            self.update_audio_progress()

    def pause_audio(self):
        """Pause the audio"""
        if hasattr(self, 'vlc_player'):
            self.vlc_player.pause()

    def stop_audio(self):
        """Stop the audio"""
        if hasattr(self, 'vlc_player'):
            self.vlc_player.stop()
            if hasattr(self, 'audio_progress'):
                self.audio_progress.set(0)

    def jump_audio(self, seconds):
        """Jump audio by specified seconds (positive or negative)"""
        if hasattr(self, 'vlc_player') and self.audio_length > 0:
            current_time = self.vlc_player.get_time()
            new_time = max(0, min(self.audio_length * 1000, current_time + seconds * 1000))
            self.vlc_player.set_time(int(new_time))
            
            # Force immediate progress update after jumping
            if hasattr(self.parent_frame, 'master'):
                self.parent_frame.master.after(50, lambda: self.update_audio_progress())
            elif hasattr(self.parent_frame, 'after'):
                self.parent_frame.after(50, lambda: self.update_audio_progress())

    def change_speed(self, delta):
        """Change playback speed"""
        self.audio_speed = max(0.5, min(2.0, self.audio_speed + delta))
        if hasattr(self, 'vlc_player'):
            self.vlc_player.set_rate(self.audio_speed)
        if hasattr(self, 'play_btn'):
            self.play_btn.config(text=f"▶ Play ({int(self.audio_speed*100)}%)")

    def slider_seek_update(self, value):
        """Handle slider dragging"""
        self._slider_dragging = True

    def slider_seek_commit(self, event=None):
        """Commit slider position to audio player"""
        if hasattr(self, 'vlc_player') and self.audio_length > 0:
            position = float(self.audio_progress.get()) / 100.0
            self.vlc_player.set_position(position)
        self._slider_dragging = False

    def update_audio_progress(self):
        """Update the audio progress bar"""
        if hasattr(self, 'vlc_player') and hasattr(self, 'audio_progress') and not self._slider_dragging:
            length = self.vlc_player.get_length()*10
            if length > 0:
                self.audio_length = length / 1000
                current_time = self.vlc_player.get_time() / 1000.0
                if current_time >= 0:
                    progress = (current_time / self.audio_length) * 1000
                    self.audio_progress.set(progress)
        # Always schedule the next update, regardless of play state
        if hasattr(self.parent_frame, 'master'):
            self.parent_frame.master.after(200, self.update_audio_progress)
        elif hasattr(self.parent_frame, 'after'):
            self.parent_frame.after(200, self.update_audio_progress)

    def setup_keyboard_bindings(self, master_window):
        """Setup keyboard shortcuts for audio control"""
        master_window.bind('<Key>', self.on_key_press)
        master_window.focus_set()
    
    def on_key_press(self, event):
        """Handle keyboard shortcuts"""
        key = event.keysym
        
        if key == 'Left':
            self.jump_audio(-4)
            return 'break'
        elif key == 'Right':
            self.jump_audio(4)
            return 'break'
        elif key == 'space':
            self.toggle_play_pause()
            return 'break'
    
    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if hasattr(self, 'vlc_player') and self.vlc_player:
            if self.vlc_player.is_playing():
                self.pause_audio()
            else:
                self.play_audio()
