import tkinter
import ttkbootstrap as ttk
from ttkbootstrap.tooltip import ToolTip


# tkinter setup
def get_int_var_value(variable):
    try:
        return variable.get()
    except tkinter.TclError:
        return 0

vcmd = None
vcmd_positive = None

def validate_input(P):
    return P.isdigit() or P == "" or P == "-" or (P[0] == "-" and P[1:].isdigit())

def validate_input_positive(P):
    return P.isdigit() or P == ""

def get_vcmd():
    return (vcmd, "%P")

def get_vcmd_positive():
    return (vcmd_positive, "%P")

def register_validate_commands(root):
    global vcmd, vcmd_positive
    vcmd = root.register(validate_input)
    vcmd_positive = root.register(validate_input_positive)

def on_focus_out(event, var):
    value = event.widget.get().lower()
    if value == "-":
        value = ""
    var.set(value)

def on_focus_out_integer(event, var):
    value = event.widget.get().lower()
    if value == "-" or value == "":
        value = 0
    var.set(value)

def set_style_if_negative(variable, entry, style1="danger", style2="success"):
    def callback(var, index, mode):
        val = variable.get()
        if val < 0:
            entry.config(bootstyle=style1)
        else:
            entry.config(bootstyle=style2)
    variable.trace_add("write", callback)

def get_widget_hierarchy(widget):
    #Recursively retrieves all widgets and their parents in a nested dictionary
    #Mainly for debugging
    hierarchy = {}
    for child in widget.winfo_children():
        hierarchy[child] = get_widget_hierarchy(child)
    return hierarchy

def print_hierarchy(hierarchy, level=0):
    #Prints the widget hierarchy in a readable format
    #Mainly for debugging
    for widget, children in hierarchy.items():
        print("  " * level + f"{widget.winfo_class()} - {widget.winfo_name()}")
        print_hierarchy(children, level + 1)

def remove_widgets_from_frame(frame, widget_classes=None, widget_names=None):
    for child in frame.winfo_children():
        if (widget_classes and child.winfo_class() in widget_classes) or \
           (widget_names and child.winfo_name() in widget_names):
            child.destroy()


class HelpIndicator(tkinter.Canvas):
    def __init__(self, parent, text, icon_text="?"):
        super().__init__(parent, width=33, height=33, bg='darkgrey')
        self.create_oval(10, 10, 30, 30, fill="lightblue")
        self.create_text(20, 20, text=icon_text, font=("arial", 8, "bold"))
        ToolTip(self, text)

class Combobox(ttk.Combobox):
    elements = []
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.elements.append(self)

    def destroy(self, *args, **kwargs):
        super().destroy(*args, **kwargs)
        self.elements.remove(self)
