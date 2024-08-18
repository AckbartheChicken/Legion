import legion_func as lf
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
#define sprites,background
spritesheet = gm.image.load("./Graphics/spritesheet.png")
with open("spritemap.json","r") as file:
    images = json.load(file)
for i in images:
    surf = gm.Surface(images[i][1],gm.SRCALPHA)
    surf.blit(spritesheet,(images[i][0][0]*-33,images[i][0][1]*-33))
    surf = gm.transform.scale(surf,(images[i][1][0]*2,images[i][1][1]*2))
    images[i] = surf
#create sprites

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
        backs[level] = gm.image.load(f"./Graphics/{data[2]}.png")
#data objects
world = lf.WorldData(allsprites,sizes,backs)
gm.display.set_caption("Legion")
view = lf.ViewData(800,600)
text = lf.Textdata()
view.debug = True
#view.hitbox = True
#main loop
def main():
    debug = False
    objectfacing = None
    player = world.sprites["0.0"]
    tics = [player.vector.copy()]
    while 1:
        #Interaction
        ys = []
        xs = []
        lst = []
        l_interact = 18
        w_interact = 20
        if objectfacing != None:
            objectfacing.change_sprite()
        objectfacing = None
        rect = player.rect
        #get starting point for interaction
        if 0 in player.facing:
            y1 = rect.y+ceil((1/2*(rect.height)*(player.facing.y+1)))-(player.facing.x*(w_interact-1))
            x1 = rect.x+ceil((1/2*(rect.width)*(player.facing.x+1)))-(player.facing.y*(w_interact-1)/2)-(player.facing.y)*10
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
                   
        #update sprite object being looked at
        if lst != []:
            objectfacing = mode(lst)
            objectfacing.change_sprite(color = [0,0,255,0])
            text.add("Press k to interact",objectfacing.rect.x,objectfacing.rect.y-18,1,objectfacing,False,15)
        
        #Event handling
        for event in gm.event.get():
            if event.type == gm.QUIT:
                gm.quit()
                exit()
            if event.type == gm.KEYDOWN:
                if event.key == gm.K_k and debug:
                    gm.display.flip()
                    sleep(0.5)
                if (event.key == gm.K_SPACE and player.vector.magnitude() != 0 and not player.dodging and
                not player.ragdoll):
                    player.dodging = 30
                    player.ragdoll = 20
                    player.iframe = 20
                    player.speed *= 2
                elif event.key == gm.K_k and objectfacing != None and not player.ragdoll:
                    objectfacing.interaction(world,player,text)
                    objectfacing.change_sprite(color = [0,0,255,0])
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
                player.facing.x = player.vector.x
                player.facing.y = player.vector.y
        #update all sprites
        world.sprites.update(world,text)
        if player.health <= 0:
            lf.death(world,view,text)
        #update text
        text.update()
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
    main()
