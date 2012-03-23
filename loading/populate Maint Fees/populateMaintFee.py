# populateMaintFee()
# by Allan Niemerg
# Populates a Mysql database with patent maintenance fee data from files found on 
# http://www.google.com/googlebooks/uspto.html

import MySQLdb as mdb

def populateMaintFee(inputFile="MaintFeeEvents_20120109.txt"):
    try:
        f = open(inputFile, 'r')
    except Exception as e:
        return
    SavedCode = ['EXP.', 'EXPX', 'M1551', 'M1552', 'M1553', 'M170', 'M171', 'M172', 'M173', 'M174', 'M175', 'M184',
                 'M185', 'M2551', 'M2552', 'M2553', 'M274', 'M273', 'M275', 'M283', 'M284', 'M285']
    fourYearCode = ['M1551', 'M170', 'M173', 'M183', 'M2551', 'M273', 'M283']
    eightYearCode = ['M1552', 'M171', 'M174', 'M184', 'M2552', 'M274', 'M284']
    twelveYearCode = ['M1553', 'M172', 'M175', 'M185', 'M2553', 'M275', 'M285']



    #mdb.connect('localhost', 'username', 'password', 'database');
    con = mdb.connect('localhost', 'root', 'password', 'Patents');
    with con:
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS MaintFeeEvents(patentNumber INT(8), fourYear INT(8), eightYear INT(8), \
            twelveYear INT(8), dateExpired INT(8), entityStatus VARCHAR(1))");
        cur.execute("SELECT MAX(patentNumber) FROM USPatents")
        row = cur.fetchone()
        maxPatent = row[0]
        cur.execute("SELECT MIN(patentNumber) FROM USPatents")
        row = cur.fetchone()
        minPatent = row[0]
        print str(maxPatent) + " " + str(minPatent)

    currentPatentNumber = None
    fourYear = None
    eightYear = None
    twelveYear = None
    currentEntityStatus = None
    currentDateExpired = None
    

    for lf in f:
        if lf[0] == 'R': continue
        patentNumber = int(lf[:7])
        entityStatus = lf[17]
        entryDate = int(lf[37:][:8])
        entryCode = lf[46:][:5]
        entryCode = entryCode.strip()

        if patentNumber < int(minPatent) or patentNumber > int(maxPatent): continue
        if not (entryCode in SavedCode): continue

        if patentNumber != currentPatentNumber:
            if currentPatentNumber:
                with con:
                    cur = con.cursor()
                    cur.execute("Select * from MaintFeeEvents WHERE patentNumber = %s", (currentPatentNumber))
                    if cur.rowcount == 0:
                        cur.execute(
                            "INSERT INTO MaintFeeEvents(patentNumber, fourYear, eightYear, \
                    twelveYear, dateExpired, entityStatus) VALUES(%s, %s, %s, %s, %s, %s)"
                            , (currentPatentNumber, fourYear, eightYear, twelveYear, currentDateExpired,
                               currentEntityStatus))
                    else:
                        cur.execute("UPDATE MaintFeeEvents set fourYear = %s, eightYear = %s, \
            twelveYear = %s, dateExpired=%s, entityStatus = %s WHERE patentNumber=%s", (
                        fourYear, eightYear, twelveYear, currentDateExpired, currentEntityStatus, currentPatentNumber))

            currentPatentNumber = patentNumber
            currentEntityStatus = entityStatus
            fourYear = None
            eightYear = None
            twelveYear = None
            currentDateExpired = None

        if entryCode in fourYearCode:
            fourYear = entryDate
        elif entryCode in eightYearCode:
            eightYear = entryDate
        elif entryCode in twelveYearCode:
            twelveYear = entryDate
        elif entryCode == 'EXP.':
            currentDateExpired = entryDate

    if currentPatentNumber:
        with con:
            cur = con.cursor()
            cur.execute("Select * from MaintFeeEvents WHERE patentNumber = %s", currentPatentNumber)
            if cur.rowcount == 0:
                cur.execute(
                    "INSERT INTO MaintFeeEvents(patentNumber, fourYear, eightYear, \
            twelveYear, dateExpired, entityStatus) VALUES(%s, %s, %s, %s, %s, %s)"
                    , (currentPatentNumber, fourYear, eightYear, twelveYear, currentDateExpired, currentEntityStatus))
            else:
                cur.execute("UPDATE MaintFeeEvents set fourYear = %s, eightYear = %s, \
    twelveYear = %s, dateExpired=%s, entityStatus = %s WHERE patentNumber=%s",
                    (fourYear, eightYear, twelveYear, currentDateExpired, currentEntityStatus, currentPatentNumber))
