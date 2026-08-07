# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\Custum_func.py

from tkinter import ttk
import tkinter as tk

# カスタム短縮表記フレーム(tk) -----------------------------
class cFr(tk.Frame):
    def __init__(self, master=None, Rel=None, W=None, H=None, Bd=None, bg=None, px=None, py=None,
                   **kwargs):

        if W   is not None: kwargs['width']      = W
        if H   is not None: kwargs['height']     = H
        if Rel is not None: kwargs['relief']     = Rel
        if Bd  is not None: kwargs['bd']         = Bd[0]; kwargs['relief'] = Bd[1]
        if bg  is not None: kwargs['background'] = bg
        if px  is not None: kwargs['padx']       = px
        if py  is not None: kwargs['pady']       = py

        super().__init__(master, **kwargs)

    def Pgate(self):
        self.grid_propagate(False)
    # ------------------------
    def Cconf(self, col, W=None, **kwargs):
       
        if W is not None: kwargs['weight'] =W

        self.grid_columnconfigure(col, **kwargs)
    # ------------------------
    def Rconf(self, row, W=None, **kwargs):
       
        if W is not None: kwargs['weight'] =W

        self.grid_rowconfigure(row, **kwargs)
    # ------------------------
    def _grid(self, R=None, C=None, Cspan=None, Rspan=None, Stk=None, px=None, py=None, **kwargs):

        if R     is not None: kwargs['row']        = R
        if C     is not None: kwargs['column']     = C
        if Cspan is not None: kwargs['columnspan'] = Cspan
        if Rspan is not None: kwargs['rowspan']    = Rspan
        if Stk   is not None: kwargs['sticky']     = Stk
        if px    is not None: kwargs['padx']       = px
        if py    is not None: kwargs['pady']       = py

        self.grid(**kwargs)
    # ------------------------
    def _pack(self, Exp=None, px=None, py=None, Anc=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if Anc is not None: kwargs['anchor'] = Anc
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)

# カスタム短縮表記フレーム(ttk) ----------------------------
class ttFr(ttk.Frame):
    def __init__(self, master=None, Rel=None, W=None, H=None, BD=None, px=None, py=None, **kwargs):

        if W   is not None: kwargs['width']       = W
        if H   is not None: kwargs['height']      = H
        if Rel is not None: kwargs['relief']      = Rel
        if BD  is not None: kwargs['borderwidth'] = BD
        if px  is not None: kwargs['padx']        = px
        if py  is not None: kwargs['pady']        = py

        super().__init__(master, **kwargs)

    def Pgate(self):
        self.grid_propagate(False)
    # ------------------------
    def Cconf(self, col, W=None, **kwargs):
       
        if W is not None: kwargs['weight'] =W

        self.grid_columnconfigure(col, **kwargs)
    # ------------------------
    def Rconf(self, row, W=None, **kwargs):
       
        if W is not None: kwargs['weight'] =W

        self.grid_rowconfigure(row, **kwargs)
    # ------------------------
    def _grid(self, R=None, C=None, Cspan=None, Rspan=None, Stk=None, px=None, py=None, **kwargs):

        if R     is not None: kwargs['row']        = R
        if C     is not None: kwargs['column']     = C
        if Cspan is not None: kwargs['columnspan'] = Cspan
        if Rspan is not None: kwargs['rowspan']    = Rspan
        if Stk   is not None: kwargs['sticky']     = Stk
        if px    is not None: kwargs['padx']       = px
        if py    is not None: kwargs['pady']       = py

        self.grid(**kwargs)
    # ------------------------
    def _pack(self, Exp=None, px=None, py=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if Anc is not None: kwargs['anchor'] = Anc
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)

# カスタム短縮表記ラベル -----------------------------------
class cLbl(tk.Label):  
    def __init__(self, master=None, Anc=None, W=None, H=None, Bd=None, Rel=None, px=None, py=None,
                                                bg=None, **kwargs ):
        if W   is not None: kwargs['width']      = W
        if H   is not None: kwargs['height']     = H
        if Anc is not None: kwargs['anchor']     = Anc
        if Bd  is not None: kwargs['bd']         = Bd[0]; kwargs['relief'] = Bd[1]
        if Rel is not None: kwargs['relief']     = Rel
        if bg  is not None: kwargs['background'] = bg
        if px  is not None: kwargs['padx']       = px
        if py  is not None: kwargs['pady']       = py

        super().__init__(master, **kwargs)

    def Pgate(self):
        self.grid_propagate(False)
    # ------------------------
    def Cconf(self, col, W=None, **kwargs):
       
        if W is not None: kwargs['weight'] =W

        self.grid_columnconfigure(col, **kwargs)
    # ------------------------
    def Rconf(self, row, W=None, **kwargs):
       
        if W is not None: kwargs['weight'] =W

        self.grid_rowconfigure(row, **kwargs)
    # ------------------------
    def _grid(self, R=None, C=None, Cspan=None, Rspan=None, Stk=None, px=None, py=None, **kwargs):

        if R     is not None: kwargs['row']        = R
        if C     is not None: kwargs['column']     = C
        if Cspan is not None: kwargs['columnspan'] = Cspan
        if Rspan is not None: kwargs['rowspan']    = Rspan
        if Stk   is not None: kwargs['sticky']     = Stk
        if px    is not None: kwargs['padx']       = px
        if py    is not None: kwargs['pady']       = py

        self.grid(**kwargs)
    # ------------------------
    def _pack(self, Exp=None, px=None, py=None, Anc=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py
        if Anc is not None: kwargs['anchor'] = Anc

        self.pack(**kwargs)

# カスタム短縮表記テキストボックス -------------------------
class cEnt(tk.Entry):  
    def __init__(self, master=None, W=None, Com=None, Bd=None, Rel=None, Jst=None,
                                                                          **kwargs ):
        if W   is not None: kwargs['width']      = W
        if Com is not None: kwargs['command']    = Com
        if Bd  is not None: kwargs['bd']         = Bd[0]; kwargs['relief'] = Bd[1]
        if Rel is not None: kwargs['relief']     = Rel
        if Jst is not None: kwargs['justify']    = Jst

        super().__init__(master, **kwargs)
    # ------------------------
    def _grid(self, R=None, C=None, Cspan=None, Rspan=None, Stk=None, px=None, py=None, **kwargs):

        if R     is not None: kwargs['row']        = R
        if C     is not None: kwargs['column']     = C
        if Cspan is not None: kwargs['columnspan'] = Cspan
        if Rspan is not None: kwargs['rowspan']    = Rspan
        if Stk   is not None: kwargs['sticky']     = Stk
        if px    is not None: kwargs['padx']       = px
        if py    is not None: kwargs['pady']       = py

        self.grid(**kwargs)
    # ------------------------
    def _pack(self, Exp=None, px=None, py=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)
# カスタム短縮表記tkボタン ---------------------------------
class cBtn(tk.Button):  
    def __init__(self, master=None, W=None, H=None, Anc=None, Bd=None, Rel=None, bg=None,
                                          Img=None,  px=None, py=None, Com=None, **kwargs ):
        if W   is not None: kwargs['width']      = W
        if H   is not None: kwargs['height']     = H
        if Anc is not None: kwargs['anchor']     = Anc
        if Bd  is not None: kwargs['bd']         = Bd[0]; kwargs['relief'] = Bd[1]
        if Rel is not None: kwargs['relief']     = Rel
        if bg  is not None: kwargs['background'] = bg
        if Img is not None: kwargs['image']      = Img
        if Com is not None: kwargs['command']    = Com
        if px  is not None: kwargs['padx']       = px
        if py  is not None: kwargs['pady']       = py

        super().__init__(master, **kwargs)
    # ------------------------
    def _grid(self, R=None, C=None, Cspan=None, Rspan=None, Stk=None, px=None, py=None, **kwargs):

        if R     is not None: kwargs['row']        = R
        if C     is not None: kwargs['column']     = C
        if Cspan is not None: kwargs['columnspan'] = Cspan
        if Rspan is not None: kwargs['rowspan']    = Rspan
        if Stk   is not None: kwargs['sticky']     = Stk
        if px    is not None: kwargs['padx']       = px
        if py    is not None: kwargs['pady']       = py

        self.grid(**kwargs)
    # ------------------------
    def _pack(self, Exp=None, px=None, py=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)
# カスタム短縮表記tkキャンバス------------------------------
class cCvs(tk.Canvas):
    def __init__(self, master=None, W=None, H=None, Rel=None, Bd=None, bg=None, Htt=None,
                   **kwargs):

        if W   is not None: kwargs['width']              = W
        if H   is not None: kwargs['height']             = H
        if Rel is not None: kwargs['relief']             = Rel
        if Bd  is not None: kwargs['borderwidth']        = Bd[0]; kwargs['relief'] = Bd[1]
        if bg  is not None: kwargs['background']         = bg
        if Htt is not None: kwargs['highlightthickness'] = Htt

        super().__init__(master, **kwargs)
    # ------------------------
    def _grid(self, R=None, C=None, Cspan=None, Rspan=None, Stk=None, **kwargs):

        if R     is not None: kwargs['row']        = R
        if C     is not None: kwargs['column']     = C
        if Cspan is not None: kwargs['columnspan'] = Cspan
        if Rspan is not None: kwargs['rowspan']    = Rspan
        if Stk   is not None: kwargs['sticky']     = Stk
        if px    is not None: kwargs['padx']       = px
        if py    is not None: kwargs['pady']       = py

        self.grid(**kwargs)
    # ------------------------
    def _pack(self, Exp=None, px=None, py=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)