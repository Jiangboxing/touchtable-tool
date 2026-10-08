Before using the demostreet model, you will need to obtain input data from the ALPG. Follow these steps (Linux commands used here)

1. Change directory to the example model folder, e.g. 
> cd workspace/example
Or similar! Check paths, assuming you are in the DEMKit folder here

2. Clone the alpg in the model folder (e.g  in workspace/example/demostreet)
> git clone https://github.com/GENETX/alpg.git

3. Change dir
> cd alpg

4 generate a profile (defaults used)
> ./profilegenerator.py -c example -o demo --force

Now you are done. This example contains the right relative paths to include the ALPG output into the model
