import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import time
import cv2
import numpy as np
from pynput import mouse, keyboard
from screeninfo import get_monitors
import ctypes

# Fix for high-DPI scaling
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class MousePathTracer:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ Mouse Path Trace")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1a1625")

        # --- State Variables ---
        self.is_recording = False
        self.points = []
        self.monitors = get_monitors()
        self.last_point = None
        
        # Background settings
        self.bg_mode = tk.StringVar(value="color")
        self.bg_color = "#0a0a0f"
        self.bg_image_path = None
        self.bg_image_data = None
        
        # --- Customizable Settings ---
        self.cfg_color = (237, 107, 255)
        self.cfg_thickness = tk.IntVar(value=4)
        self.cfg_hz = tk.IntVar(value=30) 
        self.cfg_speed_multiplier = tk.DoubleVar(value=1.0)
        self.cfg_show_dots = tk.BooleanVar(value=True)

        self.setup_styles()
        self.setup_ui()
        self.setup_hotkeys()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", 
                        fieldbackground="#252033", 
                        background="#2d2640", 
                        foreground="#e8e3f0", 
                        darkcolor="#252033", 
                        lightcolor="#252033",
                        bordercolor="#3d3450",
                        insertcolor="#c084fc")
        style.configure("TRadiobutton",
                       background="#252033",
                       foreground="#e8e3f0",
                       indicatorcolor="#1a1625",
                       focuscolor="#252033")

    def setup_ui(self):
        # Main container with two columns
        main_container = tk.Frame(self.root, bg="#1a1625")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # === LEFT COLUMN: Controls (narrower) ===
        left_col = tk.Frame(main_container, width=340, bg="#252033")
        left_col.pack(side=tk.LEFT, fill=tk.BOTH)
        left_col.pack_propagate(False)
        
        # Scrollable container for controls
        canvas_scroll = tk.Canvas(left_col, bg="#252033", highlightthickness=0)
        scrollbar = tk.Scrollbar(left_col, orient="vertical", command=canvas_scroll.yview)
        scrollable_frame = tk.Frame(canvas_scroll, bg="#252033")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
        )
        
        canvas_scroll.create_window((0, 0), window=scrollable_frame, anchor="nw", width=320)
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        
        canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        content = tk.Frame(scrollable_frame, bg="#252033", padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)

        # Header
        tk.Label(content, text="🖱️ Mouse Path Trace", bg="#252033", fg="#c084fc", 
                font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 2))
        tk.Label(content, text="Capture & Animate", bg="#252033", fg="#a78bca", 
                font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 15))
        
        tk.Frame(content, bg="#3d3450", height=2).pack(fill=tk.X, pady=(0, 15))

        # Compact card creator
        def create_section(parent, title):
            tk.Label(parent, text=title, bg="#252033", fg="#a78bca", 
                    font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(10, 5))
            frame = tk.Frame(parent, bg="#2d2640", padx=12, pady=10, 
                          highlightthickness=1, highlightbackground="#3d3450")
            frame.pack(fill=tk.X, pady=(0, 5))
            return frame

        # === DISPLAY ===
        display = create_section(content, "🖥️  DISPLAY")
        self.monitor_combo = ttk.Combobox(display, state="readonly", font=("Segoe UI", 9))
        self.monitor_combo['values'] = [f"Monitor {i+1}" for i in range(len(self.monitors))]
        self.monitor_combo.current(0)
        self.monitor_combo.pack(fill=tk.X, pady=(0, 8))
        self.monitor_combo.bind("<<ComboboxSelected>>", lambda e: self.sync_canvas_ratio())

        tk.Label(display, text=f"Sample Rate: {self.cfg_hz.get()} Hz", bg="#2d2640", 
                fg="#e8e3f0", font=("Segoe UI", 8)).pack(anchor="w")
        self.hz_label = display.winfo_children()[-1]
        
        tk.Scale(display, from_=1, to=120, orient=tk.HORIZONTAL, variable=self.cfg_hz, 
                 bg="#2d2640", fg="#c084fc", highlightthickness=0, troughcolor="#1a1625", 
                 activebackground="#c084fc", sliderrelief=tk.FLAT, showvalue=0,
                 command=self.update_hz_label).pack(fill=tk.X, pady=(3, 0))

        # === PATH STYLE ===
        style_sec = create_section(content, "🎨  PATH STYLE")
        
        color_row = tk.Frame(style_sec, bg="#2d2640")
        color_row.pack(fill=tk.X, pady=(0, 8))
        
        self.color_preview = tk.Frame(color_row, bg="#ed6bff", width=35, height=35, 
                                     relief=tk.FLAT, highlightthickness=1, 
                                     highlightbackground="#3d3450")
        self.color_preview.pack(side=tk.LEFT, padx=(0, 8))
        
        color_info = tk.Frame(color_row, bg="#2d2640")
        color_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.color_hex_label = tk.Label(color_info, text="#ED6BFF", bg="#2d2640", 
                                       fg="#e8e3f0", font=("Consolas", 10, "bold"))
        self.color_hex_label.pack(anchor="w")
        
        tk.Button(color_info, text="Choose", command=self.pick_color,
                 bg="#3d3450", fg="#e8e3f0", relief=tk.FLAT, 
                 font=("Segoe UI", 8), cursor="hand2", pady=4,
                 activebackground="#4a4060").pack(fill=tk.X, pady=(2, 0))
        
        tk.Label(style_sec, text=f"Thickness: {self.cfg_thickness.get()}px", 
                bg="#2d2640", fg="#e8e3f0", font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 3))
        self.thick_label = style_sec.winfo_children()[-1]
        
        tk.Scale(style_sec, from_=1, to=30, orient=tk.HORIZONTAL, 
                variable=self.cfg_thickness, bg="#2d2640", fg="#c084fc", 
                highlightthickness=0, troughcolor="#1a1625", activebackground="#c084fc",
                sliderrelief=tk.FLAT, showvalue=0, 
                command=self.update_thick_label).pack(fill=tk.X, pady=(0, 8))

        tk.Checkbutton(style_sec, text="Show dots", variable=self.cfg_show_dots, 
                       bg="#2d2640", fg="#e8e3f0", selectcolor="#1a1625", 
                       activebackground="#2d2640", font=("Segoe UI", 8)).pack(anchor="w")

        # === BACKGROUND ===
        bg_sec = create_section(content, "🖼️  BACKGROUND")
        
        mode_frame = tk.Frame(bg_sec, bg="#2d2640")
        mode_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Radiobutton(mode_frame, text="Color", variable=self.bg_mode, 
                       value="color", command=self.on_bg_mode_change).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(mode_frame, text="Image", variable=self.bg_mode, 
                       value="image", command=self.on_bg_mode_change).pack(side=tk.LEFT)
        
        self.bg_color_frame = tk.Frame(bg_sec, bg="#2d2640")
        self.bg_color_frame.pack(fill=tk.X)
        
        tk.Button(self.bg_color_frame, text="Choose BG Color", 
                 command=self.pick_bg_color, bg="#3d3450", fg="#e8e3f0", 
                 relief=tk.FLAT, font=("Segoe UI", 8), cursor="hand2", pady=6,
                 activebackground="#4a4060").pack(fill=tk.X)
        
        self.bg_image_frame = tk.Frame(bg_sec, bg="#2d2640")
        
        tk.Button(self.bg_image_frame, text="Select Image", 
                 command=self.pick_bg_image, bg="#3d3450", fg="#e8e3f0", 
                 relief=tk.FLAT, font=("Segoe UI", 8), cursor="hand2", pady=6,
                 activebackground="#4a4060").pack(fill=tk.X, pady=(0, 4))
        
        self.bg_image_label = tk.Label(self.bg_image_frame, text="No image", 
                                      bg="#2d2640", fg="#a78bca", font=("Segoe UI", 7, "italic"))
        self.bg_image_label.pack(anchor="w")

        # === EXPORT ===
        exp_sec = create_section(content, "🎬  EXPORT")
        
        tk.Label(exp_sec, text=f"Playback Speed: {self.cfg_speed_multiplier.get():.1f}x", bg="#2d2640", 
                fg="#e8e3f0", font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 3))
        self.speed_label = exp_sec.winfo_children()[-1]
        
        tk.Scale(exp_sec, from_=0.1, to=10.0, resolution=0.1, orient=tk.HORIZONTAL, 
                variable=self.cfg_speed_multiplier, bg="#2d2640", fg="#c084fc", 
                highlightthickness=0, troughcolor="#1a1625", activebackground="#c084fc",
                sliderrelief=tk.FLAT, showvalue=0, 
                command=self.update_speed_label).pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(exp_sec, text="1x = realtime, 2x = 2x faster, 0.5x = slower", 
                bg="#2d2640", fg="#6b6380", font=("Segoe UI", 7, "italic")).pack(anchor="w")

        # === ACTION BUTTONS ===
        tk.Frame(content, bg="#3d3450", height=2).pack(fill=tk.X, pady=(15, 12))
        
        self.btn_run = tk.Button(content, text="● START RECORDING", bg="#c084fc", 
                                fg="white", font=("Segoe UI", 10, "bold"), height=2, 
                                relief=tk.FLAT, cursor="hand2", command=self.toggle_recording,
                                activebackground="#d8b4fe")
        self.btn_run.pack(fill=tk.X, pady=(0, 8))

        self.btn_export = tk.Button(content, text="💾 EXPORT VIDEO", state=tk.DISABLED, 
                                   bg="#2d2640", fg="#6b6380", font=("Segoe UI", 9, "bold"), 
                                   height=2, relief=tk.FLAT, command=self.save_video)
        self.btn_export.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(content, text="💡 Press F8 to start/stop", 
                bg="#252033", fg="#6b6380", font=("Segoe UI", 7, "italic")).pack(pady=(5, 10))

        # === RIGHT COLUMN: Preview (wider) ===
        right_col = tk.Frame(main_container, bg="#1a1625")
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Status bar at top
        status_frame = tk.Frame(right_col, bg="#1a1625", pady=15)
        status_frame.pack(fill=tk.X, padx=25)
        
        self.status_indicator = tk.Label(status_frame, text="●", bg="#1a1625", fg="#34d399", 
                                        font=("Segoe UI", 14))
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 8))
        
        self.status_label = tk.Label(status_frame, text="Ready", bg="#1a1625", 
                                     fg="#a78bca", font=("Segoe UI", 11, "bold"))
        self.status_label.pack(side=tk.LEFT)

        # Canvas container
        canvas_area = tk.Frame(right_col, bg="#1a1625")
        canvas_area.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 25))
        
        canvas_border = tk.Frame(canvas_area, bg="#3d3450", padx=2, pady=2)
        canvas_border.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        self.canvas = tk.Canvas(canvas_border, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack()

        self.root.after(200, self.sync_canvas_ratio)
        self.on_bg_mode_change()

    def update_hz_label(self, val):
        self.hz_label.config(text=f"Sample Rate: {int(float(val))} Hz")
    
    def update_thick_label(self, val):
        self.thick_label.config(text=f"Thickness: {int(float(val))}px")
    
    def update_speed_label(self, val):
        self.speed_label.config(text=f"Playback Speed: {float(val):.1f}x")

    def pick_color(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(initialcolor="#ed6bff", title="Choose Path Color")
        if color[1]:
            rgb = tuple(int(color[1].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            self.cfg_color = (rgb[2], rgb[1], rgb[0])
            self.color_preview.configure(bg=color[1])
            self.color_hex_label.config(text=color[1].upper())

    def pick_bg_color(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(initialcolor=self.bg_color, title="Choose Background Color")
        if color[1]:
            self.bg_color = color[1]
            self.canvas.config(bg=self.bg_color)

    def pick_bg_image(self):
        filepath = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if filepath:
            self.bg_image_path = filepath
            img = cv2.imread(filepath)
            if img is not None:
                m = self.monitors[self.monitor_combo.current()]
                self.bg_image_data = cv2.resize(img, (m.width, m.height))
                
                filename = filepath.split('/')[-1].split('\\')[-1]
                self.bg_image_label.config(text=f"✓ {filename[:25]}..." if len(filename) > 25 else f"✓ {filename}")
                
                self.update_canvas_background()

    def on_bg_mode_change(self):
        if self.bg_mode.get() == "color":
            self.bg_color_frame.pack(fill=tk.X)
            self.bg_image_frame.pack_forget()
            self.canvas.config(bg=self.bg_color)
        else:
            self.bg_color_frame.pack_forget()
            self.bg_image_frame.pack(fill=tk.X)
            if self.bg_image_path:
                self.update_canvas_background()

    def update_canvas_background(self):
        if self.bg_mode.get() == "image" and self.bg_image_path:
            try:
                img = Image.open(self.bg_image_path)
                cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
                if cw > 1 and ch > 1:
                    img = img.resize((cw, ch), Image.LANCZOS)
                    self.canvas_bg_image = ImageTk.PhotoImage(img)
                    self.canvas.delete("bg_image")
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=self.canvas_bg_image, tags="bg_image")
                    self.canvas.tag_lower("bg_image")
            except Exception as e:
                print(f"Error loading background: {e}")

    def sync_canvas_ratio(self):
        m = self.monitors[self.monitor_combo.current()]
        ratio = m.width / m.height
        self.root.update_idletasks()
        
        # Get available space in right column
        right_width = self.root.winfo_width() - 340  # subtract left column width
        avail_w = right_width - 80
        avail_h = self.root.winfo_height() - 150
        
        if avail_w / avail_h > ratio:
            new_h = avail_h
            new_w = int(avail_h * ratio)
        else:
            new_w = avail_w
            new_h = int(avail_w / ratio)
        
        self.canvas.config(width=new_w, height=new_h)
        if self.bg_mode.get() == "image":
            self.root.after(100, self.update_canvas_background)

    def setup_hotkeys(self):
        def on_press(key):
            if key == keyboard.Key.f8: self.root.after(0, self.toggle_recording)
        keyboard.Listener(on_press=on_press, daemon=True).start()

    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording, self.points, self.last_point = True, [], None
            self.canvas.delete("all")
            if self.bg_mode.get() == "image":
                self.update_canvas_background()
            
            self.btn_run.config(text="■ STOP RECORDING", bg="#ef4444", activebackground="#f87171")
            self.status_label.config(text="Recording", fg="#ef4444")
            self.status_indicator.config(fg="#ef4444")
            self.btn_export.config(state=tk.DISABLED, bg="#2d2640", fg="#6b6380")
            self.stop_event = threading.Event()
            threading.Thread(target=self.track_loop, daemon=True).start()
        else:
            self.is_recording = False
            self.stop_event.set()
            self.btn_run.config(text="● START RECORDING", bg="#c084fc", activebackground="#d8b4fe")
            self.status_label.config(text="Complete", fg="#34d399")
            self.status_indicator.config(fg="#34d399")
            self.btn_export.config(state=tk.NORMAL, bg="#c084fc", fg="white", cursor="hand2",
                                 activebackground="#d8b4fe")

    def track_loop(self):
        mouse_ctrl, m = mouse.Controller(), self.monitors[self.monitor_combo.current()]
        while not self.stop_event.is_set():
            interval = 1.0 / max(1, self.cfg_hz.get())
            gx, gy = mouse_ctrl.position
            if m.x <= gx < m.x + m.width and m.y <= gy < m.y + m.height:
                rx, ry = gx - m.x, gy - m.y
                self.points.append((rx, ry))
                if self.last_point:
                    self.render_expansion(self.last_point, (rx, ry), interval, m.width, m.height)
                self.last_point = (rx, ry)
            time.sleep(interval)

    def render_expansion(self, p1, p2, duration, mw, mh):
        frames, step_ms = 4, int((duration / 4) * 1000)
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        hex_c = "#%02x%02x%02x" % (self.cfg_color[2], self.cfg_color[1], self.cfg_color[0])
        for i in range(1, frames + 1):
            t_curr, t_prev = i / frames, (i-1) / frames
            ix, iy = p1[0] + (p2[0]-p1[0])*t_curr, p1[1] + (p2[1]-p1[1])*t_curr
            px, py = p1[0] + (p2[0]-p1[0])*t_prev, p1[1] + (p2[1]-p1[1])*t_prev
            x1, y1, x2, y2 = px*(cw/mw), py*(ch/mh), ix*(cw/mw), iy*(ch/mh)
            self.root.after(i*step_ms, lambda a=x1, b=y1, c=x2, d=y2: 
                self.canvas.create_line(a, b, c, d, fill=hex_c, width=self.cfg_thickness.get(), 
                                      capstyle=tk.ROUND, joinstyle=tk.ROUND))
            if self.cfg_show_dots.get():
                r = self.cfg_thickness.get() // 2
                self.root.after(i*step_ms, lambda a=x2, b=y2: 
                    self.canvas.create_oval(a-r, b-r, a+r, b+r, fill=hex_c, outline=""))

    def save_video(self):
        filename = filedialog.asksaveasfilename(defaultextension=".mp4", 
                                               title="Export Video")
        if not filename or not self.points: return
        
        m = self.monitors[self.monitor_combo.current()]
        
        # Calculate FPS based on sample rate and speed multiplier
        # Sample rate = points per second recorded
        # Speed multiplier = how fast to play it back
        # FPS = sample_rate * speed_multiplier
        sample_rate = self.cfg_hz.get()
        speed_multiplier = self.cfg_speed_multiplier.get()
        fps = sample_rate * speed_multiplier
        
        # Calculate actual video duration
        recorded_duration = len(self.points) / sample_rate
        video_duration = recorded_duration / speed_multiplier
        
        out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'mp4v'), fps, (m.width, m.height))
        
        if self.bg_mode.get() == "image" and self.bg_image_data is not None:
            base_frame = self.bg_image_data.copy()
        else:
            hex_color = self.bg_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            bgr = (rgb[2], rgb[1], rgb[0])
            base_frame = np.full((m.height, m.width, 3), bgr, dtype=np.uint8)
        
        frame = base_frame.copy()
        
        for i in range(len(self.points)):
            curr = self.points[i]
            if i > 0:
                prev = self.points[i-1]
                cv2.line(frame, (int(prev[0]), int(prev[1])), (int(curr[0]), int(curr[1])), 
                        self.cfg_color, self.cfg_thickness.get(), cv2.LINE_AA)
                if self.cfg_show_dots.get():
                    cv2.circle(frame, (int(curr[0]), int(curr[1])), 
                             self.cfg_thickness.get()//2 + 1, self.cfg_color, -1, cv2.LINE_AA)
            out.write(frame)
        
        out.release()
        messagebox.showinfo("Export Complete", 
                          f"Video saved successfully!\n\n"
                          f"FPS: {fps:.1f}\n"
                          f"Duration: {video_duration:.2f} seconds\n"
                          f"Speed: {speed_multiplier:.1f}x")

if __name__ == "__main__":
    root = tk.Tk()
    app = MousePathTracer(root)
    root.mainloop()