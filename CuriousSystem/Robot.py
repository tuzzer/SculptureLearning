from setup import *
import random
import Motor
import Sensor
import Memory
import Exemplar
import Q_learning


random.seed()

class Robot(pygame.sprite.Sprite):


    def __init__(self, this_robot_size=robot_size):

        # pygame parameters
        # call Sprite intializer
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('bluedot.jpg', -1)

        # resize the image
        self.image = pygame.transform.scale(self.image, robot_size)
        # resize the rect
        self.rect.size = this_robot_size

        # copy the screen
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()

        # state of the robot
        self.x = random.randint(self.area.left, self.area.right)
        self.y = self.area.bottom - random.randint(self.area.top, self.area.bottom)
        self.dir = random.random()*math.pi*2

        # randomize the initial location of the dot
        self.rect.x = self.x
        self.rect.y = self.area.bottom - self.y

        # independent state variables
        positiveV = random.randint(0,1)
        positiveW = random.randint(0,1)
        self.v = 10 * (positiveV + (1-positiveV)*-1)
        self.w = 0.05 * (positiveW + (1-positiveW)*-1)
       # self.v = random.random()*20 - 10
       # self.w = random.random()*0.1 - 0.05
        self.motor = Motor.Motor()
        self.sensor = Sensor.Sensor()

        # synchronous state variables
        self.v_sync = copy.copy(self.v)
        self.w_sync = copy.copy(self.w)
        self.engage = 0.0  # level of engagement

        # instantiate the robot's memory
        self.memory = Memory.Memory()

        # Q-Learning engine
        self.Q = Q_learning.Q_learning()

        # Prediction Error history
        self.predict_history = []

        # Action History
        self.action_history = []


    def update(self, user):

        # Sense the user
        self.__sense(user)
        s1 = copy.copy(self.sensor)

        # select action
        sm_q = self.__act()
        self.action_history.append(Q_learning.Q_learning.discretize(copy.copy(self.motor)))
        m = copy.copy(self.motor)

        # predict results
        s2_predict = None
        if self.memory.getMemorySize() > 2:
            s2_predict, expert = self.__consult()

        # perform action
        self.__move()

        # check for actuation sensor inputs
        self.__sense(user)
        s2 = copy.copy(self.sensor)

        # Calculate prediction error
        lp = [0]*s2.getNumParam()
        if s2_predict is not None:
            lp = self.__observe(expert, s2_predict, s2)

        # Learn the consequence of the action
        self.__learn(sm_q, lp)

        self.memory.addExemplar(s1, m, s2)

        # self.printRegionPop()
        # print self.getSyncState()

    def __move(self):

        # calculate robot direction
        self.w += self.motor.getParam()[1]

        # w_sync follows sign of w
        if self.w < 0:
            self.w_sync = -self.w_sync
        self.dir += (1-self.engage)*self.w + self.engage*self.w_sync

        # computing the new position
        self.v += self.motor.getParam()[0]

        # v_sync follows sign of v
        if self.v < 0:
            self.v_sync = -self.v_sync

        dx = ((1-self.engage)*self.v + self.engage*self.v_sync)*math.cos(self.dir)
        dy = ((1-self.engage)*self.v + self.engage*self.v_sync)*math.sin(self.dir)
        #print "v  = " + str(self.v) + "    w = " + str(self.w) + "    dir = " + str(self.dir)
        # updating pygame rect position
        newpos = self.rect.move(dx, -dy)

        # check if it hits hall
        move_x = dx
        move_y = dy
        if not self.area.contains(newpos):
            # change direction if it does
            if newpos.left < self.area.left or newpos.right > self.area.right:
                move_x = -dx
            if newpos.top < self.area.top or newpos.bottom > self.area.bottom:
                move_y = -dy

            newpos = self.rect.move(move_x, -move_y)
        self.rect = newpos

        # remembering the state before to calculate velocity
        self.x0 = self.x
        self.y0 = self.y
        self.dir0 = self.dir

        # updating state
        self.x += move_x
        self.y += move_y

        # calculate new direction (will change if it hits wall)
        self.dir = math.atan2(move_y, move_x)

        # calculate new velocity
        self.v = math.sqrt((self.x-self.x0)**2 + (self.y-self.y0)**2)
        #self.w = self.dir-self.dir0



    def __sense(self, user):
        self.sensor.hr = user.hr
        self.sensor.skin = user.skin
        self.sensor.interest = user.interest

        self.__updateEngage()


    def __act(self):

        self.motor, sm_q = self.Q.getBestMotor(self.sensor)

        #self.motor.v = self.sensor.hr/8
        #self.motor.w = self.sensor.interest/0.2

        return sm_q

    def __consult(self):
        # consulting regional expert for action
        s2_predict, expert = self.memory.getPrediction(self.sensor, self.motor)
        #print s2_predict.getParam()
        return s2_predict, expert #reference to expert who made the prediction


    def __observe(self, expert, s2_predict, s2_actual):
        # compute error in prediction
        predict_error = expert.addPredictError(s2_actual, s2_predict)
       # print 'Prediction Error:', predict_error
        self.predict_history.append(predict_error)
        #print len(expert.error)
        # computer learning progress once sufficient sample is collected
        if len(expert.error) >= (expert.window + expert.smoothing):
            LP = expert.calcLearningProgress()
            #print LP
            return LP
        else:
            return [0]*self.motor.getNumParam()

    def __learn(self, q0, lp):

        alpha = Q_learning.Q_learning.learnRate
        gamma = Q_learning.Q_learning.gamma
        #q0 = self.Q.getQ(self.sensor, self.motor)
        reward = 0
        for comp in lp:
            reward += comp
        reward /= float(len(lp))

        q = q0 + alpha*(reward + gamma*(self.Q.getBestMotor(self.sensor))[1] - q0)

        self.Q.addQ(self.sensor, self.motor, q)

    def getState(self):
        return [self.v, self.w]

    def setState(self, new_x=None, new_y=None, new_dir=None):
        if new_x is not None:
            self.x = new_x

        if new_y is not None:
            self.y = new_y

        if new_dir is not None:
            self.dir = new_dir

        self.rect.x = self.x
        self.rect.y = self.y

    def printRegionPop(self):
        print len(self.memory.exp), '-->'
        self.memory.R.getNumExemplarRecursive()
        print('-----------')

    def getSyncState(self):
        return [self.v_sync, self.w_sync]

    def setSyncState(self, state):
        self.v_sync = state[0]
        self.w_sync = state[1]

    def __updateEngage(self):
        sensorInputs = self.sensor.getParam()
        self.engage = 0.20*sensorInputs[0] + 0.20*sensorInputs[1] + 0.60*sensorInputs[2]