from string import Template

cols = []
table = ""
colsType = {}

def makeClass(x):
    return ''.join([word[0].upper() + word[1:] for word in x.split('_')])

def makeVar(x):
    t = makeClass(x)
    return t[0].lower()+t[1:]

def getColsType(c):
    if c in colsType:
        return colsType[c]
    else:
        return "Timestamp"

def makeFunArg(c):
    vc = makeVar(c)
    return "@SQLParam(\""+vc+"\") "+getColsType(c)+" "+vc

def makeWhereSql(c):
    if " " not in c:
        return ":"+makeVar(c)+"="+c
    else:
         cArray=c.split(' ')
         return ":"+makeVar(cArray[0])+" "+' '.join(cArray[1:])

def makeWhereVar(c):
    if " " not in c:
        return c
    else:
        return c.split(" ")[0]

def makeAssignment(c):
    return c+"=:"+makeVar(c)

state = 0
daoHeadPrinted = False

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
            print "@SQL(\"SELECT \" + FIELDS + \" FROM \" + TABLE + \" WHERE " + " AND ".join([makeWhereSql(c) for c in whereArray])+"\")"
            whereVars = [makeWhereVar(c) for c in whereArray]

            method=""
            if lineArray[1]=="1":
                method+="POJO"+makeClass(table)
            else:
                method+="List<POJO"+makeClass(table)+">"
            method+=(" findBy"+"And".join([makeClass(x) for x in whereVars])+"("+", ".join([makeFunArg(x) for x in whereVars])+")\n")
            print method
        else:
            if "update" in line:
                continue;

            line = line.strip(' #\n')
            lineArray = line.split(':')
            whereArray = lineArray[0].split(',')
            whereVars = [makeWhereVar(c) for c in whereArray]
            assignVars = lineArray[1].split(',')
            print "@SQL(\"UPDATE \" + TABLE + \" SET "+','.join([makeAssignment(c) for c in assignVars])+" WHERE" +  " AND ".join([makeWhereSql(c) for c in whereArray])+"\")"
            whereVars = [makeWhereVar(c) for c in whereArray]
            print "void update"+''.join([makeClass(c) for c in assignVars])+"By"+''.join([makeClass(c) for c in whereVars])+"("+", ".join([makeFunArg(x) for x in whereVars])+")\n"

#generate dao save
values=":p."+", :p.".join(cols)
print "@SQL(\"INSERT INTO \" + TABLE + \"(\" + FIELDS + \") VALUES ("+ values+")\")"
print "void save(@SQLParam(\"p\") POJO"+makeClass(table)+" "+makeVar(table)+");"