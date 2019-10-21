authour_name = ['a','b','c']
authour_contain = [['1','3'],['4'],['2']]

for index in range(len(authour_name)):
    contain = ','.join(authour_contain[index])
    sql = "INSERT INTO authour(authour_name, authour_contain) VALUES ('%s', '%s')" % (authour_name[index], contain)
    print(sql)