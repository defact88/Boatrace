
import argparse, threading, sys, sqlite3, json
import tkinter as tk

from datetime                 import date, datetime as dt
from Custum_func              import cFr, cLbl, cBtn, cCvs

MAIN_BG = "#F0F4FA"

#=====================================================================
class PlayerFavorWindow(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

