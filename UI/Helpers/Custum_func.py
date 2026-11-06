# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\Custum_func.py

import tkinter as tk

GUI, MUI, HNH, CBR     = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, SK, BD = "groove", "solid", "ridge", "raised", "sunken", "bold"
ALL, CT                = "nsew", "center"
MAIN_BG  = "#F0F4FA"

# カスタム短縮表記 Frame -----------------------------------
class cFr(tk.Frame):
    def __init__( self, master=None, *, W=None, H=None, Rel=None, Bd=None, bg=None,
                                   hlbg=None, hlth=None, px=None, py=None, **kwargs ):

        if W    is not None: kwargs['width']               = W
        if H    is not None: kwargs['height']              = H
        if Rel  is not None: kwargs['relief']              = Rel
        if Bd   is not None: kwargs['bd']                  = Bd[0] ;kwargs['relief'] = Bd[1]
        if hlbg is not None: kwargs['highlightbackground'] = hlbg
        if hlth is not None: kwargs['highlightthickness']  = hlth
        if px   is not None: kwargs['padx']                = px
        if py   is not None: kwargs['pady']                = py

        kwargs['background'] = bg if bg else MAIN_BG

        super().__init__(master, **kwargs)

    # ------------------------
    def Pgate(self):

        self.grid_propagate(False)
    # ------------------------
    def Cconf(self, col, W=None, Min=None, **kwargs):

        if W   is not None: kwargs['weight']  = W
        if Min is not None: kwargs['minsize'] = Min

        self.grid_columnconfigure(col, **kwargs)

    # ------------------------
    def Rconf(self, row, W=None, Min=None, **kwargs):

        if W   is not None: kwargs['weight']  = W
        if Min is not None: kwargs['minsize'] = Min

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
        self.grid_propagate(False)

    # ------------------------
    def _pack(self, Anc=None, Exp=None, px=None, py=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if Anc is not None: kwargs['anchor'] = Anc
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)
        #self.pack_propagate(False)

    # ------------------------
    def _config(self, Anc=None, W=None, H=None, Bd=None, Rel=None,px=None, py=None, **kwargs):

        if W    is not None: kwargs['width']               = W
        if H    is not None: kwargs['height']              = H
        if Anc  is not None: kwargs['anchor']              = Anc
        if Bd   is not None: kwargs['bd']                  = Bd[0] ;kwargs['relief'] = Bd[1]
        if Rel  is not None: kwargs['relief']              = Rel
        if px   is not None: kwargs['padx']                = px
        if py   is not None: kwargs['pady']                = py

        self.configure(**kwargs)

# カスタム短縮表記 Text ------------------------------------
class cTxt(tk.Text):
    def __init__( self, master=None, *, W=None, H=None, Txt=None, Jst=None, Bd=None, Rel=None,
                  Wrap=None, Img=None, Csr=None, HLbg=None, HLth=None, px=None, py=None,
                  bg=None, Sp1=2, Sp2=6, **kwargs ):

        if W    is not None: kwargs['width']               = W
        if H    is not None: kwargs['height']              = H
        if Bd   is not None: kwargs['bd']                  = Bd[0] ;kwargs['relief'] = Bd[1]
        if Rel  is not None: kwargs['relief']              = Rel
        if Csr  is not None: kwargs['cursor']              = Csr
        if HLbg is not None: kwargs['highlightbackground'] = HLbg
        if HLth is not None: kwargs['highlightthickness']  = HLth
        if px   is not None: kwargs['padx']                = px
        if py   is not None: kwargs['pady']                = py

        kwargs['spacing1']   = Sp1
        kwargs['spacing2']   = Sp2
        kwargs['background'] = bg if bg else (master["bg"] if master else MAIN_BG)
        kwargs['wrap']       = Wrap if Wrap else tk.WORD

        super().__init__(master, **kwargs)

        if Jst is not None:
            self.tag_config("custom_alignment", justify=Jst)
        if Img is not None:
            self.image_create(tk.END, image=Img)
        if Txt is not None:
            tag = "custom_alignment" if Jst is not None else ""
            self.insert(tk.END, Txt, tag)

    # ------------------------
    def Pgate(self):

        self.grid_propagate(False)

    # ------------------------
    def Cconf(self, col, W=None, Min=None, **kwargs):

        if W   is not None: kwargs['weight']  = W
        if min is not None: kwargs['minsize'] = Min

        self.grid_columnconfigure(col, **kwargs)

    # ------------------------
    def Rconf(self, row, W=None, Min=None, **kwargs):

        if W   is not None: kwargs['weight']  = W
        if min is not None: kwargs['minsize'] = Min

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
    def _pack(self, Anc=None, Exp=None, px=None, py=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if Anc is not None: kwargs['anchor'] = Anc
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)

    # ------------------------
    def _config( self, W=None, H=None, Bd=None, Rel=None, Jst=None, Wrap=tk.WORD,
                 Txt=None, Img=None, Csr=None, HLbg=None, HLth=None, px=None, py=None, **kwargs ):

        if W    is not None: kwargs['width']               = W
        if H    is not None: kwargs['height']              = H
        if Bd   is not None: kwargs['bd']                  = Bd
        if Rel  is not None: kwargs['relief']              = Rel
        if Csr  is not None: kwargs['cursor']              = Csr
        if HLbg is not None: kwargs['highlightbackground'] = HLbg
        if HLth is not None: kwargs['highlightthickness']  = HLth
        if px   is not None: kwargs['padx']                = px
        if py   is not None: kwargs['pady']                = py
        if Wrap is not None: kwargs['wrap']                = Wrap 

        if (Txt is not None) or (Img is not None) or (Jst is not None):
            self.configure(state=tk.NORMAL)
            if (Txt is not None) or (Img is not None):
                self.delete("1.0", tk.END)
            tag = ""
            if Jst is not None:
                self.tag_config("custom_alignment", justify=Jst)
                tag = "custom_alignment"
            if Img is not None:
                self.image_create(tk.END, image=Img)
            if Txt is not None:
                self.insert(tk.END, Txt, tag)

            #self.configure(state=tk.DISABLED)
        if kwargs:
            self.configure(**kwargs)

# カスタム短縮表記 Label -----------------------------------
class cLbl(tk.Label):
    def __init__( self, master=None, *, W=None, H=None, Anc=None, Jst=None, Bd=None, Rel=None,
                  Wrap=None, Txtv=None, Img=None, Csr=None, HLbg=None, HLth=None, px=None, py=None,
                  bg=None, **kwargs ):

        if W    is not None: kwargs['width']               = W
        if H    is not None: kwargs['height']              = H
        if Anc  is not None: kwargs['anchor']              = Anc
        if Jst  is not None: kwargs['justify']             = Jst
        if Bd   is not None: kwargs['bd']                  = Bd[0] ;kwargs['relief'] = Bd[1]
        if Rel  is not None: kwargs['relief']              = Rel
        if Wrap is not None: kwargs['wraplength']          = Wrap
        if Txtv is not None: kwargs['textvariable']        = Txtv
        if Img  is not None: kwargs['image']               = Img
        if Csr  is not None: kwargs['cursor']              = Csr
        if HLbg is not None: kwargs['highlightbackground'] = HLbg
        if HLth is not None: kwargs['highlightthickness']  = HLth
        if px   is not None: kwargs['padx']                = px
        if py   is not None: kwargs['pady']                = py

        kwargs['background'] = bg if bg else (master["bg"] if master else MAIN_BG)

        super().__init__(master, **kwargs)

    # ------------------------
    def Pgate(self):

        self.grid_propagate(False)

    # ------------------------
    def Cconf(self, col, W=None, Min=None, **kwargs):

        if W   is not None: kwargs['weight']  = W
        if min is not None: kwargs['minsize'] = Min

        self.grid_columnconfigure(col, **kwargs)

    # ------------------------
    def Rconf(self, row, W=None, Min=None, **kwargs):

        if W   is not None: kwargs['weight']  = W
        if min is not None: kwargs['minsize'] = Min

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
        self.grid_propagate(False)

    # ------------------------
    def _pack(self, Anc=None, Exp=None, px=None, py=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if Anc is not None: kwargs['anchor'] = Anc
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)

    # ------------------------
    def _config( self, Anc=None, W=None, H=None, Bd=None, Rel=None, Jst=None, Wrap=None,
                 Txtv=None, Img=None, Csr=None, HLbg=None, HLth=None, px=None, py=None, **kwargs ):

        if W    is not None: kwargs['width']               = W
        if H    is not None: kwargs['height']              = H
        if Anc  is not None: kwargs['anchor']              = Anc
        if Bd   is not None: kwargs['bd']                  = Bd[0] ;kwargs['relief'] = Bd[1]
        if Rel  is not None: kwargs['relief']              = Rel
        if Jst  is not None: kwargs['justify']             = Jst
        if Wrap is not None: kwargs['wraplength']          = Wrap
        if Txtv is not None: kwargs['textvariable']        = Txtv
        if Img  is not None: kwargs['image']               = Img
        if Csr  is not None: kwargs['cursor']              = Csr
        if HLbg is not None: kwargs['highlightbackground'] = hlbg
        if HLth is not None: kwargs['highlightthickness']  = hlth
        if px   is not None: kwargs['padx']                = px
        if py   is not None: kwargs['pady']                = py
        if Wrap is not None: kwargs['wraplength']          = Wrap

        self.configure(**kwargs)

# カスタム短縮表記 Button ----------------------------------
class cBtn(tk.Button):
    def __init__(self, master=None, *, W=None, H=None, Anc=None, Jst=None, Bd=None, Rel=None,
                                   Img=None, Com=None, Csr=None,  px=None, py=None, **kwargs ):

        if W   is not None: kwargs['width']      = W
        if H   is not None: kwargs['height']     = H
        if Anc is not None: kwargs['anchor']     = Anc
        if Jst is not None: kwargs['justify']    = Jst
        if Bd  is not None: kwargs['bd']         = Bd[0] ;kwargs['relief'] = Bd[1]
        if Rel is not None: kwargs['relief']     = Rel
        if Img is not None: kwargs['image']      = Img
        if Com is not None: kwargs['command']    = Com
        if Csr is not None: kwargs['cursor']     = Csr
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
        self.grid_propagate(False)

    # ------------------------
    def _pack(self, Anc=None, Exp=None, px=None, py=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if Anc is not None: kwargs['anchor'] = Anc
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)

    # ------------------------
    def _config(self, Anc=None, W=None, H=None, Bd=None, Rel=None, Jst=None, Wrap=None,
                Img=None, Com=None, Csr=None, HLbg=None, HLth=None, px=None, py=None, **kwargs ):

        if W    is not None: kwargs['width']               = W
        if H    is not None: kwargs['height']              = H
        if Anc  is not None: kwargs['anchor']              = Anc
        if Bd   is not None: kwargs['bd']                  = Bd[0] ;kwargs['relief'] = Bd[1]
        if Rel  is not None: kwargs['relief']              = Rel
        if Jst  is not None: kwargs['justify']             = Jst
        if Wrap is not None: kwargs['wraplength']          = Wrap
        if Img  is not None: kwargs['image']               = Img
        if Com  is not None: kwargs['command']             = Com
        if Csr  is not None: kwargs['cursor']              = Csr
        if HLbg is not None: kwargs['highlightbackground'] = hlbg
        if HLth is not None: kwargs['highlightthickness']  = hlth
        if px   is not None: kwargs['padx']                = px
        if py   is not None: kwargs['pady']                = py

        self.configure(**kwargs)

# カスタム短縮表記 キャンバス ------------------------------
class cCvs(tk.Canvas):
    def __init__( self, master=None, *, W=None, H=None, Rel=None, Bd=None, bg=None, HLth=None,
                  **kwargs ):

        if W    is not None: kwargs['width']              = W
        if H    is not None: kwargs['height']             = H
        if Rel  is not None: kwargs['relief']             = Rel
        if Bd   is not None: kwargs['borderwidth']        = Bd[0] ;kwargs['relief'] = Bd[1]
        if bg   is not None: kwargs['background']         = bg
        if HLth is not None: kwargs['highlightthickness'] = HLth

        super().__init__(master, **kwargs)

    def _crtxt(self, x, y, *, W=None, Anc=None, Jst=None, **kwargs):

        if W   is not None: kwargs['width']   = W
        if Anc is not None: kwargs['anchor']  = Anc
        if Jst is not None: kwargs['justify'] = Jst

        self.create_text(x, y, **kwargs)

    # ------------------------
    def _itmconf( self, master=None, *, W=None, H=None, Rel=None, Bd=None, bg=None, HLth=None,
                   **kwargs):

        if W    is not None: kwargs['width']              = W
        if H    is not None: kwargs['height']             = H
        if Rel  is not None: kwargs['relief']             = Rel
        if Bd   is not None: kwargs['borderwidth']        = Bd[0] ;kwargs['relief'] = Bd[1]
        if bg   is not None: kwargs['background']         = bg
        if HLth is not None: kwargs['highlightthickness'] = HLth

        self.itemconfigure(**kwargs)

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
        self.grid_propagate(False)

    # ------------------------
    def _pack(self, Anc=None, Exp=None, px=None, py=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if Anc is not None: kwargs['anchor'] = Anc
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)

    def _config(self, W=None, H=None, Bd=None, Rel=None, Csr=None, HLbg=None, HLth=None,
                      Scrgn=None, YscrCom=None, **kwargs ):

        if W       is not None: kwargs['width']               = W
        if H       is not None: kwargs['height']              = H
        if Bd      is not None: kwargs['bd']                  = Bd[0] ;kwargs['relief'] = Bd[1]
        if Rel     is not None: kwargs['relief']              = Rel
        if Csr     is not None: kwargs['cursor']              = Csr
        if HLth    is not None: kwargs['highlightthickness']  = hlth
        if Scrgn   is not None: kwargs['scrollregion']        = Scrgn
        if YscrCom is not None: kwargs['yscrollcommand']      = YscrCom

        self.configure(**kwargs)

# カスタム短縮表記 テキストボックス ------------------------
class cEnt(tk.Entry):
    def __init__( self, master=None, *, W=None, H=None, Com=None, Bd=None, Rel=None, Jst=None,
                                                                           Txtv=None, **kwargs ):
        if W    is not None: kwargs['width']        = W
        if H    is not None: kwargs['height']       = H
        if Com  is not None: kwargs['command']      = Com
        if Bd   is not None: kwargs['bd']           = Bd[0] ;kwargs['relief'] = Bd[1]
        if Rel  is not None: kwargs['relief']       = Rel
        if Jst  is not None: kwargs['justify']      = Jst
        if Txtv is not None: kwargs['textvariable'] = Txtv

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
    def _pack(self, Anc=None, Exp=None, px=None, py=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if Anc is not None: kwargs['anchor'] = Anc
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)

# カスタム短縮表記 スクロールバー --------------------------
class cSrb(tk.Scrollbar):
    def __init__(self, master=None, *, Com=None, **kwargs):

        if Com is not None: kwargs['command'] = Com

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
        self.grid_propagate(False)

    # ------------------------
    def _pack(self, Anc=None, Exp=None, px=None, py=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if Anc is not None: kwargs['anchor'] = Anc
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)

# カスタム短縮表記 SpinBox ---------------------------------
class cSpbx(tk.Spinbox):
    def __init__( self, master=None, *, W=None, Frm=None, To=None, Inc=None, Val=None, Txtv=None,
                                                                        Jst=None, **kwargs ):

        if W    is not None: kwargs['width']        = W
        if Frm  is not None: kwargs['from_']        = Frm
        if To   is not None: kwargs['to']           = To
        if Inc  is not None: kwargs['increment']    = Inc
        if Val  is not None: kwargs['values']       = Val
        if Jst  is not None: kwargs['justify']      = Jst
        if Txtv is not None: kwargs['textvariable'] = Txtv

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
    def _pack(self, Anc=None, Exp=None, px=None, py=None, **kwargs):

        if Exp is not None: kwargs['expand'] = Exp
        if Anc is not None: kwargs['anchor'] = Anc
        if px  is not None: kwargs['padx']   = px
        if py  is not None: kwargs['pady']   = py

        self.pack(**kwargs)
