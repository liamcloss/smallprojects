import random
# Include all digits 0 through 9 so generated passwords can use any decimal
# digit. The original string omitted the digit '3'.
potentialKeys = 'abcdefghijklmnopqrstuvwxyz1234567890@;#~/><'

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
