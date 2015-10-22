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

def makeSqlWhereEqual(c):
    if all([x not in c for x in ["<", ">", "between"]]):
        return c+" = :"+sqlVarToVar(c)
    else:
         cArray=c.split(' ')
         return ":"+sqlVarToVar(cArray[0])+" "+' '.join(cArray[1:])

def makeSqlWhereVar(c):
    if " " not in c:
        return c
    else:
        return c.split(" ")[0]

def makeSqlAssign(c):
    return c+"=:"+sqlVarToVar(c)

def makeFuncSuffix(c):
    return "And".join([sqlVarToClass(x) for x in c])

def findByWithVar(dao,c):
    return dao+".findBy"+makeFuncSuffix(c)+"("+', '.join([sqlVarToVar(x) for x in c])+");"

def findByWithArg(dao, c):
    args = []
    for vc in c:
        if getColsType(vc) == "Timestamp":
            args.append("t0")
        else:
            args.append("\""+vc[0]+"0\"")
    return dao+".findBy"+makeFuncSuffix(c)+"("+','.join(args)+");"

def updateWithVar(dao,c1, c2):
    return dao+".update"+ makeFuncSuffix(c2)+"By"+makeFuncSuffix(c1)+"("+','.join([sqlVarToVar(x) for x in c1+c2])+");"

def saveWithVar(dao, c):
    return dao+".save("+sqlVarToVar(c)+");"

def makeGet(c):
    return "get"+c[0].upper()+c[1:]+"()"

def makeSet(c, v):
    return "set"+c[0].upper()+c[1:]+"("+str(v)+");"

def makeAsserts(cols, v):
    for c in cols:
        if getColsType(c) == "Timestamp":
            continue
        elif getColsType(c) == "int" or getColsType == "long":
            print "Assert.assertEquals(1, "+v+"."+makeGet(c)+");"
        else:
            print "Assert.assertEquals(\""+c[0]+"0\", "+v+"."+makeGet(c)+");"

state = 0
daoHeadPrinted = False

findFuncArray=[]
updateFuncArray=[]

POJOClass=""
POJOVar=""

with open('s') as f:
    for line in f:
        if line=="\n":
            state=(state+1)%3
            continue

        if 0==state:
            if "CREATE TABLE IF NOT EXISTS" in line:
                table = line.split(' ')[5]
                POJOClass = "POJO"+sqlVarToClass(table)
                POJOVar = sqlVarToVar(table)
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
                print "What?!"
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
            print "@SQL(\"SELECT \" + FIELDS + \" FROM \" + TABLE + \" WHERE " + " AND ".join([makeSqlWhereEqual(c) for c in whereArray])+"\")"
            sqlWhereVars = [makeSqlWhereVar(c) for c in whereArray]
            findFuncArray.append([sqlWhereVars, lineArray[1]])

            method=""
            if lineArray[1]=="1":
                method+=POJOClass
            else:
                method+="List<"+POJOClass+">"
            method+=(" findBy"+makeFuncSuffix(sqlWhereVars)+"("+", ".join([sqlVarToDAOParam(x) for x in sqlWhereVars])+");\n")
            print method
        else:
            #generate dao update
            if "update" in line:
                continue;

            line = line.strip(' #\n')
            lineArray = line.split(':')
            whereArray = lineArray[0].split(',')
            sqlWhereVars = [makeSqlWhereVar(c) for c in whereArray]
            sqlAssignVars = lineArray[1].split(',')
            print "@SQL(\"UPDATE \" + TABLE + \" SET "+','.join([makeSqlAssign(c) for c in sqlAssignVars])+" WHERE " +  " AND ".join([makeSqlWhereEqual(c) for c in whereArray])+"\")"
            sqlWhereVars = [makeSqlWhereVar(c) for c in whereArray]
            updateFuncArray.append([sqlWhereVars, sqlAssignVars])

            print "void update"+makeFuncSuffix(sqlAssignVars)+"By"+makeFuncSuffix(sqlWhereVars)+"("+", ".join([sqlVarToDAOParam(x) for x in (sqlWhereVars+sqlAssignVars)])+");\n"

#generate dao save
values=":p."+", :p.".join(cols)
print "@SQL(\"INSERT INTO \" + TABLE + \"(\" + FIELDS + \") VALUES ("+ values+")\")"
print "void save(@SQLParam(\"p\") "+POJOClass+" "+POJOVar+");\n"

#generate impl
print "@Autowired"
dao = POJOVar+"DAO"
print  sqlVarToClass(table)+"DAO "+dao+";\n"

for func in findFuncArray:
    method = "public "
    if  func[1]=="1":
        method+=POJOClass
    else:
        method+="List<"+POJOClass+">"
    method+=(" findBy"+makeFuncSuffix(func[0])+"("+", ".join([sqlVarToFuncParam(x) for x in func[0]])+")")
    method+="{return "+findByWithVar(dao, func[0])+"}"
    print method+"\n"

for func in updateFuncArray:
    method = "public void update"
    method+= makeFuncSuffix(func[1])+"By"+makeFuncSuffix(func[0])+"("+", ".join([sqlVarToFuncParam(x) for x in func[0]+func[1]])+")"
    method+="{"+updateWithVar(dao, func[0], func[1])+"}"
    print method+"\n"

method = "void save("+POJOClass+" "+POJOVar+")"
method +="{"+saveWithVar(dao,table)+"}"
print method+"\n"

#generate test
print "@RunWith(SpringJUnit4ClassRunner.class)"
print "@ContextConfiguration(locations = \"classpath:applicationContext.xml\")\n"

print "public static final Logger LOGGER = LoggerFactory.getLogger("+sqlVarToClass(table)+"DAOTest.class);\n"

print "@Autowired\nprivate "+sqlVarToClass(table)+"DAO " + dao+";\n"

print "@Override\n@Before\npublic void setUp() throws Exception {\nsuper.setUp();\n}\n"
print "@Override\n@After\npublic void tearDown() throws Exception {\nsuper.tearDown();\n}\n"

#generate  find test start
print "@Test\npublic void testFind() throws Exception {\nStatement st = conn.createStatement();\ntry{"
pstmt = "PreparedStatement pstmt = conn.prepareStatement(\"insert into \" + PosSessionDAO.TABLE + \"(\" + PosSessionDAO.FIELDS + \") values "

timeAllCount=0
timeRowCount=0
values=[]
for i in range(5):
    t=[]
    timeRowCount=0
    for c in cols:
        if colsType[c]=="Timestamp":
            t.append('?')
            timeAllCount+=1
            timeRowCount+=1
        elif colsType[c] == "int" or colsType[c] == "long":
            t.append(str(1))
        else:
            t.append('\''+c[0]+str(i)+'\'');
    values.append("("+','.join(t)+")")
pstmt=pstmt+",".join(values)+"\");"
print pstmt+"\n"

if timeAllCount>0:
    print "Timestamp t0 = new Timestamp(System.currentTimeMillis());"
    for i in range(1, timeAllCount):
        print "Timestamp t"+str(i)+"= new Timestamp(t0.getTime()+"+str(i)+"*5*60*1000);"
    for i in range(timeAllCount):
            print "pstmt.setTimestamp("+str(i+1)+",t"+str(i)+");"

print "\npstmt.executeUpdate();\npstmt.close();\n"
print POJOClass+ " pojo;"
print "List<"+POJOClass+">"+" pojos=new ArrayList<"+POJOClass+">();"
for func in findFuncArray:
    print "\n"
    if func[1]=="1":
        print "pojo="+findByWithArg(dao, func[0])
        print "Assert.assertNotNull(pojo);"
        makeAsserts(cols, "pojo")
    else:
        print "pojos="+findByWithArg(dao, func[0])
        print "Assert.assertFalse(pojos.isEmpty());"
        print "pojo=pojos.get(0);"
        makeAsserts(cols, "pojo")

print "} finally {\nst.close();\n}\n}"
print
#generate find test end

#generate save start
print "@Test\npublic void testSave() throws Exception {\nStatement st = conn.createStatement();\ntry{"
print POJOClass+" pojo = new "+POJOClass+"();"

if timeRowCount>0:
    print "Timestamp t0 = new Timestamp(System.currentTimeMillis());"
    for i in range(1, timeRowCount):
        print "Timestamp t"+str(i)+"= new Timestamp(t0.getTime()+"+str(i)+"*5*60*1000);"

timeRowIndex=0
for  c in cols:
    if getColsType(c) == "Timestamp":
        print "pojo."+makeSet(c, "t"+str(timeRowIndex))
        timeRowIndex+=1
    elif getColsType(c) == "int" or getColsType(c) == "long":
        print "pojo."+makeSet(c, 1)
    else:
        print "pojo."+makeSet(c, "\""+c[0]+"0\"")
print
print dao+".save(pojo);\n"

for func in findFuncArray:
    if func[1]=="1":
        print POJOClass + " rt = " + findByWithArg(dao, func[0])
        break
makeAsserts(cols, "rt")

print "} finally {\nst.close();\n}\n}"
#generate save end