import tkinter as tk
from Custum_func  import cFr, cLbl, cBtn, cCvs


GUI, MUI, HNH, CBR = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, SK = "groove", "solid", "ridge", "raised", "sunken"
ALL, CT ,BD        = "nsew", "center", "bold"

#===================================================================
class RichColorPickerPanel(tk.Frame):
  def __init__(self, parent, title, color_obj, width=300, height=300):
    super().__init__(parent, bd=2, relief="groove", padx=8, pady=8)

    self.title      = title
    self.color_obj  = color_obj
    self.pal_w      = width
    self.pal_h      = height
    self.slider_val = 0.0
    self.cursor_x   = int(width * 0.8)
    self.cursor_y   = int(height * 0.2)

    self._create_widgets()
    self._update_all()

  #---------------------------
  def _create_widgets(self):

    tk.Label(self, text=self.title, font=("Arial",10,BD)).pack(anchor=tk.W, pady=(0, 4))

    self.slider_canvas = tk.Canvas(self, width=self.pal_w, height=16, highlightthickness=0)
    self.slider_canvas.pack(pady=(0, 6))
    self._draw_slider_bar()

    self.slider_canvas.bind("<Button-1>",  self._on_slider_click)
    self.slider_canvas.bind("<B1-Motion>", self._on_slider_click)

    self.pal_canvas = tk.Canvas( self, width=self.pal_w, height=self.pal_h,
                                       highlightthickness=1, relief="solid" )
    self.pal_canvas.pack(pady=(0,6))

    self.pal_image = tk.PhotoImage(width=self.pal_w, height=self.pal_h)
    self.pal_canvas.create_image(0, 0, image=self.pal_image, anchor=tk.NW)

    self.cursor_id       = self.pal_canvas.create_oval(0, 0, 0, 0, outline="black", width=4)
    self.cursor_inner_id = self.pal_canvas.create_oval(0, 0, 0, 0, outline="white", width=2)

    self.pal_canvas.bind("<Button-1>",  self._on_palette_click)
    self.pal_canvas.bind("<B1-Motion>", self._on_palette_click)

    hex_frame = tk.Frame(self)
    hex_frame.pack(fill=tk.X, pady=(0,2))

    tk.Label(hex_frame, text="HEX:", font=("Arial",9,"bold")).pack(side=tk.LEFT)
    self.hex_var   = tk.StringVar(value=self.color_obj.get())
    self.hex_label = tk.Label(hex_frame, textvariable=self.hex_var, font=("Arial",9,BD), width=8)
    self.hex_label.pack(side=tk.LEFT, padx=2)

    tk.Button( hex_frame, text="コピー", command=self._copy_to_clipboard, width=5, font=("Arial",8),
              ).pack(side=tk.RIGHT)

  #---------------------------
  def _get_slider_color(self, t):

    t       = max(0.0, min(1.0, t))
    section = t * 6.0
    i       = int(section)
    f       = section -i

    if i >= 6:
      return (255, 0, 0)

    if   i == 0: return (    255,          int(255 *f),            0         )
    elif i == 1: return (int(255 *(1 -f)),     255,                0         )
    elif i == 2: return (      0,              255,          int(255 *f)     )
    elif i == 3: return (      0,          int(255 *(1 -f)),     255         )
    elif i == 4: return (int(255 *f),            0,              255         )
    else:        return (    255,                0,          int(255 *(1 -f)))

  #---------------------------
  def _draw_slider_bar(self):

    self.slider_canvas.delete("all")
    w = self.pal_w
    h = 16

    for x in range(w):
      t = x / (w -1) if w > 1 else 0
      r, g, b = self._get_slider_color(t)
      self.slider_canvas.create_line(x, 0, x, h, fill=f"#{r:02x}{g:02x}{b:02x}")

    sx = int(self.slider_val * (w -1))
    self.slider_canvas.create_rectangle(sx -2,  0, sx +2, h,     outline="white", width=4)
    self.slider_canvas.create_rectangle(sx -3, -1, sx +3, h +1, outline="black", width=2)

  #---------------------------
  def _update_palette_image(self):

    br, bg, bb = self._get_slider_color(self.slider_val)
    w          = self.pal_w
    h          = self.pal_h
    data_rows  = []

    for y in range(h):
      fy = y / (h - 1) if h > 1 else 0
      row_colors = []

      for x in range(w):
        fx    = x / (w - 1) if w > 1 else 0
        top_r = 255 * (1 - fx) + br * fx
        top_g = 255 * (1 - fx) + bg * fx
        top_b = 255 * (1 - fx) + bb * fx
        r     = int((1 - fy) * top_r)
        g     = int((1 - fy) * top_g)
        b     = int((1 - fy) * top_b)

        row_colors.append(f"#{r:02x}{g:02x}{b:02x}")

      data_rows.append("{" + " ".join(row_colors) + "}")

    self.pal_image.put(" ".join(data_rows), to=(0, 0, w, h))

  #---------------------------
  def _update_cursor_pos(self):

    cx = self.cursor_x
    cy = self.cursor_y
    r  = 5

    self.pal_canvas.coords(self.cursor_id, cx - r, cy - r, cx + r, cy + r)
    self.pal_canvas.coords(self.cursor_inner_id, cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1)

    fx = cx / (self.pal_w - 1) if self.pal_w > 1 else 0
    fy = cy / (self.pal_h - 1) if self.pal_h > 1 else 0

    br, bg, bb = self._get_slider_color(self.slider_val)
    top_r      = 255 *(1 -fx) +br *fx
    top_g      = 255 *(1 -fx) +bg *fx
    top_b      = 255 *(1 -fx) +bb *fx
    r          = int((1 -fy) *top_r)
    g          = int((1 -fy) *top_g)
    b          = int((1 -fy) *top_b)
    hex_code   = f"#{r:02x}{g:02x}{b:02x}".upper()

    self.hex_var.set(hex_code)
    self.color_obj.set(hex_code)

  #---------------------------
  def _on_slider_click(self, event):

    w                = self.pal_w
    x               = max(0, min(event.x, w -1))
    self.slider_val = x / (w -1) if w > 1 else 0

    self._draw_slider_bar()
    self._update_palette_image()
    self._update_cursor_pos()

  #---------------------------
  def _on_palette_click(self, event):
    self.cursor_x = max(0, min(event.x, self.pal_w -1))
    self.cursor_y = max(0, min(event.y, self.pal_h -1))
    self._update_cursor_pos()
  #---------------------------
  def _update_all(self):
    self._draw_slider_bar()
    self._update_palette_image()
    self._update_cursor_pos()
  #---------------------------
  def _copy_to_clipboard(self):
    self.clipboard_clear()
    self.clipboard_append(self.hex_var.get())

#===================================================================
class MultiColorPickerWindow(tk.Toplevel):
  def __init__(self, master, color_items):
    super().__init__(master)

    self.title("16進数カラーピッカー")
    self.geometry("700x420+1200+200")
    self.resizable(False, False)
    self.color_items = color_items
    self.protocol("WM_DELETE_WINDOW", self.on_close)

    main_frame = tk.Frame(self)
    main_frame.pack(padx=10, pady=10)

    for title, color_obj in color_items:
      panel = RichColorPickerPanel(main_frame, title, color_obj)
      panel.pack(side=tk.LEFT, padx=5)
  #---------------------------
  def on_close(self):
    for _, color_obj in self.color_items:
      color_obj.picker_window = None
    self.destroy()

#===================================================================
class MyColor(tk.StringVar):

  _shared_window = None
  #---------------------------
  def __init__(self, default_hex="#FFFFFF"):
    super().__init__(value=default_hex)

    self.bound_widgets = []
    self.trace_add("write", self._auto_update_widgets)
  #---------------------------
  def __str__(self):
    return self.get()
  #---------------------------
  def bind_widget(self, widget, attribute="bg"):
    self.bound_widgets.append((widget, attribute))
  #---------------------------
  def _auto_update_widgets(self, *args):

    current_color = self.get()
    for widget, attr in self.bound_widgets:
      try:
        if widget.winfo_exists():
          widget.config(**{attr: current_color})
      except Exception:
        pass
  #---------------------------
  @classmethod
  def activate_all(cls, master, color_items_dict):
    if cls._shared_window is not None and cls._shared_window.winfo_exists():
      cls._shared_window.lift()
      return

    items = list(color_items_dict.items())
    window = MultiColorPickerWindow(master, items)
    cls._shared_window = window
    #-------------------------
    def cleanup(event):
      if cls._shared_window == window:
        cls._shared_window = None
    #-------------------------
    window.bind("<Destroy>", cleanup)

#===================================================================
