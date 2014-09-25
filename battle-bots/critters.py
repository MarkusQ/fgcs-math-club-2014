from random import *
import math
import geo2d.geometry
import itertools
from tkinter import *
import time

def random_color():
    return "#%02x%02x%02x" % (randrange(0,255),randrange(0,255),randrange(0,255))


Location = geo2d.geometry.Point
def Heading(dir):
    return geo2d.geometry.Vector(1.0,dir,coordinates="polar")

class Critter:
    name  = None
    brain = None
    body  = None
    world = None
    def __init__(self,world,brain_class,name):
        self.name  = name
        self.world = world
        self.body  = CritterBody(self)
        self.brain = brain_class(self.body)
        world.spawn(self)
    def dump_status(self):
        print(self.name)
        self.brain.dump_status()
        self.body.dump_status()
    def on_tick(self):
        self.brain.on_tick()
        self.body.on_tick()
    def on_collision(self,dir,other):
        self.body.on_collision(dir,other)
        self.brain.on_collision(dir,other)
    def draw(self, canvas, scale):
        self.body.draw(canvas, scale)

class CritterBrain:
    def __init__(self,body):
        self.body = body
    def dump_status(self):
        pass
    def on_collision(self,dir,other):
        pass
    def on_attack(self,dir,attacker):
        pass
    def on_tick(self):
        pass
    def left(self,n):
        pass
    def right(self,n):
        pass
    def forward(self,n):
        pass
    def attack(self,target):
        pass
    def eat(self,target):
        pass
    def sight(self,n):
        pass
        # return set of n tuples: (color,distance,direction,width,change)
    def smell(self,n):
        pass
        # return set of n tuples (strength,smell,change)  

class CritterBody:
    world    = None
    location = None
    shape    = None
    heading  = None
    radius   = 5
    tk_id = None
    def __init__(self,critter):
        self.critter = critter
        self.heading = Heading(uniform(0.0,2*math.pi))
    def dump_status(self):
        print(self.location)
    def teleport_to(self,world,loc):
        self.world    = world
        self.location = loc
    def on_tick(self):
        self.location.translate(self.heading.x,self.heading.y)
        self.location = self.world.wrap(self.location)
    def on_collision(self,dir,other):
        self.radius  *= 0.9
        self.heading -= dir
    def draw(self, canvas,s):
        r = self.radius
        if self.tk_id is None:
            self.tk_id = canvas.create_oval(50, 50, s*2*r, s*2*r, fill=random_color())
            self.tk_text_id = canvas.create_text(50,50, text=self.critter.name)
        loc = self.location
        canvas.coords(self.tk_text_id, s*loc.x, s*loc.y)
        canvas.coords(self.tk_id,      s*loc.x-s*r, s*loc.y-s*r,s*loc.x+s*r, s*loc.y+s*r)

class Food:
    world    = None
    location = None
    value    = None
    tk_id = None
    def __init__(self,world,loc,value):
        self.world = world
        self.value = value
        self.location = loc
    def dump_status(self):
        print(self.location)
    def on_tick(self):
        # Could spoil, spread, or...?
        pass
    def on_collision(self,dir,other):
        self.radius  *= 0.9
        self.heading -= dir
    def draw(self, canvas,s):
        if self.value > 0:
            r = math.sqrt(self.value)
            if self.tk_id is None:
                self.tk_id = canvas.create_oval(50, 50, s*2*r, s*2*r, fill="Green")
            canvas.tag_lower(self.tk_id)
            loc = self.location
            canvas.coords(self.tk_id,      s*loc.x-s*r, s*loc.y-s*r,s*loc.x+s*r, s*loc.y+s*r)
        else:
            if self.tk_id:
                canvas.delete(self.tk_id)
                self.tk_id = None

class World:
    height = 100
    width  = 100
    def __init__(self):
        self.critters = []
        self.world_view = WorldView(self,5)
        self.food = [Food(self,self.random_location(),randrange(2,8)) for i in range(0,50)]
    def random_location(self):
        return Location(randrange(0,self.width),randrange(0,self.height))
    def spawn(self,critter):
        self.critters.append(critter)
        critter.body.teleport_to(self,self.random_location())
    def dump_status(self):
        for c in self.critters:
             c.dump_status()
    def display_objects(self):
        return self.critters + self.food
    def run(self):
        while self.world_view.window_open:
            shuffle(self.critters)
            for f in self.food:
                if f.value <= 0:
                    self.food.remove(f)
            for c in self.critters:
                 c.on_tick()
                 for f in self.food:
                     if f.value > 0 and c.body.location.distance_to(f.location) < c.body.radius:
                         f.value -= 1
                         c.body.radius = math.sqrt(c.body.radius**2+1)
            for c1,c2 in itertools.combinations(self.critters,2):
                 if c1.body.location.distance_to(c2.body.location) < c1.body.radius + c2.body.radius:
                     #print("{.name} collided with {.name}!".format(c1,c2))
                     v = geo2d.geometry.Vector(c2.body.location,c1.body.location).normalized
                     c1.on_collision(-v,c2)
                     c2.on_collision( v,c1)
            self.world_view.on_tick()
            time.sleep(0.1)
    def wrap(self,p):
        return Location(p.x % self.width,p.y % self.height)

class WorldView:
    def __init__(self,world,scale):
        self.world = world
        self.scale = scale
        self.tk = Tk()
        self.tk.title("Battle bots")
        self.tk.resizable(0, 0)
        self.tk.wm_attributes("-topmost", 1)
        self.canvas_height = scale*world.height
        self.canvas_width  = scale*world.width
        self.canvas = Canvas(self.tk, width=self.canvas_width, height=self.canvas_height, highlightthickness=0)
        self.canvas.pack()
        self.tk.update()
        self.window_open = True
        def they_hit_close():
            self.window_open = False
        self.tk.protocol("WM_DELETE_WINDOW",they_hit_close)
        def menu(evt):
            tk = Tk()
            btnq = Button(tk, text="Quit", command=tk.destroy)
            btnq.pack({"side": "bottom"})
            tk.title('Menu')
            tk.resizable(0, 0)
            tk.wm_attributes("-topmost", 1)
            tk.update()
        self.canvas.bind_all('<KeyPress-m>', menu)
    def on_tick(self):
        if self.window_open:
            for sprite in self.world.display_objects():
                sprite.draw(self.canvas,self.scale)
            self.tk.update_idletasks()
            self.tk.update()

w = World()
cs = [Critter(w,CritterBrain,"c{}".format(i)) for i in range(1,10)]
#w.dump_status()

w.run()

#w.dump_status()
