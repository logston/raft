import time

import keyboard


def change_state():
    out1, out2 = 'G', 'R'

    while True:
        if out1 == 'G' and out2 == 'R':
            out1, out2 = 'Y', 'R'

        elif out1 == 'Y' and out2 == 'R':
            out1, out2 = 'R', 'G'

        elif out1 == 'R' and out2 == 'G':
            out1, out2 = 'R', 'Y'

        elif out1 == 'R' and out2 == 'Y':
            out1, out2 = 'G', 'R'

        yield out1, out2


def sleep(cycles):
    for i in range(cycles):
        time.sleep(0.5)
        yield i


def get_button():
    pressed = keyboard.is_pressed('space')
    if pressed:
        print('Button was pressed')

    return pressed


def cycle():
    state_machine = change_state()
    button = False

    while True:
        out1, out2 = next(state_machine)
        print(out1, out2)

        if out1 == 'G' and out2 == 'R':
            for i in sleep(6):
                if not button:
                    button = get_button()
                if button and i > 2:
                    button = False
                    break

        elif out1 == 'Y' and out2 == 'R':
            for i in sleep(1):
                pass

        elif out1 == 'R' and out2 == 'G':
            for i in sleep(2):
                pass

        elif out1 == 'R' and out2 == 'Y':
            for i in sleep(1):
                pass


if __name__ == '__main__':
    cycle()

