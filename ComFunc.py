
import requests
import bs4 as bsoup

MainStat = ['STR','DEX','INT','LUK']




def returnIndex(ele, setToTrack):
    for i in range(0, len(setToTrack)):
        if setToTrack[i].lower() in ele.lower():
            return i
        elif ele.lower() in setToTrack[i].lower():
            return i

def removeN(item, para, deli = ''):
    
    if isinstance(para, str):
        if item.find(para) != -1:
            return item.replace(para, deli)
        else:
            return item
    elif isinstance(para, list):
        for i in para:
            if item.find(i) != -1:
                item = item.replace(i, deli)
        return item

def removeNSpace(nlist, deli):
    return [value for value in nlist if value != deli]

def assignToDict(tempList):
    
    tempData = {}
    if tempList == None:
        return tempData
    
    for i in tempList:
        if i.find('\n') != -1:
            i = removeN(i, '\n')
        
        if i.find("Attack Speed") != -1:
            tempData["AtkSpd"] = i.split(" ")[-1][1:-1]
        
        elif any(i.find(MS) != -1 for MS in MainStat) == True:
            #if i.find(':') != -1:
            #    tempStr = i.split(" ")[1][1:]
            #else:
            #    tempStr = i.split(" ")[-1][1:]
            
            #if "MainStat" in tempData:
            #    if 'SecStat' in tempData:
            #        continue
            #    tempData["SecStat"] = tempStr
            #else:
            #    tempData["MainStat"] = tempStr
            if i.find(':') != -1:
                tempStr = i.split(':')
                tempData[tempStr[0]] = tempStr[1].lstrip('+')

        elif i.find("HP") != -1:
            HPstr = i.split(" ")[-1][1:]
            HPstr = removeN(HPstr, ',')
            if HPstr.find("%") != -1:
                tempData['HP'] = HPstr
            else:
                if HPstr.find("+") != -1:
                    tempData['HP'] = HPstr[1:]
                else:
                    tempData["HP"] = HPstr
        elif i.find("MP") != -1:
            MPstr = i.split(" ")[-1][1:]
            MPstr = removeN(MPstr, ',')
            if MPstr.find("%") != -1:
                tempData['MP'] = MPstr
            else:
                tempData['MP'] = MPstr[1:]
        elif i.find("Weapon Attack") != -1:
            tempData["ATK"] = i.split(" ")[-1][1:]

        elif i.find("Magic Attack") != -1:
            tempData["MATK"] = i.split(" ")[-1][1:]
        
        elif i.find("All Stats") != -1:
            tempData["AllStat"] = i.split(" ")[-1][1:]

        elif i.find("Boss") != -1:
            tempData["BDMG"] = i.split(" ")[-1][1:-1]

        elif i.find("Ignore") != -1:
            tempData["IED"] = i.split(" ")[-1][1:-1]

        elif i.find("Defense") != -1:
            tempData["DEF"] = i.split(" ")[-1][1:]

        elif i.find("Speed") != -1:
            tempData["SPD"] = i.split(" ")[-1][1:]

        elif i.find("Jump") != -1:
            tempData["JUMP"] = i.split(" ")[-1][1:]
        
        elif i.find("Normal") != -1:
            tempData['NDMG'] = i.split(" ")[-1][1:-1]

        elif i.find("Critical Damage") != -1:
            tempData['CDMG'] = i.split(" ")[-1][1:-1]  
        elif i.find('Visible Stats') != -1:
            tempData["VStat"] = i.split(' ')[-1].lstrip('+')
        elif i.find('Visible ATT') != -1:
            tempData["VAtk"] = i.split(' ')[-1].lstrip('+')
        elif i.find('Visible DEF') != -1:
            tempData["VDef"] = i.split(' ')[-1].rstrip('%').lstrip('+')
    
    return tempData

def GetPageContent(url, session =  requests.session()):

    request_session = session
    Page = request_session.get(url)
    
    return bsoup(Page.content, 'lxml')


    ...

def removeFLSpace(item):
    
    if item[0] == " ":
        if item[-1] == " ":
            return item[1:-1]
        return item[1:]
    elif item[-1] == " ":
        return item[:-1]
    else:
        return item

