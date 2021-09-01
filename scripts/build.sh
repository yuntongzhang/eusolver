#!/bin/bash

EUSOLVER_ROOT=`pwd`

# Build libeusolver
pushd "$EUSOLVER_ROOT"/thirdparty/libeusolver/build
cmake ..
make
LIBEUSOLVER_PYTHON_PATH="$EUSOLVER_ROOT"/thirdparty/libeusolver/build
popd

# Check for existence of pyparsing
if python3 -c "import pyparsing"; then
	echo "Found pyparsing"
else
	echo "Did not find pyparsing; Attempting to install using pip3"
	python3 -m pip install pyparsing
	if [ $? -eq 0 ]; then
		echo "pyparsing installed successfully..."
	else
		echo "[ERROR] Cannot install pyparsing"
		exit 1
	fi
fi
cd $EUSOLVER_ROOT

EXEC_SCRIPT="
#!/bin/bash

PYTHONPATH=$LIBEUSOLVER_PYTHON_PATH:"'$PYTHONPATH'" python3 src/benchmarks.py "'$@'"

# EOF
"
echo "Writing executable script..."
cat > eusolver <<< "$EXEC_SCRIPT"
chmod +x eusolver
