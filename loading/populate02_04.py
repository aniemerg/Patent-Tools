# populate02_04()
# by Allan Niemerg
# Populates a Mysql database with patent data from files found on 
# http://www.google.com/googlebooks/uspto.html
# This file works with Patent files from 2002-2004

from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import tostring
import MySQLdb as mdb
import codecs

def modifyException(x):
    while x.find('/>') > -1:
        d = x.find('/>')
        x = x[:d] + x[d+1:]
        _x = ''
        for i in reversed(range(0, d)):
            if x[i] == '<':
                _x = '</' + _x
                _x = _x.split()[0] + '>'
                newx = x[:d+1] + _x + x[d+1:]
                x = newx
                break
            _x = x[i] + _x

    return x

def convertToHTMLView(x):
    num = 0
    des = ''
    for i in x:
        if (i == '<'):
            num = num + 1
            continue
        if (i == '>'):
            num = num - 1
            continue
        if num == 0:
            des = des + i
    return des

def populate02_04(inputFile):
    #cleaning XML file
    try:
        f = open(inputFile, 'r')
    except Exception as e:
        print e
        return
    #mdb.connect('localhost', 'username', 'password', 'database');
    con = mdb.connect('localhost', 'root', 'password', 'Patents');
    with con:
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS USPatents(patentNumber INT KEY, abstract TEXT, inventor TEXT, \
            currentUSClass TEXT, primaryExaminer TEXT, assistantExaminer TEXT, attorney TEXT, claims MEDIUMTEXT, description MEDIUMTEXT)");

        cur.execute(
            "CREATE TABLE IF NOT EXISTS InternationalClass(patentNumber INT, interClass TEXT)");

        cur.execute("CREATE TABLE IF NOT EXISTS \
             FurtherUSClass(patentNumber INT, furtherUSClass TEXT)");
        
        cur.execute("CREATE TABLE IF NOT EXISTS \
             FurtherUSClass(patentNumber INT, furtherUSClass TEXT)");

        cur.execute("CREATE TABLE IF NOT EXISTS \
             FieldOfResearch(patentNumber INT, class TEXT)");

        cur.execute("CREATE TABLE IF NOT EXISTS \
            PublicationReference(patentNumber INT, country TEXT, kind TEXT, name TEXT, date BIGINT)");

        cur.execute("CREATE TABLE IF NOT EXISTS \
            ApplicationReference(patentNumber INT, docNumber TEXT, country TEXT, date BIGINT)");

        cur.execute("CREATE TABLE IF NOT EXISTS \
            ReferPatcit(patentNumber INT, docNumber TEXT, country TEXT, kind TEXT, category TEXT, name TEXT, date BIGINT)");

        cur.execute("CREATE TABLE IF NOT EXISTS \
            ReferNplcit(patentNumber INT, value TEXT, category TEXT)");

    xmld = '<TOP>\n'
    codecs.register_error('spacer', lambda ex: (u' ', ex.start + 1))
    for _t in f:
        _t = _t.replace("&", "")
        _t = _t.decode('utf8', 'spacer')
        if _t.find('/>') > -1:
            xmld = xmld + modifyException(_t)
        elif (_t.find('<?xml') == -1 and _t.find('<!DOCTYPE') == -1 and _t.find('<!ENTITY') == -1 and _t.find(']>') == -1):
            xmld = xmld + _t
        try:
            if _t.find('</PATDOC>') > -1:
                xmld = xmld + '</TOP>'
                g = open("tmp", "w")
                g.write(xmld)
                g.close()
                xmld = '<TOP>\n'
                doc = ElementTree()
                doc.parse("tmp")
                root = doc.getroot()
                for n in root.iter("PATDOC"):
                    #patent number
                    patentNumber = 0
                    #appplication Number and publication Number
                    for j in n.iter("B100"):
                        dateFiled = None
                        country = ''
                        kind = ''
                        name = ''
                        for k in j.iterfind("B110/DNUM/PDAT"):
                            if k.text.isdigit():
                                patentNumber = int(k.text)
                        if not patentNumber:
                            continue
                        print patentNumber
                        for k in j.iterfind("B140/DATE/PDAT"):
                            if k.text.isdigit():
                                dateFiled = int(k.text)
                        for k in j.iterfind("B190/PDAT"):
                            country = k.text
                        for k in j.iterfind("B130/PDAT"):
                            kind = k.text
                        with con:
                            cur = con.cursor()
                            cur.execute(
                                "INSERT INTO PublicationReference(patentNumber, country, kind, name, date) VALUES(%s, %s, %s, %s, %s)"
                                , (patentNumber, country, kind, name, dateFiled))
                    if not patentNumber:
                        continue
                    for j in n.iter("B200"):
                        docNumber = 0
                        dateFiled = None
                        country = ''

                        for k in j.iterfind("B210/DNUM/PDAT"):
                            docNumber = k.text
                        for k in j.iterfind("B220/DATE/PDAT"):
                            if k.text.isdigit():
                                dateFiled = int(k.text)
                        country = 'US'
                        with con:
                            cur = con.cursor()
                            cur.execute(
                                "INSERT INTO ApplicationReference(patentNumber, docNumber, country, date) VALUES(%s, %s, %s, %s)"
                                , (patentNumber, docNumber, country, dateFiled))

                    #inventor
                    inventor = ''
                    for l in n.iter("B721"):
                        for k in l.iter("PARTY-US"):
                            firstName = ''
                            lastName = ''
                            address = ''

                            for ln in k.iterfind("NAM/FNM/PDAT"):
                                if ln.text: lastName = ln.text
                            for ln in k.iterfind("NAM/SNM/STEXT/PDAT"):
                                if ln.text: firstName = ln.text

                            for add in k.iter("ADR"):
                                for street in add.iterfind("STR/PDAT"):
                                    if street.text: address = street.text
                                for city in add.iterfind("CITY/PDAT"):
                                    if city.text: address += ' - ' + city.text
                                for country in add.iterfind("CTRY/PDAT"):
                                    if country.text: address += ' - ' + country.text
                            inventor += (firstName + ' ' + lastName + ' (' + address + ');')
                    #inter
                    for ic in n.iter("B500"):
                        for t in ic.iterfind("B510/B511/PDAT"):
                            inter = t.text
                            with con:
                                cur = con.cursor()
                                cur.execute(
                                    "INSERT INTO InternationalClass(patentNumber, interClass) VALUES(%s, %s)"
                                    , (patentNumber, inter))

                    #field of research
                    for k in n.iter("B580"):
                        for j in k.iterfind("B582/PDAT"):
                            fieldOfResearch = j.text
                            with con:
                                cur = con.cursor()
                                cur.execute("INSERT INTO FieldOfResearch(patentNumber, class) VALUES(%s, %s)",
                                    (patentNumber, fieldOfResearch.strip()))
                        for j in k.iterfind("B583US/PDAT"):
                            fieldOfResearch = j.text
                            with con:
                                cur = con.cursor()
                                cur.execute("INSERT INTO FieldOfResearch(patentNumber, class) VALUES(%s, %s)",
                                    (patentNumber, fieldOfResearch.strip()))
                    #US Class
                    #furtherUSClass
                    usClass = ''
                    for p in n.iter("B520"):
                        for ma in p.iterfind("B521/PDAT"):
                            if ma.text:
                                usClass = ma.text
                        for fu in p.iterfind("B522/PDAT"):
                            if fu.text:
                                furtherClass = fu.text.strip()
                                with con:
                                    cur = con.cursor()
                                    cur.execute("INSERT INTO FurtherUSClass(patentNumber, furtherUSClass) VALUES(%s, %s)",
                                        (patentNumber, furtherClass))

                    #examiner
                    primaryExaminer = ''
                    assitantExaminer = ''

                    for E in n.iter("B745"):
                        for pr in E.iterfind("B746/PARTY-US/NAM"):
                            firstName = ''
                            lastName = ''
                            for ln in pr.iterfind("FNM/PDAT"):
                                lastName = ln.text
                            for ln in pr.iterfind("SNM/STEXT/PDAT"):
                                firstName = ln.text
                            if firstName == None: firstName = ''
                            if lastName == None: lastName = ''
                            primaryExaminer += lastName + ' ' + firstName + '; '

                        for pr in E.iterfind("B747/PARTY-US/NAM"):
                            firstName = ''
                            lastName = ''
                            for ln in pr.iterfind("FNM/PDAT"):
                                lastName = ln.text
                            for ln in pr.iterfind("SNM/STEXT/PDAT"):
                                firstName = ln.text
                            if firstName == None: firstName = ''
                            if lastName == None: lastName = ''
                            assitantExaminer += lastName + ' ' + firstName + '; '

                    #Attorney, Agent or Firm,
                    attorney = ''
                    for k in n.iter("B740"):
                        for ln in k.iterfind("B741/PARTY-US/NAM/ONM/STEXT/PDAT"):
                            if ln.text:
                                attorney += ln.text

                    #Abstract text
                    abstr = ''
                    for abst in n.iter("abstract"):
                        p = abst.find("p")
                        _p = tostring(p)
                        abstr = convertToHTMLView(_p.encode('UTF-8'))

                    #patent references
                    for _n in n.iter("B561"):
                        country = _n.iter("PCIT/PARTY-US")
                        if country is None: continue
                        kind = ''
                        category = ''
                        dateFiled = ''
                        for t in _n.iterfind("PCIT/DOC/DNUM/PDAT"):
                            number = t.text
                        for t in _n.iterfind("PCIT/DOC/DATE/PDAT"):
                            dateFiled = int(t.text)
                        for t in _n.iterfind("PARTY-US/NAM/SNM/STEXT/PDAT"):
                            name = t.text
                        for t in _n.iterfind("PCIT/DOC/KIND/PDAT"):
                            kind = t.text
                        for t in _n.iter("CITED-BY-EXAMINER"):
                            category = "CITED-BY-EXAMINER"
                        for t in _n.iter("CITED-BY-OTHER"):
                            category = "CITED-BY-OTHER"
                        if number:
                            with con:
                                cur = con.cursor()
                                cur.execute(
                                    "INSERT INTO ReferPatcit(patentNumber, docNumber, country, kind, category, date) VALUES(%s, %s, %s, %s, %s, %s)"
                                    , (patentNumber, number, "US", kind, category, dateFiled))
                    value = ''
                    for j in n.iter("B562"):
                        category = ''
                        for t in _n.iter("CITED-BY-EXAMINER"):
                            category = "CITED-BY-EXAMINER"
                        for t in _n.iter("CITED-BY-OTHER"):
                            category = "CITED-BY-OTHER"
                        t = j.find("NCIT/STEXT/PDAT")
                        if t is None: continue
                        value = tostring(t)
                        if value:
                            with con:
                                cur = con.cursor()
                                cur.execute("INSERT INTO ReferNplcit(patentNumber, value, category) VALUES(%s, %s, %s)",
                                    (patentNumber, convertToHTMLView(value.encode("UTF-8")), category))

                    #claims
                    claim = ''
                    cl = n.find("SDOCL")
                    if cl:
                        _cl = tostring(cl)
                        claim = convertToHTMLView(_cl.encode('UTF-8')).strip()

                    #descriptions
                    description = ''
                    des = n.find("SDODE")
                    if des:
                        _des = tostring(des)
                        description = convertToHTMLView(_des.encode('UTF-8')).strip()

                    with con:
                        cur = con.cursor()
                        cur.execute("Select * from USPatents where patentNumber = %s", (patentNumber))
                        if cur.rowcount == 0:
                            cur.execute("INSERT INTO USPatents(patentNumber, abstract, inventor, currentUSClass,\
                        primaryExaminer, assistantExaminer, attorney, claims, description) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                        ,
                                (patentNumber, abstr, inventor.encode('UTF-8'), usClass.encode('UTF-8'),
                                 primaryExaminer.encode('UTF-8'), assitantExaminer.encode('UTF-8'), attorney.encode('UTF-8')
                                 , claim, description))            
        except Exception as e:
            print e
