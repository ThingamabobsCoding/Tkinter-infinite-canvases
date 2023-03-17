import tkinter as tk

class InfiniteCanvas(tk.Canvas):
    '''
    Initial idea by Nordine Lofti
    https://stackoverflow.com/users/12349101/nordine-lotfi
    written by Thingamabobs
    https://stackoverflow.com/users/13629335/thingamabobs
    with additional ideas by patrik-gustavsson
    https://stackoverflow.com/users/4332183/patrik-gustavsson

    The infinite canvas allows you to have infinite space to draw.
    A new standard tag is introduced to the Canvas named "inview".
    -> All visible items will have the tag "inview"

    ALL BINDINGS ARE JUST AVAILABLE WHEN CANVAS HAS FOCUS!
    FOCUS IS GIVEN WHEN YOU LEFT CLICK ONTO THE CANVAS!
    
    You can move around the world as follows:
    - MouseWheel for Y movement.
    - Shift-MouseWheel will perform X movement.
    - Alt-Button-1-Motion will perform X and Y movement.
    (pressing ctrl while moving will invoke a multiplier)
    
    You can zoom in and out with:
    - Alt-MouseWheel
    (pressing ctrl will invoke a multiplier)

    Additional features to the standard tk.Canvas:
    - Keeps track of the viewable area
    --> Acess via InfiniteCanvas().viewing_box()
    - Keeps track of the visibile items
    --> Acess via InfiniteCanvas().inview()
    - Keeps track of the NOT visibile items
    --> Acess via InfiniteCanvas().outofview()


    Notification bindings:
    
    "<<ItemsDropped>>" = dropped items stored in self.dropped
    "<<ItemsEntered>>" = entered items stored in self.entered
    "<<VerticalScroll>>"
    "<<HorizontalScroll>>"
    "<<Zoom>>"
    "<<DragView>>"
    "<<Scroll>>"
    "<<ViewConfigure>>"
    '''

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._xshifted  = 0             #view moved in x direction
        self._yshifted  = 0             #view moved in y direction
        self._use_multi = False         #Multiplier for View-manipulation
        self.configure(confine=False)   #confine=False ignores scrollregion
        self.dropped    = set()         #storage
        self.entered    = set()         #storage
        #NotificationBindings
        self.event_add('<<VerticalScroll>>',    '<MouseWheel>')
        self.event_add('<<HorizontalScroll>>',  '<Shift-MouseWheel>')
        self.event_add('<<DragView>>',          '<Alt-B1-Motion>')
        self.event_generate('<<Scroll>>')    
        self.event_add('<<Zoom>>',              '<Alt-MouseWheel>')
        self.event_generate('<<ViewConfigure>>')
##        self.bind('<<Scroll>>', lambda e:print(e))
        self.bind(#MouseWheel
            '<<VerticalScroll>>',   lambda e:self._wheel_scroll(e,'y'))
        self.bind(#Shift+MouseWheel
            '<<HorizontalScroll>>', lambda e:self._wheel_scroll(e,'x'))
        self.bind(#Alt+MouseWheel
            '<<Zoom>>',             self._zoom)
        self.bind(#Alt+LeftClick+MouseMovement
            '<<DragView>>',         self._drag_scroll)
        self.event_generate('<<ItemsDropped>>') #invoked in _update_tags
        self.event_generate('<<ItemsEntered>>') #invoked in _update_tags
##        self.bind('<<ItemsDropped>>', lambda e:print('d',self.dropped))
##        self.bind('<<ItemsEntered>>', lambda e:print('e',self.entered))
        #Normal bindings
        self.bind(#left click
            '<ButtonPress-1>',          lambda e:e.widget.focus_set())
        self.bind(
            '<KeyPress-Alt_L>',         self._prepend_drag_scroll, add='+')
        self.bind(
            '<KeyRelease-Alt_L>',       self._prepend_drag_scroll, add='+')
        self.bind(
            '<KeyPress-Control_L>',     self._configure_multi)
        self.bind(
            '<KeyRelease-Control_L>',   self._configure_multi)
        return None

    def viewing_box(self) -> tuple:
        'Returns a tuple of the form x1,y1,x2,y2 represents visible area'
        off = (int(self.cget('highlightthickness'))
               +int(self.cget('borderwidth')))
        x1 = 0 - self._xshifted+off
        y1 = 0 - self._yshifted+off
        x2 = self.winfo_width()-self._xshifted-off-1
        y2 = self.winfo_height()-self._yshifted-off-1
        return x1,y1,x2,y2

    def inview(self) -> set:
        'Returns a set of identifiers that are currently viewed'
        return set(self.find_overlapping(*self.viewing_box()))

    def outofview(self) -> set:
        'Returns a set of identifiers that are currently NOT viewed'
        all_ = set(self.find_all())
        return all_ - self.inview()

    def _configure_multi(self, event):
        if (et:=event.type.name) == 'KeyPress':
            self._use_multi = True
        elif et == 'KeyRelease':
            self._use_multi = False
        
    def _zoom(self,event):
        if str(self.focus_get()) == str(self):
            x = canvas.canvasx(event.x)
            y = canvas.canvasy(event.y)
            multiplier = 1.005 if self._use_multi else 1.001
            factor = multiplier ** event.delta
            canvas.scale('all', x, y, factor, factor)
            self._update_tags()

    def _prepend_drag_scroll(self, event):
        if (et:=event.type.name) == 'KeyPress':
            self._recent_drag_point_x = event.x
            self._recent_drag_point_y = event.y
            self.scan_mark(event.x,event.y)
            self.configure(cursor='fleur')
        elif et == 'KeyRelease':
            self.configure(cursor='')
            self._recent_drag_point_x = None
            self._recent_drag_point_y = None

    def _update_tags(self):
        vbox = self.viewing_box()
        old = set(self.find_withtag('inview'))
        self.addtag_overlapping('inview',*vbox)
        inbox = set(self.find_overlapping(*vbox))
        witag = set(self.find_withtag('inview'))
        self.dropped = witag-inbox
        if self.dropped:
            [self.dtag(i, 'inview') for i in self.dropped]
            self.event_generate('<<ItemsDropped>>')
        new = set(self.find_withtag('inview'))
        self.entered = new-old
        if self.entered:
            self.event_generate('<<ItemsEntered>>')
        self.event_generate('<<ViewConfigure>>')
        
    def _create(self, *args):
        ident = super()._create(*args)
        self._update_tags()
        return ident

    def _wheel_scroll(self, event, xy):
        if str(self.focus_get()) == str(self):
            parsed = int(event.delta/120)
            amount = parsed*10 if self._use_multi else parsed
            cx,cy = self.winfo_rootx(), self.winfo_rooty()
            self.scan_mark(cx, cy)
            if xy == 'x': x,y = cx+amount, cy
            elif xy == 'y': x,y = cx, cy+amount
            name = f'_{xy}shifted'
            setattr(self,name, getattr(self,name)+amount)
            self.scan_dragto(x,y, gain=1)
            self.event_generate('<<Scroll>>')
            self._update_tags()

    def _drag_scroll(self,event):
        if str(self.focus_get()) == str(self):
            self._xshifted += event.x-self._recent_drag_point_x
            self._yshifted += event.y-self._recent_drag_point_y
            gain = 2 if self._use_multi else 1
            self.scan_dragto(event.x, event.y, gain=gain)
            self._recent_drag_point_x = event.x
            self._recent_drag_point_y = event.y
            self.scan_mark(event.x,event.y)
            self.event_generate('<<Scroll>>')
            self._update_tags()

class WrapperFrame(tk.Frame):

    def __init__(self, master, widget,
                 cornercolor='white', edgecolor='grey', **kwargs):
        super().__init__(master,bg='black')
        rim = 5
        self.child = widget
        if widget.master != master:
            self.destroy()
            raise RuntimeError(
                f'Parameter widget must be child of {master}')
        self.child.pack(
            in_=self, fill=tk.BOTH, expand=True, padx=rim, pady=rim)

        #https://stackoverflow.com/q/64066592/13629335
        blues = {'se' : (1,1),'ne' : (1,0),'nw' : (0,0),'sw' : (0,1)}
        grens = {'e' : (1,0.5), 'n' : (0.5,0), 'w' : (0,0.5), 's' : (0.5,1)}
        
        for idx,i in enumerate(['nw','n','ne','e','se','s','sw','w']):
            bg = edgecolor if (idx % 2) == 0 else cornercolor
            ref= tk.Label(self, bg=bg)
            kw = {}
            if idx in [0,2,4,6]:#nw,ne,se,sw
                kw.update({'height':rim,'width':rim,'anchor':i})
                if idx == 0: kw.update({'relx':0,'rely':0})
                if idx == 2: kw.update({'relx':1,'rely':0})
                if idx == 4: kw.update({'relx':1,'rely':1})
                if idx == 6: kw.update({'relx':0,'rely':1})
            elif idx in [1,5]:#n,s
                kw.update(
                    {'relx':0,'x':rim,'height':rim,
                     'relwidth':1,'width':-rim*2})
                if i == 'n': kw.update({'rely':0})
                elif i == 's': kw.update({'rely':1,'y':-rim})
            elif idx in [3,7]:#e,w
                kw.update(
                    {'rely':0,'y':rim,'width':rim,
                     'relheight':1,'height':-rim*2})
                if i == 'e': kw.update({'relx':1,'x':-rim})
                elif i == 'w': kw.update({'relx':0})
            ref.place(**kw)
            ref.bind("<B1-Motion>", lambda e, mode=i:self._resize(e,mode))
            ref.bind('<ButtonPress-1>', self.start_drag)
        self.child.tkraise()
        return None

    def start_drag(self,event):
        self.start_width = self.winfo_width()
        self.start_height= self.winfo_height()
        self.start_abs_x = self.winfo_pointerx() - self.winfo_rootx()
        self.start_abs_y = self.winfo_pointery() - self.winfo_rooty()

    def _resize(self,event, mode):
        abs_x = self.winfo_pointerx() - self.winfo_rootx()
        abs_y = self.winfo_pointery() - self.winfo_rooty()
        width = self.winfo_width()
        height= self.winfo_height()
        x = self.winfo_x()
        y = self.winfo_y()
        x_motion = self.start_abs_x - abs_x
        y_motion = self.start_abs_y - abs_y

        self.calc_x = x;self.calc_y=y;self.calc_w=width;
        self.calc_h=self.start_height
        if 'e' in mode:
            self.calc_w = self.start_width-x_motion
        if 's' in mode:
            self.calc_h -= y_motion
        if 'n' in mode:
            self.calc_y = y-y_motion
            self.calc_h = height+y_motion
        if 'w' in mode:
            self.calc_w = width+x_motion
            self.calc_x = x-x_motion
        self.master.itemconfig(
            self.cvid,width=self.calc_w,height=self.calc_h)
        cx = self.master.canvasx(self.calc_x)
        cy = self.master.canvasy(self.calc_y)
        self.master.coords(self.cvid, cx, cy)
        self.after_idle(self.update_idletasks)
        return 'break'

    def _drag(self, event):
        return

class WidgetWorld(InfiniteCanvas):
    '''
    WidgetWorld allows you to place resizeable widgets onto the InfiniteCanvas
    '''

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

    def create_interactive_window(self, x,y, widget, **kwargs):
        wrapped = WrapperFrame(self, widget, **kwargs)
        wrapped.cvid = self.create_window(x,y, anchor=tk.NW, window=wrapped)
        return wrapped.cvid




if __name__ == '__main__':
    root = tk.Tk()
    wcanvas = WidgetWorld(root)
    wcanvas.pack(fill=tk.BOTH, expand=True)
    red = tk.Text(wcanvas,bg='red')
    lbl = tk.Label(wcanvas, text='test',bg='yellow')
    wcanvas.create_interactive_window(0,0, red)
    wcanvas.create_interactive_window(0,0, lbl)

    toplevel = tk.Toplevel(root)
    icanvas = InfiniteCanvas(toplevel)
    icanvas.pack(fill=tk.BOTH, expand=True)

    size, offset, start = 100, 10, 0
    icanvas.create_rectangle(start,start, size,size, fill='green')
    icanvas.create_rectangle(
        start+offset,start+offset, size+offset,size+offset, fill='darkgreen')
    
    
    root.mainloop()
