import socketio
import asyncio

# standard Python
loop = asyncio.get_event_loop()
sio = socketio.AsyncClient()


@sio.event
async def connect():
    await sio.emit('join_game', ('Ivan', 2))


@sio.on('player_joined')
async def handle(player_id):
    await sio.emit('leave_game', (player_id, 2))


@sio.event
async def message(msg):
    print(msg)


async def start_server():
    await sio.connect('http://localhost:5000')
    await sio.wait()


if __name__ == '__main__':
    loop.run_until_complete(start_server())

