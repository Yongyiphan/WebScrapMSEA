import requests
from bs4 import BeautifulSoup
import time
import pandas
import lxml
import cchardet

mainurl = "https://ayumilove.net/maplestory/"

setToTrack = ['Genesis', 'Arcane', 'Utgard','Absolab', 'Fafnir', 'Lapis','Lazuli']
Mclasses = ['Warrior', 'Bowman', 'Magician','Mage','Thief', 'Pirate']
WarriorW = []
BowManW = []
MageW = []
ThiefW = []
PirateW = []
WeapLinks = []
def main():

    start = time.time()

    retrieveMainP()


    end = time.time()

    print(f'Time taken: {end-start}')
    
    return

def retrieveMainP():
    
    request_session = requests.sessions.session()
    
    Mpage = request_session.get(mainurl)
    
    if Mpage.status_code == 404:
        return    
    
    soup = BeautifulSoup(Mpage.content, 'lxml')
    weapContent = soup.find_all('ul')[4].find_all('li')
    
    temp = []
    baseWeapT = {}
    # for i in weapContent:
    #     items  = i.get_text().split(",")
    #     Jtype =  items[0].split(":")[0]
    #     baseWeapT[Jtype] = []
    #     baseWeapT[Jtype].append(items[0].split(":")[1][1:])
    #     items =  items[1:]
    #     for l in items:
    #         if l == "":
    #             continue
    #         baseWeapT[Jtype].append(l[1:])
    #     for l in i:
    #         if l.find('href') != -1:
    #             WeapLinks.append(l['href'])
    #         else:
    #             continue

    for i in weapContent:
        tempD = {}
        for l in i:
            if l.find('href') != -1:
                if l.get_text().find(":") != -1:
                    ClassType = l.get_text()[:-1]
                    baseWeapT[ClassType] = tempD
                    continue
                tempD["WeaponType"] = i.get_text()
                baseWeapT[ClassType].update(tempD)
    
    print(baseWeapT['Warrior'])
    return

main()