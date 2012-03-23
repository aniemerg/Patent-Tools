# populateClassification()
# by Allan Niemerg
# Populates a Mysql database with patent classification data from files found on 
# http://www.google.com/googlebooks/uspto.html
# This data is cleaner than the patent classification data in the patent files
import MySQLdb as mdb

def populateClassification(inputFile="mcfpat.txt"):
    try:
        f = open(inputFile, 'r')
    except Exception as e:
        return


    #mdb.connect('localhost', 'username', 'password', 'database');
    con = mdb.connect('localhost', 'root', 'blueberry', 'mfees');
    with con:
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS Classification(patentNumber INT(8), class VARCHAR(3), subclass VARCHAR(7))");
        cur.execute("SELECT MAX(patentNumber) FROM USPatents")
        row = cur.fetchone()
        maxPatent = int(row[0])
        cur.execute("SELECT MIN(patentNumber) FROM USPatents")
        row = cur.fetchone()
        minPatent = int(row[0])
        #minPatent = 6000000
        print str(maxPatent) + " " + str(minPatent)
    l = 0
    for lf in f:
        l = l + 1
        if not lf[0].isdigit() : continue
        patentNumber = int(lf[:7])

        if patentNumber < int(minPatent) or patentNumber > int(maxPatent): continue
        print l
        cl = lf[:10][7:].lstrip('0');
        subcl1 = lf[:13][10:]
        subcl2 = lf[:16][13:]
        if subcl2.strip('0').isdigit():
            subcl = subcl1.strip('0') + '.' +subcl2.strip('0');
        else:
            subcl = subcl1.strip('0') +subcl2.strip('0');
        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO Classification(patentNumber, class, subclass) VALUES(%s, %s, %s)"
                                , (patentNumber, cl, subcl));
        