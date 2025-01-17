import numpy as np
import random
import math

class SimSystem():

    input_num = 1
    output_num = 1

    def __init__(self):
        self.input = np.zeros(SimSystem.input_num)
        self.output = np.zeros(SimSystem.output_num)

    def _get_input_num(self):
        return np.size(self.input)

    def _get_output_num(self):
        return np.size(self.output)

    def __extract_feature(self):

        feature = self.input
        for i in range(len(feature)):
            feature[i] = min(max(0, feature[i]), 9)

        return feature

    def __decode_command(self, command):
        for i in range(len(command)):
            self.output[i] = min(max(0, command[i]), 9)

    def simulate(self):
        # simulate the system

        # ---- AllLinear ----
        # self.input = [int(self.output[0])]

        # ---- LeftSineRightLinear ----
        # if 6 > self.input[0]:
        #     self.input = [int(10*math.sin(self.output[0]))]
        # else:
        #     self.input = [int(self.output[0])]

        # ---- RightSineLeftLinear ----
        # if 6 <= self.input[0]:
        #     self.input = [int(10*math.sin(self.output[0]))]
        # else:
        #     self.input = [int(self.output[0])]

        # ---- RightRandomLeftLinear ------
        # if 6 <= self.input[0]:
        #     self.input = [random.randint(0, 9)]
        # else:
        #     self.input = [int(self.output[0])]

        # ---- LeftRandomRightLinear ------
        # if 6 > self.input[0]:
        #     self.input = [random.randint(0, 9)]
        # else:
        #     self.input = [int(self.output[0])]

        # ---- Velocity Control -----
        if self.output == 0:
            self.input = [random.randint(0, 9)]
        elif self.output == 2:
            self.input = [self.input[0] + self.output[0] - 1]
        else:
            #self.input = [self.output[0]+2]
            #self.input = [self.input[0] + (self.output[0]-1)*0.9 + random.randint(-1, 1)*0.1]
            self.input = [self.input[0] + (self.output[0]-1)*0.5 + math.sin(self.output[0]-1)*0.5]

    def read_feature(self):

         # return the features
        return self.__extract_feature()

    def write_command(self, command):

        # decode the command and invoke the actuator
        self.__decode_command(command)

