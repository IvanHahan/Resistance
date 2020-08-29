import socketio
import asyncio

# standard Python
loop = asyncio.get_event_loop()
sio = socketio.AsyncClient()


# @sio.event
async def connect():
    print('client connected')


# @sio.on('player_joined')
# async def handle(player_id):
#     await sio.emit('leave_game', (player_id, 2))


# @sio.event
# async def message(msg):
#     print(msg)
#     await sio.disconnect()


async def start_server():
    await sio.connect('http://192.168.0.102:5000/game', )
    await sio.wait()


if __name__ == '__main__':
    loop.run_until_complete(start_server())

