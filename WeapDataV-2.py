from bs4.builder import TreeBuilder
from numpy import fabs
import pandas
import requests
import lxml
import cchardet
import time
from bs4 import BeautifulSoup
from requests.sessions import session

### PROGRAM FLOW ####
# MAIN PAGE -> GET EQUIPNAME/LINK 
# TRAVERSE TO EQUIPLINK PAGE -> GET WEAPON SET'S LINK
# TRAVERSE TO WEAPON'LINK -> RECORD INFORMATION
defaulturl = "https://maplestory.fandom.com"
weaponUrl = "/wiki/Category:Weapons"
secUrl = "/wiki/Category:Secondary_Weapons"
equipSetUrl = "/wiki/Category:Equipment_Sets"
genesisWeapUrl = "/wiki/Sealed_Genesis_Weapon_Box"
EquipSetTrack = [
    'Sengoku', 'Boss Accessory', 'Pitched Boss', 'Seven Days', "Ifia's Treasure",'Mystic','Ardentmill','Blazing Sun',
    'Necromancer', '7th', '8th', 'Royal Von Leon','Root Abyss', 'AbsoLab', 'Arcane',
    'Lionheart', 'Dragon Tail','Falcon Wing','Raven Horn','Shark Tooth',
    'Gold Parts','Pure Gold Parts'
    ]
Mclasses = ['Warrior', 'Bowman', 'Magician','Thief', 'Pirate']
trackMinLevel = 140

def main():

    ##PROCESS
    ##EQUIPMENT_SETS ==> GATHER TRACKSET LINKS
    ##ITERATE TRACKSET LINKS
    ## CREATE 3 DATAFRAME
    ## 1: EQUIPMENT SET EFFECTS
    ## 2: EQUIPMENT ARMOR/ACCESSORIES
    ## 3: EQUIPMENT WEAPON
    start = time.time()
    request_session = requests.session()
    linkCollection = []
    equipSetL = []
    equipSetLinkListPage = request_session.get(defaulturl + equipSetUrl)
    
    soup = BeautifulSoup(equipSetLinkListPage.content, 'lxml')
    linkLists = soup.find_all('a', class_='category-page__member-link')
    
    ignoreSetKeyWords = ['Immortal', 'Eternal','Walker','Anniversary']
    WeaponDF = pandas.DataFrame()
    ArmorDF = pandas.DataFrame()
    AccessoriesDF = pandas.DataFrame()
    SetEffectDF = pandas.DataFrame()
    for links in linkLists:
        linkText = links.next.lower()
        for li in EquipSetTrack:
            if li.lower() in linkText and any(ig.lower() in linkText for ig in ignoreSetKeyWords) == False:
                equipSetL.append(li)
                linkCollection.append(links['href'])

                print(f"\n Adding {li} items.\n")
                tempCollection = retrieveContents(links['href'], request_session, li)
                if len(tempCollection) == 3:
                    SetEffectDF = SetEffectDF.append(tempCollection[0], ignore_index=True)
                    ArmorDF = ArmorDF.append(tempCollection[1], ignore_index=True)
                    WeaponDF =  WeaponDF.append(tempCollection[2], ignore_index=True)
                elif len(tempCollection) == 2:
                    SetEffectDF = SetEffectDF.append(tempCollection[0], ignore_index=True)
                    AccessoriesDF = AccessoriesDF.append(tempCollection[1], ignore_index=True)


    # for i in linkCollection:
    #     print(i['href'])
    
    # retrieveContents returns 3/2 DF
    # append accordingly to empty DF
    # fillna --> push to csv

    # testSelection = 11
    # cdf = retrieveContents(linkCollection[testSelection], request_session, equipSetL[testSelection])

    SetEffectDF.to_csv('SetEffectData.csv')
    WeaponDF.to_csv('WeaponDF.csv')
    ArmorDF.to_csv('ArmorDF.csv')
    AccessoriesDF.to_csv('AccessoriesDF.csv')

    end = time.time()

    print(f"Total time taken is {end-start}")
    return

def retrieveContents(subUrl, session, equipSet):

    subPage = session.get(defaulturl + subUrl)
    if subPage.status_code != 200:
        return
    
    totalPageContent = BeautifulSoup(subPage.content, 'lxml')
    wikitables = totalPageContent.find_all('table', class_="wikitable")

    

    comList = []

    if len(wikitables) == 3:
        setTable = wikitables[0]
        equipTable = wikitables[1]
        weaponTable = wikitables[2]

        setDF = retrieveSetEffect(setTable, equipSet)
        equipDF = retrieveEquips(equipTable, equipSet)
        weapDF = retrieveWeap(weaponTable, equipSet)

        comList = [setDF, equipDF, weapDF]

    elif len(wikitables) == 2:
        setTable = wikitables[0]
        equipTable = wikitables[1]

        setDF = retrieveSetEffect(setTable, equipSet)
        equipDF = retrieveEquips(equipTable, equipSet)

        comList = [setDF, equipDF]


    return comList


def retrieveSetEffect(wikitable, equipSet):

    start = time.time()
    currentDF = pandas.DataFrame()

    tdContent = wikitable.find_all('td')

    startCounter = len(tdContent) % 2

    for i in range(startCounter, len(tdContent), 2):
        SetData = {}
        SetData['EquipSet'] = equipSet
        SetData['SetEffect'] = tdContent[i].next.next.split(" ")[0]
        statList = tdContent[i].get_text(separator = '\n').split('\n')[1:]
        SetData.update(assignToDict(statList))
        
        

        currentDF = currentDF.append(SetData, ignore_index=True)

    end = time.time()
    print(currentDF, '\n')
    print(f"{equipSet} set effect added in {end - start}.")
    
    return currentDF

def retrieveEquips(wikitable, equipSet):

    start = time.time()
    currentDF = pandas.DataFrame()
    tdContent = wikitable.find_all('td')


    for i in range(1, len(tdContent), 4):
        EquipData = {}
        EquipData['EquipSet'] = equipSet
        equipslot = tdContent[i].get_text()
        EquipData['EquipSlot'] = equipslot.replace("\n", "") if equipslot.find('\n')  != -1 else equipslot

        requirements = tdContent[i+1].get_text(separator = '\n').split("\n")
        if len(requirements) > 1:
            EquipData['EquipLevel'] = requirements[0].split(" ")[-1]
            EquipData['ClassType'] = requirements[1].split(" ")[-1]
        else:
            EquipData['EquipLevel'] = requirements[0].split(" ")[-1]
            EquipData['ClassType'] = 'Any'

        effects =  tdContent[i+2].get_text(separator = '\n').split('\n')
        EquipData.update(assignToDict(effects))

        
        currentDF = currentDF.append(EquipData, ignore_index=True)
    
    end = time.time()
    print(currentDF, '\n')
    print(f"{equipSet} equips added in {end -start}. ")
    


    return currentDF

def retrieveWeap(wikitable, equipSet):
    
    currentDF = pandas.DataFrame()
    tdContent = wikitable.find_all('td')
    
    for i in range(1, len(tdContent), 4):
        # start = time.time()
        WeapData = {}
        weapType = tdContent[i].get_text()
        WeapData['WeaponType'] = weapType.replace('\n', '') if weapType.find('\n') != -1 else weapType
        WeapData['WeaponSet'] = equipSet

        requirements = tdContent[i+1].contents

        hasHref = False
        JobType = "Any"
        WeapData['JobType'] = JobType
        WeapData['Level'] = '0'
        for ahref in requirements:
            if ahref.get_text().lower().find('level') != -1:
                WeapData['Level']  =  ahref.get_text().split(" ")[-1]
                continue
            if ahref.name != 'a':
                continue
            hasHref = True
            WeapData['JobType'] = ahref.next
            break
            
        if hasHref == False:
            for ahref in requirements:
                if ahref.get_text().lower().find('job') != -1:
                    WeapData['JobType'] = ahref.get_text().split(' ')[-1]
                    break
        
        if WeapData["JobType"].lower() == 'xenon':
            continue


        weapStats = tdContent[i+2].get_text(separator = '\n').split('\n')
        WeapData.update(assignToDict(weapStats))
    
        currentDF = currentDF.append(WeapData, ignore_index=True)
        
        # end =  time.time()
        # print(f"Time taken to add {equipSet} {WeapData['WeaponType']} is {end - start}. ")
       

    print(currentDF, '\n')
        
    return currentDF



def assignToDict(tempList):
    
    tempData = {}
    if tempList == None:
        return tempData
    
    for i in tempList:
        if i.find("Attack Speed") != -1:
            tempData["AtkSpd"] = i.split(" ")[-1][1:-1]
            continue
        elif i.find("STR") != -1:
            if "MainStat" in tempData:
                tempData["SecStat"] = i.split(" ")[1][1:]
            else:
                tempData["MainStat"] = i.split(" ")[1][1:]
            continue
        elif i.find("DEX") != -1:
            if "MainStat" in tempData:
                tempData["SecStat"] = i.split(" ")[1][1:]
            else:
                tempData["MainStat"] = i.split(" ")[1][1:]
            continue       
        elif i.find("INT") != -1:
            if "MainStat" in tempData:
                tempData["SecStat"] = i.split(" ")[1][1:]
            else:
                tempData["MainStat"] = i.split(" ")[1][1:]
            continue
        elif i.find("LUK") != -1:
            if "MainStat" in tempData:
                tempData["SecStat"] = i.split(" ")[1][1:]
            else:
                tempData["MainStat"] = i.split(" ")[1][1:]
            continue
        elif i.find("HP") != -1:
            HPstr = i.split(" ")[-1][1:]
            if HPstr.find(",") != -1:
                tempData['HP'] = HPstr.replace(",", "")
            elif HPstr.find("%") != -1:
                tempData['HP'] = HPstr
            continue
        elif i.find("MP") != -1:
            HPstr = i.split(" ")[-1][1:]
            if HPstr.find(",") != -1:
                tempData['MP'] = HPstr.replace(",", "")
            elif HPstr.find("%") != -1:
                tempData['MP'] = HPstr
            continue
        elif i.find("Weapon Attack") != -1:
            tempData["Atk"] = i.split(" ")[-1][1:]
            continue
        elif i.find("Magic Attack") != -1:
            tempData["MAtk"] = i.split(" ")[-1][1:]
            continue
        elif i.find("Boss") != -1:
            tempData["BossDMG"] = i.split(" ")[-1][1:-1]
            continue
        elif i.find("Ignore") != -1:
            tempData["IED"] = i.split(" ")[-1][1:-1]
            continue
        elif i.find("Speed") != -1:
            tempData["SPD"] = i.split(" ")[-1][1:]
            continue
        elif i.find("Defense") != -1:
            tempData["DEF"] = i.split(" ")[-1][1:]
            continue
        elif i.find("All Stats") != -1:
            tempData["AS"] = i.split(" ")[-1][1:]
            continue
        elif i.find("Normal") != -1:
            tempData['NormalDMG'] = i.split(" ")[-1][1:-1]
            continue
        
    
    
    return tempData


main()
