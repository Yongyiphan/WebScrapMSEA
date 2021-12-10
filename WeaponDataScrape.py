#Rename this file
from bs4.element import PageElement
from numpy import true_divide
import pandas
from pandas.core.frame import DataFrame
import requests
import lxml
import cchardet
import time
import re
from bs4 import BeautifulSoup
from requests.api import request

### PROGRAM FLOW ####
# MAIN PAGE -> GET EQUIPNAME/LINK 
# TRAVERSE TO EQUIPLINK PAGE -> GET WEAPON SET'S LINK
# TRAVERSE TO WEAPON'LINK -> RECORD INFORMATION
weaponLink = []
weaponNameList = []
defaulturl = "https://maplestory.fandom.com"
weaponUrl = "/wiki/Category:Weapons"
setToTrack = ['Genesis', 'Arcane', 'Utgard','Absolab', 'Fafnir', 'Lapis','Lazuli']
Mclasses = ['Warrior', 'Bowman', 'Magician','Mage','Thief', 'Pirate']
trackMinLevel = 140

def main():
    
    start = time.time()
    
    weapDF = retrieveMainWeap()
    weapDF.loc[(weapDF.WeaponType == 'Bladecaster'), 'WeaponType'] = 'Tuner'
    weapDF.loc[(weapDF.WeaponType == 'LucentGauntlet'), 'WeaponType'] = 'MagicGauntlet'
    weapDF.loc[(weapDF.WeaponType == 'Psy-limiter'), 'WeaponType'] = 'PsyLimiter'
    weapDF.loc[(weapDF.WeaponType == 'Whispershot'), 'WeaponType'] = 'BreathShooter'


    weapDF.to_csv("WeaponData.csv", encoding='utf-8')

    end = time.time()

    print(f"Time take: {end - start}")
    return

def retrieveMainWeap():

    page = requests.get(defaulturl + weaponUrl)

    soup  = BeautifulSoup(page.content, "html.parser")
    weaponList = list(soup.find_all('a', class_='category-page__member-link'))
    
    request_session = requests.sessions.session()

    df = pandas.DataFrame()
    for x in weaponList:
        if(x['href'].find("Secondary_Weapons") != -1):
            continue
        weaponLink.append(x['href'])
        df = df.append(retreiveConsolidatedPage(x['href'], request_session, setToTrack), ignore_index=True)
    df = df.fillna(0)
    print(df)
    return df


def retreiveConsolidatedPage(suburl, session, trackSet):

    newurl = suburl.replace("Category:", "")    
    page =  session.get(defaulturl + newurl)
    
    if(page.status_code == 404):
        newurl = newurl[:-1]
        page = session.get(defaulturl + newurl)

    weapName = newurl.split("/")[-1].replace("_", " ")
    
    soup = BeautifulSoup(page.content, "lxml")
    tableC =  soup.find_all('tbody')[0].find_all('td')    
    # headerP = BeautifulSoup(str(BeautifulSoup(str(soup.find_all('div', class_='mw-parser-output')),'lxml').find_all('p')), 'lxml').find_all('a', href=True)
    # headerP = BeautifulSoup(str(soup.find_all('div', class_='mw-parser-output')),'lxml').find_all('p')
    # if len(BeautifulSoup(str(headerP), 'lxml').find_all('a', href=True)) == 2:
    #     tempA = BeautifulSoup(str(headerP), 'lxml').find_all('a', href=True)
    #     JobType = tempA[0].get_text()
    #     Secondary = tempA[1].get_text()
    
    currentDF = pandas.DataFrame()
    
    for i in range(0, len(tableC),3):
        ItemData = {}
        if any(ele.lower() in tableC[i].get_text().replace(weapName, "").lower() for ele in setToTrack) == True:
            retrievedSet = tableC[i].get_text()[:-1].replace(weapName, "")
            if retrievedSet.lower().find("sealed") != -1:
                continue
            
            if retrievedSet.lower().find("utgard") != -1:
                ItemData["WeaponSet"] = "Fensalir"
            else:
                ItemData["WeaponSet"] = setToTrack[returnIndex(retrievedSet)]
            ItemData["WeaponType"] = weapName.replace(" ","")
            level = tableC[i+1].contents[0].split(" ")[1] 
            ItemData["Level"] = level[:-1] if level.find('\n') != -1 else level
            if (int(ItemData["Level"]) < trackMinLevel) and ItemData['WeaponType'].lower() != 'heavysword':
                continue
            ItemData.update(assignToDict(tableC[i+2].get_text(separator = "\n").split("\n")[:-1]))                
            currentDF = currentDF.append(ItemData, ignore_index=True)
            
    return currentDF

def returnIndex(ele):
    for i in range(0, len(setToTrack)):
        if setToTrack[i].lower() in ele.lower():
            return i
        elif ele.lower() in setToTrack[i].lower():
            return i


def assignToDict(tempList):
    
    tempData = {}
    
    for i in tempList:
        if i.find("Attack Speed") != -1:
            tempData["AtkSpd"] = i.split(" ")[-1][1:-1]
            continue
        elif i == "STR":
            if "MainStat" in tempData:
                tempData["SecStat"] = i[1:]
            else:
                tempData["MainStat"] = i[1:]
            continue
        elif i == "DEX":
            if "MainStat" in tempData:
                tempData["SecStat"] = i[1:]
            else:
                tempData["MainStat"] = i[1:]
            continue        
        elif i == "INT":
            if "MainStat" in tempData:
                tempData["SecStat"] = i[1:]
            else:
                tempData["MainStat"] = i[1:]
            continue
        elif i == "LUK":
            if "MainStat" in tempData:
                tempData["SecStat"] = i[1:]
            else:
                tempData["MainStat"] = i[1:]
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
        
        
    
    
    return tempData


main()


# def retrieveSubPageDetails(suburl, session):
#     pageurl = defaulturl + suburl
#     page = session.get(pageurl);
#     soup = BeautifulSoup(page.content, "lxml")
    
#     linkTrack = []

#     df = pandas.DataFrame(columns=[])
    
#     for a in soup.find_all('a', class_='category-page__member-link'):
#         for i in a.get_text().split(" "):
#             if i.lower() in setToTrack:
#                 linkTrack.append(a['href'])
#                 dataDict = {}
#                 dataDict["WeaponType"] = suburl.split("/")[2].split(":")[1]
#                 dataDict["WeaponSet"] = a['href'].split("/")[2].split("_")[0]
#                 dataDict.update(retrieveItemStat(a['href'], session))
                
#                 df = df.append(dataDict, ignore_index=True)
    
    
#     return df
    
# def retrieveItemStat(url, session):
#     tempTitle = []
#     tempValue = []
    
#     page = session.get(defaulturl + url);
#     soup = BeautifulSoup(page.content, "lxml")
#     tableC = soup.find_all('tbody')[0]
#     th = tableC.find_all('th')
#     td = tableC.find_all('td')
    
    
#     for i in range(0, len(td), 2):
#         tempValue.append(td[i].get_text()[:-1])

#     for i in th:
#         tempTitle.append(i.get_text()[:-1])
    
#     tempValue = tempValue[1:]
#     tempData = {}
    
    
#     for i in range(0, len(tempTitle)):
#         if tempTitle[i] == "REQ Level":
#             tempData["Level"] = tempValue[i]
#             continue
#         elif tempTitle[i] == "REQ Job":
#             tempData["ClassType"] = tempValue[i]
#             continue
#         elif tempTitle[i] == "Attack Speed":
#             tempData["AtkSpd"] = tempValue[i].split(" ")[1][1:-1]
#             continue
#         elif tempTitle[i] == "STR":
#             if "MainStat" in tempData:
#                 tempData["SecStat"] = tempValue[i][1:]
#             else:
#                 tempData["MainStat"] = tempValue[i][1:]
#             continue
#         elif tempTitle[i] == "DEX":
#             if "MainStat" in tempData:
#                 tempData["SecStat"] = tempValue[i][1:]
#             else:
#                 tempData["MainStat"] = tempValue[i][1:]
#             continue        
#         elif tempTitle[i] == "INT":
#             if "MainStat" in tempData:
#                 tempData["SecStat"] = tempValue[i][1:]
#             else:
#                 tempData["MainStat"] = tempValue[i][1:]
#             continue
#         elif tempTitle[i] == "LUK":
#             if "MainStat" in tempData:
#                 tempData["SecStat"] = tempValue[i][1:]
#             else:
#                 tempData["MainStat"] = tempValue[i][1:]
#             continue
#         elif tempTitle[i] == "Weapon Attack":
#             tempData["Atk"] = tempValue[i][1:]
#             continue
#         elif tempTitle[i] == "Magic Attack":
#             tempData["MAtk"] = tempValue[i][1:]
#             continue
#         elif tempTitle[i].find("Knockback") != -1:
#             tempData["Knockback"] = tempValue[i][:-1]
#             continue
#         elif tempTitle[i].find("Boss") != -1:
#             tempData["BossDMG"] = tempValue[i][1:-1]
#             continue
#         elif tempTitle[i].find("Ignore") != -1:
#             tempData["IED"] = tempValue[i][1:-1]
#             continue
#         elif tempTitle[i].find("Movement") != -1:
#             tempData["SPD"] = tempValue[i][1:]
#             continue
#     return tempData
