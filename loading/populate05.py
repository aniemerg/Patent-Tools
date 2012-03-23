# populate05()
# by Allan Niemerg
# Populates a Mysql database with patent data from files found on 
# http://www.google.com/googlebooks/uspto.html
# This file works with Patent files from 2005

from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import tostring
import MySQLdb as mdb
import codecs


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


def populate05(inputFile):
    #cleaning XML file
    try:
        f = open(inputFile, 'r')
    except Exception as e:
        return
    #mdb.connect('localhost', 'username', 'password', 'database');
    con = mdb.connect('localhost', 'root', 'password', 'Patents');
    
    with con:
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS USPatents(patentNumber INT, abstract TEXT, inventor TEXT, \
            currentUSClass TEXT, primaryExaminer TEXT, assistantExaminer TEXT, attorney TEXT, claims MEDIUMTEXT, description MEDIUMTEXT)");

        cur.execute(
            "CREATE TABLE IF NOT EXISTS InternationalClass(patentNumber VARCHAR(8), interClass TEXT)");
        
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
        if _t.find('<?xml') == -1 and _t.find('<!DOCTYPE') == -1:
            xmld = xmld + _t
        try:
            if _t.find('</us-patent-grant>') > -1:
                #print _t
                xmld = xmld + '</TOP>'
                g = open("tmp", "w")
                g.write(xmld)
                g.close()
                xmld = '<TOP>\n'


                #start parsing
                doc = ElementTree()
                doc.parse("tmp")
                root = doc.getroot()


                #loop for main patent
                for n in root.iter("us-patent-grant"):
                    #patent number
                    patentNumber = 0
                    #appplication Number and publication Number
                    for ar in n.iter("publication-reference"):
                        dateFiled = None
                        country = ''
                        kind = ''
                        name = ''
                        for j in ar.iter("document-id"):
                            for k in j.iter("doc-number"):
                                if k.text.isdigit():
                                    patentNumber = int(k.text)
                            if not patentNumber:
                                continue
                            for k in j.iter("date"):
                                if k.text.isdigit():
                                    dateFiled = int(k.text)
                            for k in j.iter("country"):
                                country = k.text
                            for k in j.iter("kind"):
                                kind = k.text
                            for k in j.iter("name"):
                                name = k.text
                            with con:
                                cur = con.cursor()
                                cur.execute(
                                    "INSERT INTO PublicationReference(patentNumber, country, kind, name, date) VALUES(%s, %s, %s, %s, %s)"
                                    , (patentNumber, country, kind, name, dateFiled))
                    if not patentNumber:
                        continue

                    for ar in n.iter("application-reference"):
                        docNumber = 0
                        dateFiled = None
                        country = ''
                        for j in ar.iter("document-id"):
                            for k in j.iter("doc-number"):
                                docNumber = k.text
                            for k in j.iter("date"):
                                if k.text.isdigit():
                                    dateFiled = int(k.text)
                            for k in j.iter("country"):
                                country = k.text
                            with con:
                                cur = con.cursor()
                                cur.execute(
                                    "INSERT INTO ApplicationReference(patentNumber, docNumber, country, date) VALUES(%s, %s, %s, %s)"
                                    , (patentNumber, docNumber, country, dateFiled))

                    #inventor
                    inventor = ''

                    for ar in n.iter("parties"):
                        for pr in ar.iter("applicants"):
                            for j in pr.iter("applicant"):
                                for k in j.iter("addressbook"):
                                    firstName = ''
                                    lastName = ''
                                    address = ''

                                    for ln in k.iter("last-name"):
                                        if ln.text: lastName = ln.text
                                    for ln in k.iter("first-name"):
                                        if ln.text: firstName = ln.text

                                    for add in k.iter("address"):
                                        for street in add.iter("street"):
                                            if street.text: address = street.text
                                        for city in add.iter("city"):
                                            if city.text: address += ' - ' + city.text
                                        for country in add.iter("country"):
                                            if country.text: address += ' - ' + country.text
                                    inventor += (firstName + ' ' + lastName + ' (' + address + ');')

                    #international
                    for ic in n.iter("classification-locarno"):
                        for t in ic.iterfind("main-classification"):
                            inter = t.text
                            with con:
                                cur = con.cursor()
                                cur.execute(
                                    "INSERT INTO InternationalClass(patentNumber, interClass) VALUES(%s, %s)"
                                    , (patentNumber, inter))

                    #field of research
                    for rs in n.iter("field-of-search"):
                        for k in rs.iter("classification-national"):
                            fieldOfResearch = ''
                            for j in k.iter("main-classification"):
                                fieldOfResearch = j.text
                            with con:
                                cur = con.cursor()
                                cur.execute("INSERT INTO FieldOfResearch(patentNumber, class) VALUES(%s, %s)",
                                    (patentNumber, fieldOfResearch.strip()))


                    #examiner
                    primaryExaminer = ''
                    assitantExaminer = ''

                    for E in n.iter("examiners"):
                        for pr in E.iter("primary-examiner"):
                            firstName = ''
                            lastName = ''
                            for ln in pr.iter("last-name"):
                                lastName = ln.text
                            for ln in pr.iter("first-name"):
                                firstName = ln.text
                            if firstName == None: firstName = ''
                            if lastName == None: lastName = ''
                            primaryExaminer += lastName + ' ' + firstName + '; '

                        for pr in E.iter("assistant-examiner"):
                            firstName = ''
                            lastName = ''
                            for ln in pr.iter("last-name"):
                                lastName = ln.text
                            for ln in pr.iter("first-name"):
                                firstName = ln.text

                            if firstName == None: firstName = ''
                            if lastName == None: lastName = ''
                            assitantExaminer += lastName + ' ' + firstName + '; '




                    #Attorney, Agent or Firm,
                    attorney = ''
                    p = n.find("us-bibliographic-data-grant/parties/agents/agent/addressbook")
                    if p:
                        for ar in p.iter("orgname"):
                            attorney += ar.text + ';'

                    #Abstract text
                    abstr = ''
                    for abst in n.iter("abstract"):
                        p = abst.find("p")
                        _p = tostring(p)
                        abstr = convertToHTMLView(_p.encode('UTF-8'))


                    #US Class
                    #furtherUSClass
                    usClass = ''
                    p = n.find("us-bibliographic-data-grant/classification-national")
                    for ma in p.iter("main-classification"):
                        if ma.text:
                            usClass = ma.text
                    for fu in p.iter("further-classification"):
                        if fu.text:
                            furtherClass = fu.text.strip()
                            with con:
                                cur = con.cursor()
                                cur.execute("INSERT INTO FurtherUSClass(patentNumber, furtherUSClass) VALUES(%s, %s)",
                                    (patentNumber, furtherClass))


                    #patent references
                    for _n in n.iter("references-cited"):
                        for j in _n.iter("citation"):
                            for tmp in j.iter("patcit"):
                                country = ''
                                kind = ''
                                name = ''
                                dateFiled = ''
                                for k in tmp.iter("document-id"):
                                    _t = k.find("country")
                                    if _t.text == "US":
                                        country = "US"
                                        t = k.find("kind")
                                        if t: kind = t.text
                                        t = k.find("date")
                                        if t.text.isdigit(): dateFiled = int(t.text)
                                        t = k.find("name")
                                        if t: name = t.text
                                        number = k.find("doc-number")
                                        if number.text:
                                            num = number.text
                                            with con:
                                                cur = con.cursor()
                                                cur.execute(
                                                    "INSERT INTO ReferPatcit(patentNumber, docNumber, country, kind, name, date) VALUES(%s, %s, %s, %s, %s, %s)"
                                                    , (patentNumber, num, country, kind, name, dateFiled))
                            value = ''
                            for tmp in j.iter("nplcit"):
                                cat = j.find("category")
                                t = tmp.find("othercit")
                                value = tostring(t)
                                if value:
                                    with con:
                                        cur = con.cursor()
                                        cur.execute("INSERT INTO ReferNplcit(patentNumber, value, category) VALUES(%s, %s, %s)",
                                            (patentNumber, convertToHTMLView(value.encode("UTF-8")), cat.text))

                    #claims
                    claim = ''
                    cl = n.find("claims")
                    if cl:
                        _cl = tostring(cl)
                        claim = convertToHTMLView(_cl.encode('UTF-8')).strip()

                    #descriptions
                    description = ''
                    des = n.find("description")
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

        except  Exception as e:
            print e