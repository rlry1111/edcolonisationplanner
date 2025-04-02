import tkinter
import ttkbootstrap as ttk

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tkinter.Canvas(self, borderwidth=0)
        self.vscrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vscrollbar.set)
        self.vscrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        container.bind_all("<MouseWheel>", self._on_mousewheel)
        container.bind_all("<Button-4>", self._on_up)
        container.bind_all("<Button-5>", self._on_down)
        # Prevent Combo Boxes to use the wheel
        container.unbind_class("TCombobox", "<MouseWheel>")
        container.unbind_class("TCombobox", "<ButtonPress-4>")
        container.unbind_class("TCombobox", "<ButtonPress-5>")

    def should_scroll(self):
        canvas_height = self.canvas.winfo_height()
        rows_height = self.canvas.bbox("all")[3]
        return rows_height > canvas_height # only scroll if the rows overflow the frame

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        if self.should_scroll():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_up(self, event):
        if self.should_scroll():
            self.canvas.yview_scroll(-1, "units")

    def _on_down(self, event):
        if self.should_scroll():
            self.canvas.yview_scroll(1, "units")
