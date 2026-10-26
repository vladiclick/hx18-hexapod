#!/usr/bin/env python3
"""Interactive commands with250ms PING; never arms automatically."""
import argparse
import threading
import time
import serial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('port')
    args = parser.parse_args()
    stop = threading.Event()
    lock = threading.Lock()
    with serial.Serial(args.port, 115200, timeout=0.1, write_timeout=0.5) as port:
        def send(command):
            value = command.strip()
            if len(value) > 70 or '\n' in value or '\r' in value:
                raise ValueError('One short command per line')
            with lock:
                port.write((value + '\n').encode('ascii'))

        def service():
            next_ping = time.monotonic()
            try:
                while not stop.is_set():
                    now = time.monotonic()
                    if now >= next_ping:
                        send('PING')
                        next_ping = now + 0.25
                    reply = port.readline()
                    if reply:
                        print(reply.decode('utf-8', errors='replace').rstrip(), flush=True)
            except (serial.SerialException, OSError) as exc:
                print(f'Serial stopped: {exc}', flush=True)
                stop.set()

        worker = threading.Thread(target=service, daemon=True)
        worker.start()
        print('Heartbeat active; use STATUS. No automatic ARM. Ctrl+C sends DISARM.')
        try:
            while not stop.is_set():
                send(input('> '))
        except (EOFError, KeyboardInterrupt):
            pass
        finally:
            stop.set()
            worker.join(timeout=1)
            try:
                send('DISARM')
            except (serial.SerialException, OSError):
                pass


if __name__ == '__main__':
    main()
