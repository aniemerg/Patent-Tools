# populate01()
# by Allan Niemerg
# Populates a Mysql database with patent data from files found on 
# http://www.google.com/googlebooks/uspto.html
# This file works with Patent files from 2001 

from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import tostring
import MySQLdb as mdb
from lxml.html.soupparser import fromstring
from lxml.etree import tostring as tstring
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


def populate01(inputFile):
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

    xmld = ''
    codecs.register_error('spacer', lambda ex: (u' ', ex.start + 1))
    for _t in f:
        _t = _t.replace("&", "")
        _t = _t.decode('utf8', 'spacer')
        if (_t.find('<?xml') == -1 and _t.find('<!DOCTYPE') == -1 and _t.find('<!ENTITY') == -1 and _t.find(
            ']>') == -1):
            xmld = xmld + _t
        try:
            if _t.find('</PATDOC>') > -1:
                body = fromstring(xmld)
                g = open("tmp", "w")
                g.write(tstring(body))
                g.close()
                xmld = ''
                doc = ElementTree()
                doc.parse("tmp")
                root = doc.getroot()
                for n in root.iter("patdoc"):
                    if n is None: continue
                    #patent number
                    patentNumber = 0
                    #appplication Number and publication Number
                    for j in n.iter("b100"):
                        dateFiled = None
                        country = ''
                        kind = ''
                        name = ''
                        for k in j.iterfind("b110/dnum/pdat"):
                            if k.text.isdigit():
                                patentNumber = int(k.text)
                        if not patentNumber:
                            continue
                        for k in j.iterfind("b140/date/pdat"):
                            if k.text.isdigit():
                                dateFiled = int(k.text)
                        for k in j.iterfind("b190/pdat"):
                            country = k.text
                        for k in j.iterfind("b130/pdat"):
                            kind = k.text

                        with con:
                            cur = con.cursor()
                            cur.execute(
                                "INSERT INTO PublicationReference(patentNumber, country, kind, name, date) VALUES(%s, %s, %s, %s, %s)"
                                , (patentNumber, country, kind, name, dateFiled))
                    if not patentNumber:
                        continue

                    for j in n.iter("b200"):
                        docNumber = 0
                        dateFiled = None
                        country = ''

                        for k in j.iterfind("b210/dnum/pdat"):
                            docNumber = k.text
                        for k in j.iterfind("b220/date/pdat"):
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
                    for l in n.iter("b721"):
                        for k in l.iter("party-us"):
                            firstName = ''
                            lastName = ''
                            address = ''

                            for ln in k.iterfind("nam/fnm/pdat"):
                                if ln.text: lastName = ln.text
                            for ln in k.iterfind("nam/snm/stext/pdat"):
                                if ln.text: firstName = ln.text

                            for add in k.iter("adr"):
                                for street in add.iterfind("str/pdat"):
                                    if street.text: address = street.text
                                for city in add.iterfind("city/pdat"):
                                    if city.text: address += ' - ' + city.text
                                for country in add.iterfind("ctry/pdat"):
                                    if country.text: address += ' - ' + country.text
                            inventor += (firstName + ' ' + lastName + ' (' + address + ');')
                    #international
                    for ic in n.iter("b500"):
                        for t in ic.iterfind("b510/b511/pdat"):
                            inter = t.text
                            with con:
                                cur = con.cursor()
                                cur.execute(
                                    "INSERT INTO InternationalClass(patentNumber, interClass) VALUES(%s, %s)"
                                    , (patentNumber, inter))

                    #field of research
                    for k in n.iter("b580"):
                        for j in k.iterfind("b582/pdat"):
                            fieldOfResearch = j.text
                            with con:
                                cur = con.cursor()
                                cur.execute("INSERT INTO FieldOfResearch(patentNumber, class) VALUES(%s, %s)",
                                    (patentNumber, fieldOfResearch.strip()))
                        for j in k.iterfind("b583us/pdat"):
                            fieldOfResearch = j.text
                            with con:
                                cur = con.cursor()
                                cur.execute("INSERT INTO FieldOfResearch(patentNumber, class) VALUES(%s, %s)",
                                    (patentNumber, fieldOfResearch.strip()))


                    #examiner
                    primaryExaminer = ''
                    assitantExaminer = ''

                    for E in n.iter("b745"):
                        for pr in E.iterfind("b746/party-us/nam"):
                            firstName = ''
                            lastName = ''
                            for ln in pr.iterfind("fnm/pdat"):
                                lastName = ln.text
                            for ln in pr.iterfind("snm/stext/pdat"):
                                firstName = ln.text
                            if firstName == None: firstName = ''
                            if lastName == None: lastName = ''
                            primaryExaminer += lastName + ' ' + firstName + '; '

                        for pr in E.iterfind("b747/party-us/nam"):
                            firstName = ''
                            lastName = ''
                            for ln in pr.iterfind("fnm/pdat"):
                                lastName = ln.text
                            for ln in pr.iterfind("snm/stext/pdat"):
                                firstName = ln.text
                            if firstName == None: firstName = ''
                            if lastName == None: lastName = ''
                            assitantExaminer += lastName + ' ' + firstName + '; '

                    #Attorney, Agent or Firm,
                    attorney = ''
                    for k in n.iter("b740"):
                        for ln in k.iterfind("b741/party-us/nam/onm/stext/pdat"):
                            if ln.text:
                                attorney += ln.text

                    #Abstract text
                    abstr = ''
                    for abst in n.iter("abstract"):
                        p = abst.find("p")
                        _p = tostring(p)
                        abstr = convertToHTMLView(_p.encode('UTF-8'))


                    #US Class
                    #furtherUSClass
                    usClass = ''
                    for p in n.iter("b520"):
                        for ma in p.iterfind("b521/pdat"):
                            if ma.text:
                                usClass = ma.text
                        for fu in p.iterfind("b522/pdat"):
                            if fu.text:
                                furtherClass = fu.text.strip()
                                with con:
                                    cur = con.cursor()
                                    cur.execute(
                                        "INSERT INTO FurtherUSClass(patentNumber, furtherUSClass) VALUES(%s, %s)",
                                            (patentNumber, furtherClass))


                    #patent references
                    for _n in n.iter("b561"):
                        country = _n.iter("pcit/party-us")
                        if country is None: continue
                        kind = ''
                        category = ''
                        dateFiled = ''
                        for t in _n.iterfind("pcit/doc/dnum/pdat"):
                            number = t.text
                        for t in _n.iterfind("pcit/doc/date/pdat"):
                            dateFiled = int(t.text)
                        for t in _n.iterfind("party-us/nam/snm/stext/pdat"):
                            name = t.text
                        for t in _n.iterfind("pcit/doc/kind/pdat"):
                            kind = t.text
                        for t in _n.iter("cited-by-examiner"):
                            category = "cited-by-examiner"
                        for t in _n.iter("cited-by-other"):
                            category = "cited-by-other"

                        if number:
                            with con:
                                cur = con.cursor()
                                cur.execute(
                                    "INSERT INTO ReferPatcit(patentNumber, docNumber, country, kind, category, date) VALUES(%s, %s, %s, %s, %s, %s)"
                                    , (patentNumber, number, "US", kind, category, dateFiled))
                    value = ''
                    for j in n.iter("b562"):
                        category = ''
                        for t in j.iter("cited-by-examiner"):
                            category = "cited-by-examiner"
                        for t in j.iter("cited-by-other"):
                            category = "cited-by-other"

                        t = j.find("ncit/stext/pdat")
                        if t is None: continue
                        value = tostring(t)
                        if value:
                            with con:
                                cur = con.cursor()
                                cur.execute("INSERT INTO ReferNplcit(patentNumber, value, category) VALUES(%s, %s, %s)",
                                        (patentNumber, convertToHTMLView(value.encode("UTF-8")), category))

                    #claims
                    claim = ''
                    cl = n.find("sdocl")
                    if cl:
                        _cl = tostring(cl)
                        claim = convertToHTMLView(_cl.encode('UTF-8')).strip()

                    #descriptions
                    description = ''
                    des = n.find("sdode")
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
                                     primaryExaminer.encode('UTF-8'), assitantExaminer.encode('UTF-8'),
                                     attorney.encode('UTF-8')
                                     , claim, description))
        except Exception as e:
            print e
