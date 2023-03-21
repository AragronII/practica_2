"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Array

SOUTH = 1
NORTH = 0

NCARS = 100
NPED = 10
TIME_CARS_NORTH = 2  # a new car enters each 2s
TIME_CARS_SOUTH = 2  # a new car enters each 2s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 30s, 10s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Array('i', 3) # N,S,P
        for i in range(3):
            self.patata[i] = 0
        self.ped = Condition(self.mutex)
        self.car_towards_S = Condition(self.mutex)
        self.car_towards_N = Condition(self.mutex)
        
    def good_to_go_N(self):
        return self.patata[1] == 0 and self.patata[2] == 0

    def good_to_go_S(self):
        return self.patata[0] == 0 and self.patata[2] == 0
        
    def wants_enter_car(self, direction: int):
        self.mutex.acquire()
        if direction == 0:
            self.car_towards_N.wait_for(self.good_to_go_N)
            self.patata[0] += 1
        else:
            self.car_towards_S.wait_for(self.good_to_go_S)
            self.patata[1] += 1
        self.mutex.release()

    def leaves_car(self, direction: int):
        self.mutex.acquire()
        if direction == 0:
            self.patata[0] -= 1
            if self.patata[0] == 0:
                self.car_towards_S.notify()
                self.car_towards_N.notify()
                self.ped.notify()
        else:
            self.patata[1] -= 1
            if self.patata[1] == 0:
                self.car_towards_S.notify()
                self.car_towards_N.notify()
                self.ped.notify()
        self.mutex.release()
    
    def good_to_go_P(self):
        return self.patata[0] == 0 and self.patata[1] == 0
    
    def wants_enter_pedestrian(self):
        self.mutex.acquire()
        self.ped.wait_for(self.good_to_go_P)
        self.patata[2] += 1
        self.mutex.release()

    def leaves_pedestrian(self):
        self.mutex.acquire()
        self.patata[2] -= 1
        if self.patata[2] == 0:
            self.car_towards_S.notify()
            self.car_towards_N.notify()
            self.ped.notify()
        self.mutex.release()


def delay_car_north() -> None:
    time.sleep(random.uniform(TIME_IN_BRIDGE_CARS[1], TIME_IN_BRIDGE_CARS[0]))

def delay_car_south() -> None:
    time.sleep(random.uniform(TIME_IN_BRIDGE_CARS[1], TIME_IN_BRIDGE_CARS[0]))

def delay_pedestrian() -> None:
    time.sleep(random.uniform(TIME_IN_BRIDGE_PEDESTRIAN[1], TIME_IN_BRIDGE_PEDESTRIAN[0]))

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    a =time.strftime("%M:%S", time.gmtime())
    print(f"car {cid} heading {direction} wants to enter. ", a)
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. ", a)
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    a =time.strftime("%M:%S", time.gmtime())
    print(f"car {cid} heading {direction} leaving the bridge. ", a)
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. ", a)

def pedestrian(pid: int, monitor: Monitor) -> None:
    a =time.strftime("%M:%S", time.gmtime())
    print(f"pedestrian {pid} wants to enter. ", a)
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. ", a)
    delay_pedestrian()
    a =time.strftime("%M:%S", time.gmtime())
    print(f"pedestrian {pid} leaving the bridge. ", a)
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. ", a)



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()
