import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime, timedelta

# Global variables to track the selected year and month
selected_year = None
selected_month = None
timeline = None  # Add this line to make timeline a global variable
dragging = False
drag_start_x = None
drag_start_y = None

class TextBar:
    def __init__(self, canvas, start_date, text, color):
        self.canvas = canvas
        self.start_date = start_date
        self.text = text
        self.color = color
        self.text_id = None
        self.topic = ""
        self.message = ""

    def draw(self, day_width, y_offset):
        days_from_start = (self.start_date - timeline.start_date).days
        x1 = days_from_start * day_width + timeline.scroll_offset  # Adjust for scroll_offset
        x2 = x1 + day_width / 4
        y1 = y_offset
        y2 = y1 + 30
        self.text_id = self.canvas.create_rectangle(
            x1, y1, x2, y2, fill=self.color, outline="blue", tags="text_bars"
        )
        self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=self.topic, tags="text_bars")

    def move(self, new_start_date, y_offset):
        self.start_date = new_start_date
        self.canvas.delete(self.text_id)
        self.draw(timeline.day_width, y_offset)

    def show_popup(self, event):
        popup = tk.Toplevel(root)
        popup.title("Text Bar Details")

        # Entry for the topic
        topic_label = ttk.Label(popup, text="Topic:")
        topic_label.grid(row=0, column=0)
        self.topic_entry = ttk.Entry(popup, width=30)
        self.topic_entry.grid(row=0, column=1)
        self.topic_entry.insert(0, self.topic)

        # Entry for the message
        message_label = ttk.Label(popup, text="Message:")
        message_label.grid(row=1, column=0)
        self.message_entry = ttk.Entry(popup, width=30)
        self.message_entry.grid(row=1, column=1)
        self.message_entry.insert(0, self.message)

        # Button to change color
        color_button = ttk.Button(
            popup, text="Change Color", command=self.change_color
        )
        color_button.grid(row=2, columnspan=2)

        # Button to save changes
        save_button = ttk.Button(
            popup, text="Save Changes", command=self.save_changes
        )
        save_button.grid(row=3, columnspan=2)

        # Set focus to the topic entry
        self.topic_entry.focus()

    def change_color(self):
        color = tk.colorchooser.askcolor()[1]
        if color:
            self.color = color
            self.canvas.itemconfig(self.text_id, fill=self.color)

    def save_changes(self):
        self.topic = self.topic_entry.get()
        self.message = self.message_entry.get()

class Timeline:
    def __init__(self, canvas):
        self.canvas = canvas
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=30)
        self.day_width = 100  # Width for each day on the timeline
        self.text_bars = []
        self.max_boxes_per_date = 15  # Maximum boxes per date
        self.y_offset = 0  # Vertical offset for scrolling
        self.scroll_offset = 0  # Horizontal scroll offset

        # Create a frame inside the canvas to hold text bars
        self.text_bar_frame = ttk.Frame(self.canvas)
        self.text_bar_window = self.canvas.create_window(
            0, 0, window=self.text_bar_frame, anchor="nw"
        )
        self.canvas.bind("<Configure>", self.configure_canvas)
        self.canvas.bind("<ButtonPress-3>", self.start_drag)  # Right-click to start drag
        self.canvas.bind("<B3-Motion>", self.drag_timeline)
        self.canvas.bind("<ButtonRelease-3>", self.stop_drag)

        # Increase the height of the timeline canvas
        self.canvas.config(scrollregion=(0, 0, 1500, 1080))  # Adjust the height as needed

    def configure_canvas(self, event):
        # Update the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def draw(self):
        # Clear the entire canvas
        self.canvas.delete("all")

        # Calculate the number of days to display (maximum 30)
        num_days = min((self.end_date - self.start_date).days + 1, 30)

        # Draw the timeline
        for i in range(num_days):
            x1 = i * self.day_width + self.scroll_offset
            x2 = (i + 1) * self.day_width + self.scroll_offset
            self.canvas.create_rectangle(
                x1, 0, x2, 30, fill="lightblue", outline="blue"
            )
            # Display the date on top of each day
            date_label = self.start_date + timedelta(days=i)
            self.canvas.create_text(x1 + 45, 10, text=date_label.strftime("%d"), font=("Helvetica", 12), fill="black")

        # Draw vertical grid lines
        for i in range(4, 30, 4):
            x = i * self.day_width + self.scroll_offset
            self.canvas.create_line(x, 0, x, 1000, fill="gray", dash=(2, 2))

        # Draw text bars
        for text_bar in self.text_bars:
            text_bar.draw(self.day_width, self.y_offset)

    def set_date_range(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.draw()

    def add_box(self, event):
        x = self.canvas.canvasx(event.x)
        days_from_start = int((x - self.scroll_offset) / self.day_width)
        new_start_date = self.start_date + timedelta(days=days_from_start)

        # Find the available column index for this date
        date_boxes = [box for box in self.text_bars if box.start_date == new_start_date]

        # Calculate the new column index
        column_index = len(date_boxes)

        # Calculate y_offset based on the column index
        y_offset = (column_index % self.max_boxes_per_date) * 40 + self.y_offset

        text_bar = TextBar(self.canvas, new_start_date, "New Box", "green")
        text_bar.draw(self.day_width, y_offset=y_offset)
        text_bar.column_num = column_index
        self.text_bars.append(text_bar)

    def scroll_timeline(self, event):
        num_boxes_y = (max(self.text_bars, key=lambda box: box.column_num).column_num + 1) if self.text_bars else 1
        self.y_offset += event.delta * 2
        self.y_offset = min(0, self.y_offset)
        self.y_offset = max(-(num_boxes_y - 15) * 40, self.y_offset)

    def start_drag(self, event):
        global dragging, drag_start_x, drag_start_y
        dragging = True
        drag_start_x = event.x
        drag_start_y = event.y

    def drag_timeline(self, event):
        global dragging, drag_start_x, drag_start_y
        if dragging:
            delta_x = event.x - drag_start_x
            delta_y = event.y - drag_start_y

            self.scroll_offset += delta_x
            self.y_offset += delta_y

            self.draw()
            drag_start_x = event.x
            drag_start_y = event.y

    def stop_drag(self, event):
        global dragging
        dragging = False

def day_click(event, day):
    global selected_year, selected_month, timeline
    selected_date = datetime(selected_year, selected_month, day)
    next_month_date = selected_date + timedelta(days=30)
    timeline.set_date_range(selected_date, next_month_date)
    timeline.draw()

def update_calendar(selected_year, selected_month):
    for widget in calendar_frame.winfo_children():
        widget.destroy()

    day_names = calendar.month_abbr[1:]
    for i, day in enumerate(day_names):
        day_label = ttk.Label(calendar_frame, text=day)
        day_label.grid(row=0, column=i)

    cal = calendar.monthcalendar(selected_year, selected_month)

    for week_num, week in enumerate(cal, start=1):
        for day_num, day in enumerate(week, start=1):
            if day != 0:
                day_label = ttk.Label(calendar_frame, text=str(day))
                day_label.grid(row=week_num, column=day_num)
                day_label.bind("<Button-1>", lambda event, d=day: day_click(event, d))

def change_month():
    global selected_year, selected_month, timeline
    selected_year = int(year_entry.get())
    selected_month = int(month_entry.get())
    update_calendar(selected_year, selected_month)
    selected_date = datetime(selected_year, selected_month, 1)
    next_month_date = selected_date + timedelta(days=30)
    timeline.set_date_range(selected_date, next_month_date)
    timeline.draw()

if __name__ == "__main__":
    current_date = datetime.now()
    selected_year = current_date.year
    selected_month = current_date.month

    root = tk.Tk()
    root.title("Calendar Viewer")

    calendar_frame = ttk.Frame(root)
    calendar_frame.grid(row=1, column=0, columnspan=7)

    year_label = ttk.Label(root, text="Year:")
    year_label.grid(row=0, column=0)
    year_entry = ttk.Entry(root, width=4)
    year_entry.grid(row=0, column=1)
    year_entry.insert(0, selected_year)

    month_label = ttk.Label(root, text="Month:")
    month_label.grid(row=0, column=2)
    month_entry = ttk.Entry(root, width=2)
    month_entry.grid(row=0, column=3)
    month_entry.insert(0, selected_month)

    change_button = ttk.Button(root, text="Change Month", command=change_month)
    change_button.grid(row=0, column=4, columnspan=2)

    timeline_label = ttk.Label(root, text="Timeline")
    timeline_label.grid(row=2, column=0, columnspan=7)

    timeline_canvas = tk.Canvas(root, width=1500, height=800)  # Adjust the height as needed
    timeline_canvas.grid(row=3, column=0, columnspan=7)

    timeline = Timeline(timeline_canvas)

    timeline_canvas.bind("<Double-Button-1>", timeline.add_box)
    timeline_canvas.bind("<ButtonPress-3>", timeline.start_drag)  # Right-click to start drag
    timeline_canvas.bind("<B3-Motion>", timeline.drag_timeline)
    timeline_canvas.bind("<ButtonRelease-3>", timeline.stop_drag)

    update_calendar(selected_year, selected_month)

    # Set the window size to 80% of the user's screen
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = int(screen_width * 0.8)
    window_height = int(screen_height * 0.8)
    root.geometry(f"{window_width}x{window_height}")

    root.mainloop()