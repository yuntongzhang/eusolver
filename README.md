# eusolver

Fork of the original eusolver. Requires python3.6.

(Forked from: https://github.com/akrasuski1/eusolver-priority)

## Build

Install pre-requisite with:

```bash
sudo apt install cmake python3-pip
python3 -m pip install pyparsing z3-solver==4.8.7.0
```

Build with:

```bash
./scripts/build.sh
```

## Run

To test whether it's running correctly, do:

```bash
./eusolver benchmarks/max/max_2.sl
```

If working correctly, the following should be printed:

```
(define-fun max2 ((a0 Int) (a1 Int)) Int
     (ite (>= a0 a1) a0 a1))
```
