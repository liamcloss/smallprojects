import random
potentialKeys = 'abcdefghijklmnopqrstuvwxyz124567890@;#~/><'

def getLength():
    try:
        length = int(input("Please enter a length for your password, length must be 6 or greater "),10)
        if length >= 6 and type(length) is int:
            return length
        else:
            return getLength()


    except ValueError as ve:
       return getLength()


length = getLength()
password = ''
for i in range(0,length):
    password += random.choice(potentialKeys)
print(password)
