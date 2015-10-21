from string import Template

cols = []
table = ""
colsType = {}

def sqlVarToClass(x):
    return ''.join([word[0].upper() + word[1:] for word in x.split('_')])

def sqlVarToVar(x):
    t = sqlVarToClass(x)
    return t[0].lower()+t[1:]

def getColsType(c):
    if c in colsType:
        return colsType[c]
    elif "time" in c or "Time" in c:
        return "Timestamp"
    else:
        return "NULL"

def sqlVarToDAOParam(c):
    vc = sqlVarToVar(c)
    return "@SQLParam(\""+vc+"\") "+getColsType(c)+" "+vc

def sqlVarToFuncParam(c):
    vc = sqlVarToVar(c)
    return getColsType(c)+" "+vc

def makeSqlWhere(c):
    if " " not in c:
        return ":"+sqlVarToVar(c)+"="+c
    else:
         cArray=c.split(' ')
         return ":"+sqlVarToVar(cArray[0])+" "+' '.join(cArray[1:])

def makeWhereVar(c):
    if " " not in c:
        return c
    else:
        return c.split(" ")[0]

def makeSqlAssign(c):
    return c+"=:"+sqlVarToVar(c)

def makeFuncSuffix(c):
    return "And".join([sqlVarToClass(x) for x in c])

def findByCall(dao,c):
    return dao+".findBy"+makeFuncSuffix(c)+"("+', '.join([sqlVarToVar(x) for x in c])+");"

def findByCallArg(dao, c):
    return dao+".findBy"+makeFuncSuffix(c)+"("+','.join(["\""+vc[0]+"0\"" for vc in c])+");"

def updateCall(dao,c1, c2):
    return dao+".update"+ makeFuncSuffix(c2)+"By"+makeFuncSuffix(c1)+"("+','.join([sqlVarToVar(x) for x in c1+c2])+");"

def saveCall(dao, c):
    return dao+".save("+sqlVarToVar(c)+");"

def makeGet(c):
    return "get"+c[0].upper()+c[1:]+"()"

def makeSet(c):
    return "set"+c[0].upper()+c[1:]+"()"

state = 0
daoHeadPrinted = False

findFuncArray=[]
updateFuncArray=[]

with open('s') as f:
    for line in f:
        if line=="\n":
            state=(state+1)%3
            continue

        if 0==state:
            if "CREATE TABLE IF NOT EXISTS" in line:
                table = line.split(' ')[5]
                continue

            c = line[line.index('`')+1:line.rindex('`')]
            cols.append(c)

            #generate pojo vars
            t = "NULL"
            if "BIGINT" in line:
                t = "long"
            elif "VARCHAR" in line:
                t = "String"
            elif "TIMESTAMP" in line:
                t = "Timestamp"
            elif "TINYINT" in line or "INT" in line:
                t = "int"
            else:
                print "what the fuck!!"
            colsType[c]=t

            print "private",t,c+";\n"
        elif 1 == state:
            #generate dao find
            if not daoHeadPrinted:
                print "static final String TABLE = \""+table+"\";\n"
                cols = cols[1:]
                #print "//"+",".join(cols)+"\n"
                print "static final String FIELDS = \""+','.join(cols)+"\";\n"
                daoHeadPrinted = True
                continue
            if "find" in line:
                continue

            line = line.strip(' #\n')
            lineArray = line.split(':')
            whereArray = lineArray[0].split(',')
            print "@SQL(\"SELECT \" + FIELDS + \" FROM \" + TABLE + \" WHERE " + " AND ".join([makeSqlWhere(c) for c in whereArray])+"\")"
            whereSqlVars = [makeWhereVar(c) for c in whereArray]
            findFuncArray.append([whereSqlVars, lineArray[1]])

            method=""
            if lineArray[1]=="1":
                method+="POJO"+sqlVarToClass(table)
            else:
                method+="List<POJO"+sqlVarToClass(table)+">"
            method+=(" findBy"+makeFuncSuffix(whereSqlVars)+"("+", ".join([sqlVarToDAOParam(x) for x in whereSqlVars])+");\n")
            print method
        else:
            #generate dao update
            if "update" in line:
                continue;

            line = line.strip(' #\n')
            lineArray = line.split(':')
            whereArray = lineArray[0].split(',')
            whereSqlVars = [makeWhereVar(c) for c in whereArray]
            assignSqlVars = lineArray[1].split(',')
            print "@SQL(\"UPDATE \" + TABLE + \" SET "+','.join([makeSqlAssign(c) for c in assignSqlVars])+" WHERE" +  " AND ".join([makeSqlWhere(c) for c in whereArray])+"\")"
            whereSqlVars = [makeWhereVar(c) for c in whereArray]
            updateFuncArray.append([whereSqlVars, assignSqlVars])

            print "void update"+makeFuncSuffix(assignSqlVars)+"By"+makeFuncSuffix(whereSqlVars)+"("+", ".join([sqlVarToDAOParam(x) for x in (whereSqlVars+assignSqlVars)])+");\n"

#generate dao save
values=":p."+", :p.".join(cols)
print "@SQL(\"INSERT INTO \" + TABLE + \"(\" + FIELDS + \") VALUES ("+ values+")\")"
print "void save(@SQLParam(\"p\") POJO"+sqlVarToClass(table)+" "+sqlVarToVar(table)+");\n"

#print findFuncArray
#print updateFuncArray

#generate impl
print "@Autowired"
dao = sqlVarToVar(table)+"DAO"
print  sqlVarToClass(table)+"DAO "+dao+";\n"

for func in findFuncArray:
    method = "public "
    if  func[1]=="1":
        method+="POJO"+sqlVarToClass(table)
    else:
        method+="List<POJO"+sqlVarToClass(table)+">"
    method+=(" findBy"+makeFuncSuffix(func[0])+"("+", ".join([sqlVarToFuncParam(x) for x in func[0]])+")")
    method+="{"+findByCall(dao, func[0])+"}"
    print method+"\n"

for func in updateFuncArray:
    method = "public void update"
    method+= makeFuncSuffix(func[1])+"By"+makeFuncSuffix(func[0])+"("+", ".join([sqlVarToFuncParam(x) for x in func[0]+func[1]])+")"
    method+="{"+updateCall(dao, func[0], func[1])+"}"
    print method+"\n"

method = "void save(POJO"+sqlVarToClass(table)+" "+sqlVarToVar(table)+")"
method +="{"+saveCall(dao,table)+"}"
print method+"\n"

#generate test
print "@RunWith(SpringJUnit4ClassRunner.class)"
print "@ContextConfiguration(locations = \"classpath:applicationContext.xml\")\n"

print "public static final Logger LOGGER = LoggerFactory.getLogger("+sqlVarToClass(table)+"DAOTest.class);\n"

print "@Autowired\nprivate "+sqlVarToClass(table)+"DAO " + dao+";\n"

print "@Override\n@Before\npublic void setUp() throws Exception {\nsuper.setUp();\n}\n"
print "@Override\n@After\npublic void tearDown() throws Exception {\nsuper.tearDown();\n}\n"

#generate  find test
print "@Test"
print "public void testFind() throws Exception {"
print "Statement st = conn.createStatement();"
print "try{"
pstmt = "PreparedStatement pstmt = conn.prepareStatement(\"insert into \" + PosSessionDAO.TABLE + \"(\" + PosSessionDAO.FIELDS + \") values \""

timeAllCount=0
values=[]
for i in range(5):
    t=[]
    for c in cols:
        if colsType[c]=="Timestamp":
            t.append('?')
            timeAllCount+=1
        elif colsType[c] == "int" or colsType[c] == "long":
            t.append(str(1))
        else:
            t.append('\''+c[0]+str(i)+'\'');
    values.append("("+','.join(t)+")")
pstmt=pstmt+",".join(values)+"\")"
print pstmt+"\n"

if timeAllCount>0:
    print "Timestamp t0 = new Timestamp(System.currentTimeMillis());"
    for i in range(1, timeAllCount):
        print "Timestamp t"+str(i)+"= new Timestamp(t0.getTime()+"+str(i)+"*5*60*1000);"

    for i in range(timeAllCount):
            print "pstmt.setTimestamp("+str(i+1)+",t"+str(i)+");"

print "\npstmt.executeUpdate();\npstmt.close();\n"
print "POJO"+sqlVarToClass(table)+ " pojo;"
print "POJO"+sqlVarToClass(table)+" pojos"
for func in findFuncArray:
    print "\n"
    if func[1]=="1":
        print "pojo="+findByCallArg(dao, func[0])
        print "Assert.assertNotNull(pojo);"
        for c in cols:
                if getColsType(c) == "Timestamp":
                    continue
                print "Assert.asserEquals(\""+c[0]+"0\", pojo."+makeGet(c)+");"
    else:
        print "pojos="+findByCallArg(dao, func[0])
        print "Assert.assertFalse(pojos.isEmpty())"
        for c in cols:
                if getColsType(c) == "Timestamp":
                    continue
                print "Assert.asserEquals(\""+c[0]+"0\", pojos.get(0)."+makeGet(c)+");"

print "} finally {\nst.close();\n}\n}"