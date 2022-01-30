import pandas



def main():
    
    PotDF = pandas.read_csv('DefaultData\\CalculationsData\\PotentialData.csv')
    
    print(PotDF.loc[PotDF['DisplayStat'].str.contains('become')])

    temp = pandas.Series(PotDF['DisplayStat']).str.replace("become", "be")
    
    
    PotDF['DisplayStat'] = temp
    
    print(PotDF.loc[PotDF['DisplayStat'].str.contains('become')])
    
    PotDF.to_csv('DefaultData\\CalculationsData\\PotentialData.csv', index=False)
    return


if __name__ == "__main__":
    main()