import sys
import traceback as tb


def trace(frame, event, arg):
    # Requires Python >= 3.7
    frame.f_trace_opcodes = True

    print(f"[MDB] {event} event. Current call stack:")
    tb.print_stack(frame)

    while True:
        cmd = input(">>> ").strip()
        if not cmd:
            break
        try:
            exec(cmd, frame.f_globals, frame.f_locals)
        except Exception as e:
            print(e)

    return trace


sys.settrace(trace)


def foo(a):
    print("hello world", a)
    return a


def main():
    a = 42
    foo(a << 1)


if __name__ == "__main__":
    main()
