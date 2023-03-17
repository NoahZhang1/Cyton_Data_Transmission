import time
import signal
import numpy as np
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from helper import set_board_channel_settings, set_board_timestamp, set_lead_off
import struct
import asyncio
import csv

# import socketio
# sio = socketio.AsyncClient()
# ws_url = 'http://127.0.0.1:8080'

# @sio.event
# async def connect():
    # print('connected to server')

# @sio.event
# async def disconnect():
    # print('disconnected from server')
# NUM_OF_SECS_TO_COLLECT = 5



output = open(f"D:/BrainLab_Stuff/Canine_EEG_Data/output_{int(time.time())}.csv", "w")

def prepOpenBCIBoard():
    BoardShim.enable_dev_board_logger()
    params = BrainFlowInputParams()
    # params.serial_port = '/dev/ttyUSB0'
    params.serial_port = 'COM3'
    # params.serial_port = '/dev/ttyDUMMY'
    cyton_id = BoardIds['CYTON_BOARD']
    global board_shim
    global sample_rate
    global exg_channels
    global accel_channels
    global timestamp_s_channel
    board_shim = BoardShim(cyton_id, params)
    timestamp_s_channel = [15, 16, 17, 18]
    sample_rate = board_shim.get_sampling_rate(cyton_id)
    exg_channels = board_shim.get_exg_channels(cyton_id)
    accel_channels = board_shim.get_accel_channels(cyton_id)
    num_channel = board_shim.get_package_num_channel(cyton_id)

    # print(timestamp_channel)
    # print(exg_channels)
    # print(accel_channels)
    # print(exg_channels + accel_channels + [timestamp_channel])

    # exit()
    board_shim.prepare_session()
    for channel_i in range(1, len(exg_channels)):
        set_board_channel_settings(board_shim, channel_i)
    set_board_timestamp(board_shim, True)
    set_lead_off(board_shim, 4)


async def brainFlowStream():
    global board_shim
    global sample_rate
    global exg_channels
    global accel_channels
    global timestamp_s_channel
    global output
    sample_interval = 1 / sample_rate
    sample_interval_e_margin = sample_interval * 0.5
    board_shim.start_stream()
    # prev_buff_time = time.time()
    # for i in range(1000000000):
    #     data = np.array(board_shim.get_board_data())
    #     if data.size > 1:
    #         timestamp = data[timestamp_channel, 0]
    #         print(prev_time, timestamp)
    #         print(prev_time - timestamp)
    #         prev_time = timestamp
    csv_output = csv.writer(output, delimiter=',', lineterminator='\n')
    csv_output.writerow(['timestamp_ms', 'channel_0', 'channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7'])
    while True:
        data = np.array(board_shim.get_board_data())
        if data.size > 0:
            for frame_i in range(data.shape[1]):
                timestamp_ms_raw = np.array(data[timestamp_s_channel, frame_i], dtype=np.uint8)
                timestamp_ms = (struct.unpack('>I', struct.pack('BBBB', *timestamp_ms_raw))[0])
                print(f'Got data at device time: {timestamp_ms:.5f}s')
                EXG_data = data[exg_channels, frame_i]
                EXG_data = EXG_data.tolist()
                EXG_data.insert(0, timestamp_ms)
                csv_output.writerow(EXG_data)
        await asyncio.sleep(0)

# async def ws_connect():
    # await sio.connect(ws_url)
    # await sio.wait()

async def main():
    prepOpenBCIBoard()
    # asyncio.ensure_future(brainFlowStream())
    # await ws_connect()
    await brainFlowStream()

def exit_handler(signum, frame):
    print('ctrl-c received! Closing session and exiting')
    global board_shim
    global output
    set_board_timestamp(board_shim, False)
    board_shim.stop_stream()
    board_shim.release_session()
    output.close()
    exit()

signal.signal(signal.SIGINT, exit_handler)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
