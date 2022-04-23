import chunk
from tempfile import tempdir
import pandas
import requests
import time
import unicodedata
from bs4 import BeautifulSoup as bsoup
from requests import session
from ComFunc import *


defaultUrl = 'https://strategywiki.org'
STSFurl = '/wiki/MapleStory/Spell_Trace_and_Star_Force#Star_Force_Enhancement'
formulaUrl ='/MapleStory/Formulas'
potentialUrl = '/MapleStory/Potential_System'
hyperStatUrl = "/wiki/MapleStory/Hyper_Stats"
PotDFCol =	['EquipGrp','Grade','GradeT','DisplayStat','StatT','Chance','Duration','MinLvl','MaxLvl','StatValue']
TyrantSFCol = ["SFLevel", "LevelRank", "VStat", "VAtk",	"VDef"]

def StartScraping():

    start = time.time()

    session0 = session()
    StarforceDF, AddDF = retrieveStarforce(session0)
    TyrantSFDF = retrieveTyrantSF(session0)
    StarforceDF = StarforceDF.fillna(0)
    AddDF = AddDF.fillna(0)
    
    session1 = session()
    PotDF = retrievePotential(session1)
    BPotDF = retrieveBonusPotential(session1)
    
    WeapDF = retrieveWeapMod()


    PotDF = PotDF[PotDFCol]
    BPotDF = BPotDF[PotDFCol]
    StarforceDF = StarforceDF.astype(int)
    AddDF = AddDF.astype(int)
    TyrantSFDF = TyrantSFDF[TyrantSFCol]
    TyrantSFDF = TyrantSFDF.astype(int)

    StarforceDF.to_csv('DefaultData\\CalculationsData\\StarforceGains.csv')
    AddDF.to_csv('DefaultData\\CalculationsData\\AddStarforceGains.csv')
    TyrantSFDF.to_csv('DefaultData\\CalculationsData\\SuperiorStarforceGains.csv')
    PotDF.to_csv('DefaultData\\CalculationsData\\PotentialData.csv')
    BPotDF.to_csv('DefaultData\\CalculationsData\\BonusPotentialData.csv')

    WeapDF.to_csv('DefaultData\\CalculationsData\\WeapMod.csv')

    end = time.time()
    print(f'Total time taken is {end-start}')

    return

def retrieveStarforce(request_session):
    start = time.time()
    Page = request_session.get(defaultUrl + STSFurl)
    MainContent =  bsoup(Page.content, 'lxml')    
    
    startR = MainContent.select('#Stats_Boost')[0].parent
    SFCompiledTable = startR.find_next_sibling('table')

    tableR = SFCompiledTable.contents[1].contents
    tableR = [value for value in tableR if value != '\n'][1:]
    
    currentDF = pandas.DataFrame()
    AddDF =  pandas.DataFrame()
    
    for row in tableR:
        
        r = [td for td in row.contents if td != '\n']
        currentRow = r[0]
        SFStats = r[1]
        temp = removeN(currentRow.next, ['★','→'], '').split(',')
        addSF = {}
        for sfid in temp:
            sfid = [int(value) for value in sfid.split(' ') if value != '']
            
            SFD = {}
            CSF = max(sfid)
            


            SFD['SFID'] = CSF
            if not isinstance(SFStats, list):
                if CSF > 15:
                    SFStats = [value for value in SFStats if value not in ['', '\n']]
                    varTable = SFStats[0].find_all('tr')[1:]
                    SFStats = SFStats[1].get_text().split('\n')
                    for mR in varTable:
                        addSF['SFID'] = CSF

                        Levelr = [value for value in mR.contents if value != '\n'][0].get_text().split('~')[0]
                        addSF['LevelRank'] = returnLevelRank("Normal", int(Levelr))
                        statsL = mR.find_all('ul')[0].get_text().split('\n')
                        addSF.update(ATDSF(statsL))
                        AddDF = AddDF.append(addSF, ignore_index=True)

                    
                else:
                    SFStats = SFStats.find_all('ul')[0].get_text().split('\n')

                
            SFStats = [value for value in SFStats if value != '']
            SFD.update(ATDSF(SFStats))
            currentDF = currentDF.append(SFD, ignore_index=True)
            

        
            end = time.time()
            print(f'Starforce at {CSF} added in {end-start}')

    return currentDF, AddDF

def retrieveTyrantSF(request_session):
    Page = request_session.get(defaultUrl + STSFurl)
    MainContent =  bsoup(Page.content, 'lxml')    
    
    startR = MainContent.select('#Stats_Boost_2')[0].parent
    SFCompiledTable = startR.find_next_sibling('table')

    tableR = SFCompiledTable.contents[1].contents[1:]
    SFDict = pandas.DataFrame()
    tableR = removeNSpace(tableR, '\n')
    for sfLvl in tableR:
        tempDict = pandas.DataFrame()
        if sfLvl.name == "tr":
            row = removeNSpace(sfLvl.contents, '\n')
            lvl = removeN(row[0].next.split(' ')[-1],'★', '')
            rowT = removeNSpace(row[1], '\n')
            for c in rowT:
                tempDict["SFLevel"] = lvl 
                if c.name == 'table':
                    tcr = removeNSpace(c, '\n')[0].find_all('td')
                    LvlRankStore = pandas.DataFrame()
                    for e in range(0, len(tcr), 2):
                        temp = {}
                        if findString(tcr[e].next, '~'):
                            temp["LevelRank"] = returnLevelRank("Tyrant", tcr[e].next.split('~')[-1])
                        elif findString(tcr[e].next, "+"):
                            temp["LevelRank"] = returnLevelRank("Tyrant", tcr[e].next[:-1])
                        temp.update(assignToDict(tcr[e + 1].contents))
                        tempDict = tempDict.append(temp, ignore_index=True)
                elif c.name == 'ul':
                    vdef = c.get_text().split(' ')[-1].rstrip('%').lstrip('+')
                    tempDict["VDef"] = vdef
        SFDict = SFDict.append(tempDict, ignore_index=True)
    
    SFDict = SFDict.fillna(0)   
    
    return SFDict;
    
    
    

def retrieveWeapMod():
    start = time.time()
    request_session = requests.session()
    Page = request_session.get(defaultUrl + formulaUrl)
    MainContent =  bsoup(Page.content, 'lxml')    
    
    startR = MainContent.select('#Weapon_Multiplier')[0].parent
    WeapModTable = startR.find_next_sibling('table')
    WeapModTable = [value for value in WeapModTable if value != '\n']

    ContentTable = WeapModTable[0]

    WeaponList = []
    WeaponMod = []
    for row in ContentTable.find_all('tr'):
        weaponL = row.find('th').next.split(',')
        td = row.find('td').next.split(' ')[0]

        for weap in weaponL:
            if weap.find('/') != -1:
                weap = weap.split('/')[0]
            elif weap.find('(') != -1:
                weap =  weap.split('(')[0]

            

            WeaponList.append(removeFLSpace(removeN(weap, '\n', '')))
            WeaponMod.append(removeN(td, '\n', ''))
    
    tempD = {'WeaponType':WeaponList, 'Multiplier':WeaponMod}
    WeapMDF = pandas.DataFrame(tempD) 

    end = time.time()
    print(f"Time taken is {end-start}")


    return WeapMDF
    

def retrievePotential(request_session):
    start = time.time()
    
    Page = request_session.get(defaultUrl + potentialUrl)
    PageContent = bsoup(Page.content, 'lxml')
    
    
    startR = PageContent.select('#Potentials_List')[0].parent
    endR = PageContent.select('#Bonus_Potential')[0].parent
    AllContent = PageContent.find_all('div', class_='mw-parser-output')[0]
    
    RContent = []
    reachedEnd = False
    startRecording = False
    for i in AllContent:
        if reachedEnd == True:
            break
        if i ==  endR:
            reachedEnd = True
        if  i == startR:
            startRecording = True
        if startRecording == True:
            RContent.append(i)
            
    PotDF = returnPotentialList(RContent)

    end = time.time()
    print(f"Time taken is {end-start}")

    
    return PotDF

def retrieveBonusPotential(request_session):
    
    start =  time.time()
    Page = request_session.get(defaultUrl + potentialUrl)
    PageContent = bsoup(Page.content, 'lxml')
    
    startR = PageContent.select('#Bonus_Potential_Stat_List')[0].parent
    AllContent = PageContent.find_all('div', class_='mw-parser-output')[0]
    
    
    RContent = []
    startRecording = False
    for i in AllContent:
        if i == startR:
            startRecording = True
        if startRecording == True:
            RContent.append(i)
    
    PotDF = returnPotentialList(RContent)

    end = time.time()
    print(f"Time taken is {end-start}")

    return PotDF

    
 
def returnPotentialList(RContent):
    PotDF = pandas.DataFrame()
    currentDic = {}
    for chunks in RContent:
        if chunks == '\n':
            continue 
        if chunks.name == 'h3':
            currentDic = {}
            EGrp = chunks.get_text().split('[')[0]
            if EGrp.find('(') != -1:
                EGrp = EGrp.split('(')[0]
            EGrp = removeN(EGrp,['and', ','], ';')
            currentDic['EquipGrp'] = EGrp
        if chunks.name == 'h4':
            t = chunks.contents[1].next.split(" ")
            grade = t[0]
            gradeT = removeFLSpace(removeN(t[1], ['(', ')', '-'], ' '))
            currentDic['Grade'] = grade      
            currentDic['GradeT'] = gradeT
        if chunks.name == 'div':
            subtable = chunks.contents[1:][0]
            subtable = [value for value in subtable if value != '\n']
            for statt in range(0, len(subtable)):
                if subtable[statt].name == 'h5':
                    stat = subtable[statt].get_text().split('[')[0]
                    stat = stat.encode("ascii", "ignore")
                    stat = stat.decode()
                    stat = removeN(stat, ['Increase'], '')
                    currentDic['DisplayStat'] = stat.strip()
                    currentDic['StatT'] = 'Perc' if findString(stat, '%') else "Flat"
                    
                    checkInt = True
                    if stat.split(' ')[0].find('%') != -1:
                        chance = stat.split(' ')[0]
                        try:
                            tempC = removeN(chance, '%', '')
                            int(tempC)
                        except ValueError:
                            checkInt = False

                        if checkInt == True:
                            chance = int(removeN(chance, '%', ''))
                            currentDic['Chance'] = chance/100
                    else:
                        currentDic['Chance'] = 1
                    
                    currentDic['Duration'] = 0
                if subtable[statt].name == 'table':
                    if subtable[statt-1].name == 'dl':
                        continue
                    tds = subtable[statt].find_all('td')
                    counterT = len(tds) % 2
                    for t in range(0, len(tds), counterT+2):
                        deli = ['\n', '+']
                        tempDic = {}
                        tempDic.update(currentDic)
                        currentT = removeN(tds[t].get_text(), '\n', '')

                        if findString(currentT, 'GMS'):
                            continue
                        if findString(currentT, '-'):
                            te = currentT.split('-')
                            tempDic['MinLvl'] = te[0]
                            tempDic['MaxLvl'] = te[-1]
                            tempDic['StatValue'] = 0
                        elif currentT[-1] == '+':
                            te = removeN(currentT, '+', '')
                            tempDic['MinLvl'] = te
                            tempDic['MaxLvl'] = 300
                            tempDic['StatValue'] = 0
                        if counterT == 1:
                            tempDic['StatValue'] = removeN(tds[t + 2].next, deli, '')
                        else:
                            tempDic['StatValue'] = removeN(tds[t + 1].next, deli, '')

                        if findString(tempDic['StatValue'], 'seconds'):
                            temp = removeN(tempDic['StatValue'], ['(', ')'], '').split(' ')
                            hi = temp.index('seconds')
                            tempDic['Duration'] = temp[hi-1]
                            
                        if findString(tempDic['StatValue'], 'Level'):
                            temp = removeN(tempDic['StatValue'], ')', '')
                            temp = temp.split('(')
                            tempDic['StatValue'] = temp[-1].capitalize()
                        
                        if findString(tempDic['DisplayStat'], 'poison'):
                            temp = removeN(tempDic['StatValue'], ['(', ')'], '').split(' ')
                            fdmg = temp.index('damage')
                            ffor = temp.index('for')
                            tempDic['StatValue'] = temp[fdmg-1]
                            tempDic['Duration'] = temp[ffor+1]
                        
                        
                        sStat =  tempDic['StatValue']
                        if findString(sStat,''):
                            pass
                        PotDF = PotDF.append(pandas.DataFrame(tempDic, index=[0]), ignore_index=True)
                if subtable[statt].name == 'p' and findString(subtable[statt].get_text().lower(), 'level requirement'):
                    te = subtable[statt].get_text().split(':')[-1]
                    if te.find('or higher')!= -1:
                        te = te.split("or higher")[0]
                    te = removeN(te, '\n', '')
                    currentDic['MinLvl'] = te
                    currentDic['MaxLvl'] = 300
                    stat = currentDic['DisplayStat']
                    if findString(stat, 'being attacked'):
                        stat = stat.split('seconds')[0]
                        tempL = stat.split(' ')
                        stat = tempL[:-2]
                        stat = " ".join(stat[:-1])
                        currentDic['Duration'] = tempL[-2]
                    elif findString(stat, 'Cooldown'):
                        currentDic['StatValue'] =  removeN(stat.split(' ')[-2], ['\n', '-'], '')
                        currentDic['Duration'] = removeN(stat.split(' ')[-2], ['\n', '-'], '')
                    elif findString(stat, "Invincibility Time"):
                        currentDic['StatValue'] =  removeN(stat.split(' ')[-2], ['\n', '+'], '')
                        currentDic['Duration'] = removeN(stat.split(' ')[-2], ['\n', '+'], '')
                    elif findString(stat, "Monster's DEF"):
                        tempL = stat.split(' ')[1]
                        stat = "Ignore Monster's DEF"
                        currentDic['StatValue'] = removeN(tempL, '+', '')
                        currentDic['DisplayStat'] = stat
                    elif findString(stat, 'Boss Monsters'):
                        tempL = stat.split(' ')
                        currentDic['DisplayStat'] = " ".join(tempL[:-1])
                        currentDic['StatValue'] = removeN(tempL[-1], '+', '')
                    elif findString(stat, 'chance to ignore'):
                        if "%" in stat.split('ignore')[1]:
                            currentDic['StatValue'] = stat.split('ignore')[1].split(' ')[1]   
                    elif findString(stat, 'Critical Rate'):
                        currentDic['StatValue'] = stat.split('+')[-1]  
                        currentDic['DisplayStat'] = stat.split('+')[0]                   
                    else:
                        currentDic['Duration'] = 0
                        currentDic['StatValue'] = 0
                    
                    PotDF = PotDF.append(pandas.DataFrame(currentDic, index=[0]), ignore_index=True)
         

    PotDF.drop_duplicates(keep='first', inplace=True)
    # PotDF.drop(PotDF[PotDF['DisplayStat'].str.contains('Reflect damage at a chance')].index, inplace=True)
    temp = pandas.Series(PotDF['DisplayStat']).str.replace("become", "be")

    PotDF['DisplayStat'] = temp

    PotDF['EquipGrp'] = PotDF['EquipGrp'].str.replace("Mechanical Heart", "Heart")
    PotDF['EquipGrp'] = PotDF['EquipGrp'].str.replace("Secondary Weapon", "Secondary")
    PotDF['EquipGrp'] = PotDF['EquipGrp'].str.replace("Earring", "Earrings")
    return PotDF

def retrieveHyperStat():
    start = time.time()
    request_session = requests.session()
    Page = request_session.get(defaultUrl + hyperStatUrl)
    PageContent = bsoup(Page.content, 'lxml')
    AllDiv = PageContent.find_all('div')



    end = time.time()

    print(f"Time Taken to retreive HyperStat is {end - start}")
    ...

def cleanPotDF(DF):

    

    return DF


def ATDSF(statList):
    delimiter = ['+', '%', "'s", "s'"]
    tempD = {}

    for stat in statList:
        stat =  removeN(stat, delimiter, '') 
        if findString(stat, '-'):
            stat = stat.replace('-', ' ')
        
        t =  stat.split(' ')
        value = t[-1]
        name = " ".join(t[:-1])
        tempD[name] = value


    return tempD


def returnPotLevel(lvl):
    lvl = int(lvl)
    if lvl in range(0, 21):
        return 1
    elif lvl in range(21, 41):
        return 2
    elif lvl in range(41, 51):
        return 3
    elif lvl in range(51,71):
        return 4
    elif lvl in range(71, 91):
        return 5
    elif lvl >= 91:
        return 6



def findString(s, toFind):

    if s.find(toFind) != -1:
        return True
    else:
        return False

def returnLevelRank(mode, level):

    level = int(level)
    if mode != "Tyrant" :
        if level >= 128 and level <= 137:
            return 5
        elif level >= 138 and level <= 149:
            return 4
        elif level >= 150 and level <= 159:
            return 3
        elif level >= 160 and level <= 199:
            return 2
        elif level >= 200:
            return 1
    else:
        if level >= 0 and level <= 77:
            return 9
        elif level >= 78 and level <= 87:
            return 8
        elif level >= 88 and level <= 97:	
            return 7
        elif level >= 98 and level <= 107:
            return 6
        elif level >= 108 and level <= 117:	
            return 5
        elif level >= 118 and level <= 127:	
            return 4
        elif level >= 128 and level <= 137:
            return 3
        elif level >= 138 and level <= 149:
            return 2
        elif level >= 150:
            return 1
    

if __name__ == "__main__":
    
    #StartScraping()
    retrieveHyperStat()



