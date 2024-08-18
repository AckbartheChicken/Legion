import pygame as gm
import json
from random import randint
import os
from time import sleep
gm.init()
#Data storage classes
class WorldData:
    "Class for storing world/game data."
    def __init__(self,allsprites,sizes,backgrounds, num = 0):
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
    def switch(self,num):
        player = self.sprites["0.0"]
        player.loc = num
        self.sprites = self.allsprites[num]
        self.background = self.allbackgrounds[num]
        self.size = self.allsizes[num]
        self.switches = self.allswitches[num]
        self.sprites.add(player)
class ViewData:
    "Class for storing view/screen data."
    def __init__(self,width, height, border = 8, wiggle = 12):
        self.screen = gm.display.set_mode([width,height], vsync = 1)
        self.screen_size = self.screen.get_size()
        self.view_size = [0.75 * (width - border * 3), height - border * 2]
        
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
        size = [(self.view_size[0] - rect.width)/2-self.wiggle,(self.view_size[1] - rect.height)/2-self.wiggle]
        xadjust = 0
        yadjust = 0
        #make camera have some lee way, so focus isn't directly center
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
    def __init__(self,words,x,y,time,obj,size = 25):
        self.words = gm.font.SysFont('sfnsmono', size, bold = True).render(words,False,(255,255,255))
        self.rect = self.words.get_rect()
        self.rect.move_ip(x,y)
        self.time = time
        self.max_time = time
        self.obj = obj
class Textdata():
    def __init__(self):
        self.font = gm.font.SysFont('sfnsmono', 25, bold = True)
        self.texts = []
    def add(self,words,x,y,time,obj,replace,size = 25):
        if obj != None:
            for i in self.texts:
                if i.obj == obj:
                    if not replace and i.time != 0:
                        break
                    self.texts.remove(i)
                    self.texts.append(Text(words,x,y,time,obj,size))
                    break
            else:
                self.texts.append(Text(words,x,y,time,obj,size))
        elif obj == None:
            self.texts.append(Text(words,x,y,time,obj,size))
        
    def update(self):
        removing = []
        for i in self.texts:
            if i.time > 0:
                i.time -= 1
            else:
                removing.append(i)
        for i in removing:
            self.texts.remove(i)
    
class Group:
    "Container class for storing and manipulating groups of sprites"
    def __init__(self, *sprites):
        for i in sprites:
            if not isinstance(i,Basic):
                raise TypeError(f"Must contain only game objects (Inherited from 'basic' class), not {type(i)}")
        self.sprites = dict(zip([i.tag.split(".")[1] for i in sprites], sprites))
    def update(self,world,text):
        stop = False
        for sprite in self:
            sprite.update(world,text)
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
        self.collection = dict(zip([str(i) for i in range(26)],[Group() for i in range(26)]))
        for i in sprites:
            if not isinstance(i,Basic):
                raise TypeError(f"Must only contain sprites, not {type(i)}.")
            tag = i.tag.split(".")
            self.collection[tag[0]][tag[1]] = i
    def add(self,*sprites):
        for i in sprites:
            if not isinstance(i,Basic):
                raise TypeError(f"Collection.add() must only contain sprites, not {type(i)}.")
            tag = i.tag.split(".")
            if tag[0] not in self.collection.keys():
                self.collection[tag[0]] = Group()
            self.collection[tag[0]][tag[1]] = i
    def update(self,world,text):
        for group in self:
            group.update(world,text)
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
    def update(self,world,text):
        pass
    def interaction(self,world,moving,text):
        pass
    def copy(self):
        return(__class__(self.x, self.y, self.tag, self.image))
    def remove(self):
        self.remove = True
    def movein(self,world,moving):
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
class Iblock(Basic):
    "Sprite class for immovable blocks. (Walls). Tag is 1.x."
    def __init__(self, x, y, tag, image = 'iblock'):
        super().__init__(x, y, tag, image)
class Spike(Basic):
    "Sprite class for spikes. Tag is 2.x."
    def __init__(self, x, y, tag, image = 'spike'):
        super().__init__(x, y, tag, image)
        self.empty = True
        self.hierarchy = "1"
    def checking(self,world,moving):
        return moving.alive
    def movein(self,world,moving):
        #Placeholder. Write this once player knockback and movement is done.
        if moving.alive:
            moving.hit(world,2,moving.poise + 2, gm.Vector2(moving.vector.x*-1,moving.vector.y*-1))
        return False
class Savepoint(Basic):
    "Sprite class where player will save progress. Tag is 3.x."
    def __init__(self, x, y, tag, image = "save"):
        super().__init__(x, y, tag, image)
        self.interact = True
    def interaction(self,world,moving,text):
        for level in [i for i in os.listdir("maps/") if ".json" in i]:
            pass
class Sign(Basic):
    "Sprite class that player can read by interacting with. Tag is 4.x."
    def __init__(self, x, y, tag, message = "", image = 'sign'):
        super().__init__(x, y, tag, image)
        self.message = message
        self.interact = True
        self.empty = True
    def interaction(self,world,moving,text):
        text.add(self.message,self.rect.x,self.rect.y-18,60,self,True,15)
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
    def interaction(self,world,moving,text):
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
            text.add("The chest is locked",self.rect.x,self.rect.y-18,60,self,True,15)
        else:
            text.add("The chest is locked by some mechanism",self.rect.x,self.rect.y-18,60,self,True,15)
    def update(self,world,text):
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
    def interaction(self,world,moving,text):
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
    def interaction(self,world,moving,text):
        if not self.locked:
            self.empty = True
            self.change_sprite("dooropen")
            self.interact = False
        elif self.key and moving.items[0] >= 1:
            self.locked = False
            moving.items[0] -= 1
            self.change_sprite("doorclosed")
        elif self.key:
            text.add("The door is locked",self.rect.x,self.rect.y-18,60,self,True,15)
        else:
            text.add("The door is locked by some mechanism",self.rect.x,self.rect.y-18,60,self,True,15)
    def update(self,world,text):
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
class Mapdoor(Door):
    "Sprite class for door that leads between maps. Tag is 7.x."
    def __init__(self, x, y, tag, direction, target, place, locked = False, key = False, times = 1,
                 changed = 0,switch = None,switch_val = 1):
        image = "dooropen"
        if locked:
            image = "doorlocked"
        else:
            image = "doorclosed" 
        super().__init__(x,y,tag,switch,switch_val,locked,key,times,changed,image)
        self.direction = direction
        self.target = target
        self.place = place
        self.active = True
    def update(self,world,text):
        super().update(world,text)
        if not world.sprites.collide(self):
            self.active = True
    def movein(self,world,moving):
        #return if not active (used to make sure players can move when tp'd to the mapdoor)
        if not self.active:
            return True
        self.active = False
        world.switch(self.place)
        target = world.sprites[self.target]
        target.empty = True
        target.change_sprite("dooropen")
        target.interact = False
        target.active = False
        moving = world.sprites["0.0"]
        x = target.rect.x - moving.rect.x
        y = target.rect.y - moving.rect.y
        moving.rect.move_ip(x,y)
        moving.hitbox.move_ip(x,y)
        #add better movement once cutscenes are implemented
        return False
class Lever(Basic):
    "Sprite class for a toggler that switches when interacted with. Tag is 8.x."
    def __init__(self, x, y, tag, switch, image = "leveroff"):
        super().__init__(x,y,tag,image)
        self.on = False
        self.interact = True
        self.switch = switch
    def interaction(self,world,moving,text):
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
    def update(self, world, text):
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
    def __init__(self, x, y, tag, switch, others = [""], active = False, image = "eblock"):
        super().__init__(x, y, tag, switch, image)
        self.others = others
        self.active = True
    def update(self, world, text):
        if self.active:
            super().update(world, text)
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
    def movein(self, world, moving):
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
    def movein(self,world,moving):
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
        self.facing = gm.math.Vector2(-1,0)
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
    def move(self,world):
        "A function specifically for alive sprites to check if they can move along their vector."
        for i in range(self.speed):
            for vector in (gm.math.Vector2(self.vector.x,0),gm.math.Vector2(0,self.vector.y)):
                stop = False
                self.rect.move_ip(vector.x,vector.y)
                self.hitbox.move_ip(vector.x,vector.y)
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
                    self.rect.move_ip(-1*vector.x,-1*vector.y)
                    self.hitbox.move_ip(-1*vector.x,-1*vector.y)
                    continue
                #sorting of ranks
                ordered = sorted(list(ranking)[1:]) + ["None"]
                ranking = dict(zip(ordered,[ranking[i] for i in ordered]))
                stop = False
                #calling movein ranked functions
                for group in ranking:
                    for sprite in ranking[group]:
                        if not sprite.remove:
                            stop = not sprite.movein(world,self)
                        if stop:
                            break
                    if stop:
                        break
                if stop:
                    self.rect.move_ip(-1*vector.x,-1*vector.y)
                    self.hitbox.move_ip(-1*vector.x,-1*vector.y)
    def hit(self,world,damage,power,vector):
        if self.health != None and not self.iframe:
            self.health -= damage
            if power > self.poise:
                self.vector.x,self.vector.y = [0,0]
            self.ragdoll = (power-self.poise) * 5 * (power > self.poise)
            self.iframe = (power-self.poise) * 10 * (power > self.poise)
            self.damaged = (power-self.poise) * 10 * (power > self.poise)
            self.vector = vector.copy()
    def attack(self):
        pass
class Projectile(Alive):
    "Sprite class for projectiles, including bullets/arrows etc. Tag is 16.x."
    def __init__(self,x,y,tag,vector,image = "projectile"):
        super().__init__(self,x,y,tag,image = image)
        self.empty = True
        self.vector = vector
    def update(self,world,text):
        #Placeholder
        pass
    def movein(self,world,moving):
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
    def movein(self,world,moving):
        tag = randint(20,23)
        if str(tag) in world.sprites.collection and len(world.sprites[str(tag)].sprites) !=  0:
            tag2 = int(max(world.sprites[str(tag)].sprites.keys())) + 1
        else:
            tag2 = "0"
        sprite = world.classtype[tag](self.rect.x,self.rect.y,f"{tag}.{tag2}")
        world.sprites.add(sprite)
        self.remove = True
        return True
class Pc(Alive):
    "Sprite class for player character. Tag is 0.x."
    def __init__(self, x, y, tag, health = 20, maxhealth = 20, poise = 5,items = [0,0,0,0,0,0,0], tools = [],
                 loc = 0, image = "playerdown", god = False, hitbox = None):
        super().__init__(x, y, tag , health , maxhealth , poise, god, image, hitbox)
        self.hitbox = Hitbox(gm.Rect(self.rect.x, self.rect.y, 40, 36),
                             gm.Rect(self.rect.x+6, self.rect.y+36, 28, 12))
        self.items = items
        self.inames = ["doorkey","chestkey","bosskey","ammo",None,"money",None]
        self.imax = [10,10,1,30,None,50,None]
        self.tools = tools
        self.loc = loc
    def update(self,world,text):
        psprites = [["playerupleft", "playerup", "playerupright"],
                    ["playerleft", None, "playerright"],
                    ["playerdownleft","playerdown","playerdownright"]]
        if self.damaged:
            self.change_sprite(psprites[int(self.facing.y+1)][int(self.facing.x+1)],(255,0,0))
        else:
            self.change_sprite(psprites[int(self.facing.y+1)][int(self.facing.x+1)])
        
        loc = self.loc
        if self.vector.magnitude() != 0:
            self.move(world)
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
    def additem(self, where, num):
        for i in range(num):
            if (self.imax[where] == None or self.items[where] < self.imax[where]):
                self.items[where] += 1
class Enemy(Alive):
    "Sprite class for enemy object. Tag is 17.x."
    def __init__(self, x, y, tag, health, maxhealth, poise, weapon, vision, inventory, image = "playerdown",
                 hitbox = None):
        super().__init__(x, y, tag, health, maxhealth, poise, image = image, hitbox = hitbox)
        self.hitbox = Hitbox(gm.Rect(self.rect.x, self.rect.y, 40, 36),
                             gm.Rect(self.rect.x+6, self.rect.y+36, 28, 12))
    def update(self,world,text):
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
def death(world,view,text):
    text.add("You died. Lol.",view.rect.centerx-30,view.rect.centery,1,None,False,30)
    disp(world,view,text)
    gm.display.flip()
    sleep(2)
    exit()
def disp(world,view,text,center = "0.0"):
    "Function for displaying all sprites in their correct location"
    view.screen.blit(world.background,(view.border-view.rect.x,view.border-view.rect.y))
    player = world.sprites["0.0"]
    #calls the view centering function, and then draws all the sprites
    view.center(world,center)
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
    #health bars
    for sprite in world.sprites["17"]:
        if sprite.show:
            #THIS IS WRONG. PLEASE FIX IT BEFORE ADDING ENEMIES
            continue
            view.screen.fill((255,0,0),rect=pygame.Rect(i.x*2-view.xadjust,i.y*2-5-view.yadjust,i.width*2,3))
            view.screen.fill((0,255,0),rect=pygame.Rect(i.x*2-view.xadjust,i.y*2-5-view.yadjust,round(i.health/i.maxhealth*i.width*2),3))
    view.screen.fill((255,0,0),rect=gm.Rect(10+view.border,10+view.border,round(player.maxhealth*10),10))
    view.screen.fill((0,255,0),rect=gm.Rect(10+view.border,10+view.border,round(player.health*10),10))    
    #This will show hitboxes if hitbox mode is on
    if view.hitbox:
        for i in world.sprites:
            for j in i:
                for hitbox in j.hitbox:
                    view.screen.fill((0,255,0,0),rect = hitbox)
    
    #display text from Text object
    for i in text.texts:
        if abs(i.max_time - i.time) >= 2 or i.rect.width > view.rect.width or i.rect.height > view.rect.height:
            view.screen.blit(i.words,i.rect.move(view.border-view.rect.x,view.border-view.rect.y))
            continue
        while not view.rect.contains(i.rect):
            if i.rect.y < view.rect.y:
                i.rect.move_ip(0,1)
            elif i.rect.bottom > view.rect.bottom:
                i.rect.move_ip(0,-1)
            if i.rect.right > view.rect.right:
                i.rect.move_ip(-1,0)
            elif i.rect.x < view.rect.x:
                i.rect.move_ip(1,0)
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
    if view.debug:
        buttons.append(view.font.render("FPS:%s" % (view.fps), False, (255,255,255)))
    for i in range(len(buttons)):
        view.screen.blit(buttons[i],(view.view_size[0] + view.border*2,view.border + 40*i))   
    #Drawing border:
    view.screen.fill((100,70,80),rect = gm.Rect(0,0,view.screen_size[0],view.border))#top
    view.screen.fill((100,70,80),rect = gm.Rect(0,0,view.border,view.screen_size[1]))#left
    view.screen.fill((100,70,80),rect = gm.Rect(0,view.screen_size[1]-view.border,
                                                  view.screen_size[0],view.border))#bottom
    view.screen.fill((100,70,80),rect = gm.Rect(view.screen_size[0]-view.border,0,
                                                  view.border,view.screen_size[1]))#right
    view.screen.fill((100,70,80),rect = gm.Rect(view.view_size[0]+view.border,view.border,view.border,
                                                  view.view_size[1]))#middle
#define sprites,background
spritesheet = gm.image.load("./Graphics/spritesheet.png")
with open("spritemap.json","r") as file:
    images = json.load(file)
for i in images:
    surf = gm.Surface(images[i][1],gm.SRCALPHA)
    surf.blit(spritesheet,(images[i][0][0]*-33,images[i][0][1]*-33))
    surf = gm.transform.scale(surf,(images[i][1][0]*2,images[i][1][1]*2))
    images[i] = surf
background = gm.image.load("./Graphics/background.png")
