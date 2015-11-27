cols = []
table = ""
colsType = {}


def sqlVarToClass(x):
    return ''.join([word[0].upper() + word[1:] for word in x.split('_')])


def sqlVarToVar(x):
    t = sqlVarToClass(x)
    return t[0].lower() + t[1:]


def getColsType(c):
    if c in colsType:
        return colsType[c]
    elif "time" in c or "Time" in c:
        return "Timestamp"
    else:
        return "NULL"


def sqlVarToDAOParam(c):
    vc = sqlVarToVar(c)
    return "@SQLParam(\"" + vc + "\") " + getColsType(c) + " " + vc


def sqlVarToFuncParam(c):
    vc = sqlVarToVar(c)
    return getColsType(c) + " " + vc


def makeSqlWhereEqual(c):
    if all([x not in c for x in ["<", ">", "between"]]):
        return c + " = :" + sqlVarToVar(c)
    else:
        cArray = c.split(' ')
        return ":" + sqlVarToVar(cArray[0]) + " " + ' '.join(cArray[1:])


def makeSqlWhereVar(c):
    if all([x not in c for x in ["<", ">", "between"]]):
        return c
    else:
        return c.split(" ")[0]


def makeSqlAssign(c):
    return c + "=:" + sqlVarToVar(c)


def makeFuncSuffix(c):
    return "And".join([sqlVarToClass(x) for x in c])


def findByWithVar(dao, c):
    return dao + ".findBy" + makeFuncSuffix(c) + "(" + ', '.join([sqlVarToVar(x) for x in c]) + ");"


def findByWithArg(dao, c):
    args = []
    for vc in c:
        if getColsType(vc) == "Timestamp":
            args.append("t0")
        else:
            args.append("\"" + vc[0] + "0\"")
    return dao + ".findBy" + makeFuncSuffix(c) + "(" + ','.join(args) + ");"


def updateWithVar(dao, c1, c2):
    return dao + ".update" + makeFuncSuffix(c2) + "By" + makeFuncSuffix(c1) + "(" + ','.join(
        [sqlVarToVar(x) for x in c1 + c2]) + ");"


def updateWithArg(dao, c1, c2):
    args = []
    for vc in c1:
        if getColsType(vc) == "Timestamp":
            # generate new timestamp for update
            args.append("t0")
        elif getColsType(vc) == "long" or getColsType(vc) == "int":
            args.append("0")
        else:
            args.append("\"" + vc[0] + "0\"")
    for vc in c2:
        if getColsType(vc) == "Timestamp":
            args.append("tn")
        else:
            args.append("\"" + vc[0] + "n\"")

    return dao + ".update" + makeFuncSuffix(c2) + "By" + makeFuncSuffix(c1) + "(" + ','.join(args) + ");"


def saveWithVar(dao, c):
    return dao + ".save(" + sqlVarToVar(c) + ");"


def makeGet(c):
    return "get" + c[0].upper() + c[1:] + "()"


def makeSet(c, v):
    return "set" + c[0].upper() + c[1:] + "(" + str(v) + ");"


def makeAsserts(f, cols, v):
    for c in cols:
        if getColsType(c) == "Timestamp":
            continue
        elif getColsType(c) == "int" or getColsType == "long":
            f.write("Assert.assertEquals(1, " + v + "." + makeGet(c) + ");\n\n")
        else:
            f.write("Assert.assertEquals(\"" + c[0] + "0\", " + v + "." + makeGet(c) + ");\n")
    f.write("\n")


def makeUpdateAsserts(f, c2, v):
    for c in c2:
        if getColsType(c) == "Timestamp":
            f.write("Assert.assertEquals(tn," + v + "." + makeGet(c) + ");\n\n")
        elif getColsType(c) == "int" or getColsType == "long":
            f.write("Assert.assertEquals(0, " + v + "." + makeGet(c) + ");\n")
        else:
            f.write("Assert.assertEquals(\"" + c[0] + "1\", " + v + "." + makeGet(c) + ");\n")
    f.write("\n")


def makePOJOWithSet(f):
    f.write(POJOClass + " pojo = new " + POJOClass + "();\n")

    if timeRowCount > 0:
        f.write("Timestamp t0 = new Timestamp(System.currentTimeMillis());\n")
        for i in range(1, timeRowCount):
            f.write("Timestamp t" + str(i) + "= new Timestamp(t0.getTime()+" + str(i) + "*5*60*1000);\n")

    timeRowIndex = 0
    for c in cols:
        if getColsType(c) == "Timestamp":
            f.write("pojo." + makeSet(c, "t" + str(timeRowIndex)) + "\n")
            timeRowIndex += 1
        elif getColsType(c) == "int" or getColsType(c) == "long":
            f.write("pojo." + makeSet(c, 1) + "\n")
        else:
            f.write("pojo." + makeSet(c, "\"" + c[0] + "0\"") + "\n")
    f.write("\n")


state = 0

findFuncArray = []
updateFuncArray = []

POJOClass = ""
POJOVar = ""

with open('s') as f:
    for line in f:
        if line == "\n":
            state = (state + 1) % 3
            continue

        if 0 == state:
            if "CREATE TABLE IF NOT EXISTS" in line:
                table = line.split(' ')[5]
                POJOClass = "POJO" + sqlVarToClass(table)
                POJOVar = sqlVarToVar(table)
                continue

            c = line[line.index('`') + 1:line.rindex('`')]
            cols.append(c)

            # generate pojo vars
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
            colsType[c] = t

        elif 1 == state:
            if "find" in line:
                continue

            line = line.strip(' #\n')
            lineArray = line.split(':')
            whereArray = lineArray[0].split(',')
            findFuncArray.append([whereArray, lineArray[1]])
        else:
            # generate dao update
            if "update" in line:
                continue

            line = line.strip(' #\n')
            lineArray = line.split(':')
            whereArray = lineArray[0].split(',')
            sqlAssignVars = lineArray[1].split(',')
            updateFuncArray.append([whereArray, sqlAssignVars])

with open(POJOClass + ".java", 'a') as f:
    f.write("public class " + POJOClass + "{\n\n")
    for c in cols:
        f.write("private " + colsType[c] + " " + c + ";\n\n")
    f.write("}")

with open(sqlVarToClass(table) + "DAO.java", 'a') as f:
    f.write("import net.paoding.rose.jade.annotation.DAO;\n")
    f.write("import net.paoding.rose.jade.annotation.SQL;\n")
    f.write("import net.paoding.rose.jade.annotation.SQLParam;\n\n")
    f.write("@DAO\n")
    f.write("public interface " + sqlVarToClass(table) + "DAO {\n\n")

    f.write("static final String TABLE = \"" + table + "\";\n\n")
    f.write("static final String FIELDS = \"" + ','.join(cols[1:]) + "\";\n\n")

    for findFunc in findFuncArray:
        f.write("@SQL(\"SELECT \" + FIELDS + \" FROM \" + TABLE + \" WHERE " + " AND ".join(
            [makeSqlWhereEqual(c) for c in findFunc[0]]) + ")\n")
        sqlWhereVars = [makeSqlWhereVar(c) for c in findFunc[0]]

        method = ""
        if lineArray[1] == "1":
            method += POJOClass
        else:
            method += "List<" + POJOClass + ">"
        method += (" findBy" + makeFuncSuffix(sqlWhereVars) + "(" + ", ".join(
            [sqlVarToDAOParam(x) for x in sqlWhereVars]) + ");\n")
        f.write(method + "\n")

    values = ":p." + ", :p.".join(cols)
    f.write("@SQL(\"INSERT INTO \" + TABLE + \"(\" + FIELDS + \") VALUES (" + values + ")\")\n")
    f.write("void save(@SQLParam(\"p\") " + POJOClass + " " + POJOVar + ");\n\n")

    f.write("}")

with open(sqlVarToClass(table) + "Impl.java", 'a') as f:
    f.write("import org.springframework.beans.factory.annotation.Autowired;\n")
    f.write("import org.springframework.stereotype.Service;\n\n")
    f.write("@Service\n")
    f.write("public class " + sqlVarToClass(table) + "Impl{\n\n")

    f.write("@Autowired\n")
    dao = sqlVarToVar(table) + "DAO"
    f.write(sqlVarToClass(table) + "DAO " + dao + ";\n\n")

    for func in findFuncArray:
        method = "public "
    if func[1] == "1":
        method += POJOClass
    else:
        method += "List<" + POJOClass + ">"
        method += (" findBy" + makeFuncSuffix(func[0]) + "(" + ", ".join([sqlVarToFuncParam(x) for x in func[0]]) + ")")
        method += "{return " + findByWithVar(dao, func[0]) + "}"
    f.write(method + "\n\n")

    for func in updateFuncArray:
        method = "public void update"
    method += makeFuncSuffix(func[1]) + "By" + makeFuncSuffix(func[0]) + "(" + ", ".join(
        [sqlVarToFuncParam(x) for x in func[0] + func[1]]) + ")"
    method += "{" + updateWithVar(dao, func[0], func[1]) + "}"
    f.write(method + "\n\n")

    method = "void save(" + POJOClass + " " + POJOVar + ")"
    method += "{" + saveWithVar(dao, table) + "}"
    f.write(method + "\n\n")

    f.write("}")

with open(sqlVarToClass(table) + "DAOTest.java", 'a') as f:
    f.write("import org.junit.After;\n")
    f.write("import org.junit.Assert;\n")
    f.write("import org.junit.Before;\n")
    f.write("import org.junit.Test;\n")
    f.write("import org.junit.runner.RunWith;\n")
    f.write("import org.slf4j.Logger;\n")
    f.write("import org.slf4j.LoggerFactory;\n")
    f.write("import org.springframework.beans.factory.annotation.Autowired;\n")
    f.write("import org.springframework.test.context.ContextConfiguration;\n")
    f.write("import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;\n")
    f.write("import java.sql.PreparedStatement;\n")
    f.write("import java.sql.Statement;\n")
    f.write("import java.util.ArrayList;\n")
    f.write("import java.util.List;\n")

    f.write("@RunWith(SpringJUnit4ClassRunner.class)")
    f.write("@ContextConfiguration(locations = \"classpath:applicationContext.xml\")\n")
    f.write("public class " + sqlVarToClass(table) + "DAOTest extends BaseDAOTest {\n")
    f.write("public static final Logger LOGGER = LoggerFactory.getLogger(" + sqlVarToClass(table) + "DAOTest.class);\n")

    dao = sqlVarToVar(table) + "DAO"
    f.write("@Autowired\nprivate " + sqlVarToClass(table) + "DAO " + dao + ";\n")

    f.write("@Override\n@Before\npublic void setUp() throws Exception {\nsuper.setUp();\n}\n")
    f.write("@Override\n@After\npublic void tearDown() throws Exception {\nsuper.tearDown();\n}\n")

    f.write("@Test\npublic void testFind() throws Exception {\nStatement st = conn.createStatement();\ntry{")
    pstmt = "PreparedStatement pstmt = conn.prepareStatement(\"insert into \" + " + sqlVarToClass(
        table) + "DAO.TABLE + \"(\" + " + sqlVarToClass(table) + "DAO.FIELDS + \") values "

    timeAllCount = 0
    timeRowCount = 0
    values = []
    for i in range(5):
        t = []
        timeRowCount = 0
        for c in cols:
            if colsType[c] == "Timestamp":
                t.append('?')
                timeAllCount += 1
                timeRowCount += 1
            elif colsType[c] == "int" or colsType[c] == "long":
                t.append(str(1))
            else:
                t.append('\'' + c[0] + str(i) + '\'')
        values.append("(" + ','.join(t) + ")")
    pstmt = pstmt + ",".join(values) + "\");"
    f.write(pstmt + "\n\n")

    if timeAllCount > 0:
        f.write("Timestamp t0 = new Timestamp(System.currentTimeMillis());\n")
        for i in range(1, timeAllCount):
            f.write("Timestamp t" + str(i) + "= new Timestamp(t0.getTime()+" + str(i) + "*5*60*1000);\n")
        for i in range(timeAllCount):
            f.write("pstmt.setTimestamp(" + str(i + 1) + ",t" + str(i) + ");\n")

    f.write("\npstmt.executeUpdate();\npstmt.close();\n\n")
    f.write(POJOClass + " pojo;\n")
    f.write("List<" + POJOClass + ">" + " pojos=new ArrayList<" + POJOClass + ">();\n")
    for func in findFuncArray:
        if func[1] == "1":
            f.write("pojo=" + findByWithArg(dao, [makeSqlWhereVar(c) for c in func[0]]) + "\n\n")
            f.write("Assert.assertNotNull(pojo);\n")
            makeAsserts(f, cols, "pojo")
        else:
            f.write("pojos=" + findByWithArg(dao, [makeSqlWhereVar(c) for c in func[0]]) + "\n")
            f.write("Assert.assertFalse(pojos.isEmpty());\n")
            f.write("pojo=pojos.get(0);\n")
            makeAsserts(f, cols, "pojo")

    f.write("} finally {\nst.close();\n}\n}\n\n")

    f.write("@Test\npublic void testSave() throws Exception {\nStatement st = conn.createStatement();\ntry{\n\n")
    makePOJOWithSet(f)
    f.write(dao + ".save(pojo);\n")

    uniqueFunc = []
    for func in findFuncArray:
        if func[1] == "1":
            uniqueFunc = func
            f.write(POJOClass + " rt = " + findByWithArg(dao, func[0]))
            break
    makeAsserts(f, cols, "rt")

    f.write("} finally {\nst.close();\n}\n}\n\n")

    if len(updateFuncArray):
        f.write("@Test\npublic void testUpdate() throws Exception {\nStatement st = conn.createStatement();\ntry{\n\n")
        makePOJOWithSet(f)

        f.write("Timestamp tn= new Timestamp(t0.getTime()+5*60*1000);")
        f.write(POJOClass + " rt;\n")
        for func in updateFuncArray:
            f.write(updateWithArg(dao, func[0], func[1]) + "\n")
            f.write("rt = " + findByWithArg(dao, uniqueFunc[0]) + "\n")
            makeUpdateAsserts(f, func[1], "rt")

        f.write("} finally {\nst.close();\n}\n}")
