import random
from core.action import Action, Direction, Pattern, Teleport
from core.game_state import GameState, Player
import math
import queue
import copy
from functools import reduce

class MyBot:
    """
    (fr)
    Cette classe représente votre bot. Vous pouvez y définir des attributs et des méthodes qui 
    seront conservés entre chaque appel de la méthode `tick`.

    (en)
    This class represents your bot. You can define attributes and methods in it that will be kept 
    between each call of the `tick` method.
    """
    def __init__(self):
        self.__name = "Grandmaster"
        self.__first_turn = True
        self.__second_turn = False
        self.min_x = 0
        self.max_x = 0
        self.min_y = 0
        self.max_y = 0
        self.prec_action = Action(Direction.UP)
        self.action_queue = queue.Queue()
        self.emergency_queue = queue.Queue()
        self.position_queue = queue.Queue()
        self.next_strat = "UP"
        self.greed = 1
        self.distance_to_region = 0
        self.current_strat = "UP"

    def __random_action(self) -> Action:
        return random.choice(list(Direction))


    def tick(self, state: GameState) -> Action:
        """
        (fr)
        Cette méthode est appelée à chaque tick de jeu. Vous pouvez y définir le comportement de
        votre bot. Elle doit retourner une instance de `Action` qui sera exécutée par le serveur.

        (en)
        This method is called every game tick. You can define the behavior of your bot. It must 
        return an instance of `Action` which will be executed by the server.

        Args:
            state (GameState):  (fr) L'état du jeu.
                                (en) The state of the game.
        """

        us = state.players["Grandmaster"]
        region = us.region
        train = us.trail
        current_pos = us.pos
        current_x = us.pos[0]
        current_y = us.pos[1]

        if not us.alive:
            print("DEAD")
            self.action_queue = queue.Queue()
            self.emergency_queue = queue.Queue()
            self.position_queue = queue.Queue()
            self.__first_turn = True

        if self.__first_turn:
            self.next_strat = "UP"
            self.current_strat = "UP"
            self.__first_turn = False
            self.__second_turn = True

            region = us.region
            return Action(Pattern([Direction.UP]))
       
        action: Action = self.prec_action

        if (not self.position_queue.empty()):
            print("CALL POSITON QUEUE")
            return self.position_queue.get()
        
        # closestDistance = self.getClosestDistance(state, us)
        # if closestDistance - 1 < self.distance_to_region:
        #     print("ENQUEUE emergency with distance ", closestDistance)
        #     self.enQueueReturnToBase(state, us)

        if (not self.emergency_queue.empty()):
            print("CALL EMERGENCY")
            action = self.emergency_queue.get()
        elif (not self.action_queue.empty()):
            print("CALL ACTION")
            action = self.action_queue.get()
        
        elif self.next_strat == "UP":
            print("SET STRAT UP")
            self.updateMaxes(region)
            self.stratUp(us)
            action = self.position_queue.get() if not self.position_queue.empty() else self.action_queue.get()
        elif self.next_strat == "RIGHT":
            print("SET STRAT RIGHT")
            self.updateMaxes(region)
            self.stratRight(us)
            action = self.position_queue.get() if not self.position_queue.empty() else self.action_queue.get()
        elif self.next_strat == "DOWN":
            print("SET STRAT DOWN")
            self.updateMaxes(region)
            self.stratDown(us)
            action = self.position_queue.get() if not self.position_queue.empty() else self.action_queue.get()
        else:
            print("SET STRAT LEFT")
            self.updateMaxes(region)
            self.stratLeft(us)
            action = self.position_queue.get() if not self.position_queue.empty() else self.action_queue.get()

        print("action ", actionToString(action), " [x, y]: [", current_x, ", ", current_y, "]", " maxX minY: ", self.max_x, ", ", self.min_y, "]")

        self.checkToIncrementDistanceFromBase(action)

        return action
    
    def enQueueReturnToBase(self, gameState: GameState, us: Player):
        if self.action_queue.qsize() < self.greed:
            return # We already are returning
        
        actions_list = copy.deepcopy(list(self.action_queue.queue))

        nbReturn = 0
        direction = Direction.UP
        if self.current_strat == "UP":
            direction = Direction.RIGHT
        elif self.current_strat == "RIGHT":
            direction = Direction.DOWN
        elif self.current_strat == "DOWN":
            direction = Direction.LEFT
        elif self.current_strat == "LEFT":
            direction = Direction.UP
            
        nbReturn = reduce(lambda a, i: a+1 if (i.action_type == direction) else a, actions_list, 0)

        if nbReturn == (self.max_x - self.min_x) and (self.current_strat == "UP" or self.current_strat == "DOWN"):
            self.emergency_queue.put(Action(direction))

        if nbReturn == (self.max_y - self.min_y) and (self.current_strat == "LEFT" or self.current_strat == "RIGHT"):
            self.emergency_queue.put(Action(direction))

        emergency_actions = actions_list[-self.greed:]
        # Return to base
        for action in emergency_actions:
            self.emergency_queue.put(action)

        future_x, future_y = self.getFuturePosition(emergency_actions, us.pos[0], us.pos[1])

        opposite_actions = self.pathToPosition(future_x, future_y, us.pos[0], us.pos[1])
        map(self.emergency_queue.put, opposite_actions)

    def getFuturePosition(self, actions, current_x, current_y):
        future_x = current_x
        future_y = current_y

        for action in actions:
            if action.action_type == Direction.UP:
                future_y -= 1
            elif action.action_type == Direction.RIGHT:
                future_x += 1
            elif action.action_type == Direction.DOWN:
                future_y += 1
            else: # LEFT
                future_x -= 1

        return future_x, future_y

    def checkToIncrementDistanceFromBase(self, action: Action):
        if self.current_strat == "UP" and action.action_type == Direction.UP:
            self.distance_to_region += 1
        elif self.current_strat == "RIGHT" and action.action_type == Direction.RIGHT:
            self.distance_to_region += 1
        elif self.current_strat == "DOWN" and action.action_type == Direction.DOWN:
            self.distance_to_region += 1
        elif self.current_strat == "LEFT" and action.action_type == Direction.LEFT:
            self.distance_to_region += 1
    
    def updateMaxes(self, region):
        self.distance_to_region = 0
        self.min_x = min(region, key=lambda p: p[0])[0]
        self.max_x = max(region, key=lambda p: p[0])[0]
        self.min_y = min(region, key=lambda p: p[1])[1]
        self.max_y = max(region, key=lambda p: p[1])[1]

    def stratUp(self, us: Player):
        self.current_strat = "UP"
        path = self.pathToPosition(us.pos[0], us.pos[1], self.min_x, self.min_y)

        for action in path:
            self.position_queue.put(action)

        for _ in range(self.greed):
            self.action_queue.put(Action(Direction.UP))
        for _ in range(self.max_x - self.min_x):
            self.action_queue.put(Action(Direction.RIGHT))
        for _ in range(self.greed):
            self.action_queue.put(Action(Direction.DOWN))
        
        self.next_strat = self.determineNextStratBasedOnCurrentStrat("UP")

    def stratRight(self, us: Player):
        self.current_strat = "RIGHT"
        path = self.pathToPosition(us.pos[0], us.pos[1], self.max_x, self.min_y)
        for action in path:
            self.position_queue.put(action)
        for _ in range(self.greed):
            self.action_queue.put(Action(Direction.RIGHT))
        for _ in range(self.max_y - self.min_y):
            self.action_queue.put(Action(Direction.DOWN))
        for _ in range(self.greed):
            self.action_queue.put(Action(Direction.LEFT))
        
        self.next_strat = self.determineNextStratBasedOnCurrentStrat("RIGHT")

    def stratDown(self, us: Player):
        self.current_strat = "DOWN"
        path = self.pathToPosition(us.pos[0], us.pos[1], self.max_x, self.max_y)
        for action in path:
            self.position_queue.put(action)
        for _ in range(self.greed):
            self.action_queue.put(Action(Direction.DOWN))
        for _ in range(self.max_x - self.min_x):
            self.action_queue.put(Action(Direction.LEFT))
        for _ in range(self.greed):
            self.action_queue.put(Action(Direction.UP))
        
        self.next_strat = self.determineNextStratBasedOnCurrentStrat("DOWN")

    def stratLeft(self, us: Player):
        self.current_strat = "LEFT"
        path = self.pathToPosition(us.pos[0], us.pos[1], self.min_x, self.max_y)
        for action in path:
            self.position_queue.put(action)
        for _ in range(self.greed):
            self.action_queue.put(Action(Direction.LEFT))
        for _ in range(self.max_y - self.min_y):
            self.action_queue.put(Action(Direction.UP))
        for _ in range(self.greed):
            self.action_queue.put(Action(Direction.RIGHT))
        
        self.next_strat = self.determineNextStratBasedOnCurrentStrat("LEFT")

    def pathToPosition(self, current_x, current_y, goal_x, goal_y):
        path = []
        delta_x = goal_x - current_x
        is_delta_x_negative = delta_x < 0

        for _ in range(abs(delta_x)):
            if is_delta_x_negative:
                path.append(Action(Direction.LEFT))
            else:
                path.append(Action(Direction.RIGHT))

        delta_y = goal_y - current_y
        is_delta_y_negative = delta_y < 0
        for _ in range(abs(delta_y)):
            if is_delta_y_negative:
                path.append(Action(Direction.UP))
            else:
                path.append(Action(Direction.DOWN))

        return path
    
    def getClosestDistance(self, gameState: GameState, us: Player):
        players = gameState.players
        minDist = float("inf")
        for player in players.values():
            if player.name == us.name:
                continue

            dist = self.playerDistanceToSafeZone(gameState, us, player.pos)
            if dist < minDist:
                minDist = dist

        return minDist
    
    def determineNextStratBasedOnCurrentStrat(self, strat):
        order = []
        if strat == "UP":
            order = ["RIGHT", "DOWN", "LEFT", "UP"]
        elif strat == "RIGHT":
            order = ["DOWN", "LEFT", "UP", "RIGHT"]
        elif strat == "DOWN":
            order = ["LEFT", "UP", "RIGHT", "DOWN"]
        elif strat == "LEFT":
            order = ["UP", "RIGHT", "DOWN", "LEFT"]
        
        for next_strat in order:
            if next_strat == "UP" and self.min_y >= (0 + self.greed):
                return "UP"
            elif next_strat == "RIGHT" and self.max_x <= (20 - self.greed):
                return "RIGHT"
            elif next_strat == "DOWN" and self.max_y <= (20 - self.greed):
                return "DOWN"
            elif next_strat == "LEFT" and self.min_x >= (0 + self.greed):
                return "LEFT"
        return "UP"
    
    def playerDistanceToSafeZone(self, gameState: GameState, us: Player, player_pos):
        trail = us.trail

        minDist = float("inf")
        for trail_square in trail:
            square_x = trail_square[0]
            square_y = trail_square[1]

            player_x = player_pos[0]
            player_y = player_pos[1]

            dist = math.sqrt((square_x - player_x)**2 + (square_y - player_y)**2)
            if dist < minDist:
                minDist = dist

        return minDist

def actionToString(action: Action):
    if action.action_type == Direction.UP:
        return "UP"
    elif action.action_type == Direction.DOWN:
        return "DOWN"
    elif action.action_type == Direction.LEFT:
        return "LEFT"
    else:
        return "RIGHT"