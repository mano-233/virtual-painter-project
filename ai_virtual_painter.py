import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import filedialog, colorchooser
from tkinter import Toplevel
from PIL import Image, ImageTk
import math

class AIVirtualPainter:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Virtual Painter 🎨")
        self.root.configure(bg="#1e1e1e")
        
       
        self.cap = cv2.VideoCapture(0)
        self.canvas_img = np.zeros((480, 640, 3), np.uint8)
        self.saved_snapshots = [] 
        self.is_mouse_mode = False  
        self.gesture_threshold = 30  
        self.prev_x, self.prev_y = None, None

      
        self.current_color = (255, 0, 0)  
        self.brush_size = 5
        self.brush_shape = "line" 

        
        self.video_label = tk.Label(self.root)
        self.video_label.grid(row=0, column=0)

        control_frame = tk.Frame(self.root, bg="#1e1e1e", padx=10, pady=10)
        control_frame.grid(row=0, column=1, sticky="ns")

     
        self.color_palette = [
            (255, 0, 0),  # Red
            (0, 255, 0),  # Green
            (0, 0, 255),  # Blue
            (255, 255, 0),  # Yellow
            (255, 165, 0)  # Orange
        ]
        self.create_color_palette(control_frame)

    
        self.color_btn = tk.Button(control_frame, text="Choose Color", bg=self.rgb_to_hex(self.current_color),
                                   fg="black", width=15, height=2, command=self.choose_color, relief="solid", borderwidth=2)
        self.color_btn.pack(pady=10)

        
        tk.Label(control_frame, text="Brush Size", fg="white", bg="#1e1e1e", font=("Helvetica", 12)).pack(pady=5)
        self.brush_slider = tk.Scale(control_frame, from_=1, to=30, orient=tk.HORIZONTAL,
                                     command=self.set_brush_size, bg="#1e1e1e", fg="white", relief="solid", borderwidth=2)
        self.brush_slider.set(self.brush_size)
        self.brush_slider.pack(pady=10)

        
        tk.Label(control_frame, text="Brush Type", fg="white", bg="#1e1e1e", font=("Helvetica", 12)).pack(pady=5)
        self.brush_type_buttons = {
            "Circle": tk.Button(control_frame, text="Circle", command=lambda: self.set_brush_type("circle"), width=10),
            "Square": tk.Button(control_frame, text="Square", command=lambda: self.set_brush_type("square"), width=10),
            "Star": tk.Button(control_frame, text="Star", command=lambda: self.set_brush_type("star"), width=10),
            "Line": tk.Button(control_frame, text="Line", command=lambda: self.set_brush_type("line"), width=10)
        }
        
        for brush_type in self.brush_type_buttons.values():
            brush_type.pack(pady=5)

        
        tk.Button(control_frame, text="Save Drawing", command=self.save_drawing, width=15, height=2, relief="solid", borderwidth=2).pack(pady=10)
        tk.Button(control_frame, text="Clear Canvas", command=self.clear_canvas, width=15, height=2, relief="solid", borderwidth=2).pack(pady=5)
        tk.Button(control_frame, text="View Snapshots", command=self.view_snapshots, width=15, height=2, relief="solid", borderwidth=2).pack(pady=5)
        tk.Button(control_frame, text="Save Snapshot", command=self.save_snapshot, width=15, height=2, relief="solid", borderwidth=2).pack(pady=5)


        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils

        
        self.gesture_mode = True

        self.update()

    def create_color_palette(self, frame):
        """Create color buttons for predefined palette"""
        button_width = 10
        button_height = 2
        color_frame = tk.Frame(frame, bg="#1e1e1e")
        color_frame.pack(pady=10)

        for i, color in enumerate(self.color_palette):
            color_button = tk.Button(color_frame, bg=self.rgb_to_hex(color), height=button_height, width=button_width,
                                     command=lambda color=color: self.set_color(color), relief="solid", borderwidth=2)
            color_button.grid(row=0, column=i, padx=5)

    def choose_color(self):
        """Open color chooser dialog"""
        color = colorchooser.askcolor()[0]
        if color:
            self.current_color = (int(color[2]), int(color[1]), int(color[0]))  
            self.color_btn.configure(bg=self.rgb_to_hex(self.current_color))

    def set_color(self, color):
        """Set color when a predefined color is selected"""
        self.current_color = color

    def rgb_to_hex(self, color):
        """Convert RGB to Hex color code"""
        return '#%02x%02x%02x' % (color[2], color[1], color[0])

    def set_brush_size(self, val):
        """Set brush size from slider"""
        self.brush_size = int(val)

    def set_brush_type(self, brush_type):
        """Set the brush type"""
        self.brush_shape = brush_type

    def clear_canvas(self):
        """Clear the drawing canvas"""
        self.canvas_img = np.zeros((480, 640, 3), np.uint8)

    def save_drawing(self):
        """Save the current drawing"""
        file_path = filedialog.asksaveasfilename(defaultextension=".png")
        if file_path:
            cv2.imwrite(file_path, self.canvas_img)

    def save_snapshot(self):
        """Save a snapshot of the current canvas"""
        snapshot = self.canvas_img.copy()
        self.saved_snapshots.append(snapshot)

    def view_snapshots(self):
        """Open a new window to view saved snapshots"""
        snapshot_window = Toplevel(self.root)
        snapshot_window.title("Saved Snapshots")
        snapshot_window.configure(bg="#1e1e1e")
        
        for idx, snapshot in enumerate(self.saved_snapshots):
            
            snapshot_resized = cv2.resize(snapshot, (300, 300))
            img = Image.fromarray(snapshot_resized)
            img_tk = ImageTk.PhotoImage(image=img)
            
            
            snapshot_button = tk.Button(snapshot_window, image=img_tk, command=lambda idx=idx: self.load_snapshot(idx))
            snapshot_button.grid(row=idx // 3, column=idx % 3, padx=10, pady=10)
            snapshot_button.image = img_tk  

    def load_snapshot(self, idx):
        """Load a snapshot into the canvas"""
        self.canvas_img = self.saved_snapshots[idx]

    def update(self):
        """Update the video feed and process hand gestures"""
        ret, frame = self.cap.read()
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        if result.multi_hand_landmarks and self.gesture_mode:
            for hand_landmarks in result.multi_hand_landmarks:
                lm = hand_landmarks.landmark
                h, w, _ = frame.shape
                index_x = int(lm[8].x * w)
                index_y = int(lm[8].y * h)

                fingers = []
                fingers.append(1 if lm[8].y < lm[6].y else 0)   
                fingers.append(1 if lm[12].y < lm[10].y else 0) 

                
                if fingers == [1, 0]: 
                    self.prev_x, self.prev_y = index_x, index_y
                elif fingers == [1, 1]:  
                    if self.prev_x is not None and self.prev_y is not None:
                        self.draw_line(self.prev_x, self.prev_y, index_x, index_y)
                    self.prev_x, self.prev_y = index_x, index_y
                elif sum(fingers) == 0:  
                    cv2.circle(self.canvas_img, (index_x, index_y), 30, (0, 0, 0), -1)
                    self.prev_x, self.prev_y = None, None

                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                
                for i, color in enumerate(self.color_palette):
                    button_x1, button_y1, button_x2, button_y2 = self.get_button_bounding_box(i)
                    if button_x1 < index_x < button_x2 and button_y1 < index_y < button_y2:
                        self.set_color(color)

        
        combined = cv2.addWeighted(frame, 0.5, self.canvas_img, 0.5, 0)
        img = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)

        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

        self.root.after(10, self.update)

    def draw_line(self, x1, y1, x2, y2):
        """Draw the line based on selected brush shape"""
        if self.brush_shape == "circle":
            cv2.circle(self.canvas_img, (x2, y2), self.brush_size, self.current_color, -1)
        elif self.brush_shape == "square":
            cv2.rectangle(self.canvas_img, (x2 - self.brush_size, y2 - self.brush_size), 
                          (x2 + self.brush_size, y2 + self.brush_size), self.current_color, -1)
        elif self.brush_shape == "star":
            self.draw_star(x1, y1, x2, y2)
        elif self.brush_shape == "line":
            cv2.line(self.canvas_img, (x1, y1), (x2, y2), self.current_color, self.brush_size)

    def draw_star(self, x1, y1, x2, y2):
        """Draw a star shape at the given coordinates"""
        angle = np.linspace(0, 2 * np.pi, 6)
        x_coords = [int(x2 + self.brush_size * np.cos(a)) for a in angle]
        y_coords = [int(y2 + self.brush_size * np.sin(a)) for a in angle]
        points = list(zip(x_coords, y_coords))
        for i in range(len(points)):
            cv2.line(self.canvas_img, points[i], points[(i + 1) % len(points)], self.current_color, 2)

    def get_button_bounding_box(self, index):
        """Get the bounding box for color buttons"""
        button_width = 10
        button_height = 2
        x1 = 5 + (button_width * index)
        y1 = 5
        x2 = x1 + button_width
        y2 = y1 + button_height
        return x1, y1, x2, y2


if __name__ == "__main__":
    root = tk.Tk()
    app = AIVirtualPainter(root)
    root.mainloop()
