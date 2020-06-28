# Rock, Paper, Scissors Game
# Make a rock-paper-scissors game where it is the player vs the computer. The computer’s answer will be randomly
# generated, while the program will ask the user for their input. This project will better your understanding of
# while loops and if statements.

import random
validMove = ['Rock','Paper','Scissors']

def getComputerMove():
    return  validMove[random.randint(0,2)]

def getPlayerMove():
    playerMove = input("Choose your Move [Rock,Paper,Scissors] or Quit ")
    if playerMove in validMove or playerMove == 'Quit':
        return playerMove
    else:
       return getPlayerMove()

def gameLoop():
    while(True):
        playerMove = getPlayerMove()
        computerMove = getComputerMove()

        if playerMove == 'Quit':
            print("Thanks for playing")
            return False

        if(playerMove == computerMove):
            print("You drew, you both chose ", playerMove)
        else:
            print("You chose", playerMove)
            print("The computer chose", computerMove)
            if (playerMove == "Rock" and computerMove == "Scissors") or (playerMove == "Paper" and computerMove ==
                                                                        "Rock") or (playerMove == "Scissors" and \
                    computerMove == "Paper"):
                outcome = "You Win!"
            else:
                outcome = "You Lose"
            print(outcome)



gameLoop()