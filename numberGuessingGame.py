# Guess The Number
# Write a programme where the computer randomly generates a number between 0
# and 20. The user needs to guess what the number is. If the user guesses
# wrong, tell them their guess is either too high, or too low. This will get
# you started with the random library if you haven't already used it.
import random
def check_number(guess, answer, attempt):
    if guess < answer:
        print("Try again, guess higher")
        return False
    elif guess > answer:
        print("Try again, guess lower")
        return False
    else:
        return True

def get_input():
    guess = input("Guess a number? ")
    return int(guess)

answer = random.randint(0,20)
attempt = 1
while(check_number(get_input(), answer, attempt) == False):
    attempt += 1
print("Congratulations you guessed correctly! It took ", attempt, "guesses")
