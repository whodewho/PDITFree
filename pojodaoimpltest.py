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
    else:
        return "Timestamp"

def sqlVarToDAOParam(c):
    vc = sqlVarToVar(c)
    return "@SQLParam(\""+vc+"\") "+getColsType(c)+" "+vc

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
            print "@SQL(\"SELECT \" + FIELDS + \" FROM \" + TABLE + \" WHERE " + " AND ".join([makeSqlWhere(c) for c in whereArray])+"\")"
            whereVars = [makeWhereVar(c) for c in whereArray]

            method=""
            if lineArray[1]=="1":
                method+="POJO"+sqlVarToClass(table)
            else:
                method+="List<POJO"+sqlVarToClass(table)+">"
            method+=(" findBy"+"And".join([sqlVarToClass(x) for x in whereVars])+"("+", ".join([sqlVarToDAOParam(x) for x in whereVars])+");\n")
            print method
        else:
            if "update" in line:
                continue;

            line = line.strip(' #\n')
            lineArray = line.split(':')
            whereArray = lineArray[0].split(',')
            whereVars = [makeWhereVar(c) for c in whereArray]
            assignVars = lineArray[1].split(',')
            print "@SQL(\"UPDATE \" + TABLE + \" SET "+','.join([makeSqlAssign(c) for c in assignVars])+" WHERE" +  " AND ".join([makeSqlWhere(c) for c in whereArray])+"\")"
            whereVars = [makeWhereVar(c) for c in whereArray]
            print "void update"+'And'.join([sqlVarToClass(c) for c in assignVars])+"By"+'And'.join([sqlVarToClass(c) for c in whereVars])+"("+", ".join([sqlVarToDAOParam(x) for x in (whereVars+assignVars)])+");\n"

#generate dao save
values=":p."+", :p.".join(cols)
print "@SQL(\"INSERT INTO \" + TABLE + \"(\" + FIELDS + \") VALUES ("+ values+")\")"
print "void save(@SQLParam(\"p\") POJO"+sqlVarToClass(table)+" "+sqlVarToVar(table)+");"

