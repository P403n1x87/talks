# Python Debugging

This is not a talk about how to use a debugger. There are plenty of videos and
other resources on how to use the most popular traditional debuggers, such as
`pdb` and `ipdb`. There are also plenty of videos and other resources on how to
use the most popular graphical debuggers, such as `pycharm` and `vscode`.

This is a talk about how most Python debugger work, and some ideas that I've
been thinking about and exploring while working on the topic.

## A Developer's Trinity

I tend to believe that, in software development, there are three fundamental
topics that every developer should be fairly familiar with:

- Tracing
- Profiling
- Debugging

If you really want to write robust and efficient code, you cannot do without
looking into these topics at least once.

Sometimes, the difference among these three topics is not clear-cut. For
example, you can turn a tracing flame chart into a flame graph to get a form of
deterministic profiling. Or you can look at the call stacks in a flame graph and
deduce that there is a bug somewhere, or simply fix a performance issue.

In this talk we are going to focus on debugging.

## Python Debugging, the `pdb` Way

The Python debugger that ships with the standard library is called `pdb`. The
way it works is yet another example of how the lines between tracing and
debugging are blurred. You might know that the `sys` module exposes the
[`settrace`][settrace] function, which allows you to set a callback that will be
invoked when a tracing event, such as a function call, occurs. The `pdb` module
uses this function to implement its debugger. Let's see how.

```python
def trace(frame, event, arg):
    code = frame.f_code

    print(f"[MDB] {event} event. Current call stack:")
    tb.print_stack(frame)

    while True:
        cmd = input(">>> ").strip()
        if not cmd:
            break
        exec(cmd)

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
```

Please be aware that we are targeting the CPython implementation. Some of the
utilities exposed by the `sys` modules are implementation details, and might not
be available in other Python implementations. This is a quote from the Python
docs:

> CPython implementation detail: The settrace() function is intended only for
> implementing debuggers, profilers, coverage tools and the like. Its behavior
> is part of the implementation platform, rather than part of the language
> definition, and thus may not be available in all Python implementations.


## CPython Bytecode

Let's now look at something different. CPython is based on a virtual machine
that uses a stack and evaluates bytecode instructions. The code is first parsed
into an AST, and then compiled into bytecode. Some opcodes have "stack effects",
meaning that they can push or pop values from the stack as a result of their
execution.

If we are using CPython >= 3.7, we can step through the bytecode instructions
with this extra line of code in our tracing function

```python
def trace(frame, event, arg):
    frame.f_trace_opcodes = True  # Requires Python >= 3.7
    code = frame.f_code

    print(f"[MDB] {event} event. Current call stack:")
    tb.print_stack(frame)

    while True:
        cmd = input(">>> ").strip()
        if not cmd:
            break
        exec(cmd)

    return trace
```

With a bit of extra work, we can easily get [a bytecode-level debugger][podb].
Modules compile to bytecode that defines all the objects (e.g. classes and
functions) declared within it. Then most of the code objects can be found as the
`__code__` attribute of each function. Function objects are essentially metadata
holders for the actual instructions to execute. Interestingly enough, they are
_mutable_, and we can have a bit of fun with this

```python
def foo():
    print("I'm foo")

def bar():
    print("I'm bar")

def main():
    foo.__code__, bar.__code__ = bar.__code__, foo.__code__
    foo()
    bar()

if __name__ == "__main__":
    main()
```


## Bytecode-level Injection

If we can so easily modify the code that gets executed by a function, then why
don't we just inject some arbitrary code? In fact, all we have to do is inject
a function call. This will act as a CPython equivalent of traps/interrupts.

We can use this idea for debugging in multiple ways.

- Inject a hook that, when called, takes a snapshot of what was happening at
that time (e.g. call stacks, locals, globals, arguments, ...).
- Inject a hook that runs arbitrary code (e.g. inject print statements).

Let's see how to inject a hook at a random location within a function.

```python
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
```


## The Wilma Approach to Debugging

The idea above of injecting arbitrary code into a Python function is explored
further in my R&D project [Wilma][wilma]. The essential idea is to allow
developers to perform print-statement debugging (a.k.a. caveman debugging) in a
_smarter_ way. That is, instead of modifying your source code, you can use a
separate file to descrive what Python code to inject where. The README on the
project has an example that shows you how you can do just that with Wilma.

If manually adding stuff to a TOML file feels tedious, there is a [VSCode
extension][wilma-vscode] that can help you with that.


[settrace]: https://docs.python.org/3/library/sys.html#sys.settrace
[podb]: https://github.com/p403n1x87/podb
[wilma]: https://github.com/DataDog/wilma
[wilma-vscode]: https://github.com/DataDog/wilma-vscode
