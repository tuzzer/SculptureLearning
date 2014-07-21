import usb.core
import usb.util

import sys
from time import clock
from time import sleep
import copy
import array
import math
import threading


packet_size_in = 64
packet_size_out = 64

def listen_to_Teensy(dev, intf, timeout=100, byte_num=64):

    ep = usb.util.find_descriptor(
        intf,
        # match the first OUT endpoint
        custom_match = \
        lambda e: \
            usb.util.endpoint_direction(e.bEndpointAddress) == \
            usb.util.ENDPOINT_IN)

    assert ep is not None

   # print("release device")
   # usb.util.release_interface(dev, intf)
   # print("claiming device")
   # usb.util.claim_interface(dev, intf)

    try:
        prev_time = clock()
        data = ep.read(byte_num, timeout)
        after_time = clock()
        print("Time to read " + str(byte_num) + " bytes: " + str(after_time-prev_time) + "s")

    except usb.core.USBError:
        print("Timeout! Couldn't read anything")
        data = None

    return data

def talk_to_Teensy(dev, intf, out_msg, timeout=10):

    # print("release device")
    # usb.util.release_interface(dev, intf)
    # print("claiming device")
    # usb.util.claim_interface(dev, intf)

    ep = usb.util.find_descriptor(
        intf,
        # match the first OUT endpoint
        custom_match = \
        lambda e: \
            usb.util.endpoint_direction(e.bEndpointAddress) == \
            usb.util.ENDPOINT_OUT)

    assert ep is not None

    try:
        ep.write(out_msg, timeout)
    except usb.core.USBError:
        print("Timeout! Couldn't write")


def print_data(data):
    if data:
        i = 0
        print("Number of byte: " + str(len(data)))
        while i < len(data):
            char = chr(data[i])
            print(char),
            i +=1

        print('\n')


def listen_and_respond_test(vendorID, productID, serialNumber, loop_num=1000):
    # find our device
    # dev_iter = usb.core.find(find_all=True)#, idVendor=vendorID, idProduct=productID)
    # dev_list = []
    # for iter in dev_iter:
    #     dev_list.append(iter)
    # dev = dev_list[1]
    dev = usb.core.find(idVendor=vendorID, idProduct=productID, serial_number=serialNumber)
    # was it found?
    if dev is None:
        raise ValueError('Device not found')

    # set the active configuration. With no arguments, the first
    # configuration will be the active one
    dev.set_configuration()

    # get an endpoint instance
    cfg = dev.get_active_configuration()

    interface_iter = usb.util.find_descriptor(cfg, find_all=True)
    interface = []
    for iter in interface_iter:
        interface.append(iter)
    intf = interface[0]

    loop_count = 0

    listen_string = "Hello PC! This is Teensy"
    listen_msg = bytearray(listen_string)[:packet_size_in]
    while loop_count < loop_num:


        data = listen_to_Teensy(dev, intf, timeout=0, byte_num=packet_size_in)


        if data:
            correct_msg = True
            for i in range(len(listen_msg)):
                correct_msg &= (listen_msg[i] == data[i])

            print_data(data)

            #intf = interface[0]

            if correct_msg:
                # write the data
                out_string = str(loop_count) + " I heard you Teensy!"
                padding = ' ' *(packet_size_out - len(out_string))
                out_msg = bytearray((out_string + padding)[:packet_size_out])
                #print(out_msg)
                #intf = interface[0]
                print("Sent: " + out_string + padding)
                talk_to_Teensy(dev, intf, out_msg, timeout=0)

                # read reply

                data = listen_to_Teensy(dev, intf, timeout=0, byte_num=packet_size_in)

                if data:
                    print("Replied: "),
                    print_data(data)
                else:
                    print("Received no reply.")


        loop_count += 1

def find_teensy_serial_number(vendorID=0x16C0, productID=0x0486):

    # find our device
    dev_iter = usb.core.find(find_all=True, idVendor=vendorID, idProduct=productID)

    serialNum = []
    for iter in dev_iter:
        serialNum.append(iter.serial_number)

    return tuple(serialNum)


if __name__ == '__main__':

    vendor_id = 0x16C0
    product_id = 0x0486
    serial_num_list = (find_teensy_serial_number(vendorID=vendor_id, productID=product_id))

    for serial_num in serial_num_list:
        ids = ()
        t = threading.Thread(target=listen_and_respond_test, args=(vendor_id, product_id, serial_num, 10000))
        t.daemon = False
        t.start()
        #listen_and_respond_test(vendorID=vendor_id, productID=product_id, serialNumber=serial_num, loop_num=100)

    s = raw_input()
