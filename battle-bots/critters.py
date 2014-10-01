from random import *
import math
import geo2d.geometry
import itertools
from tkinter import *
import time

def random_color():
    return "#%02x%02x%02x" % (randrange(0,255),randrange(0,255),randrange(0,255))

def as_color(r,g,b):
    return "#%02x%02x%02x" % (255*r,255*g,255*b)

def gray(x):
    return as_color(x,x,x)

Location = geo2d.geometry.Point
def Heading(dir):
    return geo2d.geometry.Vector(1.0,dir,coordinates="polar")

class DisplayObject:
    def __init__(self,world,loc):
        self.world = world
        self.location = loc
    def on_tick(self):
        pass
    def draw(self, canvas,s):
        pass
    def displacement_to(self,other):
        return geo2d.geometry.Vector(self.location,other.location)

class Sound(DisplayObject):
    def __init__(self,world,loc,volume,text):
        DisplayObject.__init__(self,world,loc)
        self.volume = volume
        self.text   = text
        self.tk_id  = None
        self.age    = 1
        self.faded  = False
    def on_tick(self):
        self.age += 1
    def stipple(self):
        r = (self.age*100)/self.volume
        if   r < 12: return 'gray12'
        elif r < 25: return 'gray25'
        elif r < 50: return 'gray50'
        elif r < 75: return 'gray75'
        else:        return 'gray75' #None
    def draw(self, canvas, s):
        if self.tk_id:
            canvas.delete(self.tk_id)
            self.tk_id = None    
        if self.age < self.volume:
            loc  = self.location
            self.tk_id = canvas.create_text(
                s*loc.x, s*loc.y,
                text=self.text,
                font=('Helvetica',int(s*((self.volume+self.age)/10)**2)),
                fill=gray(self.age*1.0/self.volume),
                stipple=self.stipple()
                )
        else:
            self.faded = True

class PhysicalObject(DisplayObject):
    def __init__(self,world,loc):
        DisplayObject.__init__(self,world,loc)
        self.tk_id = None
        self.color = {"fill": "black"}
    def dump_status(self):
        print(self.location)
    def on_collision(self,dir,other):
        pass
    def radius(self):
        return 1
    def draw(self, canvas,s):
        r = self.radius()
        if r > 0:
            if self.tk_id is None:
                self.tk_id = canvas.create_oval(50, 50, s*2*r, s*2*r, **self.color)
            canvas.tag_lower(self.tk_id)
            loc = self.location
            canvas.coords(self.tk_id,      s*loc.x-s*r, s*loc.y-s*r,s*loc.x+s*r, s*loc.y+s*r)
        else:
            if self.tk_id:
                canvas.delete(self.tk_id)
                self.tk_id = None

class Critter(PhysicalObject):
    def __init__(self,world,brain_class,name):
        PhysicalObject.__init__(self,world,None)
        if isinstance(name,int):
            name = brain_class.owner + brain_class.code + str(name)
        self.name  = name
        self.heading = Heading(uniform(0.0,2*math.pi))
        profile = [uniform(0.5,0.8) for i in range(0,10)]
        self.shape   = [1.0,1.0]+profile+list(reversed(profile))
        self.size = 25
        self.tk_id = None
        self.brain = brain_class()
        self.dead = False
        world.spawn(self)
    def dump_status(self):
        print(self.name)
        self.brain.dump_status()
        print(self.location)
    def on_tick(self):
        if not self.dead:
            self.act(self.brain.on_tick(self.senses()))
            self.location.translate(self.heading.x,self.heading.y)
            self.location = self.world.wrap(self.location)
            self.act("Eat")
    def on_collision(self,dir,other):
        if isinstance(other,Food):
            self.act("Eat")
        else:
            self.say("Ooof!")
            self.size  *= 0.9
            self.heading -= dir
            self.act(self.brain.on_collision(dir,other,self.senses()))
    def teleport_to(self,world,loc):
        self.world    = world
        self.location = loc
    def die(self):
        if not self.dead:
            self.say("Aaaaaaaaa...!",volume=20)
            self.dead = True
    def say(self,msg,volume=10):
        if not self.dead:
            self.world.sound(self.location,volume,msg)
    def act(self,cmd):
        if not cmd is None:
            word = cmd.split()
            if word[0] == "Stop":
                self.heading /= 10000
            elif word[0] == "Turn":
                self.heading = Heading(self.heading.phi+float(word[1]))
            elif word[0] == "Accelerate":
                self.heading *= float(word[1])
            elif word[0] == "Attack":
                pass
            elif word[0] == "Eat":
                for f in self.world.food:
                    if f.value > 0 and self.location.distance_to(f.location) < self.radius():
                        self.say("Yum")
                        f.value -= 1
                        self.size += 1
            else:
                print("Unknown command: {}".format(cmd))
    def radius(self):
        return math.sqrt(self.size)
    def relative_heading(self,x):
        return (x-self.heading.phi+math.pi) % 2*math.pi + math.pi
    def relative_heading_to(self,x):
        return self.relative_heading(self.displacement_to(x).phi)
    def senses(self):
        return {
            'sight':   set(), # set of tuples: (color,distance,direction,width,change)
            'smell':   set(), # set of tuples: (strength,smell,change)
            'hearing': set([(s.text,self.relative_heading_to(s),s.age) for s in self.world.sounds]),
            'gps':     self.location,
            'compass': self.heading.phi,
          }
    def draw(self, canvas,s):
        if not self.dead:
            r    = self.radius()
            loc  = self.location
            phi  = self.heading.phi
            q    = 2*math.pi/len(self.shape)
            outline = [coord for a, d in enumerate(self.shape) for coord in (s*loc.x+s*r*d*math.cos(a*q+phi),s*loc.y+s*r*d*math.sin(a*q+phi))]
            if self.tk_id is None:
                self.tk_id = canvas.create_polygon(*outline, fill=random_color(), smooth=1, stipple='gray50')
                self.tk_text_id = canvas.create_text(50,50, text=self.name)
            canvas.coords(self.tk_text_id, s*loc.x, s*loc.y)
            canvas.coords(self.tk_id,      *outline)
        elif self.tk_id:
            canvas.delete(self.tk_id)
            self.tk_id = None
            canvas.delete(self.tk_text_id)
            self.tk_text_id = None

class CritterBrain:
    code  = ''
    owner = None
    def dump_status(self):
        pass
    def on_collision(self,dir,other,senses):
        pass
    def on_attack(self,dir,attacker,senses):
        pass
    def on_tick(self,senses):
        pass

class Food(PhysicalObject):
    def __init__(self,world,loc,value):
        PhysicalObject.__init__(self,world,loc)
        self.value = value
        self.color = {"fill": "dark green", "outline": "green"}
    def on_tick(self):
        # Could spoil, spread, or...?
        pass
    def on_collision(self,dir,other):
        pass
    def radius(self):
        return math.sqrt(self.value)

class Pit(PhysicalObject):
    def __init__(self,world,loc):
        PhysicalObject.__init__(self,world,loc)
        self.r = 10
        self.color = {"fill": "black", "outline": "dark red"}
    def on_tick(self):
        pass
    def on_collision(self,dir,other):
        other.location = self.location
        other.die()
    def radius(self):
        return self.r

class World:
    height = 100
    width  = 200
    def __init__(self):
        self.critters = []
        self.world_view = WorldView(self,5)
        self.food = [Food(self,self.random_location(),randrange(2,8)) for i in range(0,50)]
        self.pits = [Pit(self,self.random_location())]
        self.sounds = []
    def random_location(self):
        return Location(randrange(0,self.width),randrange(0,self.height))
    def spawn(self,critter):
        self.critters.append(critter)
        critter.teleport_to(self,self.random_location())
    def dump_status(self):
        for c in self.critters:
             c.dump_status()
    def physical_objects(self):
        return self.critters + self.food + self.pits
    def display_objects(self):
        return self.physical_objects() + self.sounds
    def sound(self,loc,volume,text):
        self.sounds.append(Sound(self,loc,volume,text))
    def run(self):
        while self.world_view.window_open:
            self.sounds = [s for s in self.sounds if not s.faded]
            shuffle(self.critters)
            for f in self.food:
                if f.value <= 0:
                    self.food.remove(f)
            for c in self.display_objects():
                c.on_tick()
            others = set(self.physical_objects())
            for c in self.critters:
                others.remove(c)
                for o in others:
                    if c.location.distance_to(o.location) < c.radius() + o.radius():
                        v = o.displacement_to(c).normalized
                        c.on_collision(-v,o)
                        o.on_collision( v,c)
            self.world_view.on_tick()
            time.sleep(0.1)
    def wrap(self,p):
        return Location(p.x % self.width,p.y % self.height)

class WorldView:
    def __init__(self,world,scale):
        self.world = world
        self.scale = scale
        self.tk = Tk()
        self.tk.title("Critters")
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

class Users:
    registered = []
    current = None
    initial = None
    def register(name):
        Users.registered.append(name)
        Users.current = name
        Users.initial = name[0:1]
    def initial(ch):
        Users.initial = ch

class Brains:
    registered = {}
    available = []
    def register(brain_class):
        u = Users.current
        if not u in Brains.registered.keys():
            Brains.registered[u] = []
        Brains.registered[u].append(brain_class)
        Brains.available.append(brain_class)
        brain_class.owner = Users.initial

import glob,re
for file in glob.glob("*_brains.py"):
    match = re.search('^(.+)_brains.py$', file)
    if match:
        Users.register(match.group(1))
        exec(open(file, "r").read())

w = World()
[Critter(w,choice(Brains.available),i) for i in range(1,10)]
w.run()
