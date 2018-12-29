# SE-18
Code and tool outputs for CSC510-18 final project

The detailed report of our findings can be found [here](https://github.com/reCursedd/SE-18/blob/master/c_izefak.pdf)
# Pytorch VS TensorFlow
Our work was divided into 4 main parts: 
## Performance: 
We compare Pytorch with 2 variants of
TensorFlow on the tool tqdm. First one is TensorFlow Eager
which creates a dynamic graph similar to Pytorch. The second
one is using Defun with TensorFlow. Defun returns a callable
graph which can then be executed. 
Our results show that TensorFlow outperforms Pytorch in all the metrices for the 2 models we check. 

The code and results can be found under [Performance](https://github.com/reCursedd/SE-18/tree/master/performance) directory 

## Documentation
We wanted to see the understandability and usability of the document of both the project.
Again Tensorflow beats Pytorch, but we intend to conduct a bigger and more diverse survey in future before coming to definite conclusions.

The result can be found in [documentation](https://github.com/reCursedd/SE-18/blob/master/Survey%20Results.docx) file

## Deployment
We checked cross platform deployment using docker on Ubuntu and MacOS. We also check deployment in IOS. Both perform similarly 
and we the code and results are spread accross a few files:
1. [Pytorch Deployment on iOS](https://github.com/reCursedd/SE-18/tree/master/pytorch%20deployment)
2. [TensorFlow Deployment on iOS](https://github.com/reCursedd/SE-18/tree/master/tensorflow%20deployment)
3. [Guide for command line inputs](https://github.com/reCursedd/SE-18/blob/master/dockercode.txt)

## Community 
 We analyzed the Github communnities of each project. We look at various interesting measures
like ’interactions of newcomers’ and ’activity of the contribu-
tors’ using [Foss-Hearthbeat tool](https://github.com/sagesharp/foss-heartbeat). We also look at the code decay or amount
of re-factoring that occurs in the respective code bases since the start of projects to understand the quality of past code and
analyze the rate of growth of code as well using an interesting visualization. It shows us the efforts made by the communities
to keep the code bug-free and add new features.

The installations can be done using the (requirements.txt)[https://github.com/reCursedd/SE-18/blob/master/gitStats/foss-heartbeat/requirements.txt] file
Python library for growth of code can be found at [git-of-theseus](https://github.com/erikbern/git-of-theseus). 
The home grown code and some interesting results can be found at [gitStat](https://github.com/reCursedd/SE-18/tree/master/gitStats) directory. 
