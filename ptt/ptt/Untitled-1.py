import datetime
date = 'Fri Nov 30 20:08:37 2007'
date = datetime.datetime.strptime(date,'%a %b %d %H:%M:%S %Y')
print(str(date))