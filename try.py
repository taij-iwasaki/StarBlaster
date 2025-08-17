import pygame as pg

def main():
    pg.init()
    screen = pg.display.set_mode((800,800))

    while True:
        screen.fill(pg.Color("white"))
        pg.display.update()
    
main()