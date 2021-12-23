from bs4.builder import TreeBuilder
from numpy import fabs, seterrobj
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
    '8th', 'Root Abyss','Fafnir','AbsoLab', 'Arcane',
    'Lionheart', 'Dragon Tail','Falcon Wing','Raven Horn','Shark Tooth',
    'Gold Parts','Pure Gold Parts'
    ]
ArmorSet = ['Hat','Top','Btm','Overall','Shoes','Cape','Gloves']
Mclasses = ['Warrior', 'Bowman', 'Magician','Thief', 'Pirate']
SetCol = ['EquipSet','SetEffect','MainStat', 'SecStat','AS','HP','MP','DEF','Atk','MAtk','NormalDMG','IED','BossDMG','CritDMG']
WeapCol = ['JobType','WeaponSet','WeaponType','Level','AtkSpd','MainStat','SecStat','Atk','MAtk','SPD','HP','DEF','BossDMG','IED']
ArmorCol = ['EquipSet','ClassType','EquipSlot','EquipLevel','MainStat','SecStat','HP','MP','DEF','Atk','MAtk','AS','SPD','JUMP','IED']
AccCol = ['EquipName','EquipSet','ClassType','EquipSlot','EquipLevel','MainStat','SecStat','HP','MP','DEF','Atk','MAtk','AS','SPD','JUMP','IED']
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

                Mstart = time.time()
                
                tempCollection = retrieveContents(links['href'], request_session, li)
                
                SetEffectDF = SetEffectDF.append(tempCollection['SetEffect'], ignore_index=True) 
                ArmorDF = ArmorDF.append(tempCollection['Armor'], ignore_index=True)
                AccessoriesDF = AccessoriesDF.append(tempCollection['Accessories'], ignore_index=True)
                WeaponDF = WeaponDF.append(tempCollection['Weapon'], ignore_index=True)
                
                Mend = time.time()
                print(f"{li} equips added in {Mend - Mstart }. ")
                break

 
    SetEffectDF.drop_duplicates(keep='first', inplace=True)
    SetEffectDF = SetEffectDF[SetCol]
    SetEffectDF = SetEffectDF.fillna(0)
    
    WeaponDF = WeaponDF[WeapCol]
    WeaponDF = WeaponDF.fillna(0)
    
    ArmorDF = ArmorDF[ArmorCol]
    ArmorDF = ArmorDF.fillna(0)
    
    AccessoriesDF = AccessoriesDF[AccCol]
    AccessoriesDF = AccessoriesDF.fillna(0)
    
    SecWeapDF = retrieveSecWeap(request_session)
    SecWeapDF = SecWeapDF.fillna(0)
    
    SetEffectDF.to_csv('SetEffectData.csv')
    WeaponDF.to_csv('WeaponData.csv')
    ArmorDF.to_csv('ArmorData.csv')
    AccessoriesDF.to_csv('AccessoriesData.csv')
    SecWeapDF.to_csv('SecondaryWeapData.csv')
    end = time.time()

    print(f"Total time taken is {end-start}")
    return



def retrieveContents(subUrl, session, equipSet):

    #SCRAPING EACH PAGE
    subPage = session.get(defaulturl + subUrl)
    if subPage.status_code != 200:
        return
    
    totalPageContent = BeautifulSoup(subPage.content, 'lxml')
    wikitables = totalPageContent.find_all('table', class_="wikitable")

    initETDF = pandas.DataFrame()

    smallCollection = {}
    smallCollection['SetEffect'] = retrieveSetEffect(wikitables[0], equipSet)
    smallCollection['Armor'], smallCollection['Accessories'] = retrieveEquips(wikitables[1], equipSet)
    if len(wikitables) == 3:
        smallCollection['Weapon'] = retrieveWeap(wikitables[2], equipSet)
    else:
        smallCollection['Weapon'] = initETDF
    
    
    return smallCollection


def retrieveSetEffect(wikitable, equipSet):

    #SCRAPING EACH TABLE
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
        
    currentDF = currentDF.fillna(0)
    
    return currentDF

def retrieveEquips(wikitable, equipSet):

    ArmorDF = pandas.DataFrame()
    AccDF = pandas.DataFrame()
    tdContent = wikitable.find_all('td')

    for i in range(0, len(tdContent), 4):
        EquipData = {}
        EquipData['EquipSet'] = equipSet
        equipName = tdContent[i].get_text()
        equipslot = tdContent[i+1].get_text()
        EquipData['EquipSlot'] = removeN(equipslot, '\n')
        equipType = 'Armor' if EquipData['EquipSlot'] in ArmorSet else 'Accessories'
        if equipType == 'Accessories':
            TequipName = removeN(equipName, EquipData['EquipSlot'])
            EquipData['EquipName'] = removeN(TequipName, '\n')
        
        requirements = tdContent[i+2].get_text(separator = '\n').split("\n")
        EquipData['EquipLevel'] = requirements[0].split(" ")[-1]
        if len(requirements) > 2:
            EquipData['ClassType'] = requirements[1].split(" ")[-1]
        else:
            EquipData['ClassType'] = 'Any'

        
        effects =  tdContent[i+3].get_text(separator = '\n').split('\n')
        EquipData.update(assignToDict(effects))

        if equipType == 'Accessories':
            AccDF = AccDF.append(EquipData, ignore_index=True)
        else:
            ArmorDF = ArmorDF.append(EquipData, ignore_index=True)
        
    ArmorDF = ArmorDF.fillna(0)
    AccDF = AccDF.fillna(0)

    return ArmorDF, AccDF

def retrieveWeap(wikitable, equipSet):
    
    currentDF = pandas.DataFrame()
    tdContent = wikitable.find_all('td')
    ClassSetType = ''
    for i in range(1, len(tdContent), 4):
        WeapData = {}
        weapType = tdContent[i].get_text()
        WeapData['WeaponType'] = removeN(weapType, '\n')
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
                    JText = ahref.get_text().split(" ")[-1]
                    WeapData['JobType'] = JText[:-1] if JText.find('\n') != -1 else JText
                    ClassSetType = WeapData['JobType']
                    break
        


        weapStats = tdContent[i+2].get_text(separator = '\n').split('\n')
        WeapData.update(assignToDict(weapStats))
    
        currentDF = currentDF.append(WeapData, ignore_index=True)
        
    if 'Xenon' in list(currentDF['JobType']):
        t = currentDF.loc[currentDF['JobType'] == 'Xenon', 'WeaponType'] 
        currentDF.loc[currentDF['JobType'] == 'Xenon', 'WeaponType'] = t + '(' + ClassSetType + ')'
        
    
    currentDF = currentDF.fillna(0)
        
    return currentDF

def retrieveSecWeap(session):
    
    weaponLink = []
    page = session.get(defaulturl + secUrl)
    soup = BeautifulSoup(page.content, 'lxml')

    weapList = soup.find_all('a', class_="category-page__member-link")

    df = pandas.DataFrame()
    for x in weapList:
        weaponLink.append(x['href'])
        df = df.append(retreiveSecPage(x['href'], session) , ignore_index=True)

    
    df = df.fillna(0)
    


    return df

def retreiveSecPage(suburl, session):

    
    
    page = session.get(defaulturl + suburl)
    
    titleContent = BeautifulSoup(page.content, 'lxml').find_all('div', class_= "mw-parser-output")[0].find('a')
    weapListLink = titleContent['href']
    weapType = titleContent.get_text().replace(" ", "")

    if weapType == "Shield":
        return retrieveShield(weapListLink, session, weapType)

    start = time.time()
    
    weapListPage = session.get(defaulturl + weapListLink)

    PageContent = BeautifulSoup(weapListPage.content, 'lxml').find_all('div', class_= "mw-parser-output")[0]

    wikiTables = PageContent.find_all('table', class_='wikitable')
    headerContent = PageContent.find_all('p')


    for i in headerContent:
        if i.get_text().replace(" ", "").lower().find(weapType.lower()) != -1:
            headerP = i
            break
        if i.get_text().find('exclusive') != -1:
            headerP = i
            break
        continue

    headerPContent = list(headerP.contents)

    Jobs = []
    Cstart = False
    for i in headerPContent:
        if i.get_text().find('exclusive') != -1:
            Cstart = True
            continue
        if i.get_text().find('conjunction') != -1:
            Cstart = False
            break

        if Cstart == True:
            if i.name == 'a':
                # JobName = i.next.replace(" ", "") if i.next.find(" ") != -1 else i.next
                JobName = removeN(i.next, ' ')
                Jobs.append(JobName)
 
    currentDF = pandas.DataFrame()

    ignoreList = ["evolving", "frozen"]

    if len(Jobs) == 0:
        return currentDF
    
    counter = min(len(Jobs), len(wikiTables))

    for c in range(0, counter):
        tableContent = wikiTables[c].find_all('td')
        JobType = Jobs[c]
        for i in range(0, len(tableContent), 3):
            ItemData = {}
            if JobType == "Jett":
                continue
            elif JobType == "DualBlade":
                ItemData["ClassType"] = JobType
                ItemData["WeaponType"] = weapType
                weaponSet = tableContent[i].contents
                for w in weaponSet:
                    if any(ele.lower() in w.get_text().replace(weapType, "").lower() for ele in EquipSetTrack) == True:
                        EquipName = w.get_text()
                        break
                    else:
                        EquipName = ""
                if EquipName == "":
                    continue
                ItemData["EquipName"] = EquipName
                
                EquipLevel = tableContent[i+1].get_text(separator = '\n').split('\n')[0].split(" ")[-1]
                ItemData["EquipLevel"] = EquipLevel

                EquipStat = tableContent[i+2].get_text(separator = "\n").split("\n")[:-1]
                ItemData.update(assignToDict(EquipStat))
            else:
                ItemData["ClassType"] = JobType
                ItemData["WeaponType"] = weapType
                EquipName = tableContent[i].find_all('a')[-1].get_text()
                if EquipName == "":
                    continue
                if any(ele in EquipName.lower() for ele in ignoreList) == True:
                    continue

                ItemData["EquipName"] = EquipName

                EquipLevel = tableContent[i+1].get_text(separator = '\n').split('\n')[0].split(" ")[-1]
                ItemData["EquipLevel"] = EquipLevel

                EquipStat = tableContent[i+2].get_text(separator = "\n").split("\n")[:-1]
                ItemData.update(assignToDict(EquipStat))
            currentDF = currentDF.append(ItemData, ignore_index=True)
        
    end = time.time()

    print(f"Time taken to add {weapType} is {end -  start}.")
    
    return currentDF

def retrieveShield(weapListLink , session, weapType):

    start = time.time()
    
    currentDF =  pandas.DataFrame()

    for cls in Mclasses:
        newUrl = weapListLink + "/" + cls
        PageContent = session.get(defaulturl + newUrl)
        if PageContent.status_code != 200:
            continue
        currentContent = BeautifulSoup(PageContent.content, 'lxml').find_all('div', class_="wds-tab__content wds-is-current")[0]
        wikitable = currentContent.find_all('td')
        
        for i in range(0, len(wikitable), 3):
            ItemData = {}
            ItemData["ClassType"] = cls
            ItemData["WeaponType"] = weapType
            EquipName = wikitable[i].find_all('a')[-1].get_text()
            if EquipName == "":
                    continue
            ItemData["EquipName"] = EquipName

            EquipLevel = wikitable[i+1].get_text(separator = '\n').split('\n')[0].split(" ")[-1]
            if int(EquipLevel) < 110:
                continue
            ItemData["EquipLevel"] = EquipLevel

            EquipStat = wikitable[i+2].get_text(separator = "\n").split("\n")[:-1]
            ItemData.update(assignToDict(EquipStat))
            currentDF = currentDF.append(ItemData, ignore_index=True)
    end = time.time()
    print(f"Time taken to add Shield is {end - start}")
    return currentDF

def retrieveGenesis():
    
    weapLink = []
    request_session = requests.session()
    
    page = request_session.get(defaulturl + genesisWeapUrl)
    soup = BeautifulSoup(page.content, 'lxml')
    
    mainWeapLinksA = soup.find_all('tbody')[0].find_all('td')[4].find_all('div')[0].find_all('li')
    
    return


def removeN(item, para):
    
    if item.find(para) != -1:
        return item.replace(para, '')
    else:
        return item

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
            else:
                tempData['HP'] = HPstr[1:]
            continue
        elif i.find("MP") != -1:
            MPstr = i.split(" ")[-1][1:]
            if MPstr.find(",") != -1:
                tempData['MP'] = MPstr.replace(",", "")
            elif MPstr.find("%") != -1:
                tempData['MP'] = MPstr
            else:
                tempData['MP'] = MPstr[1:]
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
        elif i.find("Jump") != -1:
            tempData["JUMP"] = i.split(" ")[-1][1:]
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
        elif i.find("Critical") != -1:
            tempData['CritDMG'] = i.split(" ")[-1][1:-1]
            continue
        
    
    
    return tempData


# main()
retrieveGenesis()
