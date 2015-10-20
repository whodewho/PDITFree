from string import Template

columns = []
table = ""
columnsType = {}

def title(x):
    return ''.join([word[0].upper() + word[1:] for word in x.split('_')])

def vTitle(x):
    t = title(x)
    return t[0].lower()+t[1:]

def makeArg(c):
    vc = vTitle(c)
    return "@SQLParam(\""+vc+"\") "+columnsType[c]+" "+vc

#generate pojo variables
with open('s') as f:
     for line in f:
	if "CREATE TABLE IF NOT EXISTS" in line:
	    table = line.split(' ')[5]
	    #print table+"\n"
            continue

     	c = line[line.index('`')+1:line.rindex('`')]
	columns.append(c)

	t = ""
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
	columnsType[c]=t

        print "private",t,c+";\n"

print "----------POJO END------------\n"

print "static final String TABLE = \""+table+"\";\n"

print "//"+",".join(columns)+"\n"
#id is mostly useless
columns = columns[1:]
print "static final String FIELDS = \""+','.join(columns)+"\";\n"

pojoType = "POJO"+title(table)
vPOJOType = "pojo"+title(table)

#todo: consider unique index, query with multiple args and return lists
#generate dao finds
#find{
#a,b>*
#b>1
#}
for c in columns:
    if c == "status" or c == "valid":
        continue

    vc = vTitle(c)
    if columnsType[c] == "Timestamp":
        print "@SQL(\"SELECT \" + FIELDS + \" FROM \" + TABLE + \" WHERE "+c+"<:currentTime)"
    	print "List<"+pojoType+"> findBy"+title(c)+"(@SQLParam(\"currentTime\") "+columnsType[c]+" currentTime);\n"
        continue

    print "@SQL(\"SELECT \" + FIELDS + \" FROM \" + TABLE + \" WHERE "+c+"=:"+vc+"\")"
    print pojoType, "findBy"+title(c)+"("+makeArg(c)+");\n"


#generate dao save
values=":p."+", :p.".join(columns)
print "@SQL(\"INSERT INTO \" + TABLE + \"(\" + FIELDS + \") VALUES ("+ values+")\")"
print "void save("+makeArg(c)+");"

#generate dao update
#update{
#a,b>e,f
#a>f
#}
for c in columns:
    vc = vTitle(c)

    if c == "status" or c == "valid":
	print "@SQL(\"UPDATE \" + TABLE + \" SET "+c+"=:"+c+" WHERE XXX=:XXX\")"
	print "void update(@SQLParam(\""+vc+"\") "+columnsType[c]+" "+vc+");\n"
	

