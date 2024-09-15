import math
import os
import json
import random
import pygame as gm
from time import sleep
from math import ceil, floor
from statistics import mode
from random import randint
#initialize modules and vars
gm.init()
fps = 60
clock = gm.time.Clock()
gm.display.set_caption("Legion")
#EDIT SCREEN SIZE HERE
size = [800,600]
screen = gm.display.set_mode(size, flags = gm.SCALED, vsync = 1)
import legion_func as lf
view = lf.ViewData(screen,10)
#read in save files
allsprites = []
sizes = []
backs = []
for i in os.listdir("maps"):
    if ".json" in i:
        level = int(i[5])
        while level + 1 > len(allsprites):
            allsprites.append(None)
            sizes.append(None)
            backs.append(None)
        data = lf.read_save("maps/" + i)
        allsprites[level] = lf.Collection(*data[0])
        sizes[level] = gm.Rect(0,0,data[1][0],data[1][1])
        backs[level] = gm.image.load(f"./Graphics/{data[2]}.xcf")
        try:
            allsprites[level]["0.0"]
            num = level
        except:
            pass
#data objects
world = lf.WorldData(allsprites,sizes,backs,num = num)
text = lf.Textdata()
view.debug = True

#main loop
def main():
    debug = False
    objectfacing = None
    player = world.sprites["0.0"]
    tics = [player.vector.copy()]
    running = True
    while running:
        #lf.slide(world,view,text,5,"0.0","0.0")
        #update sprite object being looked at
        if objectfacing != None:
            objectfacing.change_sprite()
        objectfacing = None
        lst = lf.looking(world,view,debug)
        if lst != []:
            objectfacing = mode(lst)
            objectfacing.change_sprite(color = [0,0,255,0])
            text.add("Press k to interact",objectfacing.rect.x,objectfacing.rect.y-18,2,objectfacing,view,
                     False,15,True)
        #Event handling
        for event in gm.event.get():
            if event.type == gm.QUIT:
                gm.quit()
                exit()
            if event.type == gm.KEYDOWN:
                if event.key == gm.K_k and debug:
                    gm.display.flip()
                    sleep(0.25)
                if (event.key == gm.K_SPACE and player.vector.magnitude() != 0 and not player.dodging and
                    not player.ragdoll):
                    player.dodging = 30
                    player.ragdoll = 20
                    player.iframe = 20
                    player.speed *= player.dodge_factor
                elif event.key == gm.K_k and objectfacing != None and not player.ragdoll:
                    objectfacing.interaction(world,player,text,view)
                    objectfacing.change_sprite(color = [0,0,255,0])
                elif event.key == gm.K_ESCAPE:
                    if lf.pausegame(world, view) == "q":
                        running = False
                elif 49 <= event.key <= 49 + len(player.tools) - 1:
                    player.hand = player.tools[event.key - 49]
                elif event.key == gm.K_j:
                    player.attack(world)
        #Get player vector
        keys = gm.key.get_pressed()
        if not player.ragdoll:
            if keys[gm.K_w] != keys[gm.K_s]:
                if keys[gm.K_w]:
                    player.vector.y = -1
                elif keys[gm.K_s]:
                    player.vector.y = 1
            else:
                player.vector.y = 0
            if keys[gm.K_a] != keys[gm.K_d]:
                if keys[gm.K_a]:
                    player.vector.x = -1
                elif keys[gm.K_d]:
                    player.vector.x = 1
            else:
                player.vector.x = 0
        #player facing
        tics.append(player.vector.copy())
        if player.vector != [0,0] and not player.ragdoll:
            if (tics[-1] == tics[-2] == tics[-3]) or (tics[-1] != tics[-2]
                        and (tics[-2].y == 0 or tics[-2].x == 0)):
                player.facing = player.vector.copy()
        #update all sprites
        world.sprites.update(world, text, view)
        if player.health <= 0:
            lf.death(world,view,text)
        #update text
        text.update(view,objectfacing)
        #remove sprites
        removing = []
        for group in world.sprites:
            for sprite in group:
                if sprite.remove:
                    removing.append(sprite.tag)
        for tag in removing:
            del world.sprites[tag]
        #graphics
        lf.disp(world,view,text)
        gm.display.flip()
        clock.tick(fps)
        view.fps = clock.get_fps()
        
if __name__ == '__main__':
    while 1:
        main()
        print("New game")
