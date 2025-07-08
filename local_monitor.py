#!/usr/bin/env python3
"""
ThinkTwice Local Monitor - Simulates Grammarly-like local monitoring
This demonstrates how the app could work locally to monitor all text input

To run: python local_monitor.py
"""
import time
import requests
import json
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import keyboard  # For global hotkey detection
import clipboard  # For clipboard monitoring

# API Configuration
API_BASE_URL = "https://d1923bbc-a7fa-4061-b3d1-995e92c3619a.preview.emergentagent.com/api"

class ThinkTwiceMonitor:
    def __init__(self):
        self.threshold = 0.5
        self.is_monitoring = False
        self.last_text = ""
        self.root = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the monitoring UI"""
        self.root = tk.Tk()
        self.root.title("ThinkTwice Local Monitor")
        self.root.geometry("400x300")
        
        # Status frame
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Monitoring toggle
        self.monitor_var = tk.BooleanVar()
        self.monitor_check = ttk.Checkbutton(
            status_frame, 
            text="Enable Monitoring", 
            variable=self.monitor_var,
            command=self.toggle_monitoring
        )
        self.monitor_check.pack(side=tk.LEFT)
        
        # Status label
        self.status_label = ttk.Label(status_frame, text="Status: Stopped")
        self.status_label.pack(side=tk.RIGHT)
        
        # Threshold frame
        threshold_frame = ttk.Frame(self.root)
        threshold_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(threshold_frame, text="Threshold:").pack(side=tk.LEFT)
        self.threshold_var = tk.DoubleVar(value=self.threshold)
        self.threshold_scale = ttk.Scale(
            threshold_frame,
            from_=0.1,
            to=0.9,
            variable=self.threshold_var,
            orient=tk.HORIZONTAL,
            command=self.update_threshold
        )
        self.threshold_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.threshold_label = ttk.Label(threshold_frame, text=f"{self.threshold:.2f}")
        self.threshold_label.pack(side=tk.RIGHT)
        
        # Test area
        test_frame = ttk.LabelFrame(self.root, text="Test Area")
        test_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.test_text = tk.Text(test_frame, height=8, wrap=tk.WORD)
        self.test_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.test_text.bind('<KeyRelease>', self.on_text_change)
        
        # Results frame
        results_frame = ttk.LabelFrame(self.root, text="Analysis Results")
        results_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.results_label = ttk.Label(results_frame, text="Type something to analyze...")
        self.results_label.pack(padx=5, pady=5)
        
        # Instructions
        instructions = ttk.Label(
            self.root,
            text="Enable monitoring to analyze text in real-time. Press Ctrl+Shift+T to analyze clipboard.",
            font=("Arial", 8)
        )
        instructions.pack(pady=5)
        
    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        self.is_monitoring = self.monitor_var.get()
        if self.is_monitoring:
            self.status_label.config(text="Status: Monitoring")
            self.start_monitoring()
        else:
            self.status_label.config(text="Status: Stopped")
            
    def start_monitoring(self):
        """Start monitoring in a separate thread"""
        if self.is_monitoring:
            threading.Thread(target=self.monitor_loop, daemon=True).start()
            
    def monitor_loop(self):
        """Main monitoring loop"""
        try:
            # Set up global hotkey
            keyboard.add_hotkey('ctrl+shift+t', self.analyze_clipboard)
            
            while self.is_monitoring:
                time.sleep(0.1)  # Small delay to prevent high CPU usage
                
        except Exception as e:
            print(f"Monitoring error: {e}")
            
    def analyze_clipboard(self):
        """Analyze text from clipboard"""
        try:
            text = clipboard.paste()
            if text and text != self.last_text:
                self.last_text = text
                self.analyze_text(text)
                print(f"Analyzed clipboard: {text[:50]}...")
        except Exception as e:
            print(f"Clipboard analysis error: {e}")
            
    def update_threshold(self, value):
        """Update threshold value"""
        self.threshold = float(value)
        self.threshold_label.config(text=f"{self.threshold:.2f}")
        
    def on_text_change(self, event):
        """Handle text changes in test area"""
        if self.is_monitoring:
            text = self.test_text.get("1.0", tk.END).strip()
            if text and text != self.last_text:
                self.last_text = text
                # Debounce - analyze after 500ms delay
                self.root.after(500, lambda: self.analyze_text(text))
                
    def analyze_text(self, text):
        """Analyze text using the API"""
        if not text.strip():
            return
            
        try:
            response = requests.post(
                f"{API_BASE_URL}/analyze-text",
                json={"text": text, "threshold": self.threshold},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.display_results(data)
                
                # Show warning if needed
                if data.get("should_warn", False):
                    self.show_warning(data)
                    
        except Exception as e:
            self.results_label.config(text=f"Error: {str(e)}")
            
    def display_results(self, data):
        """Display analysis results"""
        score = data.get("regret_score", 0)
        should_warn = data.get("should_warn", False)
        
        color = "red" if should_warn else "green"
        status = "⚠️ HIGH RISK" if should_warn else "✅ SAFE"
        
        result_text = f"Score: {score:.2f} | {status}"
        self.results_label.config(text=result_text, foreground=color)
        
    def show_warning(self, data):
        """Show warning popup"""
        score = data.get("regret_score", 0)
        messagebox.showwarning(
            "ThinkTwice Warning",
            f"⚠️ Think twice before sending!\n\n"
            f"Regret Score: {score:.2f}\n"
            f"This message might be regrettable.\n\n"
            f"Consider rephrasing before sending."
        )
        
    def run(self):
        """Run the monitoring application"""
        print("ThinkTwice Local Monitor starting...")
        print("Press Ctrl+Shift+T to analyze clipboard content")
        self.root.mainloop()

def main():
    """Main function"""
    try:
        monitor = ThinkTwiceMonitor()
        monitor.run()
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()