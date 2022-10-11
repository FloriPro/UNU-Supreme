from PIL import Image

im = Image.open("Cards/full.png")

Farben = ["red", "yellow", "green", "blue"]
Z = ["0","1", "2", "3", "4", "5", "6", "7", "8", "9",
     "aussetzen", "richtungswechsel", "2+", "farbwechsel"]
cardXSize = 86
cardYSize = 129

jumpX = 0
jumpY = 0

startX = 0
startY = 0

iX = 0
for pX in range(startX, len(Z)*(cardXSize+jumpX), (cardXSize+jumpX)):
    iY = 0
    for pY in range(startY, len(Farben)*(cardYSize+jumpY), (cardYSize+jumpY)):
        im2 = im.crop((pX, pY, pX+cardXSize, pY+cardYSize))
        try:
            im2.save("Cards/own/"+Farben[iY]+"_"+Z[iX]+".png")
        except:
            pass
        iY += 1
    iX += 1
