"""
Shared text display component with SRT highlighting for transcription review
"""
from tkinter import Frame, Label, Text, Scrollbar
import re

class TranscriptionTextDisplay:
    """Text display widget with SRT highlighting for transcription review"""
    
    def __init__(self, parent_frame, srt_path, highlight_callback=None):
        self.parent_frame = parent_frame
        self.srt_path = srt_path
        self.highlight_callback = highlight_callback
        self.srt_segments = []
        self.current_segment_idx = -1
        
        self.setup_text_display()
        if self.srt_path:
            self.parse_and_display_srt()
    
    def setup_text_display(self):
        """Setup the text display widget"""
        # Configure grid
        self.parent_frame.grid_columnconfigure(0, weight=1)
        self.parent_frame.grid_rowconfigure(0, weight=1)
        
        # Text widget with scrollbar
        self.text_widget = Text(self.parent_frame, 
                               font=("Segoe UI", 12), 
                               wrap='word',
                               bg='#fafafa', 
                               fg='#212529',
                               relief='flat', 
                               borderwidth=0,
                               selectbackground='#0078d4',
                               selectforeground='white',
                               padx=20, 
                               pady=15)
        
        scrollbar = Scrollbar(self.parent_frame, orient='vertical', command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        self.text_widget.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
    
    def parse_and_display_srt(self):
        """Parse SRT file and display with highlighting capability"""
        self.srt_segments = []
        self.text_widget.config(state='normal')
        self.text_widget.delete('1.0', 'end')
        
        try:
            with open(self.srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            # Parse SRT format
            pattern = re.compile(r"(\d+)\s+([\d:,]+) --> ([\d:,]+)\s+([\s\S]*?)(?=\n\d+\n|\Z)")
            for match in pattern.finditer(srt_content):
                idx = int(match.group(1))
                start = self.srt_time_to_seconds(match.group(2))
                end = self.srt_time_to_seconds(match.group(3))
                text = match.group(4).strip().replace('\n', ' ')
                
                self.srt_segments.append({'idx': idx, 'start': start, 'end': end, 'text': text})
            
            # Insert lines and tag them for highlighting
            for i, seg in enumerate(self.srt_segments):
                tag = f'seg_{i}'
                self.text_widget.insert('end', seg['text'] + '\n', tag)
                # Set default background
                self.text_widget.tag_configure(tag, background='#fafafa')
            
            self.text_widget.config(state='disabled')
            
        except Exception as e:
            self.text_widget.insert('1.0', f"Failed to load transcription: {e}")
            self.text_widget.config(state='disabled')
    
    def srt_time_to_seconds(self, time_str):
        """Convert SRT time format to seconds"""
        h, m, rest = time_str.split(':')
        s, ms = rest.split(',')
        return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
    
    def highlight_current_segment(self, current_time):
        """Highlight the current segment based on audio time"""
        # Remove previous highlight
        for i in range(len(self.srt_segments)):
            tag = f'seg_{i}'
            self.text_widget.tag_configure(tag, background='#fafafa')
        
        # Find and highlight the current segment
        for i, seg in enumerate(self.srt_segments):
            if seg['start'] <= current_time <= seg['end']:
                tag = f'seg_{i}'
                self.text_widget.tag_configure(tag, background='#fff3cd')
                
                # Call highlight callback if provided
                if self.highlight_callback:
                    self.highlight_callback(i, seg)
                break
    
    def set_text(self, text_content):
        """Set plain text content (for non-SRT text)"""
        self.text_widget.config(state='normal')
        self.text_widget.delete('1.0', 'end')
        self.text_widget.insert('1.0', text_content)
        self.text_widget.config(state='disabled')
    
    def get_segments(self):
        """Get parsed SRT segments"""
        return self.srt_segments
    
    def clear(self):
        """Clear the text display"""
        self.text_widget.config(state='normal')
        self.text_widget.delete('1.0', 'end')
        self.text_widget.config(state='disabled')
