import sys
from bytecode import Bytecode, Instr


def inject(f, hook, lineno):
    bc = Bytecode.from_code(f.__code__)

    for i, instr in enumerate(bc):
        if instr.lineno == lineno:
            break
    else:
        raise ValueError(f"Line {lineno} not found")

    bc[i:i] = [
        Instr("LOAD_CONST", hook),
        Instr("CALL_FUNCTION", 0),
        Instr("POP_TOP"),
    ]

    f.__code__ = bc.to_code()


def foo(a):
    print("hello world", a)
    return a


def hook():
    import traceback as tb
    frame = sys._getframe(1)
    print("Call stack:")
    tb.print_stack(frame)
    print("locals:", frame.f_locals)


def main():
    print("Calling foo(42)...")
    foo(42)
    
    inject(foo, hook, 25)
    
    print("Calling foo(42) after hook injection ...")
    foo(42)


if __name__ == "__main__":
    main()
