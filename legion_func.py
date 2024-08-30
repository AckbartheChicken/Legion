import pygame as gm
import json
from random import randint
import os
from time import sleep
from math import floor, ceil, sqrt
gm.init()
#Data storage classes
class WorldData:
    "Class for storing world/game data."
    def __init__(self,allsprites,sizes,backgrounds, num = 0):
        if len(allsprites) != len(sizes) != len(backgrounds):
            raise ValueError("allsprites, sizes, and backgrounds must be all the same length")
        self.allsprites = allsprites
        self.allsizes = sizes
        self.allbackgrounds = [gm.transform.scale(backgrounds[i],[self.allsizes[i].width,self.allsizes[i].height])
                            for i in range(len(backgrounds))]
        self.allswitches = [[0 for i in range(256)] for i in range(len(sizes))]
        self.background = self.allbackgrounds[num]
        self.size = self.allsizes[num]
        self.sprites = allsprites[num]
        self.switches = self.allswitches[num]
        self.classtype = [Pc,Iblock,Spike,Savepoint,Sign,
                          Chest,Door,Mapdoor,Lever,Button,
                          Itrigger,Doorkey,Chestkey,Bosskey,Npc,
                          Pot,Projectile,Enemy,Fakewall,Mblock,
                          C0,C1,C2,C3,Ascension,
                          Placeholder]
    def switch(self,num,view):
        view.rect.move_ip(-view.rect.x,-view.rect.y)
        player = self.sprites["0.0"]
        player.loc = num
        self.sprites = self.allsprites[num]
        self.background = self.allbackgrounds[num]
        self.size = self.allsizes[num]
        self.switches = self.allswitches[num]
        self.sprites.add(player)
class ViewData:
    "Class for storing view/screen data."
    def __init__(self,screen, border = 8, wiggle = 12):
        self.screen = screen
        self.screen_size = self.screen.get_size()
        self.view_size = [0.75 * (self.screen_size[0] - border * 3), self.screen_size[1] - border * 2]
        
        self.rect = gm.Rect(0,0,self.view_size[0],self.view_size[1]) 
        self.focus = "0.0"
        self.wiggle = wiggle
        self.font = gm.font.SysFont('sfnsmono', 25, bold = True)
        self.hitbox = False
        self.debug = False
        self.fps = 0 
        self.border = border
    def center(self,world,focus):
        center = world.sprites[focus]
        rect = center.rect
        viewy = self.rect.y
        viewx = self.rect.x
        #'size' is a vector containg the distance from the wiggle box to the edge
        size = [(self.view_size[0] - rect.width)/2-self.wiggle,(self.view_size[1] - rect.height)/2-self.wiggle]
        xadjust = 0
        yadjust = 0
        #make camera have some lee way, so focus isn't directly center
        if world.size.height >= self.rect.height:
            if rect.y < viewy + size[1]:
                if rect.y > size[1]:
                    yadjust = rect.y - (viewy + size[1])
                else:
                    yadjust = -1 * viewy
            elif rect.bottom > viewy + size[1] + (2 * self.wiggle) + rect.height:
                if rect.bottom < world.size.height - size[1]:
                    yadjust = rect.bottom - (viewy + size[1] + rect.height  + (2*self.wiggle))
                else:
                    yadjust = world.size.height - self.rect.bottom
        if world.size.width >= self.rect.width:
            if rect.x < viewx + size[0]:
                if rect.x > size[0]:
                    xadjust = rect.x - (viewx + size[0])
                else:
                    xadjust = -1 * viewx
            elif rect.right > viewx + size[0] + (2 * self.wiggle) + rect.width:
                if rect.right < world.size.width - size[0]:
                    xadjust = rect.right - (viewx + size[0] + rect.width  + (2*self.wiggle))
                else:
                    xadjust = world.size.width - self.rect.right
        self.rect.move_ip(xadjust,yadjust)
class Text:
    def __init__(self,words,x,y,time,obj,view,size = 15,scroll = True,scale = False):
        self.raw = words
        self.scroll = scroll
        if not scroll:
            self.index = len(words)
        else:
            self.index = 0
        if scale:
            size = max(1,int(size * (view.screen_size[0] / 800)))
        self.font = gm.font.SysFont('sfnsmono', size, bold = True)
        self.view_rect = view.rect.copy()
        self.rect = gm.Rect(0,0,10,10)
        self.rect.move_ip(x,y)
        if scroll:
            self.words = self.font.render(words[0],False,(255,255,255))
        else:
            self.words = self.wrap(None)
        self.rect = self.wrap(None).get_rect()
        self.rect.move_ip(x,y)
        if self.view_rect.right - self.rect.x <= 5 * font_size[0]:
            self.rect.move_ip((self.view_rect.right - self.rect.x) - 5 * font_size[0], 0)
        self.time = time
        self.max_time = time
        self.obj = obj
    def update(self):
        surfs = []
        if self.index < len(self.raw):
            self.index += 1
        else:
            return None
        image = self.wrap(self.index)
        self.words = image
    def wrap(self,index):
        if index == None:
            index = len(self.raw)
        font_size = self.font.size("a")

        if self.font.size(self.raw[:index])[0] > self.view_rect.width - (self.rect.x - self.view_rect.x):
            cpl = floor((self.view_rect.width - (self.rect.x - self.view_rect.x)) / font_size[0])
            sizes = []
            surfs = []
            for i in range(ceil(len(self.raw[:index]) / cpl)):
                text = self.raw[:index][cpl * i: cpl * (i + 1)]
                surfs.append(self.font.render(text,False,(255,255,255)))
                sizes.append(self.font.size(text))
            #creating final image
            height = 0
            for i in sizes:
                height += i[1]
            image = gm.Surface([max([i[0] for i in sizes]),height],gm.SRCALPHA)
            for i in range(len(surfs)):
                image.blit(surfs[i],(0,i*sizes[0][1]))
        else:
            image = self.font.render(self.raw[:index],False,(255,255,255))
        return image
class Textdata():
    def __init__(self):
        self.font = gm.font.SysFont('sfnsmono', 25, bold = True)
        self.texts = []
    def add(self,words,x,y,time,obj,view,replace,size = 25,scroll = True, scale = False):
        if obj != None:
            for i in self.texts:
                if i.obj == obj:
                    if not replace and i.time != 0:
                        break
                    self.texts.remove(i)
                    self.texts.append(Text(words,x,y,time,obj,view,size,scroll,scale))
                    break
            else:
                self.texts.append(Text(words,x,y,time,obj,view,size,scroll,scale))
        elif obj == None:
            self.texts.append(Text(words,x,y,time,obj,view,size,scroll,scale))
        
    def update(self,view,*objs):
        removing = []
        for i in self.texts:
            if i.obj in objs:
                i.update()
                continue
            if i.time > 0:
                i.time -= 1
                i.update()
            else:
                removing.append(i)
        for i in removing:
            self.texts.remove(i)
    def finish(self):
        for i in self.texts:
            #the minus one is because the Text() objects do not update if the index == len(.raw)
            i.index = len(i.raw) - 1
            i.update()
class Group:
    "Container class for storing and manipulating groups of sprites"
    def __init__(self, *sprites):
        for i in sprites:
            if not isinstance(i,Basic):
                raise TypeError(f"Must contain only game objects (Inherited from 'basic' class), not {type(i)}")
        self.sprites = dict(zip([i.tag.split(".")[1] for i in sprites], sprites))
    def update(self,world,text,view):
        stop = False
        for sprite in self:
            sprite.update(world,text,view)
    def draw(self,view):
        for sprite in self.sprites:
            if gm.sprite.collide_rect(sprite,view):
                view.screen.blit(sprite.image,sprite.rect)
    def add(self,*sprites):
        for i in sprites:
            if not isinstance(i,Basic):
                raise TypeError("Must contain only game objects (Inherited from 'basic' class)")
        for i in sprites:
            where = i.tag.split(".")[1]
            if where in self.sprites:
                raise ValueError("Object with that tag already exists")
            self.sprites[where] = i
    def remove(self,*sprites):
        for sprite in sprites:
            if sprite in self.sprites:
                del self.sprites[self.sprites.tag.split(".")[1]]
            else:
                raise ValueError("Can only remove sprites already in self")
    def collide(self,sprite):
        ls = []
        for i in self:
            if sprite.collide(i):
                ls.append(i)
        return ls
    def __getitem__(self,index):
        if not isinstance(index,str):
            raise TypeError(f"Group getitem function only allows strings, not {type(index)}.")
        return self.sprites[index]
    def __setitem__(self,index,new):
        self.sprites[index] = new
    def __delitem__(self,index):
        if not isinstance(index,str):
            raise TypeError(f"Group delitem function only allows strings, not {type(index)}.")
        del self.sprites[index]
    def __iter__(self):
        return(iter(self.sprites.values()))
    def __repr__(self):
        return(str(self.sprites))
class Collection:
    """Class for storing many sprite groups. It is essentially an expanded dictionary with a
        few extra functions."""
    def __init__(self,*sprites):
        self.collection = dict(zip([str(i) for i in range(27)],[Group() for i in range(27)]))
        for i in sprites:
            if not isinstance(i,Basic):
                raise TypeError(f"Must only contain sprites, not {type(i)}.")
            tag = i.tag.split(".")
            self.collection[tag[0]][tag[1]] = i
        self.collection["26"]["0"] = Placeholder(0,0,"26.0")
    def add(self,*sprites):
        for i in sprites:
            if not isinstance(i,Basic):
                raise TypeError(f"Collection.add() must only contain sprites, not {type(i)}.")
            tag = i.tag.split(".")
            if tag[0] not in self.collection.keys():
                self.collection[tag[0]] = Group()
            self.collection[tag[0]][tag[1]] = i
    def update(self,world,text,view):
        for group in self:
            group.update(world,text,view)
    def draw(self,view):
        for i in self.collection:
            self.collection[i].draw(view)
    def collide(self,sprite):
        ls = []
        for i in self:
            ls += i.collide(sprite)
        return ls
    def __iter__(self):
        return(iter(self.collection.values()))
    def __getitem__(self,index):
        if isinstance(index,str):
            if "." in index:
                tag = index.split(".")
                if len(tag) != 2:
                    raise ValueError("Tag has too many values. Should only have 2. Eg. 'a.b', not 'a.b.c'.")
                return self[tag[0]][tag[1]]
            return(self.collection[index])
        else:
            raise TypeError("Getitem function only allows strings. Not: " + str(type(index)))
    def __delitem__(self,index):
        if isinstance(index,str):
            if "." in index:
                tag = index.split(".")
                if len(tag) != 2:
                    raise ValueError("Tag has too many values. Should only have 2. Eg. 'a.b', not 'a.b.c'.")
                del self.collection[tag[0]][tag[1]]
            else:
                del self.collection[index]
        else:
            raise TypeError("delitem function only allows strings. Not: " + str(type(index)))
    def __repr__(self):
        return(str(self.collection))
class Hitbox:
    "Container class for storing multiple rects as a compound hitbox."
    def __init__(self,*rects):
        for i in rects:
            if not isinstance(i,gm.Rect):
                raise TypeError(f"Hitbox class only accepts rects, not {type(i)}.")
        self.rects = [i.copy() for i in rects]
    def move_ip(self, x = 0, y = 0):
        for i in self.rects:
            i.move_ip(x,y)
    def move(self, x = 0, y = 0):
        ls = []
        for i in self.rects:
            ls.append(i.move(x,y))
        return self.__Class__(ls)
    def __getitem__(self,index):
        if isinstance(index, int):
            return self.rects[index]
        raise TypeError(f"Hitbox getitem function only accepts integer indices, not {type(index)}.")
    def __repr__(self):
        return str(self.rects)
#Audio classes
class Audio:
    "Audio handler class for playing sounds and music."
    def __init__(self):
        pass
#Sprite classes
class Basic:
    "Basic class all other sprite classes will inherit from."
    def __init__(self, x, y, tag, image = "eblock", hitbox = "rect"):
        self.image = images[image].copy()
        self.image_name = image
        self.rect = self.image.get_rect()
        self.rect.move_ip(x,y)
        #If hitbox != "rect", it is up to the child class to set up its hitbox, otherwise, the hitbox
        #will be the same as self.rect
        if hitbox == "rect":
            self.hitbox = Hitbox(self.rect)
        self.empty = False
        self.interact = False
        self.alive = False
        self.movable = False
        self.remove = False
        #used for ranking which movein funcs are called first during Alive.move()
        self.hierarchy = None
        #used to know if a sprite will be displayed. updated during disp() func
        self.show = False
        self.tag = tag
    def change_sprite(self,image = None, color = (0,0,0,0)):
        if image != None:
            sprite = images[image].copy()
            self.image_name = image
        else:
            sprite = images[self.image_name].copy()
        sprite.fill((color), special_flags = gm.BLEND_ADD)
        self.image = sprite
    def update(self,world,text,view):
        pass
    def interaction(self,world,moving,text,view):
        pass
    def copy(self):
        return(__class__(self.x, self.y, self.tag, self.image))
    def remove(self):
        self.remove = True
    def movein(self, moving, world, view , text):
        return self.empty
    def checkin(self,world,moving):
        return self.empty
    def collide(self,sprite):
        if self == sprite:
            return False
        for i in sprite.hitbox:
            for j in self.hitbox:
                if i.colliderect(j):
                    return True
        return False
    def collide_rect(self,rect):
        for i in self.hitbox:
            if i.colliderect(rect):
                return True
        return False
    def move_rect(self,x,y,offset = True):
        if offset:
            self.rect.move_ip(x,y)
            self.hitbox.move_ip(x,y)
        else:
            self.rect.move_ip(x - self.rect.x, y - self.rect.y)
            self.hitbox.move_ip(x - self.rect.x, y - self.rect.y)
class Iblock(Basic):
    "Sprite class for immovable blocks. (Walls). Tag is 1.x."
    def __init__(self, x, y, tag, image = 'iblock'):
        super().__init__(x, y, tag, image)
class Spike(Basic):
    "Sprite class for spikes. Tag is 2.x."
    def __init__(self, x, y, tag, image = 'spike'):
        super().__init__(x, y, tag, image)
        self.empty = True
        self.hierarchy = "0"
    def checkin(self,world,moving):
        return moving.alive
    def movein(self,moving, world, view, text):
        #Placeholder. Write this once player knockback and movement is done.
        if moving.alive:
            moving.hit(world,2,moving.poise + 2, gm.Vector2(moving.vector.x*-1,moving.vector.y*-1))
        return False
class Savepoint(Basic):
    "Sprite class where player will save progress. Tag is 3.x."
    def __init__(self, x, y, tag, image = "save"):
        super().__init__(x, y, tag, image)
        self.interact = True
    def interaction(self,world,moving,text,view):
        text.add("Saving...",self.rect.x,self.rect.y - 18, 90, self, view, True, 15)
        
        for level in [i for i in os.listdir("maps/") if ".json" in i]:
            pass
        text.add("Saved.",self.rect.x,self.rect.y - 18, 90, self, view, True, 15)
class Sign(Basic):
    "Sprite class that player can read by interacting with. Tag is 4.x."
    def __init__(self, x, y, tag, message = "", image = 'sign'):
        super().__init__(x, y, tag, image)
        self.message = message
        self.interact = True
        self.empty = True
    def interaction(self,world,moving,text,view):
        text.add(self.message, self.rect.x, self.rect.y-18 ,90 ,self , viwe, True, 15)
class Chest(Basic):
    "Sprite class for a chest. Tag is 5.x."
    def __init__(self, x,  y, tag, inside, intype, locked = False, key = False,
                 switch = None, switch_val = 1, interact = True, changed = 0, image = None):
        if image == None:
            if locked:
                image = "chestlocked"
            elif interact:
                image = "chestclosed"
            else:
                image = "chestopen"
        super().__init__(x , y , tag, image)
        self.locked = locked
        self.key = key
        self.inside = inside
        self.intype = intype
        self.interact = interact
        self.switch = switch
        self.switch_val = switch_val
        self.changed = changed
    def interaction(self,world,moving,text,view):
        if not isinstance(moving,Pc):
            return None
        if not self.locked:
            self.change_sprite("chestopen")
            self.interact = False
            if self.intype == "item":
                moving.additem(self.inside[0],self.inside[1])
            elif self.intype == "tool":
                print("Chest contains tool. Add this in later.")
            else:
                raise ValueError(f"Chests can only have 'item' or 'tool' type. Not {self.intype}.")
        elif self.key and moving[1] >= 1:
            self.locked = False
            self.change_sprite("chestclosed")
        elif self.key:
            text.add("The chest is locked", self.rect.x, self.rect.y-18, 90, self, view, True, 15)
        else:
            text.add("The chest is locked by some mechanism",self.rect.x,self.rect.y-18,90,self,view,True,15)
    def update(self,world,text,view):
        if not self.interact:
            return None
        if self.locked and self.switch != None and world.switches[self.switch] == self.switch_val:
            if self.changed >= 2:
                #add in slide animations
                pass
            self.locked = False
            self.change_sprite("chestclosed")
            if self.changed >= 2:
                #add in slide animations
                pass
        elif not self.locked and self.switch != None and world.switches[self.switch] != self.switch_val:
            if self.changed >= 2:
                #add in slide animations
                pass
            self.locked = True
            self.change_sprite("chestlocked")
            if self.changed >= 2:
                #add in slide animations
                pass
class Ascension(Basic):
    "Sprite class that ascends player (turns on god mode) when interacted with. Tag is 24.x."
    def __init__(self, x, y, tag):
        super().__init__(x, y, tag, "eblock")
        self.tag = tag
        self.empty = True
        self.interact = True
    def interaction(self,world,moving,text,view):
        if isinstance(moving, Player):
            moving.god = True
class Door(Basic):
    "Generic sprite class for all doors, including: doors and mapdoors. Tag is 6.x."
    def __init__(self, x, y, tag, switch = None, switch_val = 1, locked = False, key = False,
                 times = 1, has_switched = 0, image = None):
        if image == None:
            if locked:
                image = "doorlocked"
            else:
                image = "doorclosed"
        super().__init__(x, y, tag, image)
        self.locked = locked
        self.key = key
        self.interact = True
        self.times = times
        self.changed = has_switched
        self.switch = switch
        self.switch_val = switch_val
    def open(self,force = False):
        if not self.locked or force:
            self.empty = True
            self.change_sprite("dooropen")
            self.interact = False
    def close(self):
        if self.empty:
            self.empty = False
            self.change_sprite("doorclosed")
            self.interact = True
    def interaction(self,world,moving,text,view):
        if not self.locked:
            self.empty = True
            self.change_sprite("dooropen")
            self.interact = False
        elif self.key and moving.items[0] >= 1:
            self.locked = False
            moving.items[0] -= 1
            self.change_sprite("doorclosed")
        elif self.key:
            text.add("The door is locked",self.rect.x,self.rect.y-18,90,self, view, True,15)
        else:
            text.add("The door is locked by some mechanism",self.rect.x,self.rect.y-18,90,self,view, True,15)
    def update(self,world,text,view):
        if self.interact:
            if self.locked and self.switch != None and world.switches[self.switch] == self.switch_val:
                if self.changed >= 2:
                    #add in slide animations
                    pass
                self.locked = False
                self.change_sprite("doorclosed")
                if self.changed >= 2:
                    #add in slide animations
                    pass
            elif not self.locked and self.switch != None and world.switches[self.switch] != self.switch_val:
                if self.changed >= 2:
                    #add in slide animations
                    pass
                self.locked = True
                self.change_sprite("doorlocked")
                if self.changed >= 2:
                    #add in slide animations
                    pass
class Mapdoor(Basic):
    "Sprite class for door that leads between maps. Tag is 7.x."
    def __init__(self, x, y, tag, direction, target, place):
        if direction not in ["l","r","u","d"]:
            raise ValueError(f"Mapdoor direction argument is not a valid direction: {direction}")
        image = "mapdoor" + direction
        super().__init__(x,y,tag,image)
        self.direction = direction
        self.target = target
        self.place = place
        self.active = True
        self.empty = True
        self.hierarchy = "1"
    def update(self,world,text,view):
        if not gm.sprite.collide_rect(self,world.sprites["0.0"]):
            self.active = True
    def movein(self,moving,world,view,text):
        #return if not active (used to make sure players can move when tp'd to the mapdoor)
        if not self.active or not isinstance(moving,Pc):
            return True
        self.active = False
        fade(world,view,text,1)
        world.switch(self.place,view)
        target = world.sprites[self.target]
        target.active = False
        moving = world.sprites["0.0"]
        x = target.rect.x - moving.rect.x
        y = target.rect.y - moving.rect.y
        if target.direction == "d":
            y -= moving.rect.height - target.rect.height
        elif target.direction == "r":
            x -= moving.rect.width - target.rect.width
        moving.move_rect(x,y)
        sprites = world.sprites.collide(moving)
        for i in sprites:
            if isinstance(i,Door):
                i.open(True)
        fade(world,view,text,1,False)
        #add better movement once cutscenes are implemented
        return False
class Lever(Basic):
    "Sprite class for a toggler that switches when interacted with. Tag is 8.x."
    def __init__(self, x, y, tag, switch, image = "leveroff"):
        super().__init__(x,y,tag,image)
        self.on = False
        self.interact = True
        self.switch = switch
    def interaction(self,world,moving,text,view):
        self.on = not self.on
        if self.switch != None:
            world.switches[self.switch] +=  self.on + (not self.on) * -1
        self.change_sprite("lever" + "on" * self.on + "off" * (not self.on))
class Button(Basic):
    "Generic sprite class for all pressure plates, including: buttons and itriggers. Tag is 9.x."
    def __init__(self, x , y, tag, switch, image = "buttonoff"):
        super().__init__(x, y, tag, image)
        self.empty = True
        self.on = False
        self.switch = switch
    def update(self, world, text, view):
        for i in world.sprites.collide(self):
            if isinstance(i,Pc):
                if not self.on and self.switch != None:
                    world.switches[self.switch] += 1
                self.on = True
                self.spec(world,text)
                break
        else:
            if self.on and self.switch != None:
                world.switches[self.switch] -= 1
            self.on = False
        if not isinstance(self,Itrigger):
            self.change_sprite("buttonon" * self.on + "buttonoff" * (not self.on))
    def spec(self, world, text):
        pass
class Itrigger(Button):
    """Sprite class for toggler that switches when stepped on. It will also remove itself and any linked
        itriggers when this happens. It is intended to be used as a trigger for behind the scenes things
        like cutscenes. Tag is 10.x."""
    def __init__(self, x, y, tag, switch, others = None, active = False, image = "eblock"):
        super().__init__(x, y, tag, switch, image)
        if others == None:
            self.others = []
        else:
            self.others = others
        self.active = True
    def update(self, world, text, view):
        if self.active:
            super().update(world, text, view)
    def spec(self, world, text):
        self.active = False
        for i in self.others:
            world.sprites[i].active = False
class Collectible(Basic):
    "Generic sprite class for all collectibles, including: keys and items."
    def __init__(self, x, y, tag, where, number = 5, image = "doorkey"):
        super().__init__(x, y, tag, image)
        self.empty = True
        self.number = number
        self.where = where
    def movein(self, moving, world, view, text):
        if isinstance(moving,Pc):
            moving.additem(self.where, self.number)
            self.remove = True
        return True
class Doorkey(Collectible):
    "Sprite class for door keys. Tag is 11.x."
    def __init__(self, x, y, tag, number = 1, image = "doorkey"):
        super().__init__(x,y,tag,0,number,image)
class Chestkey(Collectible):
    "Sprite class for chest keys. Tag is 12.x."
    def __init__(self, x, y, tag, number = 1, image = "chestkey"):
        super().__init__(x,y,tag,1,number,image)
class Bosskey(Collectible):
    "Sprite class for boss keys. Tag is 13.x."
    def __init__(self, x, y, tag, number = 1, image = "chestkey"):#Change this to bosskey when you do that art
        super().__init__(x,y,tag,2,number,image)
class C0(Collectible):
    "Sprite class for a specific collectible. Tag is 20.x."
    def __init__(self, x, y, tag, number = 5, image = "c0"):
        super().__init__(x,y,tag,3,number,image)
class C1(Collectible):
    "Sprite class for a specific collectible. Tag is 21.x."
    def __init__(self, x, y, tag, number = 5, image = "c1"):
        super().__init__(x,y,tag,4,number,image)
    def movein(self, moving, world, view, text):
        if isinstance(moving,Pc):
            for i in range(self.number):
                if moving.health < moving.maxhealth:
                    moving.health += 1
        self.remove = True
        return(True)
class C2(Collectible):
    "Sprite class for a specific collectible. Tag is 22.x"
    def __init__(self, x, y, tag, number = 5, image = "c2"):
        super().__init__(x,y,tag,5,number,image)
class C3(Collectible):
    "Sprite class for a specific collectible. Tag is 23.x"
    def __init__(self, x, y, tag, number = 5, image = "c3"):
        super().__init__(x,y,tag,6,number,image)
class Alive(Basic):
    "Generic sprite class for all alive objects, including: players, enemies, fakewalls, etc."
    def __init__(self, x, y, tag, health = 1, maxhealth = 1, poise = 0,
                god = False, image = "playerdown",hitbox = "rect"):
        super().__init__(x, y, tag, image,hitbox)
        self.vector = gm.math.Vector2(0,0)
        self.facing = gm.math.Vector2(0,1)
        self.alive = True
        #stats for object
        self.health = health
        self.maxhealth = maxhealth
        self.poise = poise
        self.god = god
        #timing/condition vars
        self.ragdoll = 0
        self.iframe = 0
        self.dodging = 0
        self.attacking = 0
        self.damaged = 0
        self.speed = 2
        #class stuff
    def move(self,world, view, text):
        "A function specifically for alive sprites to check if they can move along their vector."
        for i in range(self.speed):
            for vector in (gm.math.Vector2(self.vector.x,0),gm.math.Vector2(0,self.vector.y)):
                stop = False
                self.move_rect(vector.x,vector.y)
                collides = world.sprites.collide(self)
                valid = []
                if not world.size.contains(self):
                    valid = [False]
                ranking = {"None":[]}
                #call checkin funcs to see if player could move in its current state
                for i in collides:
                    valid.append(i.checkin(world,self))
                    if str(i.hierarchy) not in ranking.keys():
                        ranking[i.hierarchy] = []
                    ranking[str(i.hierarchy)].append(i)
                #check if  player could move into all other sprites
                if valid != [True for i in valid]:
                    self.move_rect(-1*vector.x,-1*vector.y)
                    continue
                #sorting of ranks
                ordered = sorted(list(ranking)[1:]) + ["None"]
                ranking = dict(zip(ordered,[ranking[i] for i in ordered]))
                stop = False
                #calling movein ranked functions
                for group in ranking:
                    for sprite in ranking[group]:
                        if not sprite.remove:
                            stop = not sprite.movein(self, world, view, text)
                        if stop:
                            break
                    if stop:
                        break
                if stop:
                    self.move_rect(-1*vector.x,-1*vector.y)
    def update(self, world, text, view):
        if self.health <= 0:
            self.die(world, text, view)
    def hit(self,world,damage,power,vector):
        if self.health != None and not self.iframe:
            self.health -= damage
            if power > self.poise:
                self.vector.x,self.vector.y = [0,0]
            self.ragdoll = (power-self.poise) * 5 * (power > self.poise)
            self.iframe = (power-self.poise) * 10 * (power > self.poise)
            self.damaged = (power-self.poise) * 10 * (power > self.poise)
            self.vector = vector.copy()
    def attack(self,world):
        y1 = self.rect.y+floor((1/2*self.facing.y+0.5)*(self.rect.height))
        x1 = self.rect.x+floor((1/2*self.facing.x+ 0.5)*(self.rect.width))
        targeted = []
        for i in world.sprites:
            for obj in i:
                if obj.alive and obj != self:
                    j = obj.rect
                    stop = False
                    for y2 in range(j.height):
                        for x2 in range(j.width):
                            if ceil(sqrt((y1-(j.y+y2))**2+(x1-(j.x+x2))**2)) <= self.hand.reach:
                                if self.facing.x == 0 and self.facing.y*(j.y+y2-y1) >= abs(j.x+x2-x1):
                                    targeted.append(obj)
                                    stop = True
                                    break
                                elif self.facing.y == 0 and abs(j.y+y2-y1) <= self.facing.x*(j.x+x2-x1):
                                    targeted.append(obj)
                                    stop = True
                                    break
                                elif self.facing.y*(j.y+y2-y1) > 0 and self.facing.x*(j.x+x2-x1) > 0:
                                    targeted.append(obj)
                                    stop = True
                                    break
                                
                        if stop: break
        targeted = list(set(targeted))
        for sprite in targeted:
            sprite.hit(world, self.hand.damage, self.hand.strength, self.vector.copy())
    def die(self,world,text,view):
        self.remove = True
class Projectile(Alive):
    "Sprite class for projectiles, including bullets/arrows etc. Tag is 16.x."
    def __init__(self,x,y,tag,vector,image = "projectile"):
        super().__init__(self,x,y,tag,image = image)
        self.empty = True
        self.vector = vector
    def update(self,world,text, view):
        #Placeholder
        pass
    def movein(self,moving, world, view, text):
        if moving.alive:
            moving.hit(world,1,1,gm.Vector2(self.vector.x,self.vector.y))
        return True
class Npc(Alive):
    "Sprite class for npcs. They can give dialogue and items. Tag is 14.x"
    def __init__(self,x,y,tag,dialogues,inventory,intype,image = "npc"):
        super().__init__(x,y,tag,None,image = "npc")
        self.dialogues = dialogues
        self.inventory = inventory
        self.intype = intype
        self.interact = True
    def interact(self,world,moving):
        #placeholder. Do once messages are coded
        pass
class Pot(Alive):
    "Sprite class for pots; they break when attacked or dashed into and drop a collectible. Tag is 15.x."
    def __init__(self,x,y,tag,image = "pot"):
        super().__init__(x,y,tag,image = image)
        self.empty = True
    def checkin(self,world,moving):
        if isinstance(moving,Pc) and moving.dodging > 10:
            return True
        return False
    def movein(self, moving, world, view, text):
        self.hit(world,1,0,[0,0])
        return True
    def die(self,world,text,view):
        tag = randint(20,23)
        if str(tag) in world.sprites.collection and len(world.sprites[str(tag)].sprites) !=  0:
            tag2 = int(max(world.sprites[str(tag)].sprites.keys())) + 1
        else:
            tag2 = "0"
        sprite = world.classtype[tag](self.rect.x,self.rect.y,f"{tag}.{tag2}")
        world.sprites.add(sprite)
        self.remove = True
class Pc(Alive):
    "Sprite class for player character. Tag is 0.x."
    def __init__(self, x, y, tag, health = 20, maxhealth = 20, poise = 5,items = None, tools = None,
                 loc = 0, image = "playerdown", god = False, hitbox = "rect"):
        super().__init__(x, y, tag , health , maxhealth , poise, god, image, hitbox)
        if items == None:
            items = [0,0,0,0,0,0,0]
        self.items = items
        self.inames = ["doorkey","chestkey","bosskey","ammo",None,"money",None]
        self.imax = [10,10,1,30,None,50,None]
        if tools == None:
            tools = []
        empty = weapons["empty"]
        
        tools = [weapons[i] for i in tools if weapons[i] != empty] + [empty]
        self.tools = tools
        self.hand = tools[-1]
        self.loc = loc
    def update(self, world, text, view):
        psprites = [[None,"up",None],
                    ["left", None, "right"],
                    [None,"down",None]]
        if 0 in self.facing:
            self.change_sprite("player" + psprites[int(self.facing.y+1)][int(self.facing.x+1)])
        else:
            self.change_sprite("player" + psprites[1][int(self.facing.x+1)])
        if self.damaged:
            self.change_sprite(color = (255,0,0))
        
        loc = self.loc
        if self.vector.magnitude() != 0:
            self.move(world, view, text)
        if self.dodging > 0:
            if self.dodging == 10:
                self.change_sprite()
                self.speed = round(self.speed / 2)
            elif self.dodging > 10:
                self.change_sprite(color = [0,100,100,0])
            self.dodging -= 1
        if self.ragdoll > 0:
            self.ragdoll -= 1
        if self.iframe > 0:
            self.iframe -= 1
        if self.damaged > 0:
            self.damaged -= 1
        if self.health <= 0:
            self.die(world,text,view)
    def die(self,world,text,view):
        text.add("You died Lol ;)",view.rect.centerx-30,view.rect.centery,1,None,view,False,30,scroll = False)
        disp(world,view,text)
        gm.display.flip()
        timed(2,world,view,text)
        exit()
    def additem(self, where, num):
        for i in range(num):
            if (self.imax[where] == None or self.items[where] < self.imax[where]):
                self.items[where] += 1
class Enemy(Alive):
    "Sprite class for enemy object. Tag is 17.x."
    def __init__(self, x, y, tag, health, maxhealth, poise, weapon, vision, inventory, image = "playerdown",
                 hitbox = "rect"):
        super().__init__(x, y, tag, health, maxhealth, poise, image = image, hitbox = hitbox)
    def update(self,world,text, view):
        pass
        #placeholder
class Fakewall(Alive):
    "Sprite class for fakewall. When attacked they die and dissapear. Tag is 18.x."
    def __init__(self, x, y, tag, health = 1, maxhealth = 1, image = "iblock"):
        super().__init__(x, y, tag, health, maxhealth, image = image)
class Mblock(Basic):
    "Sprite class for a movable block that can be pushed. Tag is 19.x."
    def __init__(self, x, y, tag):
        super().__init__(x,y,tag,image = "mblock")
        self.health = None
    def interact(self,world,moving):
        #placeholder
        pass
class Placeholder(Basic):
    "Sprite class for a placeholder object that can be used for view centering or other processes. Tag is 25.x."
    def __init__(self,x = 0, y = 0, tag = None):
        super().__init__(x,y,tag)
        self.empty = True
class Weapon:
    "Sprite class for weapons, including swords, guns, etc."
    def __init__(self, damage, strength, reach, speed, up, down, name, taxon):
        self.damage = damage
        self.strength = strength
        self.reach = reach
        self.speed = speed
        self.up = up
        self.down = down
        self.name = name
        self.taxon = taxon
    def __eq__(self,other):
        if not isinstance(other, Weapon):
            raise TypeError(f"Can only equate other weapon objects to a weapon object, not {type(other)}")
        if self.name == other.name and self.taxon == other.taxon:
            return True
        return False
#Functions
def write_save(path,sprites,new):
    data = read_save(path)[3]
    entities = data["layers"][0]["entities"]
    for i in range(len(entities)):
        sprite = sprites[entities[i]["values"]["ID"]]
    #use sprites, which would be a collection of sprites, to edit data
    with open(new,"w") as file:
        file.write(json.dumps(data,indent = 4))
def read_save(path):
    classes = [Pc,Iblock,Spike,Savepoint,Sign,
              Chest,Door,Mapdoor,Lever,Button,
              Itrigger,Doorkey,Chestkey,Bosskey,Npc,
              Pot,Projectile,Enemy,Fakewall,Mblock,
              C0,C1,C2,C3,Ascension,
              Placeholder]
    with open(path,"r") as file:
        data = json.load(file)
    #read all sprites
    sprites = []
    for i in range(len(data["layers"][1]["data2D"])):
        row = data["layers"][1]["data2D"][i]
        for j in range(len(row)):
            if row[j] in [1,2]:
                data["layers"][0]["entities"].append({"name":"iblock","x":j*32,"y":i*32,
                                                     "values":{"ID":str(row[j]) + ".0"}})
    for i in data["layers"][0]["entities"]:
        x = i["x"]*2
        y = i["y"]*2
        #get id
        tag = i["values"]["ID"]
        tagtype = tag.split(".")[0]
        if int(tagtype) in [1,2,3,4,11,12,13,15,18,19,20,21,22,23,24]:
            tag = tagtype + "." + str(len([i for i in sprites if i.tag.split(".")[0] == tagtype]))
            i["values"]["ID"] = tag
        values = i["values"]
        #do any formatting of values, eg. turn str into lists when applicable
        for attr in values:
            if isinstance(values[attr],str):
                if values[attr] == "None":
                    values[attr] = None
                elif values[attr][:2] == "//":
                    #do list parsing
                    if values[attr][2] == "s":
                        values[attr] = values[attr][3:].split(",")
                    elif values[attr][2] == "i":
                        values[attr] = [int(i) for i in values[attr][3:].split(",")]
                    elif len(values[attr]) == 2:
                        values[attr] = []
                    else:
                        raise ValueError(f"Only accept list types are 's' and 'i'. Not {values[attr][2]}")
            elif isinstance(values[attr],int):
                if values[attr] == -1337:
                    values[attr] = None
        sprite = classes[int(tag.split(".")[0])](x,y,*list(values.values()))
        sprites.append(sprite)
    background = "background"
    size = [data["width"]*2,data["height"]*2]
    return(sprites,size,background,data)
def looking(world,view,debug = False):
    player = world.sprites["0.0"]
    ys = []
    xs = []
    lst = []
    l_interact = 18
    w_interact = 7 + 7 * (player.facing.y == 0)
    rect = player.rect
    #get starting point for interaction
    if 0 in player.facing:
        y1 = rect.y+ceil((1/2*(rect.height)*(player.facing.y+1)))-(player.facing.x*(w_interact-1))
        x1 = rect.x+ceil((1/2*(rect.width)*(player.facing.x+1)))-(player.facing.y*(w_interact-1)/2)-(player.facing.y)*3
    else:
        y1 = rect.y+round((1/2*(rect.height-1)*(player.facing.y+1))) + (player.facing.y) * 10
        x1 = rect.x+round((1/2*(rect.width-1)*(player.facing.x+1)))
    for i in range(w_interact):
        for j in range(1,l_interact):
            filled = False
            if 0 in player.facing:
                y = y1+2*(j*player.facing.y+i*player.facing.x)
                x = x1+2*(j*player.facing.x+i*player.facing.y)
            else:
                y = y1+2*(((j%2)*j*player.facing.y)+(int(not(j%2))*(j-1)*player.facing.y)-i*player.facing.y)
                x = x1+2*(int(not(j%2))*j*player.facing.x)+((j%2)*(j-1)*player.facing.x)
            if debug:
                view.screen.fill((255,255,255),rect=gm.Rect(x-view.rect.x+view.border,y-view.rect.y+view.border,1,1))
            for k in world.sprites:
                for sprite in k:
                    for box in sprite.hitbox:
                        if box.collidepoint(x,y) and sprite != player:
                            if not sprite.empty:
                                filled = True
                            if sprite.interact:
                                lst.append(sprite)
                                filled = True
                                break
                    if filled: break
                if filled: break 
            if filled: break
    return lst   
#Menu functions
def simple(message, keys, world, view, viewpoint = "0.0", x = 0, y = 200):
    keys = [ord(str(i)) for i in keys]
    stop = False
    text = Textdata()
    disp(world,view,text,viewpoint)
    
    x = view.rect.x + view.border + x
    y = view.rect.y + view.border + y
    text.add(message, x, y ,len(message)+2,None,view,False, size = 30)
    for i in range(len(message)+1):
        text.update(view)
        for event in gm.event.get():
            if event.type == gm.QUIT:
                exit()
            elif event.type == gm.KEYDOWN and event.key == gm.K_RETURN:
                text.finish()
                stop = True
                break
        disp(world,view,text,viewpoint)
        view.screen.fill((80,80,80),rect=gm.Rect(view.border, view.border,
                                                view.rect.width, view.rect.height),special_flags=gm.BLEND_ADD)
        view.screen.fill((0,0,0),rect = gm.Rect(view.border,view.border,view.rect.width,view.rect.height/6))
        view.screen.fill((0,0,0),rect = gm.Rect(view.border,view.border + view.rect.height*5/6,
                                                view.rect.width,view.rect.height/6 + 1))
        gm.display.flip()
        clock.tick(60)
        if stop:
            break
    while 1:
        for event in gm.event.get():
            if event.type == gm.QUIT:
                exit()
            elif event.type == gm.KEYDOWN:
                if event.key in keys:
                    return(chr(int(event.key)))
def timed(time, world, view, text, viewpoint = "0.0"):
    for i in range(int(time*60)):
        for event in gm.event.get():
            if event.type == gm.QUIT:
                exit()
        disp(world,view,text,viewpoint)
        view.screen.fill((80,80,80),rect=gm.Rect(view.rect.x + view.border,view.rect.y + view.border,
                                                view.rect.width, view.rect.height),special_flags=gm.BLEND_ADD)
        view.screen.fill((0,0,0),rect = gm.Rect(view.border,view.border,view.rect.width,view.rect.height/6))
        view.screen.fill((0,0,0),rect = gm.Rect(view.border,view.border + round(view.rect.height*5/6),
                                                view.rect.width,view.rect.height/6))
        gm.display.flip()
        clock.tick(60)
def binary(message, world, view, viewpoint = "0.0", x = 5, y = 200):
    return(simple(message, ["y","n"], world, view, viewpoint, x, y))
def pause(message, world, view, viewpoint = "0.0", x = 5, y = 200):
    simple(message + " Press enter to continue.", ["\r"], world, view, viewpoint, x, y)
def pausegame(world, view):
    return(simple("Game paused. Press escape to resume and q to go to main menu.", ["\x1b","q"], world, view))
def talkscene(messages, world, view, viewpoint = "0.0", x = 5, y = 200):
    for i in messages:
        self.pause(i, world, view, viepoint, x, y)
#Animation Functions
def fade(world,view,text,time,fadeout = True):
    for i in range(time*60):
        for event in gm.event.get():
            if event.type == gm.QUIT:
                exit()
        disp(world,view,text)
        surf = gm.Surface([view.rect.width,view.rect.height])
        if fadeout:
            surf.set_alpha(i/(time*60) * 256)
        else:
            surf.set_alpha(256 - (i/(time*60)) * 256)
        view.screen.blit(surf,[view.border,view.border])
        gm.display.flip()
        clock.tick(60)
def slide(world,view,text,time,start,end):
    start = world.sprites[start]
    end = world.sprites[end]
    focus = world.sprites["26.0"]
    focus.move_rect(start.rect.x,start.rect.y, offset = False)
    world.sprites.add(focus)
    for i in range(60):
        #Do stuff here
        disp(world,view,text,focus.tag)
#General Display Function
def disp(world,view,text,center = "0.0"):
    "Function for displaying all sprites in their correct location"
    player = world.sprites["0.0"]
    #calls the view centering function, and then draws all the sprites
    view.center(world,center)
    view.screen.blit(veryback,(0,0))
    view.screen.blit(world.background,(view.border-view.rect.x,view.border-view.rect.y))
    for group in world.sprites:
        for sprite in group:
            if gm.sprite.collide_rect(sprite,view):
                sprite.show = True
                if sprite.alive:
                    continue
                view.screen.blit(sprite.image,[sprite.rect.x - view.rect.x + view.border,
                                               sprite.rect.y - view.rect.y + view.border])
            else:
                sprite.show = False
    for group in world.sprites:
        for sprite in group:
            if sprite.alive and sprite.show:
                view.screen.blit(sprite.image,[sprite.rect.x - view.rect.x + view.border,
                                               sprite.rect.y - view.rect.y + view.border])
            if isinstance(sprite,Pc) and sprite.dodging > 10:
                direction = sprite.image_name[6:]
                xchange = 0
                ychange = 0
                if direction == "left":
                    xchange = 20
                elif direction == "right":
                    xchange = -20
                elif direction == "up":
                    ychange = 50
                elif direction == "down":
                    ychange = -10
                image = images["playerdash" + direction]
                view.screen.blit(image,[sprite.rect.x + xchange - view.rect.x + view.border,
                                        sprite.rect.y +ychange - view.rect.y + view.border])
    #health bars
    for sprite in world.sprites["17"]:
        if sprite.show:
            view.screen.fill((255,0,0),rect=gm.Rect(sprite.rect.x - view.rect.x + view.border,
                                    sprite.rect.y - 5 - view.rect.y + view.border, sprite.rect.width, 3))
            view.screen.fill((0,255,0),rect=gm.Rect(sprite.rect.x - view.rect.x + view.border,
                                    sprite.rect.y - 5 - view.rect.y + view.border,
                                    round(sprite.health/sprite.maxhealth * sprite.rect.width * 1.3),3))
    view.screen.fill((255,0,0),rect=gm.Rect(10+view.border,10+view.border,round(player.maxhealth*10),10))
    view.screen.fill((0,255,0),rect=gm.Rect(10+view.border,10+view.border,round(player.health*10),10))    
    #This will show hitboxes if hitbox mode is on
    if view.hitbox:
        for i in world.sprites:
            for j in i:
                for hitbox in j.hitbox:
                    view.screen.fill((0,255,0,0),rect = gm.Rect(hitbox.x - view.rect.x + view.border,
                                    hitbox.y - view.rect.y + view.border, hitbox.width,hitbox.height))
    
    #display text from Text object
    for i in text.texts:
        view.screen.blit(i.words,i.rect.move(view.border-view.rect.x,view.border-view.rect.y))
        continue
        if abs(i.max_time - i.time) >= 2:# or i.rect.height >= view.rect.height or i.rect.width >= view.rect.width:
            view.screen.blit(i.words,i.rect.move(view.border-view.rect.x,view.border-view.rect.y))
            continue
        if not view.rect.contains(i.rect):
            if i.rect.y < view.rect.y:
                i.rect.move_ip(0,view.rect.y - i.rect.y)
            elif i.rect.bottom > view.rect.bottom:
                i.rect.move_ip(0,view.rect.bottom - i.rect.bottom)
            if i.rect.right > view.rect.right:
                i.rect.move_ip(view.rect.right - i.rect.right,0)
            elif i.rect.x < view.rect.x:
                i.rect.move_ip(view.rect.x - i.rect.x, 0)
        view.screen.blit(i.words,i.rect.move(view.border-view.rect.x,view.border-view.rect.y))
             
    #drawing black spaces
    rect = gm.Rect(0,view.view_size[1]+view.border,view.screen_size[0],view.screen_size[1]-view.view_size[1])
    view.screen.fill([0,0,0],rect = rect)
    rect = gm.Rect(view.view_size[0]+view.border,0,view.screen_size[0]-view.view_size[0],view.screen_size[1])
    view.screen.fill([0,0,0],rect = rect)
    #getting text
    space = view.font.render("",False,(255,255,255))
    buttons = [view.font.render(player.inames[i] + ": " + str(player.items[i]),False,(255,255,255))
                for i in range(len(player.items)) if player.inames[i] != None]
    buttons.append(space)
    buttons += [view.font.render(i.name,False,(255,255,255)) if i != player.hand
                else view.font.render(i.name,False,(255,0,0)) for i in player.tools]
    if view.debug:
        buttons.append(view.font.render("FPS:%s" % (view.fps), False, (255,255,255)))
    for i in range(len(buttons)):
        view.screen.blit(buttons[i],(view.view_size[0] + view.border*2,view.border + 40*i))   
    #Drawing border:
    border_color = (120,80,20)
    view.screen.fill((border_color),rect = gm.Rect(0,0,view.screen_size[0],view.border))#top
    view.screen.fill((border_color),rect = gm.Rect(0,0,view.border,view.screen_size[1]))#left
    view.screen.fill((border_color),rect = gm.Rect(0,view.screen_size[1]-view.border,
                                                  view.screen_size[0],view.border))#bottom
    view.screen.fill((border_color),rect = gm.Rect(view.screen_size[0]-view.border,0,
                                                  view.border,view.screen_size[1]))#right
    view.screen.fill((border_color),rect = gm.Rect(view.view_size[0]+view.border,view.border,view.border,
                                                  view.view_size[1]))#middle
#define images, background
spritesheet = gm.image.load("./Graphics/spritesheet.png")
with open("spritemap.json","r") as file:
    images = json.load(file)
for i in images:
    surf = gm.Surface(images[i][1],gm.SRCALPHA)
    surf.blit(spritesheet,(images[i][0][0]*-33,images[i][0][1]*-33))
    surf = gm.transform.scale(surf,(images[i][1][0]*2,images[i][1][1]*2)).convert_alpha()
    #gm.image.save(gm.transform.scale_by(surf,0.5),f"individual_sprites/{i}.png")
    images[i] = surf
background = gm.image.load("./Graphics/background.png").convert_alpha()
veryback = gm.transform.scale(gm.image.load("./Graphics/veryback.png").convert_alpha(),(1200,1200))
#FYI: weapon(damage, strength, reach, speed, up, down, name, taxon)
weapons = {"empty": Weapon(1, 0, 16, 50, 20, 10, "Empty Hand", "empty"),
           "sword": Weapon(5, 10, 32, 50, 25, 15, "Basic Sword", "sword"),
           "worsesword": Weapon(2, 9, 32, 90, 35,15, "Worse Sword", "sword"),
           "heavysword": Weapon(5, 15, 48, 120, 50, 15, "Heavy Sword", "sword"),
           "gun": Weapon(1, 1, None, 45, 5, 5, "Basic Gun", "Gun"),
           "autogun" : Weapon(1, 1, None, 3, 0, 1, "Machine Gun", "gun")}
clock = gm.time.Clock()
